use std::collections::HashMap;
use std::fs;
use std::os::unix::process::ExitStatusExt;
use std::path::PathBuf;
use std::time::Duration;
use std::time::Instant;

use anyhow::{Context, Result};
use clap::Parser;
use clap_verbosity_flag::{InfoLevel, Verbosity};
use rand::Rng;
use regex::Regex;
use tree_sitter::Language;
use tree_sitter::Tree;
use tree_splicer::splice::{Config, Splicer};
use treereduce::Check;
use treereduce::CmdCheck;

/// An easy-to-use grammar-based black-box fuzzer
#[derive(Clone, Debug, clap::Parser)]
#[command(author, version, about, long_about = None)]
pub struct Args {
    /// Percent of "chaotic" mutations - may introduce syntax errors
    #[arg(help_heading = "Mutation options", short, long, default_value_t = 5)]
    pub chaos: u8,

    /// Percent of deletion mutations - the rest are splices
    #[arg(help_heading = "Mutation options", long, default_value_t = 5)]
    pub deletions: u8,

    /// Approximate maximum file size to produce (bytes); default = 1MiB
    #[arg(help_heading = "Mutation options", long, default_value_t = 1048576)]
    pub max_size: usize,

    /// Number of mutations per test
    #[arg(help_heading = "Mutation options", short, long, default_value_t = 16)]
    pub mutations: usize,

    /// Use Radamsa for mutations; ignore all other mutation options
    #[cfg(feature = "radamsa")]
    #[arg(help_heading = "Mutation options", short, long)]
    pub radamsa: bool,

    /// Run a single thread and show stdout, stderr of target
    #[arg(short, long)]
    pub debug: bool,

    /// Exit code to consider interesting
    #[arg(help_heading = "Interestingness check options",
          long, default_values_t = Vec::<i32>::new(), value_name = "CODE")]
    interesting_exit_code: Vec<i32>,

    /// Regex to match interesting stdout
    #[arg(
        help_heading = "Interestingness check options",
        long,
        value_name = "REGEX"
    )]
    interesting_stdout: Option<String>,

    /// Regex to match interesting stderr
    #[arg(
        help_heading = "Interestingness check options",
        long,
        value_name = "REGEX"
    )]
    interesting_stderr: Option<String>,

    /// Regex to match *uninteresting* stdout, overrides interesting regex
    #[arg(
        help_heading = "Interestingness check options",
        long,
        value_name = "REGEX",
        requires = "interesting_stdout"
    )]
    uninteresting_stdout: Option<String>,

    /// Regex to match *uninteresting* stderr, overrides interesting regex
    #[arg(
        help_heading = "Interestingness check options",
        long,
        value_name = "REGEX",
        requires = "interesting_stderr"
    )]
    uninteresting_stderr: Option<String>,

    /// Number of threads
    #[arg(short, long, default_value_t = num_cpus::get())]
    pub jobs: usize,

    /// Directory to output to
    #[arg(short, long, default_value_os = "tree-crasher.out")]
    pub output: PathBuf,

    /// Seed
    #[arg(short, long, default_value_t = 0)]
    pub seed: u64,

    /// Timeout (ms)
    #[arg(long, default_value_t = 500)]
    pub timeout: u64,

    #[clap(flatten)]
    verbose: Verbosity<InfoLevel>,

    /// Input files
    #[arg(value_name = "DIR", required = true)]
    pub files: String,

    /// Interestingness check; fed test case on stdin or via '@@' file
    #[arg(value_name = "CMD", required = true, num_args = 1..)]
    pub check: Vec<String>,
}

fn read_file(file: &PathBuf) -> Result<String> {
    fs::read_to_string(file).with_context(|| format!("Failed to read file {}", file.display()))
}

fn parse(language: Language, code: &str) -> Result<Tree> {
    let mut parser = tree_sitter::Parser::new();
    parser
        .set_language(language)
        .context("Failed to set tree-sitter parser language")?;
    parser.parse(code, None).context("Failed to parse code")
}

#[allow(clippy::too_many_arguments)]
fn make_check(
    debug: bool,
    timeout: Duration,
    check: Vec<String>,
    mut interesting_exit_codes: Vec<i32>,
    interesting_stdout: Option<String>,
    interesting_stderr: Option<String>,
    uninteresting_stdout: Option<String>,
    uninteresting_stderr: Option<String>,
) -> Result<CmdCheck> {
    if check.is_empty() {
        eprintln!("Internal error: empty interestingness check!");
        std::process::exit(1);
    }
    let mut argv: Vec<_> = check.iter().collect();
    let cmd = argv[0];
    argv.remove(0);
    let stdout_regex = match &interesting_stdout {
        Some(r) => Some(Regex::new(r).context("Invalid interesting stdout regex")?),
        None => None,
    };
    let stderr_regex = match &interesting_stderr {
        Some(r) => Some(Regex::new(r).context("Invalid interesting stderr regex")?),
        None => None,
    };
    let un_stdout_regex = match &uninteresting_stdout {
        Some(r) => Some(Regex::new(r).context("Invalid uninteresting stdout regex")?),
        None => None,
    };
    let un_stderr_regex = match &uninteresting_stderr {
        Some(r) => Some(Regex::new(r).context("Invalid uninteresting stderr regex")?),
        None => None,
    };
    interesting_exit_codes.extend(128..256);
    Ok(CmdCheck::new(
        cmd.clone(),
        argv.iter().map(|s| (*s).clone()).collect(),
        interesting_exit_codes,
        None,
        stdout_regex,
        stderr_regex,
        un_stdout_regex,
        un_stderr_regex,
        debug,
        debug,
        Some(timeout),
    ))
}

const BATCH: usize = 100_000; // not all materialized at once

fn check(
    language: Language,
    node_types: &treereduce::NodeTypes,
    chk: &CmdCheck,
    inp: &[u8],
) -> i32 {
    let state = match chk.start(inp) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Problem when running target: {e}");
            return -1;
        }
    };
    let (interesting, status, stdout, stderr) = chk.wait_with_output(state).unwrap();
    let code = status.and_then(|s| s.code()).unwrap_or(-1);
    let sig = status.and_then(|s| s.signal());
    if interesting || sig.is_some() {
        if let Some(s) = sig {
            if s == 6 {
                return code;
            }
            eprintln!("signal {s}!");
        } else {
            eprintln!("interesting!");
        }
        let mut rng = rand::rng();
        let i = rng.random_range(0..10192);
        fs::write(format!("tree-crasher-{i}.out"), inp).unwrap();
        fs::write(format!("tree-crasher-{i}.stdout"), stdout).unwrap();
        fs::write(format!("tree-crasher-{i}.stderr"), stderr).unwrap();
        let tree = parse(language, &String::from_utf8_lossy(inp)).unwrap();
        match treereduce::treereduce_multi_pass(
            language,
            node_types,
            treereduce::Original::new(tree, inp.to_vec()),
            &treereduce::Config {
                check: chk.clone(),
                delete_non_optional: true,
                jobs: 1,
                min_reduction: 2,
                replacements: HashMap::new(),
            },
            Some(8),
        ) {
            Err(e) => eprintln!("Failed to reduce! {e}"),
            Ok((reduced, _)) => {
                fs::write(format!("tree-crasher-{i}.reduced.out"), reduced.text).unwrap();
            }
        }
    }
    code
}

// TODO: print executions/sec
fn job(
    language: Language,
    // HACK: there should be another crate that deals with this...
    node_types1: &treereduce::NodeTypes,
    node_types2: &tree_splicer::node_types::NodeTypes,
    args: &Args,
    files: &HashMap<String, (Vec<u8>, Tree)>,
    chk: CmdCheck,
) {
    if files.is_empty() {
        eprintln!("No files provided.");
        return;
    }
    #[cfg(feature = "radamsa")]
    if args.radamsa {
        unsafe { radamsa_sys::radamsa_init() };
        let mut rng = rand::rng();
        let file_bytes: Vec<_> = files.values().map(|(bytes, _tree)| bytes).collect();
        loop {
            const MAX_SIZE: usize = 4096;
            // TODO: Mutate in-place
            let mut input: Vec<u8> = file_bytes
                .get(rng.random_range(0..files.len()))
                .unwrap()
                .to_vec();
            let mut mutant = vec![0u8; MAX_SIZE];
            let out_len = unsafe {
                radamsa_sys::radamsa(
                    input.as_mut_ptr(),
                    input.len(),
                    mutant.as_mut_ptr(),
                    MAX_SIZE,
                    0,
                )
            };
            assert!(out_len <= MAX_SIZE);
            mutant.truncate(out_len);
            check(language, node_types1, &chk, &mutant);
        }
    }
    loop {
        let config = Config {
            chaos: args.chaos,
            deletions: args.deletions,
            language,
            // intra_splices: 10,
            inter_splices: args.mutations,
            node_types: node_types2.clone(),
            max_size: args.max_size,
            reparse: usize::MAX,
            seed: args.seed,
        };
        let start = Instant::now();
        let mut execs = 0;
        for (i, out) in Splicer::new(config, files).enumerate() {
            if i == BATCH {
                break;
            }
            let _code = check(language, node_types1, &chk, &out);
            execs += 1;
            let secs = start.elapsed().as_secs();
            if execs % 10_000 == 0 {
                println!("execs/sec: {}", execs / secs);
            }
        }
    }
}

// TODO: graceful exit
pub fn main(language: Language, node_types_json_str: &'static str) -> Result<()> {
    let args = Args::parse();
    debug_assert!(args.interesting_stdout.is_some() || args.uninteresting_stdout.is_none());
    debug_assert!(args.interesting_stderr.is_some() || args.uninteresting_stderr.is_none());

    if args.debug {
        eprintln!("Loading testcases...");
    }
    let mut files = HashMap::new();
    // TODO error messages
    for entry in fs::read_dir(&args.files)
        .with_context(|| format!("When reading tests from {}", args.files))?
    {
        let entry = entry?;
        let path = entry.path();
        if let Ok(s) = read_file(&path) {
            let tree = parse(language, &s)?;
            files.insert(String::from(path.to_string_lossy()), (s.into_bytes(), tree));
        }
    }
    let chk = make_check(
        args.debug,
        Duration::from_millis(args.timeout),
        args.check.clone(),
        args.interesting_exit_code.clone(),
        args.interesting_stdout.clone(),
        args.interesting_stderr.clone(),
        args.uninteresting_stdout.clone(),
        args.uninteresting_stderr.clone(),
    )?;
    let node_types1 = treereduce::NodeTypes::new(node_types_json_str).unwrap();
    let node_types2 = tree_splicer::node_types::NodeTypes::new(node_types_json_str).unwrap();

    if args.debug {
        eprintln!("Spawning threads...");
    }
    #[cfg(not(feature = "radamsa"))]
    let jobs = if args.debug { 1 } else { args.jobs };
    #[cfg(feature = "radamsa")]
    let jobs = if args.debug {
        if args.jobs != 1 {
            eprintln!("[WARN] Radamsa can only be used with one thread.");
        }
        1
    } else {
        args.jobs
    };
    std::thread::scope(|s| {
        for _ in 0..jobs {
            s.spawn(|| {
                job(
                    language,
                    &node_types1,
                    &node_types2,
                    &args,
                    &files,
                    chk.clone(),
                );
            });
        }
    });

    Ok(())
}

#!/usr/bin/env python

"""Run formatters and linters incrementally and in parallel using Ninja"""

# TODO: rumdl

# Ninja is essentially a simpler, faster version of Make. A Ninja configuration
# consists of *rules* (`rule`) and some number of *build statements* (`build`).
# A rule is an abbreviation for a shell command, and a build statement is a
# recipe for producing some number of output files (*targets*) from some number
# of input files by running a rule.
#
# Conceptually, we can consider the Ninja configuration as a hypergraph where
# the nodes are files and the hyperedges are build statements, labeled by rules.
# The inputs to Ninja are this hypergraph and a set of desired targets. Ninja
# traverses the hypergraph and recursively runs rules to build everything until
# it can build the desired targets.
#
# Just like Make, Ninja checks *file modification times* to see if rebuilding
# is necessary. If the output was modified more recently than all of the inputs
# (according to filesystem metadata), then Ninja will skip rebuilding that
# target.
#
# See ninja.build for more information about Ninja.
#
# This script generates Ninja configurations to run linters. It works by
# generating build statements that produce one target file (in `.out/`) for each
# combination of linter and input files. For example, for a file `foo/bar.py`
# and the linter `ruff`, it would generate a `build` statement like
#
#     build .out/foo/bar.py: ruff-check foo/bar.py
#
# where the `ruff-check` rule is something like:
#
#     rule ruff-check
#       command = ruff check -- $in && touch $out
#
# Together, these say "to produce output file `.out/foo-bar.py`, run `ruff
# check` on `foo/bar.py` and then (if it succeeds) `touch foo-bar.py`". Hence,
# the rules produce empty output files in `.out/` indicating that the linter has
# been run.
#
# To run on every change:
#
#     git ls-files | entr -c -s './scripts/lint/lint.py --format'
#
# As a git pre-commit hook:
#
#     cat <<'EOF' > .git/hooks/pre-commit
#     #!/usr/bin/env bash
#     ./scripts/lint/lint.py
#     EOF
#     chmod +x .git/hooks/pre-commit

from argparse import ArgumentParser
from dataclasses import dataclass
from os import environ
from pathlib import Path
from subprocess import run
from textwrap import dedent
from typing import NewType, cast

NinjaScript = NewType("NinjaScript", str)


@dataclass
class NinjaScripts:
    lint: NinjaScript
    fix: NinjaScript
    format: NinjaScript


def build(ninja: NinjaScript, out: str, rule: str, ins: str, /) -> NinjaScript:
    assert " " not in out
    ninja = cast(NinjaScript, ninja + f"build $builddir/{out}: {rule} {ins}\n")
    return ninja


def rules(ninja: NinjaScript, rule_def: str) -> NinjaScript:
    return cast(NinjaScript, ninja + dedent(rule_def))


def lint(ninja: NinjaScript, rule: str, ins: str, /) -> NinjaScript:
    # replace directory separators `/` with hyphens `-`
    slug = ins.replace("/", "-") + "." + rule
    return build(ninja, slug, rule, ins)


def ls_files(pats: list[str]) -> list[str]:
    for pat in pats:
        assert pat in ALL_PATS, f"{pat} not in {ALL_PATS}"
    out = run(
        ["git", "ls-files", "--exclude-standard", "--"] + pats,
        capture_output=True,
        shell=False,
    )
    stdout = out.stdout.strip()
    if stdout == b"":
        return []
    return stdout.decode("utf-8").split("\n")


def txt_lint(ninja: NinjaScript, path: str) -> NinjaScript:
    if environ.get("CI") is None:
        # requires rg
        ninja = lint(ninja, "bom", path)
        ninja = lint(ninja, "crlf", path)
    ninja = lint(ninja, "merge", path)
    ninja = lint(ninja, "ws", path)
    return ninja


def txt_format(ninja: NinjaScript, path: str) -> NinjaScript:
    ninja = lint(ninja, "ws-fix", path)
    return ninja


# ---------------------------------------------------------


def bash(scripts: NinjaScripts) -> NinjaScripts:
    bash = ls_files(["*.bash"])
    if bash == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule bash-n
      command = bash -n -- $in && touch $out
      description = bash -n

    rule bash-sc
      command = shellcheck --shell=bash -- $in && touch $out
      description = shellcheck
    """,
    )
    for path in bash:
        scripts.lint = lint(scripts.lint, "bash-n", path)
        scripts.lint = lint(scripts.lint, "bash-sc", path)
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def _gha(scripts: NinjaScripts) -> NinjaScripts:
    gha = ls_files([".github/**/*.yml"])
    if gha == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule zizmor
      command = zizmor --quiet -- $in && touch $out
      description = zizmor
    """,
    )
    scripts.fix = rules(
        scripts.fix,
        """
    rule zizmor-fix
      command = zizmor --fix=safe -- $in && touch $out
      description = zizmor --fix=safe
    """,
    )
    for path in gha:
        if path.endswith("workflows/dependabot.yml"):
            # https://github.com/zizmorcore/zizmor/issues/1341
            continue
        scripts.lint = lint(scripts.lint, "zizmor", path)
        scripts.fix = lint(scripts.fix, "zizmor-fix", path)
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def json(scripts: NinjaScripts) -> NinjaScripts:
    json = ls_files(["*.json"])
    if json == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule jq
      command = jq null -- $in > /dev/null && touch $out
      description = jq
    """,
    )
    for path in json:
        scripts.lint = lint(scripts.lint, "jq", path)
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def make(scripts: NinjaScripts) -> NinjaScripts:
    make = ls_files(["**/Makefile"])
    if make == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule make-n
      command = make -n -f $$in && touch $out
      description = make -n
    """,
    )
    for path in make:
        scripts.lint = lint(scripts.lint, "make-n", path)
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def md(scripts: NinjaScripts) -> NinjaScripts:
    md = ls_files(["*.md"])
    if md == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule mdlynx
      command = mdlynx $in && touch $out
      description = mdlynx

    rule typos
      command = typos $in && touch $out
      description = typos
    """,
    )
    scripts.fix = rules(
        scripts.fix,
        """
    rule typos-fix
      command = typos --write-changes -- $in && touch $out
      description = typos --write-changes
    """,
    )
    for path in md:
        scripts.lint = lint(scripts.lint, "mdlynx", path)
        scripts.lint = lint(scripts.lint, "typos", path)
        scripts.fix = lint(scripts.fix, "typos-fix", path)
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def nix(scripts: NinjaScripts) -> NinjaScripts:
    nix = ls_files(["*.nix"])
    if nix == []:
        return scripts

    for path in nix:
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def py(scripts: NinjaScripts) -> NinjaScripts:
    py = ls_files(["*.py"])
    if py == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule mypy
      command = mypy --no-error-summary --strict -- $in && touch $out
      description = mypy

    rule py
      command = ./scripts/lint/py.py -- $in && touch $out
      description = python style

    rule ruff-check
      command = ruff check --quiet -- $in && touch $out
      description = ruff check

    rule ruff-fmt-check
      command = ruff format --check --quiet -- $in && touch $out
      description = ruff format --check
    """,
    )
    scripts.fix = rules(
        scripts.fix,
        """
    rule ruff-check-fix
      command = ruff check --fix -- $in && touch $out
      description = ruff check --fix
    """,
    )
    scripts.format = rules(
        scripts.format,
        """
    rule ruff-fmt
      command = ruff format --quiet -- $in && touch $out
      description = ruff format
    """,
    )
    for path in py:
        if Path(path).read_text().startswith("# noqa"):
            continue
        scripts.lint = lint(scripts.lint, "mypy", path)
        scripts.lint = lint(scripts.lint, "ruff-check", path)
        scripts.lint = lint(scripts.lint, "ruff-fmt-check", path)
        scripts.lint = lint(scripts.lint, "py", path)
        scripts.fix = lint(scripts.fix, "ruff-check-fix", path)
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = lint(scripts.format, "ruff-fmt", path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def rs(scripts: NinjaScripts) -> NinjaScripts:
    cargo = ls_files(["**/Cargo.toml"])
    rs = ls_files(["*.rs"])
    if rs == []:
        return scripts

    cd = ""
    if len(cargo) == 1:
        cd = "cd " + str(Path(cargo[0]).parent) + "; "
    root = Path(__file__).absolute().parent.parent.parent

    scripts.lint = rules(
        scripts.lint,
        f"""
    rule cargo-clippy
      command = {cd}cargo clippy --all-targets --quiet -- --deny warnings && touch {root}/$out
      description = cargo clippy

    rule cargo-fmt-check
      command = {cd}cargo fmt --check && touch {root}/$out
      description = cargo fmt --check
    """,
    )
    scripts.fix = rules(
        scripts.fix,
        f"""
    rule cargo-clippy-fix
      command = {cd}cargo clippy  --all-targets --allow-dirty --fix --quiet -- --deny warnings && touch {root}/$out
      description = cargo clippy --fix
    """,
    )
    scripts.format = rules(
        scripts.format,
        f"""
    rule cargo-fmt
      command = {cd}cargo fmt && touch {root}/$out
      description = cargo fmt
    """,
    )
    scripts.lint = build(
        scripts.lint, "cargo-clippy", "cargo-clippy", " ".join(cargo + rs)
    )
    scripts.lint = build(
        scripts.lint, "cargo-fmt-check", "cargo-fmt-check", " ".join(rs)
    )
    scripts.format = build(scripts.format, "cargo-fmt", "cargo-fmt", " ".join(rs))
    scripts.fix = build(
        scripts.fix, "cargo-clippy-fix", "cargo-clippy-fix", " ".join(cargo + rs)
    )
    for path in rs:
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def sh(scripts: NinjaScripts) -> NinjaScripts:
    sh = ls_files(["*.sh", "files/scripts/bin/*"])
    if sh == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule sc
      command = shellcheck --shell=bash -- $in && touch $out
      description = shellcheck
    """,
    )
    for path in sh:
        scripts.lint = lint(scripts.lint, "sc", path)
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def toml(scripts: NinjaScripts) -> NinjaScripts:
    toml = ls_files(["*.toml"])
    if toml == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule taplo-format-check
      command = taplo format --check --diff | grep -v 'found files' -- $in && touch $out
      description = taplo format --check
    """,
    )
    scripts.format = rules(
        scripts.format,
        """
    rule taplo-format
      command = taplo format -- $in && touch $out
      description = taplo format
    """,
    )
    for path in toml:
        scripts.lint = lint(scripts.lint, "taplo-format-check", path)
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = lint(scripts.format, "taplo-format", path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


def zsh(scripts: NinjaScripts) -> NinjaScripts:
    zsh = ls_files(["*.zsh"])
    if zsh == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule zsh-n
      command = zsh -n -- $in && touch $out
      description = zsh -n

    rule zsh-sc
      command = shellcheck --shell=bash -- $in && touch $out
      description = shellcheck
    """,
    )
    for path in zsh:
        scripts.lint = lint(scripts.lint, "zsh-n", path)
        scripts.lint = lint(scripts.lint, "zsh-sc", path)
        scripts.lint = txt_lint(scripts.lint, path)
        scripts.format = txt_format(scripts.format, path)
    return scripts


ALL_PATS = [
    "*.bash",
    "*.cabal",
    "**/Cargo.toml",
    "files/scripts/bin/*",
    ".github/**/*.yml",
    "*.hs",
    "*.json",
    "**/Makefile",
    "*.md",
    "*.mk",
    "*.nix",
    "*.project",
    "*.py",
    "*.rs",
    "*.scala",
    "*.sh",
    "*.toml",
    "*.zsh",
]


def xref(scripts: NinjaScripts) -> NinjaScripts:
    files = ls_files(ALL_PATS)
    if files == []:
        return scripts

    scripts.lint = rules(
        scripts.lint,
        """
    rule xref
      command = ./scripts/lint/xref.py -- $in && touch $out
      description = xref
    """,
    )
    scripts.lint = build(scripts.lint, "xref", "xref", " ".join(files))
    return scripts


def ok(ninja: NinjaScript) -> None:
    if environ.get("CI") is not None:
        return
    rule_names = [
        line.split()[1] for line in ninja.splitlines() if line.startswith("rule")
    ]
    for rule in rule_names:
        ok = False
        for line in ninja.splitlines():
            if line.startswith("build") and f": {rule}" in line:
                ok = True
                break
        assert ok, f"{rule} not in any `build` lines"


def go(do_format: bool, do_fix: bool) -> None:
    lint = NinjaScript(
        dedent(r"""
    builddir=.out/

    rule bom
      command = rg '\xEF\xBB\xBF' -- $in && exit 1 || touch $out
      description = check for utf-8 byte-order mark

    rule crlf
      command = rg --multiline '\r\n' -- $in && exit 1 || touch $out
      description = check for crlf

    rule merge
      command = grep -E '^(<<<<<<<|=======|>>>>>>>)' -- $in && exit 1 || touch $out
      description = check for merge conflict markers

    rule ws
      command = ./scripts/lint/whitespace.py -- $in && touch $out
      description = whitespace
    """)
    )
    fix = NinjaScript(
        dedent(r"""
    builddir=.out/
    """)
    )
    format = NinjaScript(
        dedent(r"""
    builddir=.out/

    rule ws-fix
      command = ./scripts/lint/whitespace.py --fix -- $in && touch $out
      description = whitespace --fix
    """)
    )
    scripts = NinjaScripts(lint, fix, format)
    scripts = bash(scripts)
    # TODO
    # scripts = gha(scripts)
    scripts = json(scripts)
    scripts = md(scripts)
    scripts = make(scripts)
    scripts = nix(scripts)
    scripts = py(scripts)
    scripts = rs(scripts)
    scripts = sh(scripts)
    scripts = toml(scripts)
    scripts = xref(scripts)
    ok(scripts.lint)
    ok(scripts.fix)
    ok(scripts.format)
    Path("lint.ninja").write_text(scripts.lint)
    Path("fix.ninja").write_text(scripts.fix)
    Path("format.ninja").write_text(scripts.format)
    if do_fix:
        run(["ninja", "-f", "fix.ninja"], check=True)
    if do_format:
        run(["ninja", "-f", "format.ninja"], check=True)
    run(["ninja", "-f", "lint.ninja"], check=True)


parser = ArgumentParser(description=__doc__)
parser.add_argument("--fix", action="store_true")
parser.add_argument("--format", action="store_true")
args = parser.parse_args()
go(args.format, args.fix)

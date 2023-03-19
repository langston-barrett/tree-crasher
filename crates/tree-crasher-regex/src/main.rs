use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(tree_sitter_regex::language(), tree_sitter_regex::NODE_TYPES)
}

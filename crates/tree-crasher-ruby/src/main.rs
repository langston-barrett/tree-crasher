use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(tree_sitter_ruby::language(), tree_sitter_ruby::NODE_TYPES)
}

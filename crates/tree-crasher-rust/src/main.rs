use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(tree_sitter_rust::language(), tree_sitter_rust::NODE_TYPES)
}

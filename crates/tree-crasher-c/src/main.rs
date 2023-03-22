use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(tree_sitter_c::language(), tree_sitter_c::NODE_TYPES)
}

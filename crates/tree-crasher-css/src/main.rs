use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(tree_sitter_css::language(), tree_sitter_css::NODE_TYPES)
}

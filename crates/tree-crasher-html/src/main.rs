use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(tree_sitter_html::language(), tree_sitter_html::NODE_TYPES)
}

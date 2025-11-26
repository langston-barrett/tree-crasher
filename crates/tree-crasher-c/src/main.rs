use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(tree_sitter_c::LANGUAGE.into(), tree_sitter_c::NODE_TYPES)
}

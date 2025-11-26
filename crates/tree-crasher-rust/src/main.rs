use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_rust::LANGUAGE.into(),
        tree_sitter_rust::NODE_TYPES,
    )
}

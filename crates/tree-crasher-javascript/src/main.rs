use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_javascript::LANGUAGE.into(),
        tree_sitter_javascript::NODE_TYPES,
    )
}

use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_css::LANGUAGE.into(),
        tree_sitter_css::NODE_TYPES,
    )
}

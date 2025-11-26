use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_html::LANGUAGE.into(),
        tree_sitter_html::NODE_TYPES,
    )
}

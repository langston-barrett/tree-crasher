use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_openscad::LANGUAGE.into(),
        tree_sitter_openscad::NODE_TYPES,
    )
}

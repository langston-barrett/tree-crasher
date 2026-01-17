use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_openscad_ng::LANGUAGE.into(),
        tree_sitter_openscad_ng::NODE_TYPES,
    )
}

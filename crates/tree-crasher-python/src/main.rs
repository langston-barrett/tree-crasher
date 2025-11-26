use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_python::LANGUAGE.into(),
        tree_sitter_python::NODE_TYPES,
    )
}

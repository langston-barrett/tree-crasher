use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_python::language(),
        tree_sitter_python::NODE_TYPES,
    )
}

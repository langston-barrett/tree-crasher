use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_typescript::language_typescript(),
        tree_sitter_typescript::TYPESCRIPT_NODE_TYPES,
    )
}

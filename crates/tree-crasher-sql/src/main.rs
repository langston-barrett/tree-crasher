use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(tree_sitter_sql::language(), tree_sitter_sql::NODE_TYPES)
}

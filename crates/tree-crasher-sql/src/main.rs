use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_sequel::LANGUAGE.into(),
        tree_sitter_sequel::NODE_TYPES,
    )
}

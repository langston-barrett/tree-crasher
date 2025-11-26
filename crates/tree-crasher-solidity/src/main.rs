use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(
        tree_sitter_solidity::LANGUAGE.into(),
        tree_sitter_solidity::NODE_TYPES,
    )
}

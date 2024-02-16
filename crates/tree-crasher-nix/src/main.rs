use anyhow::Result;

fn main() -> Result<()> {
    tree_crasher::main(tree_sitter_nix::language(), tree_sitter_nix::NODE_TYPES)
}

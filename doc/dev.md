# Developer's guide

## Build

To install from source, you'll need to install Rust and [Cargo][cargo]. Follow
the instructions on the [Rust installation page][install-rust]. Then, get
the source:

```bash
git clone https://github.com/langston-barrett/tree-crasher
cd tree-crasher
```

Finally, build everything:

```bash
cargo build --release
```

You can find binaries in `target/release`. Run tests with `cargo test`.

[cargo]: https://doc.rust-lang.org/cargo/
[install-rust]: https://www.rust-lang.org/tools/install

## Docs

HTML documentation can be built with [mdBook][mdbook]:

```sh
cd doc
mdbook build
```

[mdbook]: https://rust-lang.github.io/mdBook/

## Format

All code should be formatted with [rustfmt][rustfmt]. You can install rustfmt
with [rustup][rustup] like so:

```sh
rustup component add rustfmt
```

and then run it like this:

```sh
cargo fmt --all
```

[rustfmt]: https://rust-lang.github.io/rustfmt
[rustup]: https://rustup.rs/

## Lint

All code should pass [Clippy][clippy]. You can install Clippy with rustup
like so:

```sh
rustup component add clippy
```

and then run it like this:

```sh
cargo clippy --workspace -- --deny warnings
```

[clippy]: https://doc.rust-lang.org/stable/clippy/

## Release

- Create branch with a name starting with `release`
- Update `CHANGELOG.md`
- Update the version numbers in `./crates/**/Cargo.toml`

  ```sh
  find crates/ -type f -name "*.toml" -print0 | \
    xargs -0 sed -E -i 's/^version = "U.V.W"$/version = "X.Y.Z"/'
  ```

- Run `cargo build --release`
- Commit all changes and push the release branch
- Check that CI was successful on the release branch
- Merge the release branch to `main`
- `git checkout main && git pull origin && git tag -a vX.Y.Z -m vX.Y.Z && git push --tags`
- Verify that the release artifacts work as intended
- Release the pre-release created by CI
- Check that the crates were properly uploaded to crates.io

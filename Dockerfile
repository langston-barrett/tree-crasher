ARG BASE="rustlang/rust:nightly"

FROM rust:1.91 AS build
ARG LANG="rust"
WORKDIR /work
COPY . /work
ENV RUSTFLAGS="-C target-cpu=native"
RUN cargo build --release --package=tree-crasher-${LANG}

FROM ${BASE} AS dist
ARG LANG="rust"
COPY --from=build /work/target/release/tree-crasher-${LANG} /usr/bin
WORKDIR /work
ENV RUST_BACKTRACE=1
ENV RUSTC_ICE=0
ENTRYPOINT ["tree-crasher-rust"]

# docker run \
#   --name tree-crasher \
#   --rm \
#   --interactive \
#   --tty \
#   --cpus=2 \
#   --memory=12g \
#   --memory-swap=0b \
#   --mount "type=bind,src=${PWD}/corpus/,destination=/corpus" \
#   --mount "type=bind,src=${PWD}/out/,destination=/work" \
#   --network=none \
#   tree-crasher-rust \
#   --interesting-stderr "(?m)^error: (internal compiler error:|the compiler unexpectedly panicked|rustc interrupted by SIGSEGV)" \
#   /corpus \ 
#   -- \
#   /usr/local/rustup/toolchains/nightly-x86_64-unknown-linux-gnu/bin/rustc \
#   --crate-type=lib \
#   --emit=mir \
#   -o /dev/null \
#   -Zmir-opt-level=4 \
#   -Zvalidate-mir \
#   @@.rs
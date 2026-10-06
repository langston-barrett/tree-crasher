# docker build -t tree-crasher-ty -f targets/ty.dockerfile .
#
# docker run \
#   --name=tree-crasher-ty \
#   --interactive \
#   --rm \
#   --tty \
#   --cpus=4 \
#   --memory=12g \
#   --memory-swap=12g \
#   --network=none \
#   --mount "type=bind,src=${PWD}/corpus-python/,destination=/corpus" \
#   --mount "type=bind,src=${PWD}/out/,destination=/out" \
#   tree-crasher-ty

FROM rust:1.91
RUN apt-get update && \
  apt-get install --no-install-recommends -y \
  ca-certificates \
  git && \
  rm -rf /var/lib/apt/lists/*
# Clone ruff repository (where ty lives) and build ty from source
RUN git clone --depth 1 https://github.com/astral-sh/ruff /ruff
WORKDIR /ruff
RUN cargo build --bin ty --release
# Install tree-crasher-python
RUN cargo install --locked --git https://github.com/langston-barrett/tree-crasher tree-crasher-python --rev 1c0959df89efeb278553c7923a888b88cab24fae
WORKDIR /work
ENTRYPOINT tree-crasher-python \
  -vvv \
  --output /out \
  /corpus \
  --seed=$(date +%s) \
  --interesting-stderr "(?m)^(Panicked|panic|thread 'main' panicked)" \
  /ruff/target/release/ty check @@.py

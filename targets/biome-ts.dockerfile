# docker build -t tree-crasher-biome-ts -f targets/biome-ts.dockerfile .
#
# docker run \
#   --name=tree-crasher-biome-ts \
#   --interactive \
#   --rm \
#   --tty \
#   --cpus=4 \
#   --memory=12g \
#   --memory-swap=12g \
#   --network=none \
#   --mount "type=bind,src=${PWD}/corpus-ts/,destination=/corpus" \
#   --mount "type=bind,src=${PWD}/out/,destination=/out" \
#   tree-crasher-biome-ts

FROM rust:1.91
RUN apt-get update && \
  apt-get install --no-install-recommends -y \
  ca-certificates \
  curl && \
  rm -rf /var/lib/apt/lists/*
# Install biome
RUN curl -L https://github.com/biomejs/biome/releases/latest/download/biome-linux-x64 -o /usr/local/bin/biome && \
  chmod +x /usr/local/bin/biome
# Install tree-crasher-typescript
RUN cargo install --locked --git https://github.com/langston-barrett/tree-crasher tree-crasher-typescript --rev 1c0959df89efeb278553c7923a888b88cab24fae
WORKDIR /work
ENTRYPOINT tree-crasher-typescript \
  -v \
  --output /out \
  /corpus \
  --seed=$(date +%s) \
  --interesting-stderr "This is a bug in Biome" \
  -- biome check --stdin-file-path=@@.ts

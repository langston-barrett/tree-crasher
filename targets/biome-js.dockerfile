# docker build -t tree-crasher-biome-js -f targets/biome-js.dockerfile .
#
# docker run \
#   --name=tree-crasher-biome-js \
#   --interactive \
#   --rm \
#   --tty \
#   --cpus=4 \
#   --memory=12g \
#   --memory-swap=12g \
#   --network=none \
#   --mount "type=bind,src=${PWD}/corpus-js/,destination=/corpus" \
#   --mount "type=bind,src=${PWD}/out/,destination=/out" \
#   tree-crasher-biome-js

FROM rust:1.91
RUN apt-get update && \
  apt-get install --no-install-recommends -y \
  ca-certificates \
  curl && \
  rm -rf /var/lib/apt/lists/*
# Install biome
RUN curl -L https://github.com/biomejs/biome/releases/latest/download/biome-linux-x64 -o /usr/local/bin/biome && \
  chmod +x /usr/local/bin/biome
# Install tree-crasher-javascript
RUN cargo install --locked --git https://github.com/langston-barrett/tree-crasher tree-crasher-javascript --rev 1c0959df89efeb278553c7923a888b88cab24fae
WORKDIR /work
ENTRYPOINT tree-crasher-javascript \
  -v \
  --output /out \
  /corpus \
  --seed=$(date +%s) \
  --interesting-stderr "This is a bug in Biome" \
  -- biome check --stdin-file-path=@@.js

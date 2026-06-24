# docker build -t tree-crasher-oxc-js -f targets/oxc-js.dockerfile .
#
# docker run \
#   --name=tree-crasher-oxc-js \
#   --interactive \
#   --rm \
#   --tty \
#   --cpus=4 \
#   --memory=12g \
#   --memory-swap=12g \
#   --network=none \
#   --mount "type=bind,src=${PWD}/corpus-js/,destination=/corpus" \
#   --mount "type=bind,src=${PWD}/out/,destination=/out" \
#   tree-crasher-oxc-js

FROM rust:1.91
RUN apt-get update && \
  apt-get install --no-install-recommends -y \
  ca-certificates \
  curl && \
  rm -rf /var/lib/apt/lists/*
# Install Node.js for npm
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
  apt-get install -y nodejs && \
  rm -rf /var/lib/apt/lists/*
# Install oxlint
RUN npm install -g oxlint
# Install tree-crasher-javascript
RUN cargo install --locked --git https://github.com/langston-barrett/tree-crasher tree-crasher-javascript --rev 1c0959df89efeb278553c7923a888b88cab24fae
WORKDIR /work
ENTRYPOINT tree-crasher-javascript \
  -v \
  --output /out \
  /corpus \
  --seed=$(date +%s) \
  --interesting-stderr "panicked at" \
  oxlint @@.js

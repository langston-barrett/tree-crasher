# docker build -t tree-crasher-boa -f targets/boa.dockerfile .
#
# docker run \
#   --name=tree-crasher-boa \
#   --interactive \
#   --rm \
#   --tty \
#   --cpus=4 \
#   --memory=12g \
#   --memory-swap=12g \
#   --network=none \
#   --mount "type=bind,src=${PWD}/corpus/,destination=/corpus" \
#   --mount "type=bind,src=${PWD}/out/,destination=/out" \
#   tree-crasher-boa

FROM rust:1.91
RUN cargo install --locked --git https://github.com/boa-dev/boa boa_cli
RUN cargo install --locked --git https://github.com/langston-barrett/tree-crasher tree-crasher-javascript --rev 1c0959df89efeb278553c7923a888b88cab24fae
ENTRYPOINT tree-crasher-javascript \
  -v \
  --output /out \
  /corpus \
  --seed=$(date +%s) \
  --interesting-stderr "(?m)^thread 'main'" \
  boa

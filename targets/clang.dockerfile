# docker build -t tree-crasher-clang -f targets/clang.dockerfile .
#
# docker run \
#   --name=tree-crasher-clang \
#   --interactive \
#   --rm \
#   --tty \
#   --cpus=4 \
#   --memory=12g \
#   --memory-swap=12g \
#   --network=none \
#   --mount "type=bind,src=${PWD}/corpus-c/,destination=/corpus" \
#   --mount "type=bind,src=${PWD}/out/,destination=/out" \
#   tree-crasher-clang

FROM rust:1.91
RUN apt-get update && \
  apt-get install --no-install-recommends -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  tar \
  wget \
  zstd && \
  curl -fsSLO https://apt.llvm.org/llvm.sh && \
  chmod +x llvm.sh && \
  ./llvm.sh 21 && \
  rm -rf /var/lib/apt/lists/*
RUN cargo install --locked --git https://github.com/langston-barrett/tree-crasher tree-crasher-c --rev 1c0959df89efeb278553c7923a888b88cab24fae
WORKDIR /work
ENTRYPOINT tree-crasher-c \
  -v \
  --output /out \
  /corpus \
  --seed=$(date +%s) \
  --interesting-stderr "(?m)^PLEASE submit a bug report" \
  /usr/bin/clang-21 @@.c

#!/usr/bin/env bash

# TODO
# shellcheck disable=all

set -e

repos=(
  "gcc-mirror/gcc"
  "llvm/llvm-project"
)
mkdir -p c
for repo in "${repos[@]}"; do
  base=$(basename "${repo}")
  if ! [[ -d "${base}" ]]; then
    git clone --jobs 4 --depth 1 "https://github.com/${repo}"
  fi
  for f in $(find "${base}" -type f -name "*.c"); do
    echo "${f}"
    cp "${f}" c/"${base}-$(sha256sum "${f}" | head -c 5)-$(basename "${f}")"
  done
done

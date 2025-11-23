#!/usr/bin/env bash

# TODO
# shellcheck disable=all

set -e

repos=(
    "ethereum/solidity"
)
mkdir -p sol
for repo in "${repos[@]}"; do
  base=$(basename "${repo}")
  if ! [[ -d "${base}" ]]; then
    git clone --jobs 4 --depth 1 "https://github.com/${repo}"
  fi
  for f in $(find "${base}" -type f -name "*.sol"); do
    echo "${f}"
    cp "${f}" sol/"${base}-$(sha256sum "${f}" | head -c 5)-$(basename "${f}")"
  done
done

#!/usr/bin/env bash

# TODO
# shellcheck disable=all

set -e

repos=(
    "python/cpython"
    "mozillazg/pypy"
)
mkdir -p python
for repo in "${repos[@]}"; do
  base=$(basename "${repo}")
  if ! [[ -d "${base}" ]]; then
    git clone --jobs 4 --depth 1 "https://github.com/${repo}"
  fi
  for f in $(find "${base}" -type f -name "*.py"); do
    echo "${f}"
    cp "${f}" python/"${base}-$(sha256sum "${f}" | head -c 5)-$(basename "${f}")"
  done
done

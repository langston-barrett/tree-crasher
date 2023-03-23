#!/usr/bin/env bash

set -e

repos=(
  "twbs/bootstrap"
  "web-platform-tests/wpt"
)
mkdir -p css
for repo in "${repos[@]}"; do
  base=$(basename "${repo}")
  if ! [[ -d "${base}" ]]; then
    git clone --jobs 4 --depth 1 "https://github.com/${repo}"
  fi
  for f in $(find "${base}" -type f -name "*.css"); do
    echo "${f}"
    cp "${f}" css/"${base}-$(sha256sum "${f}" | head -c 5)-$(basename "${f}")"
  done
done

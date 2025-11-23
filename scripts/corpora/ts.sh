#!/usr/bin/env bash

# TODO
# shellcheck disable=all

set -e

repos=(
  "angular/angular"
  "denoland/deno"
  "microsoft/TypeScript"
  "microsoft/vscode"
  "swc-project/swc"
)
mkdir -p ts
for repo in "${repos[@]}"; do
  base=$(basename "${repo}")
  if ! [[ -d "${base}" ]]; then
    git clone --jobs 4 --depth 1 "https://github.com/${repo}"
  fi
  for f in $(find "${base}" -type f -name "*.ts"); do
    echo "${f}"
    cp "${f}" ts/"${base}-$(sha256sum "${f}" | head -c 5)-$(basename "${f}")"
  done
done

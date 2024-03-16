#!/usr/bin/env bash

set -e

repos=(
    "rails/rails"
    "sparklemotion/nokogiri"
    "Homebrew/brew"
)
mkdir -p ruby
for repo in "${repos[@]}"; do
  base=$(basename "${repo}")
  if ! [[ -d "${base}" ]]; then
    git clone --jobs 4 --depth 1 "https://github.com/${repo}"
  fi
  for f in $(find "${base}" -type f -name "*.rb"); do
    echo "${f}"
    cp "${f}" ruby/"${base}-$(sha256sum "${f}" | head -c 5)-$(basename "${f}")"
  done
done

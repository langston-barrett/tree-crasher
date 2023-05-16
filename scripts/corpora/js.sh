#!/usr/bin/env bash

set -e

repos=(
  "tc39/test262"
  "jquery/esprima"
  "v8/v8"
  "mozilla/gecko-dev"
  "svaarala/duktape"
  "Samsung/escargot"
  "jerryscript-project/jerryscript"
  "chakra-core/ChakraCore"
  "boa-dev/boa"
  "cesanta/elk"
  "Starlight-JS/starlight"
  "denoland/deno"
  "facebook/hermes"
)
mkdir -p js
for repo in "${repos[@]}"; do
  base=$(basename "${repo}")
  if ! [[ -d "${base}" ]]; then
    git clone --jobs 4 --depth 1 "https://github.com/${repo}"
  fi
  for f in $(find "${base}" -type f -name "*.js"); do
    echo "${f}"
    cp "${f}" js/"${base}-$(sha256sum "${f}" | head -c 5)-$(basename "${f}")"
  done
done

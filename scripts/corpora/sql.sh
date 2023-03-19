#!/usr/bin/env bash

set -e

shopt -s globstar
shopt -s nullglob

repos=(
  "ClickHouse/ClickHouse"
  "cockroachdb/cockroach"
  "duckdb/duckdb"
  "MonetDB/MonetDB"
  "postgres/postgres"
  "sqlite/sqlite"
)
mkdir -p sql
for repo in "${repos[@]}"; do
  base=$(basename "${repo}")
  if ! [[ -d "${base}" ]]; then
    git clone --jobs 4 --depth 1 "https://github.com/${repo}"
  fi
  pushd "${base}"
  if [[ "${base}" != ClickHouse ]]; then
    git submodule update --init
  fi
  popd
  for f in ./"${base}"/**/*.sql; do
    cp "${f}" sql/"${base}-$(sha256sum "${f}" | head -c 5)-$(basename "${f}")"
  done
done

for f in sql/*.sql; do
  if file "${f}" | grep -E '(ISO-8859|Non-ISO|: data)' > /dev/null 2>&1; then
    rm "${f}"
  fi
done

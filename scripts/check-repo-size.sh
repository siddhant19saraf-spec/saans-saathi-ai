#!/usr/bin/env bash
# Fail when the tracked repository exceeds the given size (default 10 MB).
set -euo pipefail

limit_mb="${1:-10}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: $repo_root is not a git repository" >&2
  exit 2
fi

total_bytes="$(git ls-files -z | xargs -0 -r wc -c | tail -n 1 | awk '{print $1}')"
total_mb="$(awk -v bytes="$total_bytes" 'BEGIN { printf "%.2f", bytes / 1048576 }')"

echo "Tracked repository size: ${total_mb} MB (limit: ${limit_mb} MB)"

if awk -v bytes="$total_bytes" -v limit="$limit_mb" 'BEGIN { exit !(bytes > limit * 1048576) }'; then
  echo "error: repository exceeds the ${limit_mb} MB limit" >&2
  exit 1
fi

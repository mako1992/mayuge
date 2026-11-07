#!/usr/bin/env bash
# 号ごとの作業フォルダを作る: ./scripts/new_issue.sh "theme-slug"
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <theme-slug>" >&2
  exit 1
fi

root="$(cd "$(dirname "$0")/.." && pwd)"
date="$(date +%Y-%m-%d)"
slug="$(echo "$1" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"
if [ -z "$slug" ]; then
  echo "slug must contain at least one ASCII letter or digit" >&2
  exit 1
fi
dir="$root/issues/${date}_${slug}"

if [ -e "$dir" ]; then
  echo "already exists: $dir" >&2
  exit 1
fi

mkdir -p "$dir/photos"
sed -e "s/{{SLUG}}/${slug}/" -e "s/{{DATE}}/${date}/" "$root/templates/issue.md" > "$dir/issue.md"
echo "created: $dir"

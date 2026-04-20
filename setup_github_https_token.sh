#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_dir"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <GITHUB_PAT>"
  echo "Example: $0 ghp_xxx..."
  exit 2
fi

token="$1"
user="vergileZhang"
cred_file="${repo_dir}/.git-credentials"

./gitw remote get-url origin >/dev/null 2>&1 || ./gitw remote add origin "https://github.com/${user}/langchain_learning.git"

./gitw config credential.useHttpPath true
./gitw config credential.helper "store --file ${cred_file}"

umask 077
printf "https://%s:%s@github.com\n" "$user" "$token" > "$cred_file"

echo "Saved credentials to: ${cred_file}"
echo "Next: ./gitw push -u origin main"


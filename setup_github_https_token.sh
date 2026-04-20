#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_dir"

user="vergileZhang"
repo="langchain_learning"

usage() {
  cat <<'EOF'
Usage:
  setup_github_https_token.sh [--store] [--no-rebase]

What it does:
  - Prompts for a GitHub PAT (input hidden)
  - Configures HTTPS auth for pushing to GitHub

Modes:
  (default) No persistent storage: uses a temporary GIT_ASKPASS helper for one push.
  --store   Persist credentials to ./.git-credentials (plaintext) for future pushes.
  --no-rebase  Skip fetching/rebasing before push.
EOF
}

store=false
do_rebase=true
if [[ $# -gt 2 ]]; then
  usage
  exit 2
fi
for arg in "$@"; do
  case "$arg" in
    --store) store=true ;;
    --no-rebase) do_rebase=false ;;
    *) usage; exit 2 ;;
  esac
done

./gitw remote get-url origin >/dev/null 2>&1 || ./gitw remote add origin "https://github.com/${user}/${repo}.git"

read -r -s -p "Enter GitHub PAT (will not echo): " token
echo
if [[ -z "${token}" ]]; then
  echo "Error: empty token."
  exit 1
fi

if $store; then
  cred_file="${repo_dir}/.git-credentials"
  ./gitw config credential.useHttpPath true
  ./gitw config credential.helper "store --file ${cred_file}"
  umask 077
  printf "https://%s:%s@github.com\n" "$user" "$token" > "$cred_file"
  echo "Saved credentials to: ${cred_file}"
  echo "Next: ./gitw push -u origin main"
  exit 0
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

askpass="${tmpdir}/askpass.sh"
cat >"$askpass" <<EOF
#!/usr/bin/env bash
case "\$1" in
  *Username*) echo "${user}" ;;
  *Password*) echo "${token}" ;;
  *) echo "" ;;
esac
EOF
chmod 700 "$askpass"

echo "Pushing without storing credentials..."
if $do_rebase; then
  echo "Fetching remote and rebasing (to avoid non-fast-forward push)..."
  GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 ./gitw fetch origin main || true
  if ./gitw show-ref --verify --quiet refs/remotes/origin/main; then
    GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 ./gitw rebase origin/main
  fi
fi

GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 ./gitw push -u origin main

echo "Done."

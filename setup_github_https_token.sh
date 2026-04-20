#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_dir"

user="vergileZhang"
repo="langchain_learning"

usage() {
  cat <<'EOF'
Usage:
  setup_github_https_token.sh [--store]

What it does:
  - Prompts for a GitHub PAT (input hidden)
  - Configures HTTPS auth for pushing to GitHub

Modes:
  (default) No persistent storage: uses a temporary GIT_ASKPASS helper for one push.
  --store   Persist credentials to ./.git-credentials (plaintext) for future pushes.
EOF
}

store=false
if [[ $# -gt 1 ]]; then
  usage
  exit 2
fi
if [[ $# -eq 1 ]]; then
  if [[ "$1" == "--store" ]]; then
    store=true
  else
    usage
    exit 2
  fi
fi

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
GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 ./gitw push -u origin main

echo "Done."

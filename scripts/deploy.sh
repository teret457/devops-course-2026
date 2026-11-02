#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${DEVOPS_REMOTE:-devops}"
CA_CERT="${DEVOPS_CA_CERT:-${HOME}/devops.crt}"
DRY=()
if [[ $# -gt 1 ]]; then echo "Usage: $0 [--dry-run]" >&2; exit 1; fi
if [[ $# -eq 1 ]]; then
  [[ $1 == --dry-run ]] || { echo "Unknown argument: $1" >&2; exit 1; }
  DRY=(--dry-run)
fi
[[ -f "$ROOT/site/index.html" ]] || { echo "site/index.html is missing" >&2; exit 1; }
[[ -z "$(git -C "$ROOT" status --porcelain)" ]] || { echo "Working tree is not clean" >&2; exit 1; }
rsync -avz --delete --chmod=D755,F644 "${DRY[@]}" -e "ssh -o BatchMode=yes -o ConnectTimeout=5" "$ROOT/site/" "$REMOTE:/var/www/devops-site/"
if [[ ${#DRY[@]} -eq 0 ]]; then
  curl --fail --silent --show-error --connect-timeout 5 --max-time 15 --cacert "$CA_CERT" https://devops.local/ >/dev/null || exit 1
fi
printf 'Delivered commit %s\n' "$(git -C "$ROOT" rev-parse --short HEAD)"

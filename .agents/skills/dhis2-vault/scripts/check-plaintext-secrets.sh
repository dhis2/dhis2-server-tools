#!/usr/bin/env bash
# Fail if inventory vault files are plaintext, or if hosts/vars files carry
# secret-shaped values that should live in an ansible-vault file.
#
# Usage: check-plaintext-secrets.sh [inventory-root]
set -euo pipefail

_script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
_repo_root=$(cd -- "$_script_dir/../../../.." && pwd)

INV="${1:-$_repo_root/deploy/inventory}"
errors=0

fail() {
  echo "ERROR: $*" >&2
  errors=$((errors + 1))
}

if [[ ! -d "$INV" ]]; then
  echo "ERROR: $INV not found (expected the inventory directory, e.g. deploy/inventory)" >&2
  exit 1
fi

# Keep this in step with dhis2-inventory/scripts/validate-inventory.sh.
# Anchored at the end of the key: `password_encryption` and `oidc_token_endpoint`
# are ordinary settings, not secrets.
secret_key_suffix='(password|passwd|_pass|secret|secret_key|access_key|private_key|preshared_key|token|munin_users)'

# Files named vault.yml/vault.yaml must be encrypted.
while IFS= read -r -d '' vault; do
  header=$(head -1 "$vault" || true)
  if [[ "$header" != \$ANSIBLE_VAULT* ]]; then
    fail "$vault is not encrypted — run: ansible-vault encrypt $vault"
  fi
done < <(find "$INV" -type f \( -name 'vault.yml' -o -name 'vault.yaml' \) -print0 2>/dev/null)

# hosts (INI). A '#' with no preceding whitespace is part of the value, not a
# comment — `ansible_ssh_pass=#hunter2` is a secret.
hosts="$INV/hosts"
if [[ -f "$hosts" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$line" ]] && continue
    if [[ "$line" =~ ([a-z0-9_]*${secret_key_suffix})[[:space:]]*=[[:space:]]*([^[:space:]]+) ]]; then
      key="${BASH_REMATCH[1]}"
      val="${BASH_REMATCH[3]}"
      val="${val#[\"\']}"
      if [[ -n "$val" && "$val" != "{{"* ]]; then
        fail "password-shaped assignment in $hosts: '$key' — move it to an ansible-vault file"
      fi
    fi
  done <"$hosts"
fi

# Every non-template file under host_vars/ and group_vars/, not just vars.yml:
# this repo's own convention (host_vars/postgres.template -> host_vars/postgres)
# produces extensionless files, and single-file group_vars/<group>.yml is common.
while IFS= read -r -d '' vars; do
  case "$(basename "$vars")" in
    vault.yml | vault.yaml) continue ;;  # already header-checked above
  esac
  header=$(head -1 "$vars" 2>/dev/null || true)
  [[ "$header" == \$ANSIBLE_VAULT* ]] && continue   # encrypted single-file host_vars
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*([a-z0-9_]*${secret_key_suffix})[[:space:]]*:[[:space:]]*(.*)$ ]] || continue
    key="${BASH_REMATCH[1]}"
    val="${BASH_REMATCH[3]}"
    val="${val%"${val##*[![:space:]]}"}"
    [[ -z "$val" ]] && continue                                 # block scalar / nested mapping
    [[ "$val" =~ ^!vault([[:space:]]|$) ]] && continue           # inline encrypt_string
    [[ "$val" =~ \{\{[^}]*vault_ ]] && continue                  # {{ vault_* }} reference
    fail "possible plaintext secret in $vars: '$key' (move the value to vault.yml as vault_$key and reference it here)"
  done <"$vars"
done < <(find "$INV/host_vars" "$INV/group_vars" -type f ! -name '*.template' -print0 2>/dev/null)

if [[ "$errors" -gt 0 ]]; then
  echo "$errors error(s) under $INV" >&2
  exit 1
fi

echo "OK: no plaintext vault/secret issues under $INV"
exit 0

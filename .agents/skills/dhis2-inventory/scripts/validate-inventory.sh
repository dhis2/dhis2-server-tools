#!/usr/bin/env bash
# Validate deploy/inventory/hosts before a playbook run.
#
# Checks: file mode, required [instances] fields, duplicate hostnames, duplicate
# ansible_host across ALL groups, LXD IPs inside lxd_network, and
# password-shaped values.
#
# Known limits: hosts reached only through [group:children] are not field-checked,
# and variables set in group_vars/host_vars files are only partially visible.
#
# Usage: validate-inventory.sh [path-to-hosts]
set -euo pipefail

# Resolve the repo root from this script's own location so the default path
# works regardless of the caller's working directory.
_script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
_repo_root=$(cd -- "$_script_dir/../../../.." && pwd)

HOSTS="${1:-$_repo_root/deploy/inventory/hosts}"
errors=0

fail() {
  echo "ERROR: $*" >&2
  errors=$((errors + 1))
}

note() {
  echo "NOTE: $*" >&2
}

if [[ ! -f "$HOSTS" ]]; then
  echo "ERROR: $HOSTS not found. Create it with:" >&2
  echo "  cp $_repo_root/deploy/inventory/hosts.template $HOSTS && chmod 600 $HOSTS" >&2
  exit 1
fi

# GNU first: BSD stat rejects -c, while GNU stat mis-parses -f '%Lp' as a
# filename, exits 1, and still prints filesystem info on stdout — so ordering
# these the other way round produces a multi-line blob on every Linux run.
mode=$(stat -c '%a' "$HOSTS" 2>/dev/null || stat -f '%Lp' "$HOSTS" 2>/dev/null || echo unknown)
if [[ "$mode" != "600" ]]; then
  fail "$HOSTS mode is $mode (expected 600) — fix with: chmod 600 $HOSTS"
fi

# Keep this in step with dhis2-vault/scripts/check-plaintext-secrets.sh.
# Anchored at the end of the key so ordinary settings whose names merely contain
# one of these words (password_encryption, oidc_token_endpoint) are not flagged.
secret_key_suffix='(password|passwd|_pass|secret|secret_key|access_key|private_key|preshared_key|token|munin_users)'

# Strip a trailing comment only when the '#' follows whitespace. A '#' with no
# space before it is part of the value — `ansible_ssh_pass=#hunter2` is a
# plaintext secret, not a comment, and must stay visible to the check below.
clean_line() {
  local l="$1"
  if [[ "$l" =~ ^([^#]*[[:space:]])# ]]; then
    l="${BASH_REMATCH[1]}"
  elif [[ "$l" =~ ^[[:space:]]*# ]]; then
    l=""
  fi
  l="${l#"${l%%[![:space:]]*}"}"
  l="${l%"${l##*[![:space:]]}"}"
  printf '%s' "$l"
}

is_ipv4() {
  [[ "$1" =~ ^(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])){3}$ ]]
}

# 10# on every octet: a leading zero would otherwise be read as octal, and `09`
# is not even valid octal — bash would emit a raw arithmetic error.
ip_to_int() {
  local a b c d
  IFS=. read -r a b c d <<<"$1"
  printf '%s' $(((10#$a << 24) + (10#$b << 16) + (10#$c << 8) + 10#$d))
}

valid_cidr() {
  local net="${1%/*}" prefix="${1#*/}"
  [[ "$1" == */* ]] || return 1
  is_ipv4 "$net" || return 1
  [[ "$prefix" =~ ^[0-9]+$ ]] && [[ "$prefix" -ge 0 && "$prefix" -le 32 ]]
}

# True when $1 is inside CIDR $2. Caller must have validated both.
ip_in_cidr() {
  local ip="$1" cidr="$2"
  local net="${cidr%/*}" prefix="${cidr#*/}"
  [[ "$prefix" -eq 0 ]] && return 0
  local ip_i net_i mask
  ip_i=$(ip_to_int "$ip")
  net_i=$(ip_to_int "$net")
  mask=$(((0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF))
  [[ $((ip_i & mask)) -eq $((net_i & mask)) ]]
}

# Split `key = value` (Ansible tolerates spaces around '=') into key/value.
kv_key() { local k="${1%%=*}"; k="${k%"${k##*[![:space:]]}"}"; printf '%s' "$k"; }
kv_val() { local v="${1#*=}"; v="${v#"${v%%[![:space:]]*}"}"; printf '%s' "$v"; }

# ---------------------------------------------------------------------------
# Pre-pass: group vars may be declared AFTER the host groups that need them.
# hosts.template puts [all:vars] at the bottom and [instances] near the top, so
# a single-pass parser validates every instance IP against the wrong network.
# ---------------------------------------------------------------------------
lxd_network=""
default_conn="lxd"
db_host_from_vars=0
ssh_groups=" "   # groups whose :vars set ansible_connection=ssh
_section=""

while IFS= read -r raw || [[ -n "$raw" ]]; do
  line=$(clean_line "$raw")
  [[ -z "$line" ]] && continue
  if [[ "$line" =~ ^\[(.+)\]$ ]]; then
    _section="${BASH_REMATCH[1]}"
    continue
  fi
  [[ "$_section" == *":vars" ]] || continue
  [[ "$line" == *"="* ]] || continue
  _k=$(kv_key "$line"); _v=$(kv_val "$line")
  _grp="${_section%:vars}"
  case "$_k" in
    lxd_network) [[ "$_grp" == "all" ]] && lxd_network="$_v" ;;
    ansible_connection)
      if [[ "$_grp" == "all" ]]; then
        default_conn="$_v"
      elif [[ "$_v" == "ssh" ]]; then
        ssh_groups="$ssh_groups$_grp "
      fi
      ;;
    database_host) [[ "$_grp" == "all" || "$_grp" == "instances" ]] && db_host_from_vars=1 ;;
  esac
done <"$HOSTS"

# lxd_network may live in group_vars/all/vars.yml instead of the hosts file.
if [[ -z "$lxd_network" ]]; then
  _gv="$_repo_root/deploy/inventory/group_vars/all/vars.yml"
  if [[ -f "$_gv" ]]; then
    lxd_network=$(sed -n 's/^[[:space:]]*lxd_network:[[:space:]]*["'"'"']\{0,1\}\([^"'"'"' ]*\).*/\1/p' "$_gv" | head -1)
  fi
fi

check_cidr=1
if [[ -z "$lxd_network" ]]; then
  lxd_network="172.19.2.1/24"
  note "lxd_network not found in $HOSTS or group_vars/all/vars.yml — assuming $lxd_network; IP bounds reported as notes only"
  check_cidr=0
elif ! valid_cidr "$lxd_network"; then
  fail "lxd_network '$lxd_network' is not valid IPv4 CIDR (expected e.g. 172.19.2.1/24) — IP bounds cannot be checked"
  check_cidr=0
elif [[ "${lxd_network#*/}" != "24" ]]; then
  note "lxd_network $lxd_network is not a /24 — IP bounds are checked against the full prefix"
fi

# ---------------------------------------------------------------------------
# Main pass
# ---------------------------------------------------------------------------
section=""
seen_pairs=" "   # "<ip>|<hostname>" already recorded
seen_ips=" "     # "<ip>=<first hostname>"
seen_hosts=" "

while IFS= read -r raw || [[ -n "$raw" ]]; do
  line=$(clean_line "$raw")
  [[ -z "$line" ]] && continue

  if [[ "$line" =~ ^\[(.+)\]$ ]]; then
    section="${BASH_REMATCH[1]}"
    continue
  fi

  # Secret-shaped assignments matter anywhere in the file, including :vars.
  if [[ "$line" =~ ([a-z0-9_]*${secret_key_suffix})[[:space:]]*=[[:space:]]*([^[:space:]]+) ]]; then
    _sk="${BASH_REMATCH[1]}"
    _sv="${BASH_REMATCH[3]}"
    _sv="${_sv#[\"\']}"
    if [[ -n "$_sv" && "$_sv" != "{{"* ]]; then
      fail "password-shaped value in $HOSTS: '$_sk' — move it to an ansible-vault file (see the dhis2-vault skill)"
    fi
  fi

  # :vars sections hold variables; :children lists group names, not hosts.
  [[ "$section" == *":vars" || "$section" == *":children" ]] && continue
  # A line before any group header (the bare 127.0.0.1 entry) has nothing to check.
  [[ -z "$section" ]] && continue

  hostname="${line%%[[:space:]]*}"
  [[ "$hostname" == *"="* ]] && continue

  case "$seen_hosts" in
    *" $hostname "*)
      # Same host legitimately appears in several groups; only flag a repeat
      # inside the same group, which silently overwrites the first definition.
      case "$seen_hosts" in
        *" $section/$hostname "*)
          fail "duplicate host '$hostname' in [$section] — the later definition silently wins" ;;
      esac
      ;;
  esac
  seen_hosts="$seen_hosts$hostname $section/$hostname "

  if [[ "$section" == "instances" ]]; then
    [[ "$line" =~ ansible_host= ]] ||
      fail "[instances] host '$hostname' missing ansible_host — add ansible_host=<ip>"
    if [[ "$db_host_from_vars" -eq 0 ]] && [[ ! "$line" =~ database_host= ]]; then
      fail "[instances] host '$hostname' missing database_host — set it on the host line, or once under [instances:vars]"
    fi
  fi

  # Duplicate-address and CIDR checks apply to EVERY group: a proxy and an
  # instance sharing an address breaks the deployment just as surely as two
  # instances would.
  if [[ "$line" =~ ansible_host=([^[:space:]]+) ]]; then
    addr="${BASH_REMATCH[1]}"

    if [[ "$seen_pairs" != *" $addr|$hostname "* ]]; then
      case "$seen_ips" in
        *" $addr="*)
          owner="${seen_ips##*" $addr="}"; owner="${owner%% *}"
          fail "duplicate ansible_host $addr — claimed by '$hostname' [$section] and '$owner'" ;;
        *)
          seen_ips="$seen_ips $addr=$hostname " ;;
      esac
      seen_pairs="$seen_pairs $addr|$hostname "
    fi

    host_conn="$default_conn"
    [[ "$ssh_groups" == *" $section "* ]] && host_conn="ssh"
    if [[ "$line" =~ ansible_connection=([^[:space:]]+) ]]; then
      host_conn="${BASH_REMATCH[1]}"
    fi

    if [[ "$host_conn" == "lxd" ]]; then
      if [[ "$addr" == *:* ]]; then
        fail "[$section] $hostname ansible_host '$addr' has a port or is IPv6 — LXD hosts need a plain IPv4 address"
      elif ! is_ipv4 "$addr"; then
        fail "[$section] $hostname ansible_host '$addr' is not an IPv4 address — LXD containers are addressed by IP inside lxd_network"
      elif [[ "$check_cidr" -eq 1 ]] && ! ip_in_cidr "$addr" "$lxd_network"; then
        fail "[$section] $hostname ansible_host $addr is outside lxd_network $lxd_network — pick an address in that range, or set ansible_connection=ssh on the host line"
      fi
    fi
  fi
done <"$HOSTS"

if [[ "$errors" -gt 0 ]]; then
  echo "$errors error(s) in $HOSTS" >&2
  exit 1
fi

echo "OK: $HOSTS"
exit 0

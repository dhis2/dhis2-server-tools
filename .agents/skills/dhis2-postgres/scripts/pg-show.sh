#!/usr/bin/env bash
# Show running PostgreSQL cluster majors and key tuning GUCs.
#
# Usage:
#   pg-show.sh                 # run on the database host (SSH deployments)
#   pg-show.sh --lxd           # run via lxc exec from the LXD hypervisor
#   PG_CONTAINER=pg1 pg-show.sh --lxd    # non-default [databases] host name
#
# Read-only. Queries no credential GUCs and prints no secrets.
set -euo pipefail

container="${PG_CONTAINER:-postgres}"
prefix=()

if [[ $# -gt 1 ]]; then
  echo "ERROR: too many arguments. Usage: pg-show.sh [--lxd]" >&2
  exit 2
fi

case "${1:-}" in
  --lxd)
    if ! command -v lxc >/dev/null 2>&1; then
      echo "ERROR: 'lxc' not found — --lxd only works on the LXD hypervisor." >&2
      echo "       On an SSH deployment, run pg-show.sh with no arguments on the database host." >&2
      exit 1
    fi
    # Bare `lxc` uses the caller's default remote and project. If that is not
    # `local`, this would silently report another machine's state as if it were
    # this host's — refuse rather than guess.
    remote=$(lxc remote get-default 2>/dev/null || echo "?")
    if [[ "$remote" != "local" ]]; then
      echo "ERROR: default LXD remote is '$remote', not 'local'. Refusing to guess the target host." >&2
      echo "       Run 'lxc remote switch local', then retry." >&2
      exit 1
    fi
    if ! lxc info "$container" >/dev/null 2>&1; then
      echo "ERROR: no LXD container named '$container'." >&2
      echo "       Set PG_CONTAINER=<name> to match your [databases] host in deploy/inventory/hosts." >&2
      exit 1
    fi
    prefix=(lxc exec "$container" --)
    ;;
  "")
    : # local mode — run directly on the database host
    ;;
  *)
    echo "ERROR: unknown argument '$1'." >&2
    echo "       Usage: pg-show.sh [--lxd]   (no argument = run on the database host)" >&2
    exit 2
    ;;
esac

run() {
  if [[ ${#prefix[@]} -gt 0 ]]; then
    "${prefix[@]}" "$@"
  else
    "$@"
  fi
}

# sudo -n and psql -w, with stdin closed: without all three, a host lacking
# passwordless sudo (or a psql that wants a DB password) blocks on an
# interactive prompt forever, which hangs a non-interactive agent.
psql_ro() {
  run sudo -n -u postgres psql -w "$@" </dev/null
}

echo "== clusters =="
run pg_lsclusters || true

echo
echo "== listeners =="
run ss -tlnp 2>/dev/null | grep -E 'postgres|5432|5433' || true

# Prefer the online cluster's major from pg_lsclusters (status "online")
ver=$(
  run pg_lsclusters --no-header 2>/dev/null \
    | awk '$4 == "online" { print $1; exit }' \
    || true
)
if [[ -z "${ver:-}" ]]; then
  # server_version_num is zero-padded (160004 → 16). Two chars is right for the
  # 10+ majors this toolkit supports; 9.x would need different handling.
  ver=$(psql_ro -Atc 'SHOW server_version_num;' 2>/dev/null | head -c 2 || true)
fi

echo
if [[ -n "${ver:-}" ]]; then
  echo "== tuned values (cluster major ${ver}) =="
else
  echo "== tuned values =="
fi

if ! psql_ro -c \
  "SHOW shared_buffers; SHOW work_mem; SHOW maintenance_work_mem; SHOW effective_cache_size; SHOW max_connections; SHOW jit; SHOW max_locks_per_transaction; SHOW log_min_duration_statement;"; then
  echo "WARN: could not query PostgreSQL." >&2
  echo "      On LXD, run this from the hypervisor with --lxd." >&2
  echo "      On an SSH deployment, run it on the database host with passwordless sudo." >&2
fi

# Do not gate this on $ver: when the cluster is DOWN, ver is empty — and that is
# exactly when you most want to read the config. Glob every installed major.
echo
echo "== dhispg.conf =="
if ! run bash -c 'shopt -s nullglob
found=0
for f in /etc/postgresql/*/main/conf.d/dhispg.conf; do
  found=1; echo "--- $f ---"; cat "$f" || echo "(could not read — run with sudo)"
done
[ "$found" = 1 ]'; then
  echo "(no dhispg.conf under /etc/postgresql/*/main/conf.d/ — tuning was never applied, or it was removed; see the dhis2-postgres skill)"
fi

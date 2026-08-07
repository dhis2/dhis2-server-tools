---
name: dhis2-postgres
description: >-
  Configures and tunes PostgreSQL for DHIS2 in dhis2-server-tools — memory
  tuning (shared_buffers, work_mem, max_connections), the dhispg.conf/conf.d
  mechanism, pg_hba and firewall access, slow-query troubleshooting, and
  PostgreSQL major version changes. Use when tuning database performance,
  diagnosing slow queries or connection exhaustion, changing postgresql_version,
  or reviewing database access control. Not for taking or restoring DB dumps —
  use dhis2-backup-restore. Not for DHIS2 application version changes — use
  dhis2-upgrade.
license: BSD-2-Clause
compatibility: Requires Ansible >=2.15, Ubuntu 22.04/24.04 database hosts. LXD path uses lxc exec from the hypervisor; SSH path runs on the database host.
metadata:
  project: dhis2-server-tools
  version: "1.0"
---

# DHIS2 PostgreSQL configuration and tuning

Operate the PostgreSQL server installed by the `postgres` role on `[databases]` hosts.

## Hard rules

1. **Changing `postgresql_version` does not upgrade an existing database.** On a host that already runs PostgreSQL, raising the version installs a _second_ empty cluster on the next free port (often 5433) next to the old one; data stays in the old cluster. create-instance then talks to whichever cluster is currently running (`postgresql_info`), not the inventory version. A major upgrade is a manual operation: full backup, then dump/restore or `pg_upgrade` (see `docs/how-to/db-backup-and-restore.md`). Never present the inventory edit alone as an upgrade.
2. **Tuning edits do not reapply automatically.** The role writes `/etc/postgresql/<ver>/main/conf.d/dhispg.conf` with `force: false` — it is only created once. Changing `pg_*` vars in `host_vars/postgres` after first install has no effect until you follow "Apply tuning changes" below. (Some docs claim this file is overwritten every run; that is wrong — trust the role task.)
3. **Tuning values are format-validated and silently dropped.** `pg_shared_buffers`, `pg_work_mem`, `pg_maintenance_work_mem`, `pg_effective_cache_size` must match `^\d+(GB|MB|KB)$` exactly — `8GB` works; `8 GB`, `0.5GB`, or `8g` are skipped without any error. `pg_max_connections` uses an unanchored digit check: any value containing a digit is written verbatim and will stop PostgreSQL from starting if malformed (`20 0`, `200x`); only fully non-numeric values fall back to 200. Verify with `SHOW` after applying.
4. **`shared_buffers` and `max_connections` changes need a PostgreSQL restart** — brief downtime for every DHIS2 instance on that database, and it aborts running analytics generation. Schedule it; take a backup first if combining with other changes.
5. Do not widen access beyond what the roles manage: no `listen_addresses` broadening, no permissive `pg_hba.conf` lines (`0.0.0.0/0`, `trust`), no UFW allow on 5432 from anywhere. Access is per-instance-IP, `hostssl` + `scram-sha-256`, written by the create-instance role.

## Credential access

**Default deny:** do not read, decrypt, or print secrets unless a step in this skill explicitly requires it. Tuning and verification do not need the DHIS2 database password — use peer auth as the `postgres` OS user (`lxc exec postgres -- sudo -u postgres psql` on LXD; `sudo -u postgres psql` on SSH). Config files under `/etc/postgresql/` have no secrets. Do not read instance DB passwords, `.pgpass`, or vault contents for tuning work.

## What the role installs

`deploy/roles/postgres/` targets `[databases]` hosts, branching on `ansible_connection` (LXD container vs SSH host). It installs from the PGDG apt repo: `postgresql-<ver>`, client, `postgis-3`, `python3-psycopg2`, `libdbd-pg-perl`. Default `postgresql_version` is `16` (from `inventory/hosts.template`; the role's own fallback is 13).

Baseline config written to `/etc/postgresql/<ver>/main/conf.d/dhispg.conf` (overrides `postgresql.conf`):

- `password_encryption = scram-sha-256`, `max_connections = 200` (unless `pg_max_connections` set)
- `checkpoint_completion_target = 0.8`, `synchronous_commit = off`, `wal_writer_delay = 10000ms`, `random_page_cost = 1.1` (SSD assumption)
- `max_locks_per_transaction = 128` (required by DHIS2 2.32+)
- `jit = off` when `postgresql_version > 10` (all currently supported versions)
- `log_min_duration_statement = 300s` — queries over 5 minutes land in the log
- `include_if_exists = custom` as the last line — a `conf.d/custom` file wins over everything above

Per-instance databases, owner roles, and the `postgis`, `btree_gin`, `pg_trgm` extensions are created by the create-instance role, not here.

Re-run just this component with:

```bash
ansible-playbook dhis2.yml --tags postgresql-install
```

For conf regeneration only (no apt/repo/role setup): `--tags postgresql-conf`.

## Tuning variables

Set in `inventory/host_vars/<database_host>` (copy `host_vars/postgres.template`). Guidance from `docs/Optimizing-PostgreSQL.md`; "RAM" means RAM allocated to PostgreSQL, not total server RAM.

| Variable | Rule of thumb |
| --- | --- |
| `pg_max_connections` | Each DHIS2 instance needs up to 80 connections by default (less if `pool` is set in `dhis.conf`). 200–400 typical |
| `pg_shared_buffers` | 0.25 × RAM |
| `pg_work_mem` | (0.25 × RAM) / max_connections |
| `pg_maintenance_work_mem` | As much as affordable — speeds up index builds during analytics generation |
| `pg_effective_cache_size` | ~80% of (RAM − maintenance_work_mem − max_connections × work_mem) |

Sizing RAM itself: a server with 32GB running one production and one test instance can reasonably dedicate 16GB to PostgreSQL. On LXD, also cap the container so the host stays healthy:

```bash
sudo lxc config set postgres limits.memory 16GB
```

## Apply tuning changes to an existing deployment

Because of `force: false` (hard rule 2), pick one:

**Option A — regenerate `dhispg.conf` from inventory (keeps Ansible as source of truth):**

```bash
# Prefer scripts/pg-show.sh to resolve the running major — do not assume 16.
# LXD from the hypervisor; on SSH hosts run rm on that host instead.
sudo lxc exec postgres -- rm /etc/postgresql/<ver>/main/conf.d/dhispg.conf
ansible-playbook dhis2.yml --tags postgresql-conf
# Fallback if the conf tag is unavailable: --tags postgresql-install
```

The template task notifies a PostgreSQL restart. Confirm the values landed (hard rule 3):

```bash
# From repo root on the LXD hypervisor (or omit --lxd on the DB host):
./.agents/skills/dhis2-postgres/scripts/pg-show.sh --lxd
```

**Option B — edit `/etc/postgresql/<ver>/main/conf.d/custom` directly** (loaded last, takes precedence, survives Ansible runs). Suits one-off experiments; port winners back to `host_vars` so a rebuild keeps them. Reload or restart afterwards: `work_mem`, `maintenance_work_mem`, `effective_cache_size` need only `systemctl reload postgresql`; `shared_buffers` and `max_connections` need a restart.

## Access control model

Written by the roles — verify against this, do not hand-edit:

- `pg_hba.conf` (`/etc/postgresql/<ver>/main/`): one `hostssl <instance> <instance> <ip>/32 scram-sha-256` line per instance, written by create-instance (not the postgres role). `<ip>` is the instance `service_ip`/`ansible_host` unless `lxd_host_ip` is defined (NAT/external-host case), in which case that address is used instead.
- UFW on the database host: 5432/tcp allowed from those same source IPs. With WireGuard lockdown active, also from the VPN subnet `10.0.0.0/24`. Lockdown may add further `pg_hba` lines from `wireguard_peers[].pg_access` (e.g. a sysadmin peer `/32`).
- `listen_addresses`: `*` normally; when `wireguard_data_plane=true`, only localhost plus the host's own VPN IP, removing the public 5432 surface.
- Deleted instances: the delete-instance flow removes the matching `pg_hba.conf` entry and UFW rule.

## Troubleshooting

```bash
./.agents/skills/dhis2-postgres/scripts/pg-show.sh --lxd   # clusters + tuned SHOW values
# On SSH deployments: run without --lxd on the database host

# Connection pressure / long queries (same peer-auth path):
sudo lxc exec postgres -- sudo -u postgres psql -c \
  "SELECT datname, state, count(*) FROM pg_stat_activity GROUP BY 1,2 ORDER BY 3 DESC;"
sudo lxc exec postgres -- sudo -u postgres psql -c \
  "SELECT pid, now()-query_start AS runtime, state, left(query,80) FROM pg_stat_activity WHERE state <> 'idle' ORDER BY runtime DESC;"
```

On SSH deployments drop the `lxc exec postgres --` prefix and run on the database host. Common findings:

- **`FATAL: remaining connection slots are reserved`** — connection exhaustion. Count instances × 80 against `max_connections`; raise `pg_max_connections` (restart) or set `pool` in the instances' `dhis.conf`.
- **Analytics runs slow** — check `maintenance_work_mem` and disk latency (`dd if=/dev/zero of=/tmp/testfile bs=512 count=1000 oflag=direct`); analytics is index-build heavy.
- **Instance cannot connect after IP/inventory change** — stale `pg_hba.conf` or UFW rule. Re-run `--tags create-instance --limit <instance>,<database_host>` (and WireGuard lockdown if peer access applies). `postgresql-install` alone does not rewrite pg_hba or instance firewall rules.

## Sources of truth

- `deploy/roles/postgres/` — role tasks and the `dhis-pg.conf.j2` template
- `deploy/roles/create-instance/tasks/postgresql-db.yml` — databases, roles, pg_hba, UFW
- `deploy/inventory/host_vars/postgres.template`, `docs/Optimizing-PostgreSQL.md` — tuning variables
- `docs/how-to/db-backup-and-restore.md` — backup before major PG moves
- https://docs.dhis2.org/en/manage/manage.html — official DHIS2 server guide

# Apache Doris Integration

Apache Doris (optional analytics database backend for DHIS2) is provisioned
automatically by `deploy/dhis2.yml` / `deploy/deploy.sh` as part of the
`doris` role — no separate playbook to run.

## Enabling Doris

1. Add a host under the `[apache_doris]` group in `deploy/inventory/hosts`:

   ```ini
   [apache_doris]
   doris  ansible_host=172.19.2.43  lxd_memory_limit=44GB  doris_fe_heap_size=8192m  doris_be_mem_limit=32G
   ```

2. Point the DHIS2 instance at it by adding `apache_doris_db=doris` to the
   relevant `[instances]` host line:

   ```ini
   [instances]
   dhis  ansible_host=172.19.2.11  database_host=postgres  dhis2_version=2.43  apache_doris_db=doris
   ```

3. Run the normal deploy:

   ```bash
   sudo ./deploy.sh
   ```

That's it — no additional command. If neither of the two inventory changes
above is made, the `doris` role is skipped entirely and nothing about your
deployment changes.

## What it does

- Creates and configures an LXD container for the Doris node.
- Installs Java 17, sysctl tuning (`vm.max_map_count`), and raised file
  descriptor limits; disables swap on the LXD host.
- Downloads and installs Apache Doris (FE + BE), sized by
  `doris_fe_heap_size` / `doris_be_mem_limit` if set.
- Creates systemd services (`doris-fe`, `doris-be`) and starts them.
- Creates the `analytics` database in Doris, a Doris user, and grants.
- Installs the PostgreSQL JDBC driver into Doris's FE and BE.
- Opens `pg_hba.conf` and a UFW rule on the paired PostgreSQL host so Doris
  can reach it.
- `deploy/roles/create-instance/templates/dhis.conf.j2` separately (and
  automatically) points DHIS2's `analytics.database` config at Doris
  whenever `apache_doris_db` is set on the instance host — that part isn't
  in this role at all.

## Requirements

- Ansible collections: `community.general`, `community.mysql`,
  `community.postgresql`, `ansible.posix`, `ansible.utils` (installed
  automatically by `deploy.sh`).
- LXD-managed Doris hosts only — `ansible_connection=ssh` on an
  `[apache_doris]` host is not yet supported and fails with a clear error.

## Manual walkthrough

For a from-scratch, non-Ansible walkthrough of what this role automates
(useful for understanding internals or troubleshooting), see
`docs/how-to/Apache-Doris-setup.md`.

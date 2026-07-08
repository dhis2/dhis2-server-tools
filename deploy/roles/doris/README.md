# doris

Provisions a single-node Apache Doris FE+BE (analytics database backend for
DHIS2) inside an LXD container, and wires it up to the paired PostgreSQL
instance and DHIS2 instance.

## Requirements

LXD only — hosts in `[apache_doris]` with `ansible_connection=ssh` cause this
role to fail with a clear error. Requires `community.general`,
`community.mysql`, `community.postgresql`, `ansible.posix`, and
`ansible.utils` collections (installed by `deploy/deploy.sh`).

## Role Variables

See `defaults/main.yml` for `doris_version`, `doris_user`, `doris_home`,
`java_home`, `doris_download_url`. Per-host inventory variables (set in
`deploy/inventory/hosts`, documented in `hosts.template`):

- `apache_doris_db` (on an `[instances]` host) — name of the `[apache_doris]`
  host this instance's analytics queries should use. Required to opt in.
- `apache_doris_db_user` / `apache_doris_db_password` — optional, default to
  `doris_user` and an auto-generated password stored under
  `/opt/ansible/secrets/apache_doris_db_password`.
- `lxd_memory_limit`, `doris_fe_heap_size`, `doris_be_mem_limit` — optional
  memory tuning, unset = no limit.

## How it's invoked

Not run directly — included from `deploy/dhis2.yml` as `- role: doris`,
gated on `groups['apache_doris'] | length > 0`, after `postgres` and before
`create-instance`.

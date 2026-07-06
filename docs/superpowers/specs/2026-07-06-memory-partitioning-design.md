# Memory Partitioning for LXD Containers and Services

## Context

On memory-constrained LXD hosts (e.g. a 64GB dev box running `dev`, `postgres`,
`doris`, `proxy`, and `monitor` containers), nothing today caps how much
memory each container — or the services inside it (PostgreSQL, Tomcat/DHIS2,
Doris FE/BE) — can consume. Without hard limits, any one container can starve
the others and the host itself, especially once Doris (which auto-sizes its
backend memory budget off whatever it can see) is in the mix.

This was worked out and manually verified on a real deployment (a 64GB dev
box: `dev`=8GB, `postgres`=8GB, `doris`=44GB, with Postgres/Tomcat/Doris
service-level tuning layered on top). This spec codifies that manual work
into the Ansible roles so it's reproducible for this and future
deployments, rather than rediscovered by hand each time.

Two things are genuinely new here; everything else already exists in code
and only needs to be documented:

- **New:** an LXD container `limits.memory` variable — nothing in the
  codebase sets this today.
- **New:** Doris FE/BE memory tuning variables — `apache-doris-setup.yml`
  never sets JVM heap or `mem_limit` at all today; both run on whatever
  Doris ships as its own default.
- **Already exists, undocumented:** `pg_shared_buffers`, `pg_work_mem`,
  `pg_maintenance_work_mem`, `pg_effective_cache_size`, `pg_max_connections`
  (`deploy/roles/postgres/templates/dhis-pg.conf.j2`) and `heap_memory_size`
  (`deploy/roles/create-instance/templates/tomcat_default.j2`). Neither
  appears anywhere in `deploy/inventory/hosts.template`.

## Goals

- Let an operator cap any LXD container's memory via one inventory variable.
- Let an operator tune Doris FE heap size and BE `mem_limit` via inventory
  variables, following the same optional/opt-in pattern as the existing
  Postgres/Tomcat tuning variables.
- Document all of the above (new and pre-existing) in `hosts.template` so
  the next deployment doesn't have to reverse-engineer it from source, the
  way this one did.
- Zero behavior change when these variables are left unset.

## Non-goals

- Not changing any default values or forcing memory limits on existing
  deployments that don't opt in.
- Not adding Molecule/CI coverage for the LXD memory limit — Molecule uses
  the Docker driver, not LXD, so the `lxd_container` / `limits.memory` code
  path isn't exercised in CI today regardless of this change, and fixing
  that gap is out of scope here.
- Not touching the separate, already-identified `pg_hba.conf` reload bug or
  the "wire `apache-doris-setup.yml` into `dhis2.yml`" structural question —
  both are being tracked as separate follow-up work.

## Design

### 1. `lxd_memory_limit` — LXD container memory cap

New optional per-host inventory variable. Added to the `config:` dict of
every `community.general.lxd_container` task across all container-creating
roles: `postgres`, `create-instance` (both the initial-create and the
recreate-after-OS-migration tasks), `proxy`, `monitoring`, `integration`,
and the ad hoc container-creation task in `deploy/playbooks/apache-doris-setup.yml`.

Ansible's `omit` sentinel only works for top-level module arguments, not
values nested inside a dict you construct yourself, so a plain
`default(omit)` inside the `config:` dict would leave a literal
`__omit_place_holder__...` string as the value. Instead, use a conditional
`combine()`:

```yaml
config: "{{ {'boot.autostart.priority': '2', 'user.type': group_names[0]}
             | combine({'limits.memory': lxd_memory_limit} if lxd_memory_limit is defined else {}) }}"
```

Each role's existing `config:` dict keeps its own current keys (e.g.
`postgres` also sets `security.protection.delete: "true"`) — only the
conditional `limits.memory` merge is added.

Applying this to an already-running container updates its cgroup limit live
(no restart required) since `lxd_container` manages full declarative state.

### 2. Doris FE/BE memory tuning

Two new optional variables, applied in `apache-doris-setup.yml` using the
same `lineinfile`-based approach already used there for `JAVA_HOME` and
`lower_case_table_names` (not a new templating mechanism):

- `doris_fe_heap_size` (e.g. `8192m`) — when defined, sets/updates
  `JAVA_OPTS="${JAVA_OPTS} -Xmx{{ doris_fe_heap_size }} -Xms{{ doris_fe_heap_size }}"`
  in `fe.conf`. Gated on `when: doris_fe_heap_size is defined`; unset
  leaves Doris's own shipped default (`-Xmx8192m`) untouched.
- `doris_be_mem_limit` (e.g. `32G`) — when defined, sets/updates
  `mem_limit = {{ doris_be_mem_limit }}` in `be.conf`. Gated on
  `when: doris_be_mem_limit is defined`; unset leaves Doris's own default
  (auto-calculated as 80% of detected system memory) in place.

Both tasks run in the same per-host loop/`when` pattern already used for the
other `apache-doris-setup.yml` tasks (`hostvars[item]['apache_doris_db'] is
defined` / `inventory_hostname == hostvars[item]['apache_doris_db']`).

### 3. `hosts.template` documentation

Add commented example lines to `deploy/inventory/hosts.template` covering
both the new variables and the pre-existing-but-undocumented Postgres/Tomcat
ones, inline on the relevant host's line (matching the existing
`apache_doris_db=doris`-style convention — no new `host_vars/` files or
`[group:vars]` blocks):

```ini
[instances]
dev ansible_host=172.19.2.12 database_host=postgres dhis2_version=2.43 proxy_rewrite=True apache_doris_db=doris
# heap_memory_size=5G lxd_memory_limit=8GB

[databases]
postgres ansible_host=172.19.2.20
# lxd_memory_limit=8GB pg_shared_buffers=2GB pg_work_mem=16MB pg_maintenance_work_mem=1GB pg_effective_cache_size=5GB pg_max_connections=100

[apache_doris]
doris ansible_host=172.19.2.43
# lxd_memory_limit=44GB doris_fe_heap_size=8192m doris_be_mem_limit=32G
```

## Testing / Verification

- `ansible-lint` and `yamllint` pass on all modified role/playbook files.
- Manual re-run against a real inventory (with the variables above set
  uncommented) confirming:
  - `lxc config show <container>` reflects `limits.memory` for `dev`,
    `postgres`, and `doris`.
  - `dhispg.conf`/`conf.d/custom` and `/etc/default/tomcat10` reflect the
    configured values (or, since manual tuning is already live on that box,
    confirming the Ansible-rendered files match what's already there rather
    than reverting it).
  - `fe.conf`/`be.conf` reflect `doris_fe_heap_size`/`doris_be_mem_limit`.
- No Molecule changes — see Non-goals.

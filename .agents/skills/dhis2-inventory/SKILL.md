---
name: dhis2-inventory
description: >-
  Configures the Ansible inventory for dhis2-server-tools deployments — hosts
  file, host groups, architecture selection (LXD vs SSH vs hybrid), and per-host
  and per-group variables. Use when creating or editing deploy/inventory/hosts,
  adding a DHIS2 instance, choosing a deployment architecture, or setting
  variables like fqdn, proxy, or TLS_TYPE. Not for changing dhis2_version on an
  existing instance — use dhis2-upgrade. Not for PostgreSQL tuning values or
  pg_* sizing — use dhis2-postgres. Not for encrypting secrets — use
  dhis2-vault.
license: BSD-2-Clause
compatibility: Requires Ansible >=2.15 inventory layout under deploy/inventory/. LXD architecture assumes a non-overlapping lxd_network; SSH architecture needs controller SSH to every host.
metadata:
  project: dhis2-server-tools
  version: "1.0"
---

# DHIS2 inventory configuration

Configure `deploy/inventory/hosts` and `deploy/inventory/{host_vars,group_vars}` for a dhis2-server-tools deployment.

## Safety rules

- Never write passwords, keys, or tokens into `hosts` or a plaintext vars file. Secrets go in an ansible-vault encrypted file (see the dhis2-vault skill if available, or `docs/Ansible-Vault.md`).
- Only use variables that exist in `deploy/inventory/hosts.template`, `docs/Variables.md`, or role defaults. Do not invent variable names.
- Keep `hosts` at mode 600 (`chmod 600 deploy/inventory/hosts`). `deploy.sh` enforces this.
- After editing, prefer a dry run before applying: `ansible-playbook dhis2.yml --check --diff`.

## Credential access

**Default deny:** do not read, decrypt, or print secrets unless a step in this skill explicitly requires it. Inventory editing is non-secret: hosts, IPs, versions, proxy/TLS toggles. Confirm vault files exist via `$ANSIBLE_VAULT;` headers only — do not decrypt. Write new secrets only through the dhis2-vault skill. Do not read runtime `dhis.conf`, `/opt/ansible/secrets/`, WG private keys, or TLS `.key` files.

## Workflow

1. Create the file if missing: `cp deploy/inventory/hosts.template deploy/inventory/hosts && chmod 600 deploy/inventory/hosts`
2. Pick the architecture (below) and set `ansible_connection` in `[all:vars]`.
3. Set the basics in `[all:vars]`: `fqdn` (empty → self-signed TLS), `email` (needed for Let's Encrypt), `timezone`.
4. Define hosts per group. Read [references/variables.md](references/variables.md) before setting anything beyond the basics (TLS, proxy choice, monitoring, LXD image settings, WireGuard toggles, or non-default instance vars).
5. Validate: `./.agents/skills/dhis2-inventory/scripts/validate-inventory.sh` — checks mode 600, required `[instances]` fields, duplicate `ansible_host` across all groups, LXD IPs inside `lxd_network`, and password-shaped values. It does not validate variable *names* or reachability; still dry-run with `--check --diff` before applying.

## Architecture selection

**Single server?** → LXD (default). `ansible_connection=lxd`. All components become LXD containers on one host. Verify `lxd_network` (default `172.19.2.1/24`) does not overlap the host's real network — overlap breaks routing.

**Separate servers/VMs per component?** → SSH. `ansible_connection=ssh`. Requires an ansible controller with working SSH to every host. Test first: `ansible 'all:!127.0.0.1' -m ping -u <user> -k`.

**Mix?** → Hybrid. Set `ansible_connection=ssh ansible_user=<user>` on individual host lines; the rest inherit the group/all default.

## Host groups

| Group | Runs | Notes |
| --- | --- | --- |
| `[web]` | nginx / apache2 / openresty reverse proxy | One host, e.g. `proxy ansible_host=172.19.2.2` |
| `[databases]` | PostgreSQL | Default name `postgres`; instances point at it via `database_host` |
| `[instances]` | DHIS2 Tomcat instances | One line per DHIS2 instance; hostname = container name = default URL path |
| `[monitoring]` | Munin, Grafana, or Prometheus | Controlled by `server_monitoring` — see the caveat in [references/variables.md](references/variables.md) before using anything other than `munin` on LXD |
| `[wireguard_hub]` | WireGuard hub | Only used when `wireguard_enabled=true` |
| `[backup_servers]` | Optional dedicated backup host | |
| `[integration]` | Optional integration JAR services | |

The bare `127.0.0.1` line at the top is required — do not remove it.

## Adding a DHIS2 instance

Add a line under `[instances]`:

```ini
[instances]
dhis   ansible_host=172.19.2.11  database_host=postgres  dhis2_version=2.42  proxy_rewrite=True
dhis2  ansible_host=172.19.2.12  database_host=postgres  dhis2_version=2.40  dhis2_base_path=dhis2
```

- Pick an unused IP inside `lxd_network` (LXD) or the real server IP (SSH).
- `dhis2_base_path` defaults to the inventory hostname; it becomes the URL path (`https://<fqdn>/<base_path>`).
- Instance-level `fqdn` on the host line gives the instance its own domain.
- Changing `dhis2_version` on an existing instance is an upgrade — stop and follow the dhis2-upgrade skill (or `docs/Upgrade-Guide.md`) instead of just editing the value.
- Prefer setting `dhis2_version` on the host line (or host_vars) over `[instances:vars]`. A host-line value wins; a stale group default can mislead operators reading the file top-to-bottom. Role default is `2.42`; the shipped `hosts.template` sets `[instances:vars] dhis2_version=2.40` **and `2.42` on the `dhis` host line**, so a stock copy deploys 2.42.
- `guest_os` in `[all:vars]` is a default for new containers; the toolkit may force 24.04 at create time for DHIS2 2.42+. Editing `guest_os` later does not reimage an existing guest.

## Per-host variable files

For anything beyond a couple of inline vars, use directory-form host_vars:

```
deploy/inventory/host_vars/
  postgres/
    vars.yml    # plaintext; may reference vault_ variables
    vault.yml   # ansible-vault encrypted secrets
```

Templates exist: `host_vars/{dhis,postgres,proxy}.template`. PostgreSQL tuning vars (`pg_*`) belong in `host_vars/postgres/vars.yml`; for the values themselves, use the dhis2-postgres skill.

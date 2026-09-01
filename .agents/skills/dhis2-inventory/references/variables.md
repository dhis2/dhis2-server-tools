# Inventory variable reference

## Contents
- Global variables (`[all:vars]`)
- Instance variables (`[instances]` lines or `[instances:vars]`)
- LXD-specific variables
- PostgreSQL tuning (host_vars/postgres)
- WireGuard variables
- Sources of truth

## Global variables (`[all:vars]`)

| Variable | Default | Notes |
|---|---|---|
| `fqdn` | (empty) | Domain for the deployment. Empty → self-signed certificate. Required for Let's Encrypt. |
| `email` | (empty) | Let's Encrypt expiry notifications. |
| `timezone` | `Africa/Nairobi` | List options with `timedatectl list-timezones`. |
| `ansible_connection` | `lxd` | `lxd` (single server) or `ssh` (distributed). Overridable per host. |
| `proxy` | `nginx` | `nginx`, `apache2`, or `openresty`. Switching stops/disables the others. |
| `TLS_TYPE` | `letsencrypt` if fqdn set, else `selfsigned` | `letsencrypt`, `customssl`, `selfsigned`. For `customssl`, place `customssl.crt` and `customssl.key` in **`deploy/roles/create-instance/files/`**. The copy tasks live in `create-instance/tasks/tls/customssl.yml`, so Ansible resolves the bare `src:` against that role first and the playbook directory last — `deploy/files/` also works. `roles/proxy/files/` is **never** searched, despite what several docs say. Legacy uppercase name — keep as is. |
| `postgresql_version` | `16` | PostgreSQL major version. |
| `server_monitoring` | `munin` | `munin`, `grafana`, `prometheus`. **LXD caveat:** `pre-install/tasks/lxd.yml` includes `{{ server_monitoring }}-client.yml` unguarded, and only `munin-client.yml`, `grafana-client.yml`, `prometheus-client.yml` exist there. `grafana/prometheus` resolves to a nonexistent `grafana/prometheus-client.yml` and `zabbix` has no pre-install client at all — both fail on LXD despite being listed elsewhere. The SSH path is unaffected (`pre-install/tasks/ssh.yml` → `Debian.yml` has no monitoring include), and the `monitoring` role itself does split `grafana/prometheus` correctly — pre-install fails first. `ansible_connection=local` hits the same bug (`local.yml` symlinks to `lxd.yml`). Verify before using anything but `munin` on LXD. |
| `app_monitoring` | `glowroot` | In-JVM APM, reachable at `/<instance>-glowroot`. |
| `unattended_upgrades` | `yes` | OS unattended security upgrades. |
| `wireguard_enabled` | `false` | Master switch for the WireGuard mesh + service lockdown. |
| `use_proxy_protocol` | (unset) | Set `true` only behind an upstream proxy sending PROXY protocol headers. |
| `proxy_protocol_trusted_cidr` | `lxd_network` | Trusted CIDR for PROXY protocol sources. |

## Instance variables

Set inline on the host line under `[instances]`, in `[instances:vars]`, or in `host_vars/<instance>/vars.yml`.

| Variable | Default | Notes |
|---|---|---|
| `ansible_host` | required | Container IP (LXD) or server IP (SSH). |
| `database_host` | `postgres` | Inventory name of the PostgreSQL host. |
| `create_db` | `yes` | Whether to create the instance database. |
| `dhis2_version` | role default `2.42`; `hosts.template` sets `2.40` in `[instances:vars]` **and `2.42` on the shipped `dhis` host line** | Major (`2.42` → latest stable of that line) or exact (`2.42.2.2`). Host line wins over `[instances:vars]`, which wins over the role default — so a stock `cp hosts.template hosts` deploy installs 2.42, not 2.40. Drives Java/Tomcat/guest OS selection when `dhis2_war_file` is unset. |
| `dhis2_war_file` | (unset) | URL or local path to a WAR. **Overrides `dhis2_version`** and skips Java/Tomcat auto-selection — set `java_version` explicitly when pinning a WAR. |
| `dhis2_auto_upgrade` | `false` | Auto-upgrade to latest patch of `dhis2_version`. Take a DB backup before enabling. |
| `dhis2_base_path` | inventory hostname | URL path of the instance. |
| `fqdn` (per instance) | (unset) | Dedicated domain for this instance. |
| `proxy_rewrite` | (unset) | `True` → redirect `/` to the instance path. One instance only. |
| `heap_memory_size` | (unset) | Tomcat JVM heap, e.g. `4G`. |
| `java_version` | auto from `dhis2_version` via `set_fact` | On the normal path (`dhis2_war_file` unset), `set-dhis2-url.yml` overwrites inventory with the auto-detected JDK — inventory cannot override. When `dhis2_war_file` is set, auto-selection is skipped and inventory / role default (`JAVA_VERSION: 17`) applies. |
| `wireguard_ip` | (unset) | This host's VPN address when WireGuard is enabled, e.g. `10.0.0.4`. |

## LXD-specific variables

| Variable | Default | Notes |
|---|---|---|
| `lxd_network` | `172.19.2.1/24` | Container network. Must not overlap the host LAN. |
| `lxd_bridge_interface` | `lxdbr1` | Bridge name. |
| `lxd_storage_driver` | `dir` | `dir` or `zfs`. |
| `guest_os` | `24.04` | Container Ubuntu release. The toolkit may force this per DHIS2 version at container **creation**; changing it later does not reimage an existing container. |
| `guest_os_arch` | `amd64` | `amd64`, `arm64`, `armhf`. |
| `lxd_host_ip` | auto-detected | Only set to override detection. |

## PostgreSQL tuning (host_vars/postgres)

`pg_max_connections`, `pg_shared_buffers`, `pg_work_mem`, `pg_maintenance_work_mem`, and
`pg_effective_cache_size` go in `host_vars/<database_host>/vars.yml` (copy `host_vars/postgres.template`).

For sizing rules, the silent format-validation traps, and how to apply changes to an existing deployment, use
the **dhis2-postgres** skill — that is the single source for tuning values. Do not size from this file.

## WireGuard variables

Basics only — the dhis2-wireguard skill (or `docs/WireGuard-VPN.md`) covers the rest.

| Variable | Default | Notes |
|---|---|---|
| `wireguard_enabled` | `false` | Enables mesh + lockdown in one deploy. |
| `wireguard_ip` (per host) | template-provided | `10.0.0.2`–`10.0.0.5` app hosts, `10.0.0.1` hub. |
| `wireguard_endpoint_public` | (empty) | Set to the public IP/DNS on NAT'd cloud VMs (EIP etc.). |
| `wireguard_lockdown_monitoring` | `true` | `false` keeps monitoring UIs public during cutover. |
| `wireguard_data_plane` | `false` | Route app-to-app traffic over the VPN (distributed setups). |
| `wireguard_peers` | sample `sysadmin` peer | Admin peers, defined in `group_vars/all/vars.yml`, IPs from `10.0.0.6` up. |

## Sources of truth

- `deploy/inventory/hosts.template` — canonical layout and inline comments
- `docs/Variables.md` — variable descriptions
- `docs/Deployment-Architectures.md` — LXD vs SSH vs hybrid
- Role defaults under `deploy/roles/*/defaults/`

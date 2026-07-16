# WireGuard VPN for DHIS2 Server Tools

WireGuard provides a secure VPN tunnel for administering DHIS2 infrastructure. A hub joins every component (proxy, postgres, dhis, monitor) plus each admin machine into a single `10.0.0.0/24` mesh. Public DHIS2 web access (80/443) and SSH (22) are unaffected.

`dhis2.yml` sets it up in one deploy, in two stages run back-to-back:

1. **Mesh bring-up** (`playbooks/wireguard.yml`): creates the hub, installs WireGuard everywhere, connects every peer.
2. **Service lockdown** (`playbooks/wireguard-lockdown.yml`): restricts Grafana, Prometheus, Munin, Glowroot and PostgreSQL to the VPN subnet.

Both are gated on `wireguard_enabled`, so a single `sudo ./deploy.sh` (or `ansible-playbook dhis2.yml`) takes you to a hardened deployment. To bring up the mesh while keeping monitoring public (e.g. mid-cutover), set `wireguard_lockdown_monitoring=false` in the inventory (see [Skipping or reverting the lockdown](#skipping-or-reverting-the-lockdown)).

## Architecture

Hub-and-spoke: each spoke has a single `[Peer]` pointing at the hub with `AllowedIPs = 10.0.0.0/24` and `PersistentKeepalive = 25`. Spoke-to-spoke traffic relays through the hub (`net.ipv4.ip_forward=1`, `iptables -A FORWARD -i wg0 -o wg0 -j ACCEPT`).

```
                    Internet
                       │
                ┌──────┴──────┐
                │  LXD Host   │   UDP 51820 → hub
                └──────┬──────┘
                       │  lxdbr1 (172.19.2.0/24)
   ┌──────────────┐    │
   │  wireguard   │◄───┼─── wg over UDP between hub and peers
   │ 172.19.2.200 │    │
   │  wg 10.0.0.1 │    │
   └──────────────┘    │
   ┌──────┐  ┌──────────┐  ┌──────┐  ┌──────────┐   ┌────────────┐
   │proxy │  │ postgres │  │ dhis │  │  monitor │   │ home/admin │
   │ .2   │  │   .3     │  │  .4  │  │   .5     │   │  .6 …      │
   └──────┘  └──────────┘  └──────┘  └──────────┘   └────────────┘
      (numbers are the wg IP: 10.0.0.x)
```

**Endpoint resolution**: two vars decouple the host listen address from what home peers dial.

| Var | Used for | Default |
|---|---|---|
| `wireguard_endpoint_listen` | `lxc network forward` listen address on the host (LXD) | auto-detect (`ansible_default_ipv4.address`) |
| `wireguard_endpoint_public` | `Endpoint =` line in home-peer `.conf` files | falls back to `wireguard_endpoint_listen` |

On a host with one public IP, leaving both empty works. On cloud VMs with 1:1 NAT (AWS EIP, GCP/Azure external IP), the primary interface holds a *private* IP: the forward binds there, but home peers must dial the public IP, so set `wireguard_endpoint_public` explicitly:

```ini
# inventory/hosts [all:vars]
wireguard_endpoint_public=203.0.113.42   # public IP or DNS name
```

App-to-app traffic (e.g. dhis to postgres) keeps using the LXD bridge (`172.19.2.x`); only admin/external traffic routes through WG. Lockdown rules allow `src=10.0.0.0/24`. Distributed deployments can move app-to-app traffic onto the VPN too; see [Encrypting app-to-app traffic](#encrypting-app-to-app-traffic-wireguard_data_plane).

## Prerequisites

- Ubuntu 22.04+ (kernel 5.6+ includes the WireGuard module)
- UFW active on each host being locked down
- A working dhis2-server-tools deployment (LXD or distributed/SSH)
- A WireGuard client on your admin workstation

## Quick Start (LXD)

For distributed/SSH deployments, read this section first, then see [Distributed (SSH) deployment](#distributed-ssh-deployment) for the differences.

### 1. Configure the inventory

```bash
cp deploy/inventory/hosts.template deploy/inventory/hosts
chmod 600 deploy/inventory/hosts
```

The template already lists the hub and a per-host `wireguard_ip`. Set the master switch in `[all:vars]`:

```ini
[all:vars]
wireguard_enabled=true
```

```ini
[web]
proxy     ansible_host=172.19.2.2   wireguard_ip=10.0.0.2
[databases]
postgres  ansible_host=172.19.2.20  wireguard_ip=10.0.0.3
[instances]
dhis      ansible_host=172.19.2.11  ... wireguard_ip=10.0.0.4
[monitoring]
monitor   ansible_host=172.19.2.30  wireguard_ip=10.0.0.5

# Group is wireguard_hub (not "wireguard") to avoid the host/group name clash.
[wireguard_hub]
wireguard ansible_host=172.19.2.200 wireguard_ip=10.0.0.1
```

### 2. Define human peers

In `deploy/inventory/group_vars/all/vars.yml`, assign IPs from `10.0.0.6` up (`.2`–`.5` are reserved for app containers). Each peer needs only a name and IP; keypairs are generated hub-side.

```yaml
wireguard_peers:
  - name: sysadmin
    allowed_ips: "10.0.0.6/32"
    pg_access:
      - { instance: dhis }
  - name: admin-bob
    allowed_ips: "10.0.0.7/32"
```

### 3. Deploy

```bash
cd deploy/
sudo ./deploy.sh          # DHIS2 + mesh + lockdown
```

A `wireguard_enabled=true` run provisions the hub container and UDP `51820` forward (LXD only), installs WireGuard on the hub and every app container, generates keypairs (preserved across runs), renders and starts every `wg0.conf`, then applies the lockdown. For mesh-without-lockdown, set `wireguard_lockdown_monitoring=false` first (see [Skipping or reverting the lockdown](#skipping-or-reverting-the-lockdown)).

### 4. Retrieve and import a human peer config

```bash
sudo lxc exec wireguard -- cat /etc/wireguard/clients/sysadmin.conf   # view
sudo lxc file pull wireguard/etc/wireguard/clients/sysadmin.conf .    # copy out
```

The config is complete; import it directly (Linux `wg-quick up <file>`; macOS/Windows/mobile via the WireGuard app). For a mobile QR code (the redirection must run inside the container):

```bash
sudo lxc exec wireguard -- apt-get install -y qrencode
sudo lxc exec wireguard -- bash -c \
  'qrencode -t ansiutf8 < /etc/wireguard/clients/sysadmin.conf'
```

### 5. Verify

```bash
# Mesh (run regardless of lockdown):
sudo lxc exec wireguard -- wg show          # peers + recent handshakes
sudo lxc network forward show lxdbr1        # confirms UDP 51820 forward
ping 10.0.0.1                               # hub, from a connected client
ping 10.0.0.5                               # monitor, via mesh relay

# Lockdown (skip if wireguard_lockdown_monitoring=false):
curl -m 3 http://172.19.2.30:3000/          # Grafana from host - now blocked
curl -m 3 http://10.0.0.5:3000/             # Grafana over VPN - reachable
curl -I https://your.dhis2.fqdn/            # DHIS2 stays public - expect 200/302
```

If lockdown checks fail but the mesh is up, suspect `wireguard_endpoint_public` (cloud 1:1 NAT) or UDP `51820` blocked upstream; see [Troubleshooting](#troubleshooting).

## Distributed (SSH) deployment

The same playbooks run on distributed/multi-VM setups. The hub is a regular VM you manage instead of an LXD container, and external UDP reaches it via your own firewall. Differences from the LXD flow:

- Set `ansible_connection=ssh` per-host or in `[all:vars]`.
- Add the hub as a VM in `[wireguard_hub]` with its reachable address:

```ini
[wireguard_hub]
wireguard ansible_host=<hub-ip> ansible_connection=ssh ansible_user=<user> wireguard_ip=10.0.0.1

[all:vars]
ansible_connection=ssh
wireguard_enabled=true
wireguard_endpoint_public=<hub public IP or DNS>   # what home peers dial
```

- The deploy mode is derived from the hub's `ansible_connection`. With `ssh`, the LXD-only tasks (hub container creation, `lxc network forward`) skip automatically; you own routing UDP `51820` to the hub (cloud security group, on-prem firewall, etc.).
- `wireguard_endpoint_public` is **required** in SSH mode (a pre-flight assertion fails without it): app peers on separate VMs have no shared LXD bridge, so every peer dials this address.

Run it (the `lxc exec` commands in the LXD section become plain SSH/`wg show` on each VM):

```bash
# Smoke-test the mesh first, lockdown separately:
ansible-playbook playbooks/wireguard.yml -u <user> -K
ansible-playbook playbooks/wireguard-lockdown.yml -u <user> -K

# Or the full run:
ansible-playbook dhis2.yml -u <user> -K
```

Everything else (peer definitions, `pg_access`, lockdown tags, split tunneling) is identical to the LXD flow.

### Encrypting app-to-app traffic (`wireguard_data_plane`)

By default only admin traffic uses the VPN; app-to-app traffic (JDBC, proxy upstreams, monitoring scrapes) uses the hosts' regular addresses. On a distributed deployment where VMs talk over untrusted networks, set `wireguard_data_plane=true` to route all inter-service traffic through `wg0` as well:

- Each host's computed `service_ip` becomes its `wireguard_ip`, so PostgreSQL listens on localhost + the WG address only, and proxy/monitoring point at `10.0.0.x` peers.
- `dhis2.yml` brings the mesh up *before* the service roles (the services need the tunnel to reach each other).
- Requires `ansible_connection=ssh`, `wireguard_enabled=true` and `wireguard_endpoint_public`; asserted at pre-flight. Any `[backup_servers]` host must also have a `wireguard_ip`, since it can only reach PostgreSQL over the VPN.

Leave it `false` (the default) on LXD and single-VPC deployments; nothing changes there.

## Service lockdown

Runs automatically as part of `dhis2.yml` when `wireguard_enabled=true`. Idempotent, and re-runnable standalone after manual UFW edits:

```bash
cd deploy/
sudo ansible-playbook playbooks/wireguard-lockdown.yml --check --diff   # dry-run
sudo ansible-playbook playbooks/wireguard-lockdown.yml                  # re-apply
```

### What gets locked down

| Service | Container | Port | After lockdown |
|---|---|---|---|
| Grafana | monitor | 3000 | VPN-only (`10.0.0.5:3000`) |
| Prometheus | monitor | 9090 | VPN-only |
| Munin | monitor | 80 | VPN-only |
| Glowroot | dhis instances | 4000 | VPN-only |
| munin-node | dhis instances | 4949 | Monitor container only |
| PostgreSQL | postgres | 5432 | VPN-only, per-peer rules |

**Not affected**: SSH (22) and the DHIS2 web app (80/443) stay public.

### Per-component control

Each step has its own tag (works via `dhis2.yml` or standalone):

| Tag | Effect |
|---|---|
| `lockdown-proxy` | Empties monitoring upstreams; re-renders DHIS2 vhosts without `/glowroot` |
| `lockdown-monitor` | UFW: Grafana/Prometheus/Munin from VPN only; drops proxy-to-Grafana/Munin rules |
| `lockdown-postgres` | Per-peer `pg_hba.conf` rules from `pg_access`; UFW 5432 from VPN subnet |
| `lockdown-instances` | UFW Glowroot 4000 from VPN; munin-node 4949 to monitor container only |
| `wireguard-lockdown` | Umbrella tag for all four (used by `--skip-tags wireguard-lockdown`) |

```bash
sudo ansible-playbook playbooks/wireguard-lockdown.yml --tags lockdown-proxy   # one component, standalone
```

### PostgreSQL VPN access

Access is granted **per peer** via the optional `pg_access` field; a peer without it has no PostgreSQL access. Each entry is either `{ instance: <hostname> }` (derives database and role from an `[instances]` host name, since a DHIS2 instance's db, role and owner all equal its container name) or an explicit `{ database, user }` pair. The role writes one `hostssl <database> <user> <peer_ip> scram-sha-256` line per entry; a password is still required.

```yaml
wireguard_peers:
  - name: sysadmin
    allowed_ips: "10.0.0.6/32"
    pg_access:
      - { instance: dhis }                 # least-privilege
  # - name: superuser
  #   pg_access:
  #     - { database: all, user: all }     # superuser-equivalent
```

Referenced `instance` hosts must be in `[instances]`. Resolved `database`/`user` names must match `^[a-zA-Z0-9_]+$` (`all` is allowed via the explicit form). If `allowed_ips` routes extra networks, set `peer_ip` to the single `/32` used for pg_hba/UFW rules. App-level pg_hba entries (from `create-instance`) are unaffected. All `pg_access` rules live in one `blockinfile` block; removing a peer and re-running removes its line.

### Skipping or reverting the lockdown

The monitoring/proxy lockdown is controlled by an inventory variable, not just tags. When `wireguard_enabled=true`, the provisioning roles (proxy, monitoring, create-instance) already render monitoring in its locked state, so `--skip-tags wireguard-lockdown` alone won't keep Grafana/Munin reachable through the proxy. To keep monitoring public during a cut-over:

```ini
[all:vars]
wireguard_enabled=true
wireguard_lockdown_monitoring=false   # mesh up, monitoring stays behind the proxy
```

The PostgreSQL and instance firewall steps only run in the lockdown phase, so tags do work for them:

```bash
sudo ansible-playbook dhis2.yml --skip-tags lockdown-postgres      # PG stays LXD-only
sudo ansible-playbook dhis2.yml --skip-tags wireguard-lockdown     # skip the whole phase this run
```

Skipping does **not** restore previously applied UFW rules / `pg_hba.conf` lines / nginx vhosts; it just stops re-applying them. To revert a locked-down monitoring stack, set `wireguard_lockdown_monitoring=false` and re-run the roles that own that state:

```bash
sudo ansible-playbook dhis2.yml --tags monitoring,proxy-install
```

To turn WireGuard off completely, set `wireguard_enabled=false` and re-run: both stages no-op, but already-locked services won't auto-revert (use the recipe above).

## Configuration reference

Set in `deploy/roles/wireguard/defaults/main.yml`; override in the inventory.

| Variable | Default | Description |
|---|---|---|
| `wireguard_enabled` | `false` | Master switch |
| `wireguard_data_plane` | `false` | Distributed/SSH only: route app-to-app traffic through the VPN |
| `wireguard_network` | `10.0.0.0/24` | VPN subnet |
| `wireguard_server_ip` | `10.0.0.1` | Hub address on the VPN |
| `wireguard_port` | `51820` | UDP listen port |
| `wireguard_interface` | `wg0` | Interface name |
| `wireguard_hub_inventory_hostname` | `wireguard` | Inventory name of the hub |
| `wireguard_hub_lxd_ip` | `172.19.2.200` | Static LXD IP for the hub container |
| `wireguard_endpoint_listen` | `""` | Host-side listen IP for `lxc network forward`; auto-detected when empty |
| `wireguard_endpoint_public` | `""` | Public IP/hostname for home-peer `Endpoint =`; falls back to `wireguard_endpoint_listen`. **Set on cloud 1:1 NAT and distributed hubs.** |
| `wireguard_auto_generate_keys` | `true` | Generate peer keypairs hub-side |
| `wireguard_auto_generate_psk` | `false` | Auto-generate pre-shared keys |
| `wireguard_client_config_dir` | `/etc/wireguard/clients` | Hub dir for peer configs |
| `wireguard_client_key_dir` | `/etc/wireguard/clients/keys` | Hub dir for peer keys |
| `wireguard_prune_orphans` | `false` | Remove files for peers no longer in inventory |
| `wireguard_lockdown_monitoring` | `true` | Restrict monitoring and `/glowroot` to the VPN. Set `false` in inventory to keep them public (cut-over) |
| `wireguard_peers` | `[]` | List of human/admin peers |

### Peer definition (human peers only)

App containers are auto-derived from inventory `wireguard_ip` and must **not** be listed in `wireguard_peers`.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Filesystem-safe id (`^[a-zA-Z0-9._-]+$`) |
| `allowed_ips` | Yes | Peer's VPN IP (e.g. `10.0.0.6/32`); may be comma-separated to route extra networks |
| `public_key` | No* | Peer's WG public key. *Required only when `wireguard_auto_generate_keys: false` |
| `preshared_key` | No | Optional PSK |
| `peer_ip` | No | Single `/32` for pg_hba/UFW; defaults to first CIDR in `allowed_ips` |
| `pg_access` | No | List of `{ instance }` or `{ database, user }`; adds per-peer pg_hba rules |

**Key modes**: auto-generate (default) needs only `name` + `allowed_ips`; the hub generates every keypair. With `wireguard_auto_generate_keys: false`, each peer must supply `public_key`. Set `wireguard_auto_generate_psk: true` to add a PSK to peers lacking an explicit `preshared_key` (affected clients must re-import their config).

## Split tunneling

Default is split-tunnel: only `10.0.0.0/24` routes through WG. To full-tunnel a peer, edit its `.conf`:

```ini
AllowedIPs = 10.0.0.0/24   # split tunnel (default)
AllowedIPs = 0.0.0.0/0     # full tunnel
```

## Adding and removing peers

Add or remove the entry in `wireguard_peers` and re-run `sudo ansible-playbook dhis2.yml`. The mesh applies changes with `wg syncconf` (no existing tunnels dropped); lockdown picks up new `pg_access` entries. Retrieve a new peer's config from `/etc/wireguard/clients/<name>.conf` on the hub. Set `wireguard_prune_orphans: true` to clean up orphaned key/config files on removal.

Rotate a peer's keys by deleting them on the hub and re-running (the peer must re-import):

```bash
sudo lxc exec wireguard -- rm /etc/wireguard/clients/keys/sysadmin.{key,pub,psk}
sudo ansible-playbook dhis2.yml
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Peer shows `latest handshake: never` | UDP `51820` not reaching the hub | Check `wireguard_endpoint_public`, host UFW, cloud security group |
| VPN checks fail, mesh looks up on the hub | Bad `wireguard_endpoint_public` (cloud 1:1 NAT) or blocked UDP | Set the public IP explicitly; open UDP `51820` |
| Monitoring unreachable for everyone after lockdown | `wireguard_peers` empty, or peers' WG not up | `wg show` on each peer; to restore public access while debugging, set `wireguard_lockdown_monitoring=false` and run `dhis2.yml --tags monitoring,proxy-install` |
| Lockdown applied when you wanted mesh only | `wireguard_lockdown_monitoring` defaults to `true` | Set it to `false`, re-run `dhis2.yml --tags monitoring,proxy-install` |
| `deploy.sh` prompts for a vault password | `host_vars/postgres/vault.yml` is encrypted | Run with `--vault-id prod@prompt` or a vault password file |

## Migration from 10.8.0.0/24 (host-bridge architecture)

Earlier versions ran WireGuard on the LXD host with a `wg0`-to-`lxdbr1` bridge on `10.8.0.0/24`. To migrate:

```bash
# 1. Tear down the old host WG instance.
sudo wg-quick down wg0 && sudo systemctl disable wg-quick@wg0
sudo apt purge wireguard wireguard-tools -y && sudo rm -rf /etc/wireguard

# 2. Remove old UFW/iptables rules referencing 10.8.0.0/24 or wg0
#    (including the WIREGUARD VPN FORWARDING block in /etc/ufw/before.rules).
sudo ufw status numbered && sudo ufw delete <num>

# 3. Confirm the inventory has wireguard_ip per app host, then re-deploy.
cd deploy/ && sudo ./deploy.sh
```

Old `10.8.0.0/24` client `.conf` files won't work; re-import the new `10.0.0.0/24` configs.

## Disabling WireGuard

Set `wireguard_enabled=false` and re-run. Future runs no-op both stages, but this does **not** tear down the hub or revert already-applied UFW / `pg_hba.conf` / proxy edits. To fully remove:

```bash
# 1. Remove the hub (LXD only) and its port-forward.
sudo lxc stop wireguard && sudo lxc delete wireguard
sudo lxc network forward port remove lxdbr1 <host-ip> udp 51820

# 2. Stop wg-quick on each app container.
for c in proxy postgres dhis monitor; do
  sudo lxc exec "$c" -- systemctl disable --now wg-quick@wg0
  sudo lxc exec "$c" -- rm -rf /etc/wireguard
done

# 3. Restore public access to locked-down services.
sudo ansible-playbook dhis2.yml --tags monitoring,proxy-install
```

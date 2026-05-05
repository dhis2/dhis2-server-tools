# WireGuard VPN for DHIS2 Server Tools

WireGuard provides a secure VPN tunnel for administering DHIS2 infrastructure. The hub runs in its own LXD container; every app container (proxy, postgres, dhis, monitor) joins as a WG peer with its own `wg0` interface. Home/admin peers (sysadmin laptops) connect to the hub via the LXD host's public IP over UDP `51820`. Public DHIS2 web access is unaffected.

## Architecture

```
                    Internet
                       │
                ┌──────┴──────┐
                │  LXD Host   │   104.105.9.136
                │  lxc fwd    │   UDP 51820 → 172.19.2.200:51820
                └──────┬──────┘
                       │
          ┌────────────┼────────────┐
          │     lxdbr1 (172.19.2.0/24)
          │            │
   ┌──────┴───────┐    │
   │  wireguard   │    │   LXD bridge (in-band, encrypted by WG)
   │ 172.19.2.200 │◄───┼─── wg over UDP between hub and peers
   │  wg 10.0.0.1 │    │
   └──────────────┘    │
                       │
   ┌──────┐  ┌──────────┐  ┌──────┐  ┌──────────┐
   │proxy │  │ postgres │  │ dhis │  │  monitor │
   │.2/.2 │  │ .20/.3   │  │.11/.4│  │  .30/.5  │
   └──────┘  └──────────┘  └──────┘  └──────────┘
                                         ▲
                                         │  wg
   ┌────────────┐                        │
   │  Home/admin │ wg 10.0.0.6 ──────────┘ (over public internet,
   └────────────┘                            host fwd's UDP 51820)
```

(Numbers under each box: `<lxd-bridge-ip>/<wg-ip-last-octet>`.)

**Topology**: hub-and-spoke. Each spoke (app container, home machine) has a single `[Peer]` pointing at the hub with `AllowedIPs = 10.0.0.0/24` and `PersistentKeepalive = 25`. Spoke ↔ spoke traffic relays through the hub (which has `net.ipv4.ip_forward=1` and `iptables -A FORWARD -i wg0 -o wg0 -j ACCEPT`).

**Endpoint resolution**:
- App container peers: `Endpoint = 172.19.2.200:51820` — resolved internally over `lxdbr1`.
- Home peers: `Endpoint = <wireguard_endpoint_public>:51820` — resolved over the internet, NAT'd by the LXD host through `lxc network forward`.

Two separate vars control this:

| Var | Used for | Default |
|---|---|---|
| `wireguard_endpoint_listen` | `lxc network forward` listen address on the host | auto-detect (`ansible_default_ipv4.address`) |
| `wireguard_endpoint_public` | `Endpoint =` line written into home-peer `.conf` files | falls back to `wireguard_endpoint_listen` |

On a host with a single primary public IP, leaving both empty works. On cloud VMs with 1:1 NAT (AWS EIP, GCP external IP, Azure public IP), the host's primary interface holds a *private* IP — auto-detect picks the private IP. The forward must still bind on that private IP (it is the only IP the host owns), but home peers must dial the public IP. In that case set:

```ini
# in inventory/hosts [all:vars]
wireguard_endpoint_public=203.0.113.42      # public IP or DNS name
# wireguard_endpoint_listen left empty — auto-detect picks the private primary
```

**App-to-app traffic** (e.g. dhis → postgres) continues to use the LXD bridge (`172.19.2.x`); only admin/external traffic is routed through WG. UFW lockdown rules continue to allow `src=10.0.0.0/24`; packets arrive on each container's `wg0` with the peer's WG IP as source.

## Prerequisites

- Ubuntu 22.04+ (kernel ≥ 5.6 includes the WireGuard kernel module)
- UFW firewall enabled on the host
- A working dhis2-server-tools LXD deployment (or ready to deploy)
- WireGuard client installed on your admin workstation

## Quick Start

### 1. Configure the inventory

Edit `deploy/inventory/hosts` and set:

```ini
[all:vars]
wireguard_enabled=true
```

The default `hosts.template` already lists the hub and per-host `wireguard_ip`:

```ini
[web]
proxy     ansible_host=172.19.2.2   wireguard_ip=10.0.0.2

[databases]
postgres  ansible_host=172.19.2.20  wireguard_ip=10.0.0.3

[instances]
dhis      ansible_host=172.19.2.11  ... wireguard_ip=10.0.0.4

[monitoring]
monitor   ansible_host=172.19.2.30  wireguard_ip=10.0.0.5

[wireguard]
wireguard ansible_host=172.19.2.200 wireguard_ip=10.0.0.1
```

### 2. Define human peers

Edit `deploy/inventory/group_vars/all/vars.yml`. Assign IPs from `10.0.0.6` upward (`.2`–`.5` are reserved for app containers in the default inventory):

```yaml
wireguard_peers:
  - name: sysadmin
    allowed_ips: "10.0.0.6/32"
    pg_access:
      - { database: dhis, user: dhis }

  - name: admin-bob
    allowed_ips: "10.0.0.7/32"
```

Each peer needs only a **name** and **IP address**. Keypairs are generated hub-side automatically.

### 3. Deploy

```bash
cd deploy/

# Full deployment (includes WireGuard)
sudo ./deploy.sh

# Or deploy only WireGuard on an existing setup
sudo ansible-playbook dhis2.yml --tags wireguard
```

The playbook will:
- Provision the `wireguard` LXD container at `172.19.2.200`.
- Add an `lxc network forward` rule so UDP `51820` from the host's public IP lands inside the wireguard container.
- Install WireGuard packages inside the hub and inside every app container.
- Generate hub + peer keypairs (preserved across runs).
- Render `wg0.conf` for the hub and per-peer `.conf` files for every container and every human peer.
- Pull each app container's config from the hub via Ansible `slurp` and start `wg-quick@wg0`.
- Lock down monitoring and database access to VPN-only.

### 4. Retrieve and import a human peer config

```bash
# View the config (it's rendered inside the hub container)
sudo lxc exec wireguard -- cat /etc/wireguard/clients/sysadmin.conf

# Or copy it out to the host and scp
sudo lxc file pull wireguard/etc/wireguard/clients/sysadmin.conf .
scp sysadmin.conf my-laptop:~/
```

The config is complete — no editing needed. Import directly into your WireGuard client.

**Connect:**

```bash
# Linux
sudo wg-quick up /path/to/sysadmin.conf

# macOS / Windows
# Import the .conf file into the WireGuard app

# Mobile (generate QR code on the hub)
sudo lxc exec wireguard -- qrencode -t ansiutf8 < /etc/wireguard/clients/sysadmin.conf
```

### 5. Verify connectivity

```bash
# On the home machine (connected over WG):
ping 10.0.0.1                # hub
ping 10.0.0.5                # monitor (via mesh)
curl http://10.0.0.5:3000    # Grafana (locked-down, VPN-only)
psql -h 10.0.0.3 -U dhis -d dhis2

# On the LXD host:
sudo lxc exec wireguard -- wg show
sudo lxc exec proxy -- wg show
sudo lxc network forward show lxdbr1   # confirms UDP 51820 forward
```

## What gets locked down

When `wireguard_enabled=true` and `wireguard_lockdown_monitoring=true` (default):

| Service | Container | Port | Before VPN | After VPN |
|---|---|---|---|---|
| Grafana | monitor | 3000 | Accessible via proxy `/grafana` | VPN-only (`10.0.0.5:3000`) |
| Prometheus | monitor | 9090 | Accessible via proxy | VPN-only |
| Munin | monitor | 80 | Accessible via proxy `/munin` | VPN-only |
| Glowroot | dhis instances | 4000 | Accessible from LXD network | VPN-only |
| munin-node | dhis instances | 4949 | Accessible from monitor container | Monitor container only |
| PostgreSQL | postgres | 5432 | LXD network only | VPN-only, per-peer rules |

**Not affected**: DHIS2 web app on ports 80/443 through the proxy stays public.

### PostgreSQL VPN access

Database access is granted **per peer** via the optional `pg_access` field. A peer without `pg_access` has **no** PostgreSQL access — the role does not add a blanket grant.

Each `pg_access` entry is a `{database, user}` pair. The role writes one `hostssl <database> <user> <peer_ip> scram-sha-256` line to `pg_hba.conf` per entry. A password is still required.

```yaml
wireguard_peers:
  - name: sysadmin
    allowed_ips: "10.0.0.6/32"
    pg_access:
      - { database: dhis, user: dhis }            # least-privilege

  # - name: superuser
  #   allowed_ips: "10.0.0.7/32"
  #   pg_access:
  #     - { database: all, user: all }            # superuser-equivalent
```

`database` and `user` must match `^[a-zA-Z0-9_]+$`. The PostgreSQL keyword `all` is allowed; arbitrary identifiers with regex metacharacters are rejected at validation time.

If a peer's `allowed_ips` routes additional networks (comma-separated CIDRs), set `peer_ip` explicitly to the single `/32` used for pg_hba/UFW rules.

App-level pg_hba entries (added by the `create-instance` role) are unaffected — they continue to work over the LXD bridge.

The role manages all `pg_access`-derived rules inside a single `blockinfile` block delimited by `# BEGIN/END ANSIBLE MANAGED — wireguard per-peer pg_access`. Removing a peer (or its `pg_access` entry) and re-running the role removes the corresponding `hostssl` line. A blanket `host all all <lxd_gateway_ip>/32` grant added by older versions of this role is removed on upgrade.

### Restoring public monitoring access

Set `wireguard_lockdown_monitoring: false` and re-run:

```bash
sudo ansible-playbook dhis2.yml --tags monitoring,proxy-install,wireguard
```

The monitoring and proxy roles recreate the deleted config files idempotently.

## Configuration reference

All variables are set in `deploy/roles/wireguard/defaults/main.yml` and can be overridden in the inventory.

| Variable | Default | Description |
|---|---|---|
| `wireguard_enabled` | `false` | Master switch |
| `wireguard_network` | `10.0.0.0/24` | VPN subnet |
| `wireguard_server_ip` | `10.0.0.1` | Hub address on the VPN |
| `wireguard_port` | `51820` | UDP listen port |
| `wireguard_interface` | `wg0` | WireGuard interface name |
| `wireguard_hub_inventory_hostname` | `wireguard` | Inventory name of the hub container |
| `wireguard_hub_lxd_ip` | `172.19.2.200` | Static LXD IP for the hub container |
| `wireguard_endpoint_listen` | `""` | Host-side listen IP for `lxc network forward`. Must be on the host. Auto-detect via `ansible_default_ipv4.address` when empty |
| `wireguard_endpoint_public` | `""` | Public IP/hostname advertised to home peers as `Endpoint =`. Falls back to `wireguard_endpoint_listen` when empty. **Set explicitly on cloud VMs with 1:1 NAT.** |
| `wireguard_auto_generate_keys` | `true` | Generate peer keypairs hub-side |
| `wireguard_auto_generate_psk` | `false` | Auto-generate pre-shared keys |
| `wireguard_client_config_dir` | `/etc/wireguard/clients` | Directory on the hub for peer configs |
| `wireguard_client_key_dir` | `/etc/wireguard/clients/keys` | Directory on the hub for peer keys |
| `wireguard_prune_orphans` | `false` | Remove files for peers no longer in inventory |
| `wireguard_lockdown_monitoring` | `true` | Restrict monitoring/DB to VPN-only |
| `wireguard_peers` | `[]` | List of human/admin peers |

### Peer definition (human peers only)

App containers are auto-derived from inventory `wireguard_ip` and must NOT be listed in `wireguard_peers`.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Identifier — filesystem-safe (letters, digits, dot, underscore, hyphen) |
| `allowed_ips` | Yes | Peer's VPN IP (e.g. `10.0.0.6/32`). May be comma-separated to route additional networks |
| `public_key` | No* | Peer's WG public key. *Required only when `wireguard_auto_generate_keys: false` |
| `preshared_key` | No | Optional PSK for post-quantum hedge |
| `peer_ip` | No | Single `/32` CIDR for pg_hba/UFW rules. Defaults to first CIDR in `allowed_ips` |
| `pg_access` | No | List of `{database, user}` — adds per-peer pg_hba rules |

### Key generation modes

**Auto-generate (default)**: `wireguard_auto_generate_keys: true`

Only `name` and `allowed_ips` required per human peer. The hub container generates every keypair — including its own and one per app container — and produces complete, ready-to-import `.conf` files.

**Manual keys**: `wireguard_auto_generate_keys: false`

Each peer must supply a `public_key`. App containers fall back to manual key supply via host_vars (advanced, rare).

### Pre-shared key (PSK) auto-generation

Set `wireguard_auto_generate_psk: true` to generate a PSK for each peer that doesn't supply an explicit `preshared_key`.

> **Warning**: enabling on an existing deployment generates fresh PSKs on the next run for every peer that lacks an explicit `preshared_key`. All affected clients must re-import their `.conf`.

## Split tunneling

Default is split-tunnel: only `10.0.0.0/24` routes through WG. App-to-app traffic continues via the LXD bridge. To route all client traffic through the VPN, edit a human peer's `.conf` and change:

```ini
# Split tunnel (default)
AllowedIPs = 10.0.0.0/24

# Full tunnel
AllowedIPs = 0.0.0.0/0
```

## Adding and removing peers

### Adding a new peer

Add the peer to `wireguard_peers` and re-run:

```bash
sudo ansible-playbook dhis2.yml --tags wireguard
```

Then retrieve the config from `/etc/wireguard/clients/<name>.conf` inside the hub container.

The hub uses `wg syncconf` to apply peer changes **without dropping existing VPN sessions**.

### Removing a peer

Remove the peer entry and re-run. Set `wireguard_prune_orphans: true` to also clean up orphaned key/config files.

### Rotating peer keys

```bash
# On the LXD host, reach into the hub container:
sudo lxc exec wireguard -- rm /etc/wireguard/clients/keys/sysadmin.{key,pub,psk}
sudo ansible-playbook dhis2.yml --tags wireguard
```

The affected peer must re-import their updated `.conf`.

## File layout on the hub container

```
/etc/wireguard/
├── wg0.conf
├── server_private.key
├── server_public.key
└── clients/
    ├── proxy.conf       # auto-derived app container
    ├── postgres.conf
    ├── dhis.conf
    ├── monitor.conf
    ├── sysadmin.conf    # human peer
    └── keys/
        ├── proxy.{key,pub}
        ├── sysadmin.{key,pub,psk}
        └── ...
```

## Migration from 10.8.0.0/24 (host-bridge architecture)

Earlier versions of this role ran WireGuard on the LXD host with a `wg0 ↔ lxdbr1` bridge and used the `10.8.0.0/24` subnet. To migrate:

```bash
# 1. On the LXD host: tear down the old WG instance.
sudo wg-quick down wg0
sudo systemctl disable wg-quick@wg0
sudo apt purge wireguard wireguard-tools -y
sudo rm -rf /etc/wireguard

# 2. Remove old UFW/iptables rules on the host.
sudo ufw status numbered     # find any rules referencing 10.8.0.0/24 or wg0
sudo ufw delete <num>         # delete each
# Also remove the old WIREGUARD VPN FORWARDING block from /etc/ufw/before.rules.

# 3. Verify the new inventory has wireguard_ip per app host (see Quick Start).
# 4. Re-deploy.
cd deploy/
sudo ./deploy.sh
```

Old `10.8.0.0/24` client `.conf` files will not work — re-import the freshly generated `10.0.0.0/24` configs.

## Disabling WireGuard

Set `wireguard_enabled=false` in the inventory. Subsequent playbook runs skip WG tasks but do **not** tear down an existing hub container. To fully remove:

```bash
sudo lxc stop wireguard && sudo lxc delete wireguard
sudo lxc network forward port remove lxdbr1 <host-ip> udp 51820
```

Then revert any UFW lockdown rules and re-enable proxy monitoring paths if needed by re-running the monitoring and proxy roles.

# WireGuard VPN for DHIS2 Server Tools

WireGuard provides a secure VPN tunnel for administering DHIS2 infrastructure. When enabled, monitoring dashboards (Grafana, Prometheus, Munin), application performance monitoring (Glowroot), and direct PostgreSQL access are restricted to VPN-connected clients only. Public DHIS2 web access remains unaffected.

## Architecture

```
                         Internet
                            │
                     ┌──────┴──────┐
                     │  Host (UFW) │
                     │             │
              ┌──────┤  wg0        │◄──── VPN Clients (10.8.0.0/24)
              │      │  10.8.0.1   │       UDP port 51820
              │      └──────┬──────┘
              │             │
              │        lxdbr1 (172.19.2.1/24)
              │             │
     ┌────────┼─────────────┼─────────────┐
     │        │             │             │
 ┌───┴───┐ ┌─┴──────┐ ┌────┴────┐ ┌──────┴───┐
 │ proxy │ │postgres│ │  dhis   │ │ monitor  │
 │  .2   │ │  .20   │ │  .11   │ │   .30    │
 └───────┘ └────────┘ └────────┘ └──────────┘
```

**Traffic flow:**

1. VPN client connects to the host on UDP port 51820.
2. The host kernel forwards packets from `wg0` to `lxdbr1` via iptables FORWARD rules.
3. MASQUERADE translates VPN source IPs (10.8.0.x) to the LXD gateway IP (172.19.2.1) so containers can route replies without needing a static route back to the VPN subnet.
4. Container-level UFW rules allow traffic only from the LXD gateway IP, ensuring that only VPN-routed traffic reaches protected services.

## Prerequisites

- Ubuntu 22.04+ (kernel >= 5.6 includes the WireGuard kernel module)
- UFW firewall enabled on the host
- A working dhis2-server-tools LXD deployment (or ready to deploy)
- WireGuard client installed on your admin workstation

## Quick Start

### 1. Configure the Inventory

Edit `deploy/inventory/hosts` and set:

```ini
[all:vars]
wireguard_enabled=true
```

### 2. Define VPN Peers

Edit `deploy/inventory/group_vars/all/vars.yml`:

```yaml
wireguard_peers:
  - name: sysadmin
    allowed_ips: "10.8.0.2/32"

  - name: admin-bob
    allowed_ips: "10.8.0.3/32"
```

Each peer needs only a **name** and **IP address**. Client keys are generated automatically on the server.

Each peer must have a unique IP address within the `10.8.0.0/24` subnet. The server uses `10.8.0.1`; assign clients starting from `10.8.0.2`.

### 3. Deploy

```bash
cd deploy/

# Full deployment (includes WireGuard)
sudo ./deploy.sh

# Or deploy only WireGuard on an existing setup
sudo ansible-playbook dhis2.yml --tags wireguard
```

The playbook will:
- Install WireGuard packages on the host
- Generate server keypair (preserved across runs)
- Generate client keypairs server-side (preserved across runs)
- Deploy the `wg0` interface configuration
- Configure UFW and iptables forwarding rules
- Lock down monitoring and database access to VPN-only
- Generate complete, ready-to-import client configs in `/etc/wireguard/clients/`

### 4. Retrieve and Import Client Config

```bash
# View the config
sudo cat /etc/wireguard/clients/sysadmin.conf

# Copy to local machine
scp your-user@your-server:/etc/wireguard/clients/sysadmin.conf .
```

The config is complete — no editing needed. Import directly into your WireGuard client.

**Connect:**

```bash
# Linux
sudo wg-quick up /path/to/sysadmin.conf

# macOS / Windows
# Import the .conf file into the WireGuard app

# Mobile (generate QR code on the server)
sudo qrencode -t ansiutf8 < /etc/wireguard/clients/sysadmin.conf
```

### 5. Verify Connectivity

```bash
# Check VPN interface is up
sudo wg show

# Ping the VPN server
ping 10.8.0.1

# Ping an LXD container (e.g., monitoring)
ping 172.19.2.30

# Access Grafana directly (if monitoring is Grafana/Prometheus)
curl http://172.19.2.30:3000

# Access Munin directly (if monitoring is Munin)
curl http://172.19.2.30/munin/

# Connect to PostgreSQL directly
psql -h 172.19.2.20 -U dhis -d dhis2
```

## What Gets Locked Down

When `wireguard_enabled=true` and `wireguard_lockdown_monitoring=true` (default):

| Service | Container | Port | Before VPN | After VPN |
|---|---|---|---|---|
| Grafana | monitor | 3000 | Accessible via proxy `/grafana` | VPN-only direct access |
| Prometheus | monitor | 9090 | Accessible via proxy | VPN-only direct access |
| Munin | monitor | 80 | Accessible via proxy `/munin` | VPN-only direct access |
| Glowroot | dhis instances | 4000 | Accessible from LXD network | VPN-only via LXD gateway |
| munin-node | dhis instances | 4949 | Accessible from monitor container | Monitor container only |
| PostgreSQL | postgres | 5432 | LXD network only | VPN-only direct access |

**Not affected:** DHIS2 web application (HTTP/HTTPS on ports 80/443 through the proxy) remains publicly accessible.

### PostgreSQL VPN access

The VPN lockdown adds a `host all all <lxd_gateway_ip>/32 scram-sha-256` entry to `pg_hba.conf`. This grants VPN users access to all databases as any PostgreSQL user — intentionally broad to support ad-hoc admin access (`psql`) over the VPN. A password is still required (`scram-sha-256`). Application-level pg_hba entries (per-instance db/user restrictions) are managed separately by the `create-instance` role.

### Restoring public monitoring access

Enabling `wireguard_lockdown_monitoring` removes monitoring proxy configs (Grafana/Munin paths) from nginx/apache2. To restore public proxy access:

1. Set `wireguard_lockdown_monitoring: false` in your inventory.
2. Re-run the playbook:
   ```bash
   sudo ansible-playbook dhis2.yml --tags monitoring,proxy-install,wireguard
   ```

The monitoring and proxy roles recreate the deleted config files idempotently.

## Configuration Reference

All variables are set in `deploy/roles/wireguard/defaults/main.yml` and can be overridden in the inventory.

| Variable | Default | Description |
|---|---|---|
| `wireguard_enabled` | `false` | Master switch — must be `true` to activate |
| `wireguard_network` | `10.8.0.0/24` | VPN subnet |
| `wireguard_server_ip` | `10.8.0.1` | Server address on the VPN |
| `wireguard_port` | `51820` | UDP listen port |
| `wireguard_interface` | `wg0` | WireGuard interface name |
| `wireguard_auto_generate_keys` | `true` | Generate client keypairs server-side |
| `wireguard_auto_generate_psk` | `false` | Auto-generate pre-shared keys for peers |
| `wireguard_client_config_dir` | `/etc/wireguard/clients` | Directory for client config files |
| `wireguard_client_key_dir` | `/etc/wireguard/clients/keys` | Directory for client key files |
| `wireguard_prune_orphans` | `false` | Remove files for peers no longer in inventory |
| `lxd_bridge_interface` | `lxdbr1` | LXD bridge (must match your LXD network) |
| `lxd_network` | `172.19.2.0/24` | LXD container subnet |
| `lxd_gateway_ip` | `172.19.2.1` | Host-side IP of the LXD bridge |
| `wireguard_lockdown_monitoring` | `true` | Restrict monitoring/DB to VPN-only |
| `wireguard_peers` | `[]` | List of VPN client peers |

### Peer definition

Each entry in `wireguard_peers` accepts:

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Identifier — must be filesystem-safe (letters, digits, dot, underscore, hyphen) |
| `allowed_ips` | Yes | Client's VPN IP (e.g., `10.8.0.2/32`) |
| `public_key` | No* | Client's WireGuard public key. *Required only when `wireguard_auto_generate_keys: false` |
| `preshared_key` | No | Optional preshared key for post-quantum security |

### Key generation modes

**Auto-generate (default):** `wireguard_auto_generate_keys: true`

Only `name` and `allowed_ips` required per peer. The playbook generates client keypairs on the server and produces complete, ready-to-import `.conf` files. If a peer provides `public_key`, auto-generation is skipped for that peer (no client `.conf` emitted since the server never sees the private key).

**Manual keys:** `wireguard_auto_generate_keys: false`

Each peer must provide a `public_key`. This is the traditional workflow where admins generate keys on their workstation and paste the public key into inventory.

### Pre-shared key (PSK) auto-generation

Set `wireguard_auto_generate_psk: true` to generate a PSK for each peer that doesn't supply an explicit `preshared_key`. PSKs add a symmetric post-quantum hedge.

> **Warning:** Enabling this on an existing deployment generates fresh PSKs on the next run for every peer that lacks an explicit `preshared_key`. All affected clients must re-import their `.conf`.

## Split Tunneling

The client configuration uses **split tunneling** by default: only traffic destined for the VPN subnet (`10.8.0.0/24`) and the LXD container subnet (`172.19.2.0/24`) routes through the tunnel. All other internet traffic uses the client's normal connection.

To route all traffic through the VPN (full tunnel), change the client config:

```ini
# Split tunnel (default)
AllowedIPs = 10.8.0.0/24, 172.19.2.0/24

# Full tunnel
AllowedIPs = 0.0.0.0/0
```

## Adding and Removing Peers

### Adding a new peer

1. Add the peer to `wireguard_peers` in your inventory with a unique name and IP.
2. Re-run the playbook:

```bash
sudo ansible-playbook dhis2.yml --tags wireguard
```

3. Retrieve the config from `/etc/wireguard/clients/<name>.conf`.

The playbook uses `wg syncconf` to apply peer changes **without dropping existing VPN sessions**.

### Removing a peer

1. Remove the peer entry from `wireguard_peers`.
2. Re-run the playbook:

```bash
sudo ansible-playbook dhis2.yml --tags wireguard
```

The `wg syncconf` command removes peers that are no longer in the configuration. To also clean up orphaned key and config files, set `wireguard_prune_orphans: true`.

### Rotating client keys

Delete the client's key files on the server and re-run:

```bash
# Rotate keys only
sudo rm /etc/wireguard/clients/keys/sysadmin.{key,pub}

# Rotate PSK only
sudo rm /etc/wireguard/clients/keys/sysadmin.psk

# Rotate both
sudo rm /etc/wireguard/clients/keys/sysadmin.{key,pub,psk}

sudo ansible-playbook dhis2.yml --tags wireguard
```

The affected client must re-import their updated `.conf`.

## File Layout on Server

```
/etc/wireguard/
├── wg0.conf                  # Server config
├── server_private.key         # Server private key
├── server_public.key          # Server public key
└── clients/
    ├── user.conf       # Complete, ready-to-import config
    ├── sysadmin.conf
    └── keys/
        ├── user.key    # Client private key (0600)
        ├── user.pub    # Client public key (0600)
        ├── user.psk    # Client PSK (0600, only if auto_generate_psk=true)
        ├── sysadmin.key
        ├── sysadmin.pub
        └── sysadmin.psk
```

## Network Customization

### Changing the VPN subnet

If `10.8.0.0/24` conflicts with your network, override it in the inventory:

```ini
[all:vars]
wireguard_network=10.99.0.0/24
wireguard_server_ip=10.99.0.1
```

Update peer `allowed_ips` accordingly and re-deploy.

### Changing the WireGuard port

```ini
[all:vars]
wireguard_port=41820
```

Ensure the new port is open on any upstream firewalls or cloud security groups.

## Disabling WireGuard

Set `wireguard_enabled=false` in the inventory. This prevents the WireGuard tasks from running on subsequent playbook runs but does **not** tear down an existing WireGuard interface. To fully remove WireGuard:

```bash
# On the host
sudo wg-quick down wg0
sudo systemctl disable wg-quick@wg0
sudo apt remove wireguard wireguard-tools
sudo rm -rf /etc/wireguard
```

Then manually revert any UFW rule changes and re-enable proxy monitoring paths if needed by re-running the monitoring and proxy roles.

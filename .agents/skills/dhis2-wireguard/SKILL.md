---
name: dhis2-wireguard
description: >-
  Configures the WireGuard VPN mesh and service lockdown in dhis2-server-tools —
  enabling wireguard_enabled, hub and peer setup, admin client configs, endpoint
  resolution behind NAT, and locking PostgreSQL, Grafana, Prometheus, Munin, and
  Glowroot to VPN-only access. Use when setting up or troubleshooting WireGuard,
  VPN access, service lockdown, or admin peer configs in a DHIS2 deployment. Not
  for general inventory architecture (LXD vs SSH) — use dhis2-inventory. Not for
  vaulting unrelated app secrets — use dhis2-vault.
license: BSD-2-Clause
compatibility: Requires Ansible >=2.15, active UFW on locked-down hosts, and lxc when the hub is an LXD container. Assumes VPN subnet 10.0.0.0/24 and UDP 51820.
metadata:
  project: dhis2-server-tools
  version: "1.0"
---

# DHIS2 WireGuard VPN

Set up and operate the WireGuard mesh that protects admin services in a dhis2-server-tools deployment.

## Safety rules

1. **Lockout risk is the main hazard.** Lockdown restricts PostgreSQL (5432), Grafana (3000), Prometheus (9090), Munin, and Glowroot (4000) to the VPN subnet. Before applying lockdown, confirm at least one admin peer exists in `wireguard_peers` and its client config has been retrieved and tested.
2. **Never close SSH (22) or web (80/443) as part of WireGuard hardening.** The design leaves public DHIS2 access and SSH untouched.
3. UFW must be active on hosts being locked down; the roles manage rules, not the firewall state.
4. Peer private keys are secrets: they live on the hub under `/etc/wireguard/clients/`; retrieve configs over SSH, never paste key material into chat or commit it.

## Credential access

**Default deny:** do not read, decrypt, or print secrets unless a step in this skill explicitly requires it. Most WireGuard ops need no application secrets. Inventory toggles, `wg show`, and UFW/nginx lockdown stubs are fine. When handing a client config to a human, use their terminal — if the agent must inspect the file, print only `Address` / `Endpoint` / `AllowedIPs` / `PublicKey` and **redact `PrivateKey` / `PresharedKey`**. Never dump hub/peer private keys, DB passwords, S3 keys, or app admin passwords.

## Architecture (hub-and-spoke)

- Hub: `[wireguard_hub]` host, VPN IP `10.0.0.1`, LXD IP `172.19.2.200`, UDP 51820 forwarded from the host.
- Spokes: proxy `.2`, postgres `.3`, dhis `.4`, monitor `.5` (via per-host `wireguard_ip`); admin peers from `10.0.0.6` up.
- Spoke-to-spoke traffic relays through the hub. App-to-app traffic stays on the LXD bridge unless `wireguard_data_plane=true`.
- Keys are generated hub-side by default (`wireguard_auto_generate_keys: true`).

## Enable

1. In `deploy/inventory/hosts` `[all:vars]`: `wireguard_enabled=true`. Verify every host line has a unique `wireguard_ip` and the `[wireguard_hub]` entry exists (template provides both).
2. Define admin peers in `deploy/inventory/group_vars/all/vars.yml`:

```yaml
wireguard_peers:
  - name: sysadmin
    allowed_ips: '10.0.0.6/32'
    pg_access:
      - { instance: dhis } # DB access as that instance's role
```

`pg_access: [{ database: all, user: all }]` grants superuser-equivalent reach — only with explicit human approval.

3. Run the deploy (full `dhis2.yml` handles mesh bring-up and lockdown in order). To bring up the mesh but keep monitoring public during a cutover: `wireguard_lockdown_monitoring=false`.

4. Have the **operator** retrieve the admin client config on their terminal (do not paste PrivateKey into chat):

```bash
sudo lxc exec wireguard -- cat /etc/wireguard/clients/sysadmin.conf
# agent-safe check (no private key):
sudo lxc exec wireguard -- grep -E '^(Address|Endpoint|AllowedIPs|PublicKey|\[)' /etc/wireguard/clients/sysadmin.conf
```

Expect `Address = 10.0.0.6/32` (spaces around `=` are normal), `AllowedIPs = 10.0.0.0/24`, `Endpoint = <public-ip>:51820`.

## NAT / cloud endpoint

On cloud VMs with 1:1 NAT (AWS EIP, GCP/Azure external IPs) the primary interface has a private IP. The listen forward binds there, but clients must dial the public address:

```ini
[all:vars]
wireguard_endpoint_public=203.0.113.42   # public IP or DNS
```

`wireguard_endpoint_listen` overrides the auto-detected bind address only when detection picks the wrong interface.

## Verify

1. Handshakes on the hub: `sudo lxc exec wireguard -- wg show` — every spoke and connected admin peer listed with a recent handshake. Admin peers with no client connected show AllowedIPs but no recent handshake — that is normal until they dial in.
2. From a connected admin client: PostgreSQL `10.0.0.3:5432` (SSL required), Glowroot `10.0.0.4:4000`, Grafana `10.0.0.5:3000`, Prometheus `10.0.0.5:9090`.
3. Public paths still work: `https://<fqdn>/<instance>/...` and SSH.
4. After lockdown: container UFW should allow 5432/3000/9090/4000 only from `10.0.0.0/24` (plus required LXD bridge sources for app traffic). The proxy often stubs Grafana/Munin locations with a "Monitoring disabled by WireGuard lockdown" upstream — public `/grafana` then fails closed even if the browser can reach the proxy.

## Troubleshooting

- **Client cannot connect:** check the imported config matches the current deployment network (`10.0.0.0/24`) — stale configs from a previous key generation stop working after redeploys regenerate keys.
- **A peer's WireGuard landed on the wrong machine (e.g. LXD host instead of a container):** inspect for a leaked `ansible_connection` fact from an earlier play; verify the role files, then re-run the peer stage scoped with `--limit`.
- **Lockdown partially applied** (e.g. postgres locked but instances not): re-run `ansible-playbook playbooks/wireguard-lockdown.yml --tags <lockdown-tags> --limit <hosts>` after fixing the failing task.
- **Reverting lockdown:** set `wireguard_lockdown_monitoring=false` and re-run; disabling `wireguard_enabled` skips all WireGuard plays but does not remove existing firewall rules — remove those explicitly.

Full guide with distributed/SSH specifics: `docs/WireGuard-VPN.md`.

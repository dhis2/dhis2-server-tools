# How to Expose an LXD Container Port to a Specific Source IP

This guide explains how to forward a port from an LXD container (e.g. PostgreSQL on port 5432)
to the host machine, while restricting access to a single trusted source IP using UFW and iptables.

---

## Overview

LXD containers are on a private bridge network (e.g. `172.19.2.0/24`) and are not directly
reachable from outside the host. To allow an external server to connect to a service inside
a container, you need two things:

1. **DNAT rule** — forwards inbound traffic from `host-ip:port` to `container-ip:port`
2. **Source IP restriction** — limits which remote IP can reach that port

---

## Step 1: Add the DNAT rule in `/etc/ufw/before.rules`

UFW manages the `filter` table but not the `nat` table. Add your DNAT rule at the top of
`/etc/ufw/before.rules`, before the `*filter` section:

```
*nat
:PREROUTING ACCEPT [0:0]
# Forward PostgreSQL port from host to container, only from trusted source IP
-A PREROUTING -s <source-ip> -p tcp --dport 5432 -j DNAT --to-destination <container-ip>:5432
COMMIT
```

Replace:
- `<source-ip>` — the remote server that is allowed to connect (e.g. `10.1.2.3`)
- `<container-ip>` — the LXD container's IP on the bridge (e.g. `172.19.2.20`)

The `-s <source-ip>` match ensures the DNAT only applies to traffic from your trusted host.
All other sources are not forwarded and will be dropped by UFW.

---

## Step 2: Allow forwarded traffic through UFW

DNAT rewrites the destination before routing, so the packet is forwarded — it never hits the
INPUT chain. `ufw allow port 5432` has no effect here.

Instead, ensure the FORWARD chain allows the traffic. If `DEFAULT_FORWARD_POLICY="ACCEPT"` is
set (Step 3), forwarded packets are allowed by default. If you prefer an explicit rule, add it
directly in `before.rules` under the `*filter` section:

```
*filter
...
# Allow forwarded PostgreSQL traffic from trusted source to container
-A FORWARD -s <source-ip> -d <container-ip> -p tcp --dport 5432 -j ACCEPT
```

The source IP restriction is already enforced by `-s <source-ip>` in the DNAT rule — traffic
from any other IP is never forwarded.

---

## Step 3: Ensure UFW forwards traffic to the bridge

Make sure `/etc/default/ufw` has:

```
DEFAULT_FORWARD_POLICY="ACCEPT"
```

And that traffic on the LXD bridge interface is allowed:

```bash
sudo ufw allow in on <lxd-bridge> from any
```

Replace `<lxd-bridge>` with your bridge name (e.g. `lxdbr0` or `lxdbr1`).

---

## Step 4: Reload UFW

```bash
sudo ufw reload
```

---

## Verify

From the trusted source server, test the connection:

```bash
psql -h <host-ip> -U <db-user> -d <db-name>
```

On the host, confirm the DNAT rule is active:

```bash
sudo iptables -t nat -L PREROUTING -n -v
```

---

## Notes

- The `-s <source-ip>` in the DNAT rule is the key guard — traffic from any other IP is never
  forwarded into the container.
- UFW reloads rebuild the filter table but preserve `before.rules`, so the DNAT rule survives
  `ufw reload`. It does **not** survive a full `iptables -F` or manual nat table flush.
- For PostgreSQL specifically, configure `pg_hba.conf` **inside the container** to whitelist
  `<source-ip>` directly. Because there is no MASQUERADE/SNAT, the container sees the original
  source IP — not the host's bridge IP. Add a line like:
  ```
  hostssl   <dbname>   <dbuser>   <source-ip>/32   scram-sha-256
  ```
  This gives a second layer of access control independent of the firewall.

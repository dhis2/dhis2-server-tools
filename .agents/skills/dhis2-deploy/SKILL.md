---
name: dhis2-deploy
description: >-
  Runs dhis2-server-tools Ansible playbooks safely — deploy.sh, ansible-playbook
  dhis2.yml, tag-scoped runs, check mode, and the destructive delete-instance
  flow. Use when deploying DHIS2, running or re-running the playbook, limiting a
  run to one component, or deleting a DHIS2 instance. Not for DHIS2 version
  upgrades or WAR pin planning — use dhis2-upgrade. Not for inventory layout —
  use dhis2-inventory.
license: BSD-2-Clause
compatibility: Requires Ansible >=2.15, Ubuntu 22.04/24.04 targets. LXD path needs lxc CLI and root or lxd-group on the hypervisor; SSH path needs working SSH to every host.
metadata:
  project: dhis2-server-tools
  version: "1.0"
---

# DHIS2 deploy

Run dhis2-server-tools playbooks with the right scope and without destructive surprises.

## Safety rules

1. **Dry-run first on existing systems.** For any change to an already-deployed environment, run check mode and review before the real run (LXD: `sudo ansible-playbook dhis2.yml --check --diff`). Skip check mode only for a fresh install.
2. **Never run the delete flow on your own initiative.** Deleting an instance requires the human to explicitly confirm the instance name. See "Deleting an instance" for the two independent switches it requires.
3. **Never put a vault password on the command line.** Use `--vault-id prod@prompt` or `--vault-password-file <path>`.
4. **Scope runs with tags and `--limit`** instead of re-running everything when only one component changed.
5. deploy.sh refuses to run without an active UFW firewall — that is intentional; enable UFW (allowing SSH first), do not bypass the check.

## Credential access

**Default deny:** do not read, decrypt, or print secrets unless a step in this skill explicitly requires it. Deploy needs **transport** credentials only: SSH/sudo prompts and vault unlock via `--vault-id …@prompt` or `--vault-password-file <path>`. Do not dump DB passwords, `dhis.conf`, `/opt/ansible/secrets/`, WireGuard private keys, S3 keys, or TLS private keys to debug a deploy — verify with HTTP status / login page load.

## Fresh install

LXD single-server (run on the target host):

```bash
cd deploy/
sudo ./deploy.sh
```

`deploy.sh` creates `inventory/hosts` from the template if missing (mode 600), installs Ansible if needed, installs/upgrades `community.general` via `ansible-galaxy`, and runs `dhis2.yml`. It does **not** install `community.postgresql` — install that collection yourself when needed. If any host line has `ansible_connection=ssh` it runs with `-kK` (SSH + sudo password prompts).

Distributed/SSH (run on the ansible controller):

```bash
cd deploy/
ansible-galaxy collection install community.general community.postgresql
ansible-playbook dhis2.yml -u <ssh_user> -K -k    # drop -k with SSH keys, -K with passwordless sudo
```

Preflight for SSH mode: `ansible 'all:!127.0.0.1' -m ping -u <ssh_user> -k` must succeed for every host.

**LXD privilege:** `ansible_connection=lxd` needs to talk to the LXD socket and create temp dirs inside containers. Run playbooks as root (`sudo ansible-playbook …`) or as a user in the `lxd` group. Unprivileged check-mode often ends `UNREACHABLE` with a temp-directory error — that is a privilege problem, not a broken inventory.

After a successful run, verify:

- `https://<fqdn-or-ip>/dhis` (or the instance base path) — DHIS2 login
- `https://<host>/<instance>-glowroot` — Glowroot APM
- Monitoring: `/munin` or Grafana on the monitor host, per `server_monitoring`

## Scoped runs (tags)

| Goal | Command |
| --- | --- |
| PostgreSQL only | `ansible-playbook dhis2.yml --tags postgresql-install` |
| PostgreSQL conf only | `ansible-playbook dhis2.yml --tags postgresql-conf` |
| Proxy only | `ansible-playbook dhis2.yml --tags proxy-install` |
| Proxy vhost config only | `ansible-playbook dhis2.yml --tags proxy-conf` |
| Instances (create/update) | `ansible-playbook dhis2.yml --tags create-instance` |
| Redeploy WAR only | `ansible-playbook dhis2.yml --tags deploy-war --limit <instance>` |
| Monitoring stack | `ansible-playbook dhis2.yml --tags monitoring` |
| Backup script | `ansible-playbook dhis2.yml --tags backup-script` |
| Unattended upgrades config | `ansible-playbook dhis2.yml --tags unattended-upgrades` |

Combine with `--limit <host|group>` to restrict target hosts. Version changes via `deploy-war` are upgrades — follow the dhis2-upgrade skill first.

## Deleting an instance (destructive)

Removal needs **both** switches; either alone does nothing:

1. Mark the instance in the inventory: append `instance_state=deleted` to its `[instances]` host line.
2. Run with the never-tag: `ansible-playbook dhis2.yml --tags delete-instance`

**Do not use `--limit` with this flow at all.** Cleanup is spread across four groups: container removal on the instance host, proxy upstream cleanup on `[web]`, `pg_hba`/UFW cleanup on `[databases]`, and — when `server_monitoring=munin` — the Munin `hosts.conf` rewrite on `[monitoring]`. Limiting to the instance alone leaves nginx includes, `pg_hba.conf` lines, and UFW rules behind.

Adding the other groups back does **not** make `--limit` safe: `roles/monitoring/templates/hosts.conf.j2` iterates `ansible_play_hosts_all`, which `--limit` shrinks, so the regenerated `hosts.conf` contains only the hosts you named — every other instance silently disappears from Munin. Run it unscoped:

```bash
ansible-playbook dhis2.yml --tags delete-instance
```

This deletes the LXD container, removes its proxy configuration, and strips its PostgreSQL access entries. It does **not** always drop the PostgreSQL database/role — remove those separately if required (`dropdb` / `DROP ROLE`). Before running:

- Have the human confirm the exact instance name in writing.
- Confirm a database backup exists if the data has any value.
- Afterwards, remove the host line (or leave `instance_state=deleted` to keep it excluded from proxy/DB config).

## Troubleshooting a run

- Failed on one host: re-run with `--limit <host>` after fixing, rather than the full inventory.
- `deploy.sh` prompting for a vault password: an encrypted vault file exists under `inventory/` — run `ansible-playbook dhis2.yml --vault-id prod@prompt` or use a vault password file.
- WireGuard-related plays are gated on `wireguard_enabled` — see the dhis2-wireguard skill before touching lockdown behavior.
- Handler/permission errors specific to LXD connections: re-run the failed play scoped with `--tags` + `--limit` after reading the failing task in the role source.
- `ERROR! couldn't resolve module/action 'community.general.ufw'` (or `community.postgresql.*`): collections missing — run `ansible-galaxy collection install community.general community.postgresql`. `deploy.sh` installs `community.general` only.
- Check mode `UNREACHABLE` + temp directory on LXD: re-run with `sudo`. Check mode can still fail later on tasks that skip under `--check` then template skipped registers — treat that as a check-mode limitation, not proof the live config is broken; verify with a scoped real run if needed.

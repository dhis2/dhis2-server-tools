---
name: dhis2-vault
description: >-
  Manages secrets for dhis2-server-tools with ansible-vault — encrypting
  host_vars, the vars.yml/vault.yml split, vault_ variable naming, no_log usage,
  and running playbooks against encrypted inventories. Use when handling
  database passwords, S3 backup credentials, sudo/SSH passwords, Munin logins,
  or any ansible-vault operation in this repository. Not for non-secret
  inventory edits (hosts, IPs, versions) — use dhis2-inventory. Not for running
  playbooks once secrets are already in place — use dhis2-deploy.
license: BSD-2-Clause
compatibility: Requires ansible-vault (Ansible >=2.15). Operates on deploy/inventory/ host_vars and group_vars.
metadata:
  project: dhis2-server-tools
  version: "1.0"
---

# DHIS2 vault and secrets

Handle secrets in dhis2-server-tools without leaking them.

## Non-negotiable rules

1. **Never output decrypted vault contents** into chat, logs, commits, or files outside the vault. To inspect, tell the operator to run `ansible-vault view <file>` in their terminal.
2. **Never commit plaintext secrets.** Before any commit touching `deploy/inventory/`, run `./.agents/skills/dhis2-vault/scripts/check-plaintext-secrets.sh`: files named `vault.yml` must start with `$ANSIBLE_VAULT;`, and no password-looking values may sit in `hosts` or plaintext `vars.yml`.
3. **Every Ansible task that handles a password, token, or key needs `no_log: true`.**
4. Vault passwords go via `--vault-id <label>@prompt` or `--vault-password-file <path>` — never as inline command text.

## Credential access

**Default deny:** do not read, decrypt, or print secrets unless a step in this skill explicitly requires it. This is the only skill whose job is secret material — still minimize what enters agent context. Prefer `ansible-vault create|encrypt|edit|rekey` with the editor/prompt staying with the operator. Confirm encryption and variable **names** only. Accept a new secret from the human once, write-only into vault — do not echo it back. Never `ansible-vault view` into the agent session; never open runtime `dhis.conf` / `/opt/ansible/secrets/*` / WG keys "to compare with vault" unless the human asked to rotate that specific secret (and then do not print the old value).

## What must be vaulted

- Database usernames/passwords (`db_password` and friends)
- S3 backup credentials: `s3_access_key`, `s3_secret_key`, `s3_cluster_id`, `s3_bucket` (in `host_vars/postgres/vault.yml`)
- `ansible_become_pass` / SSH passwords for distributed deployments
- Munin web logins (`munin_users`)
- WireGuard peer private keys (normally generated and kept on the hub — do not relocate them into the repo)

Generated runtime secrets live on the controller in `/opt/ansible/secrets/` (e.g. per-instance DB passwords) — leave them there; do not copy into the repository.

## Preferred pattern: vars.yml + vault.yml

Directory-form host_vars keeps variable names reviewable while values stay encrypted:

```
deploy/inventory/host_vars/postgres/
  vars.yml     # plaintext aliases
  vault.yml    # encrypted, vault_ prefixed values
```

`vars.yml`:

```yaml
db_password: '{{ vault_db_password }}'
s3_access_key: '{{ vault_s3_access_key }}'
s3_secret_key: '{{ vault_s3_secret_key }}'
```

`vault.yml` (then encrypt it):

```yaml
vault_db_password: '...'
vault_s3_access_key: '...'
vault_s3_secret_key: '...'
```

Legacy single-file vaults (`ansible-vault encrypt inventory/host_vars/proxy`) exist in older setups and still work — do not convert them unless asked.

## Commands

```bash
ansible-vault create  deploy/inventory/host_vars/<host>/vault.yml   # new, encrypted from the start
ansible-vault encrypt deploy/inventory/host_vars/<host>/vault.yml   # encrypt existing plaintext
ansible-vault edit    deploy/inventory/host_vars/<host>/vault.yml   # opens $EDITOR
ansible-vault view    deploy/inventory/host_vars/<host>/vault.yml   # read-only (operator terminal)
ansible-vault rekey   deploy/inventory/host_vars/<host>/vault.yml   # rotate vault password
```

Find which files are encrypted:

```bash
grep -rl '^\$ANSIBLE_VAULT' deploy/inventory/
```

Run playbooks against encrypted inventory:

```bash
ansible-playbook dhis2.yml --vault-id prod@prompt
ansible-playbook dhis2.yml --vault-password-file ~/.ansible_vault_pass   # CI: store the file path secretly, never the content in the repo
```

## Leak response

If a secret lands in chat output, a commit, or a plaintext file: treat it as compromised. Rotate the credential (DB password, S3 key, vault password via `rekey`), then purge the plaintext occurrence. Rotation comes first; history cleanup second.

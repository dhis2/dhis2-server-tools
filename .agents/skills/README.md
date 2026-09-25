# Agent Skills for dhis2-server-tools

Instructions for agents, in the [Agent Skills](https://agentskills.io/specification) format. Each folder is one skill: `SKILL.md` plus optional `references/` and `scripts/`.

Ask an agent to do the work. It loads the matching `SKILL.md`. There is no skill binary to run.

## Asking the agent

Name the skill when you care which one runs:

```
Follow dhis2-inventory and add a second instance named training.
```

```
Use dhis2-upgrade. Take dhis from 2.40 to 2.42.
```

Or describe the job and let routing pick. Routing reads the `description` field in each skill's frontmatter (what it does, and when). That text is the source of truth. Do not treat the table below as a second copy.

Name the skill yourself when the request is ambiguous, when the agent ignored it, or when you want that skill's hard stops (delete, restore, lockdown, vault).

## Which skill

| Skill                                                   | Name it when you want to                                                                                    |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| [dhis2-inventory](./dhis2-inventory/SKILL.md)           | Create or edit `deploy/inventory/hosts`, pick LXD / SSH / hybrid, add an instance, set non-secret variables |
| [dhis2-vault](./dhis2-vault/SKILL.md)                   | Encrypt host_vars, put passwords and S3 keys in vault, run playbooks against encrypted inventory            |
| [dhis2-deploy](./dhis2-deploy/SKILL.md)                 | Run `deploy.sh` or `dhis2.yml`, scope with tags / `--limit`, delete an instance                             |
| [dhis2-postgres](./dhis2-postgres/SKILL.md)             | Tune PostgreSQL, apply `pg_*` values, read `dhispg.conf`, change `postgresql_version`                       |
| [dhis2-backup-restore](./dhis2-backup-restore/SKILL.md) | Take, verify, or restore database dumps; see where the cron script actually lives                           |
| [dhis2-wireguard](./dhis2-wireguard/SKILL.md)           | Bring up the VPN mesh, add admin peers, apply or undo service lockdown                                      |
| [dhis2-upgrade](./dhis2-upgrade/SKILL.md)               | Change `dhis2_version` or pin a WAR on an instance that already exists                                      |

New install: inventory, then vault if you have secrets, then deploy. After that, postgres / backup-restore / wireguard only if you need them. Upgrade is for a later version change, not first install.

## What the agent will do

- Dry-run an already-deployed system before applying (`--check --diff`).
- Stop and ask before delete-instance, a destructive restore, or WireGuard lockdown.
- Leave vault unlock, SSH/sudo, and WireGuard private keys in your terminal.
- Refuse to print DB passwords, vault contents, TLS keys, or WireGuard `PrivateKey` into chat.

If it does none of that, name the skill again.

## Scripts

The agent runs these from the repository root. You can run the same commands. Once invoked, the inventory and vault scripts locate `hosts` / inventory from their own path. `pg-show.sh` has no such lookup.

| Script                                           | Skill     | What it checks                                                                                                          |
| ------------------------------------------------ | --------- | ----------------------------------------------------------------------------------------------------------------------- |
| `dhis2-inventory/scripts/validate-inventory.sh`  | inventory | Mode 600, required `[instances]` fields, duplicate `ansible_host`, LXD IPs inside `lxd_network`, password-shaped values |
| `dhis2-postgres/scripts/pg-show.sh`              | postgres  | Running cluster majors and tuned `SHOW` values. `--lxd` from the hypervisor; no flag on the database host               |
| `dhis2-vault/scripts/check-plaintext-secrets.sh` | vault     | `vault.yml` starts with `$ANSIBLE_VAULT;`; no password-looking values in `hosts` or plaintext `vars.yml`                |

None of them print secrets. `validate-inventory.sh` does not check variable names or reachability; still dry-run before apply.

## How the agent finds them

**Cursor** loads `.agents/skills/` on its own. No extra setup.

**Claude Code** loads `.claude/skills/` only. After a clone, or when a skill is added:

```bash
mkdir -p .claude/skills
for s in .agents/skills/dhis2-*; do
  ln -sfn "../../$s" ".claude/skills/$(basename "$s")"
done
```

Restart Claude Code. `.claude/` is gitignored, so every clone repeats this. Claude Code cloud sessions and routines that only see a committed `.claude/skills/` will not get these skills.

In Claude Code, `/dhis2-inventory` (and the other `/dhis2-*` names) also works. `/vault` is a short local cheat-sheet under `.claude/commands/`. Vault work belongs to `dhis2-vault` (`/dhis2-vault`).

**Other Agent Skills clients** should point at this directory. See the [specification](https://agentskills.io/specification).

## Credential access

Each `SKILL.md` has its own default-deny list. In short: do not read DB passwords, decrypt vaults into chat, dump WireGuard private keys, or print S3/TLS secrets. Leave SSH/sudo/vault-unlock prompts with the operator.

## Maintaining skills

When toolkit behavior changes (version matrix, tags, role paths), update the affected skill in the same PR and bump `metadata.version` in that skill's frontmatter. Validate with `skills-ref validate .agents/skills/<skill>` when available.

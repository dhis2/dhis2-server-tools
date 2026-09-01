# Agent Skills for dhis2-server-tools

Portable skills following the [Agent Skills](https://agentskills.io/specification) standard. Canonical copies live here under `.agents/skills/`. Claude Code discovers them via symlinks in `.claude/skills/` (restart Claude Code after creating those links).

Each skill is a folder with `SKILL.md` plus optional `references/` and `scripts/`. Descriptions in each skill's frontmatter are the source of truth for routing — do not duplicate them here.

## Skills

Routing comes from each skill's `description` frontmatter — read that, not this list.

- [dhis2-inventory](./dhis2-inventory/SKILL.md)
- [dhis2-deploy](./dhis2-deploy/SKILL.md)
- [dhis2-upgrade](./dhis2-upgrade/SKILL.md)
- [dhis2-postgres](./dhis2-postgres/SKILL.md)
- [dhis2-backup-restore](./dhis2-backup-restore/SKILL.md)
- [dhis2-wireguard](./dhis2-wireguard/SKILL.md)
- [dhis2-vault](./dhis2-vault/SKILL.md)

**Greenfield order:** inventory → vault (if secrets) → deploy → postgres / backup-restore / wireguard as needed → upgrade only when changing versions later.

## Credential access

Every skill carries its own default-deny statement and the exceptions it needs; each `SKILL.md` is
self-contained on this point, so nothing here is load-bearing. In short: do not read DB passwords, decrypt
vaults into chat, dump WireGuard private keys, or print S3/TLS secrets, and leave SSH/sudo/vault-unlock prompts
with the operator where possible.

## Claude Code discovery

Claude Code only loads project skills from `.claude/skills/`, not `.agents/skills/`. After clone (or when skills are added), create symlinks locally and restart Claude Code:

```bash
mkdir -p .claude/skills
for s in .agents/skills/dhis2-*; do
  ln -sfn "../../$s" ".claude/skills/$(basename "$s")"
done
```

`.claude/` is gitignored (local agent state); the canonical skill trees live under `.agents/skills/` and are what you commit.

Slash command `/vault` (`.claude/commands/vault.md`) is a short cheat-sheet; the `dhis2-vault` skill owns full vault guidance (`/dhis2-vault`).

## Maintaining skills

When toolkit behavior changes (version matrix, tags, role paths), update the affected skill in the same PR and bump `metadata.version` in that skill's frontmatter. Validate with `skills-ref validate .agents/skills/<skill>` when available.

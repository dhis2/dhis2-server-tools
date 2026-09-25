---
name: dhis2-upgrade
description: >-
  Plans and executes DHIS2 version upgrades in dhis2-server-tools deployments —
  changing dhis2_version or dhis2_war_file, enabling dhis2_auto_upgrade,
  redeploying WAR files, and handling the Tomcat 10 / Ubuntu 24.04 requirement
  for DHIS2 2.42+. Use when upgrading, downgrading, or redeploying a DHIS2
  instance, or when a user mentions changing the DHIS2 version. Not for
  first-time inventory layout — use dhis2-inventory. Not for playbook mechanics
  or delete-instance — use dhis2-deploy.
license: BSD-2-Clause
compatibility: Requires Ansible >=2.15 and an existing instance guest (Ubuntu 22.04 or 24.04). Guest OS/Java/Tomcat selection follows the toolkit version matrix.
metadata:
  project: dhis2-server-tools
  version: "1.0"
---

# DHIS2 upgrade

Upgrade a DHIS2 instance managed by dhis2-server-tools safely.

## Hard rules

1. **Backup before any upgrade.** Confirm a recent database backup exists before changing versions or enabling `dhis2_auto_upgrade`. No backup → stop and make one first (see dhis2-backup-restore for where `/usr/local/bin/dhis2-backup` lives in LXD vs SSH, or `docs/how-to/db-backup-and-restore.md`).
2. **DHIS2 2.42+ cannot be an in-place upgrade on an old guest.** It requires Tomcat 10 and Java 17, which this toolkit only installs on Ubuntu 24.04 guests. Existing containers/VMs created on 22.04 cannot be reimaged by changing inventory values.
3. **`dhis2_war_file` overrides `dhis2_version`.** If both are set, the WAR file wins. It also skips Java/Tomcat auto-selection (`set-dhis2-url.yml` is gated on `dhis2_war_file` undefined), so set `java_version` explicitly when pinning a WAR — otherwise the role default (`JAVA_VERSION: 17`) applies even for older lines that need JDK 11. Check for both before reasoning about versions.
4. **Never present a downgrade as "change the WAR back".** Downgrading across a major version means a different Tomcat/Java/OS stack plus a database restored from the pre-upgrade backup.
5. Do not invent database schema or metadata migration steps. Point to the official upgrade guide and version release notes: https://docs.dhis2.org/en/manage/concepts/upgrade-guide.html

## Credential access

**Default deny:** do not read, decrypt, or print secrets unless a step in this skill explicitly requires it. Version planning and WAR redeploy need no secrets. Read inventory, About page / `pom.properties`, and `lsb_release` / `java -version` / `dpkg -l 'tomcat*'`. If reading `dhis.conf` for the JDBC URL only, use `grep -E '^\s*connection\.url'` and never print `connection.password`. Do not open vault, S3, WG keys, or app admin passwords.

## Decide the upgrade path

Determine current and target versions first. Prefer the instance host line in `inventory/hosts` over `[instances:vars]` (host-line values win). Also check the running instance:

- Login/About page, or
- Exploded webapp under Tomcat `webapps/<base_path>/` (often the inventory hostname, e.g. `webapps/dhis/`). Prefer `META-INF/maven/org.hisp.dhis/dhis-web-server/pom.properties` (`version=…`). `webapps/ROOT` may be a stub; `build.properties` is often absent.

**Patch update within the same major (e.g. 2.41.1 → 2.41.3)?**
→ In-place. Set the full version (`dhis2_version=2.41.3`) or set `dhis2_auto_upgrade=true` to track the latest patch of the major. Then run:

```bash
ansible-playbook dhis2.yml --tags deploy-war --limit <instance>
```

**Major upgrade to 2.41 or lower (e.g. 2.39 → 2.41)?**
→ In-place is supported (Tomcat 9 on both 22.04 and 24.04 guests). Update `dhis2_version`, back up, run with `--tags create-instance` or full playbook. Read the release notes for schema changes; the first startup performs the DB migration and can take a long time.

**Major upgrade to 2.42+ from an instance created before 24.04?**
→ **New instance migration.** Do not edit the version in place:

1. Add a new `[instances]` host line with a new name/IP and `dhis2_version=2.42` (the toolkit creates it on a 24.04 guest with Tomcat 10 automatically).
2. Deploy it, pointing at the same `database_host` **only after** backing up, or restore the backup into a fresh database for a test run first.
3. Verify, then retire the old instance (see delete guardrails in the dhis2-deploy skill).

**Only redeploying the same WAR (config change, corrupted webapp)?**
→ `ansible-playbook dhis2.yml --tags deploy-war --limit <instance>`. No version change, still confirm a backup exists.

## Version requirements

The toolkit selects Java/Tomcat/guest OS from the DHIS2 version. Read [references/version-matrix.md](references/version-matrix.md) when the target and current DHIS2 majors differ, or when guest OS / Java / Tomcat selection is in question.

Quick facts:

- 2.42+ → Java 17, Tomcat 10, Ubuntu 24.04 only
- 2.41 → Java 17, Tomcat 9
- 2.35–2.40 → toolkit installs Java 11 (official docs recommend 17 for 2.40)
- Version format: `2.42` installs the latest stable of that line; `2.42.2.2` pins exactly. Invalid versions fail validation against releases.dhis2.org.

## Verification after upgrade

1. Instance responds: `https://<host>/<base_path>` (login page loads).
2. Version shown in the login page / About matches the target.
3. Watch Tomcat logs during first startup — schema migration errors appear there.
4. Only three most recent major releases are supported upstream; flag if the target is already out of support.

## Planning a large upgrade

For multi-version jumps, OS end-of-life, or PostgreSQL upgrades in the same window, follow `docs/Upgrade-Guide.md` (in this repo) — it covers backup types, test strategy, upgrade calendar, and roles. Upgrade one layer at a time: OS first, then database, then DHIS2.

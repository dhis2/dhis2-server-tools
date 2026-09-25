# DHIS2 version matrix

## Contents
- Toolkit behavior (what this repo actually installs)
- Official DHIS2 requirements
- Deltas between toolkit and official docs
- Where the logic lives in code

## Toolkit behavior

Selection logic in `deploy/filter_plugins/custom_filters.py` (`get_dhis2_instance_specs`):

| DHIS2 version | JDK installed | Tomcat | Allowed guest OS |
|---|---|---|---|
| ≥ 2.42 (or auto-upgrade toward it) | 17 | 10 | 24.04 only |
| 2.41 | 17 | 9 | 22.04 or 24.04 |
| 2.35 – 2.40 | 11 | 9 | 22.04 or 24.04 |
| < 2.35 | 8 | 9 | 22.04 or 24.04 |

Tomcat package choice is driven by the **guest OS**, not directly by the DHIS2 version (`create-instance/tasks/tomcat-setup.yml`):

- Ubuntu 24.04 → `tomcat10`, `tomcat10-admin`, plus `tomcat-jakartaee-migration`
- Otherwise → `tomcat9`, `tomcat9-admin`

The runtime `tomcat_version` fact maps `24.04 → 10`, else `9`. WARs for pre-2.42 DHIS2 deployed on Tomcat 10 go through the Jakarta EE migration tool automatically.

**Guest OS is fixed at container/VM creation.** The toolkit picks the guest image from the DHIS2 version when it first creates the container. Editing `guest_os` or `dhis2_version` later does not reimage an existing guest — that is why 2.42 needs a new instance when the old one runs 22.04.

**`dhis2_war_file` skips auto-selection.** When set, `set-dhis2-url.yml` is skipped, so Java/Tomcat are not chosen from the version matrix. Pin `java_version` (and ensure the guest already has a compatible Tomcat) when deploying an older WAR by URL.

## Official DHIS2 requirements

From https://docs.dhis2.org/en/manage/manage.html (DHIS2 version compatibility matrix):

| DHIS2 | JRE recommended | JRE minimum | Tomcat | Ubuntu LTS |
|---|---|---|---|---|
| 2.42 | 17 | 17 | 10 | 24.04 |
| 2.41 | 17 | 17 | 9 | 22.04 |
| 2.40 | 17 | 11 | 9 | 22.04 |
| 2.38 | 11 | 11 | 9 | 22.04 |
| 2.35 | 11 | 8 | 9 | 22.04 |
| Pre-2.35 | 8 | 8 | 9 | 22.04 |

Database: PostgreSQL 13+ (16 recommended), PostGIS 2.2+ (3 recommended). Toolkit default is PostgreSQL 16 with extensions `postgis`, `btree_gin`, `pg_trgm`.

Support window: only the three most recent major DHIS2 releases receive patches.

## Deltas between toolkit and official docs

- **2.40 Java:** official docs recommend JRE 17 (minimum 11); the toolkit installs 11 for 2.35–2.40. Both work; do not "fix" a running instance without being asked.
- **Version pinning:** `dhis2_version=2.42` resolves to the latest stable release of that line from releases.dhis2.org; a full version like `2.41.2.5` pins exactly and must exist upstream.
- **Precedence:** `dhis2_war_file` (URL or local path) beats `dhis2_version` when both are defined.

## Where the logic lives in code

Re-read these before relying on this file — they are the source of truth if the repo has changed:

- `deploy/filter_plugins/custom_filters.py` — `get_dhis2_instance_specs`, `normalize_dhis2_version`, `tomcat_version`
- `deploy/roles/create-instance/tasks/tomcat-setup.yml` — package selection
- `deploy/roles/create-instance/tasks/deploy-war.yml` — WAR deploy + Jakarta migration conditions
- `deploy/roles/create-instance/tasks/lxd.yml` / `ssh.yml` — guest OS selection at create time

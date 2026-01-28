# Apache Doris Installation & Configuration via Ansible (Ubuntu 24.04 + LXD)

This repository contains an Ansible playbook that installs and configures **Apache Doris** on Ubuntu 24.04.  
It supports running Doris inside an **LXD container**, configuring system requirements, deploying FE/BE services, creating analytics databases, and integrating with DHIS2.

---

## 🚀 Features

- Creates and configures an **LXD container** for the Doris node.
- Installs **Java 17**, sysctl tuning, and high file descriptor limits.
- Downloads and installs **Apache Doris** (FE + BE).
- Creates **systemd services** for Doris frontend and backend.
- Creates the **analytics** database in Doris.
- Creates Doris users and assigns required permissions.
- Configures **DHIS2** to use Doris as its analytics backend.
- Optionally configures **PostgreSQL** (`pg_hba.conf`, UFW rules) to allow Doris connectivity.

---

## 📦 Requirements

- **Ansible ≥ 2.15**
- **Ubuntu 24.04** on target or host running LXD
- **LXD ≥ 5.x**
-  running dhis2 install
- Installed Ansible collections:
  ```bash


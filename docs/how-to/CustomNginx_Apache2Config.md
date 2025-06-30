### Nginx Configuration

Ansible generates Nginx configuration files based on whether a **Fully Qualified Domain Name (FQDN)** is defined:

| Condition          | Ansible-Generated File              |
| ------------------ | ----------------------------------- |
| `fqdn` is defined  | `/etc/nginx/conf.d/{{ fqdn }}.conf` |
| `fqdn` not defined | `/etc/nginx/conf.d/default.conf`    |

These files are **fully managed by Ansible**, meaning **any manual changes will be lost** when the playbook is re-applied.

#### Safe Manual Customization

Each Ansible-generated config file includes an **explicit static file**, which is created during the initial setup and never modified by Ansible after that.

| Condition          | Included Static File (safe for manual edits) |
| ------------------ | -------------------------------------------- |
| `fqdn` is defined  | `/etc/nginx/static/{{ fqdn }}.conf`          |
| `fqdn` not defined | `/etc/nginx/static/default.conf`             |

Customize only the static file included in your dynamic configuration. Since this is not touched by Ansible, it will **persist across playbook runs**.

**Important**: After making changes, manually reload Nginx:

```bash
sudo systemctl reload nginx
```

---

### Apache2 Configuration

Apache2 uses a similar setup to Nginx, with a slightly different directory structure.

#### Ansible-Managed Files

Ansible generates the main config file based on whether a **Fully Qualified Domain Name (FQDN)** is defined.  
These files are overwritten on every playbook run — do not edit them manually.

| Condition          | Ansible-Generated File                |
|--------------------|---------------------------------------|
| `fqdn` is defined  | `/etc/apache2/conf.d/{{ fqdn }}.conf` |
| `fqdn` not defined | `/etc/apache2/conf.d/default.conf`    |

#### Static Files for Manual Edits

Each Ansible config includes a static file created at setup and never modified afterward.  
Place all manual changes here.

| Condition          | Static File (safe for manual edits)     |
|--------------------|------------------------------------------|
| `fqdn` is defined  | `/etc/apache2/static/{{ fqdn }}.conf`    |
| `fqdn` not defined | `/etc/apache2/static/default.conf`       |

> **Note** 
>
> Always make manual changes in the static file. These are explicitly included in the main Ansible config.

#### Reload Apache After Edits

```bash
sudo systemctl reload apache2
```

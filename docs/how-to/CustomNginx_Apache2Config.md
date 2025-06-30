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

Apache2 uses a similar setup with a slightly different directory layout:

| Role                         | File Path Example                                                                         |
| ---------------------------- | ----------------------------------------------------------------------------------------- |
| Ansible-managed config       | `/etc/apache2/sites-enabled/{{ fqdn }}.conf` or `/etc/apache2/sites-enabled/default.conf` |
| Static file for custom edits | `/etc/apache2/static/{{ fqdn }}.conf` or `/etc/apache2/static/default.conf`               |

As with Nginx, the Ansible-managed Apache config explicitly includes the relevant static file. All manual changes should go into this static file, not the Ansible-managed one.

After editing, reload Apache:

```bash
sudo systemctl reload apache2
```

---

#### Summary

| Service | Ansible-Managed File                                           | Static Included File (editable)                         | Notes                         |
| ------- | -------------------------------------------------------------- | ------------------------------------------------------- | ----------------------------- |
| Nginx   | `/etc/nginx/conf.d/{{ fqdn }}.conf` or `default.conf`          | `/etc/nginx/static/{{ fqdn }}.conf` or `default.conf`   | Manually reload after editing |
| Apache2 | `/etc/apache2/sites-enabled/{{ fqdn }}.conf` or `default.conf` | `/etc/apache2/static/{{ fqdn }}.conf` or `default.conf` | Manually reload after editing |

---

This setup allows Ansible to manage core configuration while giving you a safe place to apply persistent manual customizations.


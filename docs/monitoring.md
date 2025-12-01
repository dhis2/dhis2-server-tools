# Monitoring

Monitoring covers both application and server resources. Set `server_monitoring` in your inventory to choose your stack.

## Available Options

| Value     | Description                     |
| --------- | ------------------------------- |
| `munin`   | Munin server/client monitoring  |
| `zabbix`  | Zabbix server/client monitoring |
| `grafana` | Grafana + Prometheus stack      |

## Grafana/Prometheus

Deploys Prometheus with postgres exporter and Grafana with pre-configured dashboards.

Access: `https://your-domain/grafana`

### Security

On first deployment, the default Grafana admin password is automatically rotated to a secure random password.

**Retrieve password:**

```
sudo cat /opt/ansible/secrets/grafana_admin_password
```

All secrets are stored in `/opt/ansible/secrets/` with `0600` permissions.

## Munin

Munin provides server resource monitoring.

**Server setup:**

- Installs munin server on monitoring host
- Deploys configuration

**Client setup:**

- Installs munin-node on monitored hosts
- Opens firewall port 4949 from monitoring server
- Registers nodes with server

Access: `https://your-domain/munin`

## Zabbix

Zabbix provides comprehensive server and application monitoring.

**Server setup:**

- Installs and configures zabbix server

**Client setup:**

- Installs zabbix agent on monitored hosts
- Opens firewall port 10050

## Application Monitoring

DHIS2 application performance is monitored with [Glowroot](https://glowroot.org/) APM.

Access: `https://your-domain/dhis-glowroot`

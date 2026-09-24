# Alerting

Centralized alerting hub co-located on the `[monitoring]` host. Prometheus
Alertmanager handles routing, dedup, and silencing. Glowroot APM alerts are
forwarded into the same hub.

Infra alerts (CPU, memory, disk, PostgreSQL) require `server_monitoring=grafana`
(the deployable Grafana + Prometheus stack). Glowroot APM alerts work with the
hub whenever `app_monitoring=glowroot`, including under Munin.

## Architecture

```
[monitoring]
  Prometheus ──127.0.0.1:9093──► Alertmanager ──► Telegram / Slack / Email
  Grafana    (Alertmanager datasource for silences UI only)
  Glowroot-fwd :9099 ──loopback──► Alertmanager

[instances] Glowroot ──HTTP POST──► monitor:9099/?token=...
[web] proxy ──► Grafana only (never Alertmanager or the forwarder)
```

- Alertmanager binds `127.0.0.1:9093` (no inbound from other hosts).
- The Glowroot forwarder binds `0.0.0.0:9099`; UFW allows only `[instances]`
  source IPs (`ansible_host`, typically the LXD bridge address).
- Grafana does **not** own alert rules or contact points. Prometheus rules fire
  into Alertmanager; Grafana’s Alertmanager datasource is for silences / AM UI.

## Secrets (`/opt/ansible/secrets/`)

Same controller directory used for database passwords. Do **not** put tokens in
`[all:vars]`.

### User-supplied (create these files)

| File                          | Purpose                            |
| ----------------------------- | ---------------------------------- |
| `alerting_telegram_bot_token` | Telegram bot token from @BotFather |
| `alerting_telegram_chat_id`   | Telegram chat / group ID           |
| `alerting_slack_webhook_url`  | Slack incoming webhook URL         |
| `alerting_smtp_auth_password` | Optional SMTP password for email   |

```bash
sudo mkdir -p /opt/ansible/secrets
echo -n '123456:ABC-DEF...' | sudo tee /opt/ansible/secrets/alerting_telegram_bot_token
echo -n '-1001234567890' | sudo tee /opt/ansible/secrets/alerting_telegram_chat_id
sudo chown "$USER:" /opt/ansible/secrets /opt/ansible/secrets/alerting_*
sudo chmod 700 /opt/ansible/secrets
sudo chmod 600 /opt/ansible/secrets/alerting_*
```

Use at least one channel (Telegram pair, Slack URL, or email settings in
inventory).

### Auto-generated (created on first run)

| File                                | Purpose                                                 |
| ----------------------------------- | ------------------------------------------------------- |
| `alerting_web_password`             | Alertmanager / Prometheus / Grafana basic-auth password |
| `alerting_glowroot_forwarder_token` | Shared `?token=` for instance → forwarder               |

The Alertmanager bcrypt hash is generated once on the monitoring host under
`/etc/alertmanager/secrets/web_password.bcrypt` (not on the controller).

No ansible-vault step. Re-runs reuse the same files for idempotence.

## Quick start (Telegram)

1. Create a bot with [@BotFather](https://t.me/BotFather) and note the token.
2. Add the bot to your chat/group and get the chat ID.
3. Write the secret files as above.
4. In `inventory/hosts`:

```ini
server_monitoring=grafana
alerting_enabled=true
alerting_default_contact_point=telegram
```

5. Deploy:

```bash
ansible-playbook dhis2.yml --tags alerting
```

Or include monitoring/create-instance on a full run so Prometheus/Grafana/Glowroot
exist before peer wiring.

## Slack / Email

**Slack:** create `/opt/ansible/secrets/alerting_slack_webhook_url` and set
`alerting_default_contact_point=slack` (optional `alerting_slack_channel` in
inventory or `host_vars/monitor/vars.yml`).

**Email:** set non-secret SMTP settings in inventory / host_vars
(`alerting_email_addresses`, `alerting_smtp_smarthost`, `alerting_smtp_from`,
optional `alerting_smtp_auth_username`). Put the SMTP password in
`/opt/ansible/secrets/alerting_smtp_auth_password` if needed.

## Glowroot APM

When `alerting_enabled=true` and `app_monitoring=glowroot`, the alerting role
patches each instance’s Glowroot `admin.json` / `config.json` (change-only) to
post Slack-formatted webhooks at:

`http://<monitor ansible_host>:9099/?token=<shared secret>`

The shared secret is auto-generated on the controller. No per-instance Telegram
forwarder. Set `alerting_glowroot_force_config=true` only as a break-glass
rewrite of alert rules.

On SSH/distributed installs, also allow instance→monitoring TCP 9099 in any
cloud security group / NACL. UFW on the monitoring host is opened automatically
from each instance `ansible_host`.

## Alert rules

### Infrastructure (Prometheus → Alertmanager)

| Alert                  | Condition             | Duration | Severity | Default    |
| ---------------------- | --------------------- | -------- | -------- | ---------- |
| Instance Down          | Target unreachable    | 5m       | critical | up == 0    |
| High CPU               | CPU usage             | 10m      | warning  | > 85%      |
| High Memory            | Memory usage          | 5m       | warning  | > 90%      |
| Disk Space Warning     | Free space low        | 5m       | warning  | < 15%      |
| Disk Space Critical    | Free space very low   | 5m       | critical | < 5%       |
| PostgreSQL Down        | DB unreachable        | 2m       | critical | pg_up == 0 |
| PostgreSQL Connections | Connection saturation | 5m       | warning  | > 80%      |
| Long Running Query     | Query duration        | 5m       | warning  | > 1 hour   |
| DHIS2 Endpoint Down    | Metrics unreachable   | 5m       | critical | up == 0    |

### Glowroot

| Alert             | Condition         | Duration | Severity | Default            |
| ----------------- | ----------------- | -------- | -------- | ------------------ |
| Heartbeat         | JVM/agent down    | 5m       | critical | No heartbeat       |
| Error Rate        | Web errors        | 5m       | critical | > 10%              |
| Response Time p95 | Slow responses    | 10m      | high     | > 10,000 ms        |
| Heap Memory       | JVM heap pressure | 5m       | high     | > 80% of heap size |

Threshold variables: `alert_cpu_threshold`, `alert_memory_threshold`,
`alert_disk_warning_pct`, `alert_disk_critical_pct`, `alert_pg_connection_pct`,
and the `glowroot_alert_*` defaults in `roles/alerting/defaults/main.yml`.

## Munin

`alerting_enabled=true` with `server_monitoring=munin` installs the hub and
Glowroot path only, and prints a warning. Munin is not bridged to Alertmanager.
Legacy `munin_alerts` contact configuration is unchanged and separate from the hub.

## Testing

```bash
# Telegram Bot API
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" -d "text=Test from DHIS2 alerting hub"

# Forwarder rejects bad token
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
  "http://<monitor-ip>:9099/?token=wrong" \
  -H "Content-Type: application/json" \
  -d '{"text":"test"}'
# expect 401

# Forwarder → Alertmanager (token from /opt/ansible/secrets/alerting_glowroot_forwarder_token)
TOKEN=$(sudo cat /opt/ansible/secrets/alerting_glowroot_forwarder_token)
curl -s -X POST "http://<monitor-ip>:9099/?token=${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "attachments": [{
      "fallback": "[dhis] Test alert - triggered",
      "pretext": "[dhis] Test alert triggered",
      "color": "danger",
      "text": "This is a test alert"
    }]
  }'

# Alertmanager requires basic auth (password in alerting_web_password)
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9093/api/v2/alerts
# expect 401 on the monitoring host

promtool check rules /etc/prometheus/rules/dhis2-alerts.yml
amtool check-config /etc/alertmanager/alertmanager.yml
```

Manual smoke: breach CPU (or temporarily lower `alert_cpu_threshold`) and
confirm Telegram/Slack; trigger a Glowroot slow-transaction alert and confirm
the forwarder receives a POST.

## Troubleshooting

- **No infra alerts:** confirm `server_monitoring=grafana`, Prometheus is
  scraping, and `/etc/prometheus/rules/dhis2-alerts.yml` loads after reload.
- **No Glowroot alerts:** check UFW allow from the instance `ansible_host` to
  `:9099` (WireGuard VPN CIDR alone is not enough on LXD), forwarder unit
  logs, and that Glowroot `slackWebhookId` is `dhis2-hub`.
- **401 from Alertmanager:** Prometheus `password_file` and Grafana datasource
  password must match `/opt/ansible/secrets/alerting_web_password`.
- **Missing channel assert:** ensure token files exist under
  `/opt/ansible/secrets/` and are readable by the deploy user.
- **armhf hosts:** upstream Alertmanager builds are amd64/arm64 only; the role
  fails clearly on unsupported arches.

# Alerting

DHIS2 server tools supports alerting via Telegram, Slack, and email for both infrastructure monitoring (Grafana/Prometheus) and application monitoring (Glowroot APM).

## Quick Start: Telegram

Requires `server_monitoring=grafana` or `server_monitoring=grafana/prometheus`.

### 1. Create a Telegram Bot

- Message [@BotFather](https://t.me/BotFather) on Telegram
- Send `/newbot`, follow the prompts
- Save the bot token (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Get Your Chat ID

- Add the bot to your Telegram group
- Message [@getmyid_bot](https://t.me/getmyid_bot) in the group, or use [@userinfobot](https://t.me/userinfobot)
- Save the chat ID (e.g., `-1001234567890` for groups)

### 3. Configure and Deploy

Edit `deploy/inventory/hosts` and update the `[all:vars]` section:

```ini
server_monitoring=grafana
alerting_enabled=true
alerting_default_contact_point=telegram
alerting_telegram_bot_token=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
alerting_telegram_chat_id=-1001234567890
```

Then deploy:

```bash
ansible-playbook dhis2.yml --tags monitoring,alerting
```

After deployment, verify alerts are working -- see [Testing Alerts](#testing-alerts) below.

> **Note:** The `inventory/hosts` file is gitignored, so your token won't be committed to version control. For production hardening, see [Securing Credentials with Vault](#securing-credentials-with-vault) below.

## Quick Start: Slack

Same as Telegram, but set these variables instead:

```ini
alerting_default_contact_point=slack
alerting_slack_webhook_url=https://hooks.slack.com/services/T.../B.../xxx
alerting_slack_channel=#dhis2-alerts
```

Create an incoming webhook at https://api.slack.com/messaging/webhooks.

---

## Alert Rules Reference

### Infrastructure Alerts (Grafana/Prometheus)

| Alert                  | Condition             | Duration | Severity | Default Threshold |
| ---------------------- | --------------------- | -------- | -------- | ----------------- |
| Instance Down          | Target unreachable    | 5m       | critical | up == 0           |
| High CPU               | CPU usage             | 10m      | warning  | > 85%             |
| High Memory            | Memory usage          | 5m       | warning  | > 90%             |
| Disk Space Warning     | Free space low        | 5m       | warning  | < 15%             |
| Disk Space Critical    | Free space very low   | 5m       | critical | < 5%              |
| PostgreSQL Down        | DB unreachable        | 2m       | critical | pg_up == 0        |
| PostgreSQL Connections | Connection saturation | 5m       | warning  | > 80% of max      |
| Long Running Query     | Query duration        | 5m       | warning  | > 1 hour          |
| DHIS2 Endpoint Down    | Metrics unreachable   | 5m       | critical | up == 0           |

### Glowroot APM Alerts (Optional)

| Alert             | Condition         | Duration | Severity | Default Threshold         |
| ----------------- | ----------------- | -------- | -------- | ------------------------- |
| Heartbeat         | JVM/agent down    | 5m       | critical | No heartbeat              |
| Error Rate        | Web errors        | 5m       | critical | > 10%                     |
| Response Time p95 | Slow responses    | 10m      | high     | > 10,000 ms               |
| Heap Memory       | JVM heap pressure | 5m       | high     | > 80% of heap_memory_size |

---

## Customizing Thresholds

Override these variables in `host_vars/monitor/vars.yml` or `inventory/hosts`:

### Infrastructure Thresholds

| Variable                  | Default | Description                       |
| ------------------------- | ------- | --------------------------------- |
| `alert_cpu_threshold`     | 85      | CPU usage percentage              |
| `alert_memory_threshold`  | 90      | Memory usage percentage           |
| `alert_disk_warning_pct`  | 15      | Disk free space warning (%)       |
| `alert_disk_critical_pct` | 5       | Disk free space critical (%)      |
| `alert_pg_connection_pct` | 80      | PostgreSQL connections (% of max) |

### Glowroot Thresholds

| Variable                                        | Default | Description                         |
| ----------------------------------------------- | ------- | ----------------------------------- |
| `glowroot_alert_p95_threshold_ms`               | 10000   | p95 response time (ms)              |
| `glowroot_alert_p95_time_period_seconds`        | 600     | Evaluation window for p95           |
| `glowroot_alert_error_rate_threshold`           | 10.0    | Error rate percentage               |
| `glowroot_alert_error_rate_time_period_seconds` | 300     | Evaluation window for errors        |
| `glowroot_alert_heartbeat_seconds`              | 300     | Heartbeat timeout                   |
| `glowroot_alert_min_transaction_count`          | 10      | Min transactions before alert fires |

---

## Glowroot APM Alerts

Glowroot alerts on transaction times, error rates, JVM metrics, and heartbeat. These require `app_monitoring=glowroot` (the default) and Grafana/Prometheus alerting configured first (steps 1-3 above) since they share the same bot token and chat ID.

### How It Works

Glowroot supports Slack natively but not Telegram. A Python forwarder bridges the gap:

1. `glowroot-telegram-forwarder.py` runs as a systemd service on each instance host
2. Glowroot's Slack webhook points at `http://127.0.0.1:9099` (the forwarder)
3. The forwarder translates the Slack payload to a Telegram Bot API call

The forwarder uses only Python 3 stdlib, binds to localhost, auto-restarts via systemd, and is independent of Tomcat. One forwarder per host serves all instances.

### Enabling Glowroot Alerts

Add to `inventory/hosts`:

```ini
glowroot_alerting_enabled=true
```

The forwarder uses the same `alerting_telegram_bot_token` and `alerting_telegram_chat_id` already configured for Grafana.

### Deploying

```bash
ansible-playbook dhis2.yml --tags create-instance
```

---

## Munin Alerts

For users running `server_monitoring=munin`, configure the `munin_alerts` variable in `host_vars` or `group_vars`:

### Telegram

```yaml
munin_alerts:
  - name: telegram
    type: telegram
    bot_token: 'your-bot-token-from-botfather'
    chat_id: '-1001234567890'
    level: 'warning critical'
```

### Slack

```yaml
munin_alerts:
  - name: slack
    type: slack
    webhook_url: 'https://hooks.slack.com/services/T.../B.../xxx'
    level: 'warning critical'
```

### Email (Default)

```yaml
munin_alerts:
  - name: admin
    type: email
    email: admin@example.com
    subject: 'Munin Alert'
    level: 'warning critical'
```

---

## Testing Alerts

### Test Telegram Delivery

```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" -d "text=Test alert from DHIS2 monitoring"
```

### Test Glowroot Forwarder

```bash
# Check service status
systemctl status glowroot-telegram-forwarder

# Send a test alert
curl -s -X POST http://127.0.0.1:9099 \
  -H "Content-Type: application/json" \
  -d '{
    "attachments": [{
      "fallback": "[dhis2] Test alert - triggered",
      "pretext": "[dhis2] Test alert triggered",
      "color": "danger",
      "text": "This is a test alert",
      "ts": 1712500000.0
    }],
    "channel": "#alerts"
  }'
```

### Verify Grafana Alerting

```bash
# List contact points
curl -u admin:admin http://localhost:3000/grafana/api/v1/provisioning/contact-points

# List alert rules
curl -u admin:admin http://localhost:3000/grafana/api/v1/provisioning/alert-rules
```

### Verify Prometheus Rules

```bash
promtool check rules /etc/prometheus/rules/dhis2-alerts.yml
```

---

## Troubleshooting

**Bot not sending messages:**

- Ensure the bot is added to the Telegram group/chat
- Verify the chat ID sign (groups use negative IDs like `-1001234567890`)
- Test with a direct curl to the Bot API

**Grafana unified alerting not working:**

- Check Grafana version is 9.0+ (`grafana-server -v`)
- Verify `/etc/grafana/grafana.ini` has `[unified_alerting] enabled = true`
- Check `/etc/grafana/provisioning/alerting/` directory exists and files are owned by `grafana`

**Glowroot forwarder not running:**

- Check `systemctl status glowroot-telegram-forwarder`
- Check logs: `journalctl -u glowroot-telegram-forwarder`
- Verify the script exists: `ls -la /opt/glowroot/glowroot-telegram-forwarder.py`

**Prometheus rules not loading:**

- Validate syntax: `promtool check rules /etc/prometheus/rules/dhis2-alerts.yml`
- Check `/etc/prometheus/prometheus.yml` has `rule_files:` directive
- Reload Prometheus: `systemctl reload prometheus`

**No alerts firing:**

- Alerts need the `for` duration to pass before firing (e.g., 5 minutes)
- Check Grafana UI at `/grafana/alerting/list` for alert states
- Verify Prometheus targets are being scraped at `/grafana/explore`

---

## Securing Credentials with Vault

For production deployments where you want to encrypt tokens at rest, you can optionally move credentials to an ansible-vault encrypted file.

Create the directory structure:

```bash
cd deploy/inventory
mkdir -p host_vars/monitor
```

`host_vars/monitor/vars.yml` (plaintext -- references the vault):

```yaml
alerting_enabled: true
alerting_telegram_bot_token: '{{ vault_alerting_telegram_bot_token }}'
alerting_telegram_chat_id: '-1001234567890'
```

`host_vars/monitor/vault.yml` (will be encrypted):

```yaml
vault_alerting_telegram_bot_token: '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
```

Encrypt and deploy:

```bash
ansible-vault encrypt host_vars/monitor/vault.yml
ansible-playbook dhis2.yml --tags monitoring,alerting --vault-id @prompt
```

Remove the token from `inventory/hosts` after moving it to the vault.

#!/usr/bin/env python3
"""Change-only patch of Glowroot admin.json / config.json for the alerting hub."""

from __future__ import annotations

import argparse
import json
import os
import sys
from copy import deepcopy
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return data


def write_json(path: Path, data: dict, owner_gid: int | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=False)
        handle.write("\n")
    os.chmod(tmp, 0o660)
    if owner_gid is not None:
        os.chown(tmp, 0, owner_gid)
    tmp.replace(path)


def default_alerts(args: argparse.Namespace) -> list[dict]:
    heap_raw = (args.heap_memory_size or "4G").strip()
    if heap_raw.lower().endswith("m"):
        heap_bytes = int(heap_raw[:-1]) * 1048576
    elif heap_raw.lower().endswith("g"):
        heap_bytes = int(heap_raw[:-1]) * 1073741824
    else:
        heap_bytes = int(heap_raw) * 1073741824

    slack = {
        "slackWebhookId": args.webhook_id,
        "slackChannels": ["#alerts"],
    }
    return [
        {
            "condition": {
                "conditionType": "heartbeat",
                "timePeriodSeconds": args.heartbeat_seconds,
            },
            "severity": "CRITICAL",
            "slackNotification": deepcopy(slack),
        },
        {
            "condition": {
                "conditionType": "metric",
                "metric": "error:rate",
                "transactionType": "Web",
                "threshold": args.error_rate_threshold,
                "timePeriodSeconds": args.error_rate_period,
            },
            "severity": "CRITICAL",
            "slackNotification": deepcopy(slack),
        },
        {
            "condition": {
                "conditionType": "metric",
                "metric": "transaction:x-percentile",
                "transactionType": "Web",
                "percentile": 95.0,
                "threshold": args.p95_threshold_ms,
                "timePeriodSeconds": args.p95_period,
                "minTransactionCount": args.min_transaction_count,
            },
            "severity": "HIGH",
            "slackNotification": deepcopy(slack),
        },
        {
            "condition": {
                "conditionType": "metric",
                "metric": "gauge:java.lang:type=Memory:HeapMemoryUsage.used",
                "threshold": int(heap_bytes * 0.8),
                "timePeriodSeconds": 300,
            },
            "severity": "HIGH",
            "slackNotification": deepcopy(slack),
        },
    ]


def patch_admin(admin: dict, args: argparse.Namespace) -> dict:
    patched = deepcopy(admin)
    slack = patched.setdefault("slack", {})
    webhooks = slack.setdefault("webhooks", [])
    if not isinstance(webhooks, list):
        webhooks = []
        slack["webhooks"] = webhooks

    desired = {
        "id": args.webhook_id,
        "url": args.webhook_url,
        "display": "DHIS2 Alerting Hub",
    }
    found = False
    for index, webhook in enumerate(webhooks):
        if not isinstance(webhook, dict):
            continue
        if webhook.get("id") == args.webhook_id or webhook.get("url") == args.webhook_url:
            webhooks[index] = {**webhook, **desired}
            found = True
            break
    if not found:
        webhooks.append(desired)
    return patched


def patch_config(config: dict, args: argparse.Namespace) -> dict:
    patched = deepcopy(config)
    alerts = patched.get("alerts")
    if args.force or not isinstance(alerts, list) or len(alerts) == 0:
        patched["alerts"] = default_alerts(args)
        return patched

    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        notification = alert.setdefault("slackNotification", {})
        if not isinstance(notification, dict):
            notification = {}
            alert["slackNotification"] = notification
        notification["slackWebhookId"] = args.webhook_id
        notification.setdefault("slackChannels", ["#alerts"])
    return patched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admin", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--webhook-url", required=True)
    parser.add_argument("--webhook-id", required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--heap-memory-size", default="4G")
    parser.add_argument("--heartbeat-seconds", type=int, default=300)
    parser.add_argument("--error-rate-threshold", type=float, default=10.0)
    parser.add_argument("--error-rate-period", type=int, default=300)
    parser.add_argument("--p95-threshold-ms", type=int, default=10000)
    parser.add_argument("--p95-period", type=int, default=600)
    parser.add_argument("--min-transaction-count", type=int, default=10)
    parser.add_argument("--tomcat-gid", type=int, default=-1)
    args = parser.parse_args()

    admin_path = Path(args.admin)
    config_path = Path(args.config)
    owner_gid = None if args.tomcat_gid < 0 else args.tomcat_gid

    original_admin = load_json(admin_path)
    original_config = load_json(config_path)
    new_admin = patch_admin(original_admin, args)
    new_config = patch_config(original_config, args)

    changed = new_admin != original_admin or new_config != original_config
    if changed:
        write_json(admin_path, new_admin, owner_gid)
        write_json(config_path, new_config, owner_gid)
        print("CHANGED")
    else:
        print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

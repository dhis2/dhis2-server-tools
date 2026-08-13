# ClamAV upload scanning

Opt-in malware scan of files uploaded to DHIS2 through the web UI or mobile
apps. The reverse proxy sends create-upload URLs to a dedicated scanner host;
everything else still goes straight to Tomcat.

Default installs are unchanged. `clamav_enabled` is false, and an empty
`[clamav_servers]` group is fine.

## What is scanned

Per-instance create URLs only (versioned API included):

- `/api/fileResources`
- `/api/dataValues/file`
- `/api/messageConversations/attachments`
- `/api/apps` when `clamav_scan_app_zips=true`
- `/api/files/script`, `/api/files/style`, and `/api/staticContent/logo_*`
  when `clamav_scan_ui_assets=true`

`GET` on those same URLs is not scanned. UID/download paths and
`POST /api/tracker` are not intercepted (tracker carries FileResource UIDs
whose bytes already went through `/api/fileResources`).

The gateway does not re-encode multipart. File parts are extracted and
scanned as raw bytes; the original request is forwarded so DHIS2's MD5 of
the stored bytes still matches.

## Requirements

- A host in `[clamav_servers]`
- About 4 GiB extra RAM on the LXD hypervisor (or on the clamav VM in SSH
  mode). The playbook measures **host** `MemAvailable` before creating the
  LXD container. Many 8 GiB single-server hosts cannot enable this without a
  RAM upgrade.
- Official Cisco CVD/CDIFF signatures via Ubuntu `clamav-freshclam`. No
  third-party PPA or unofficial signature packs.

The scanner is not published on the host. UFW allows the gateway port from
`[web]` (uploads) and from `[monitoring]` when Prometheus is in use.

## Inventory

```ini
[clamav_servers]
clamav  ansible_host=172.19.2.40  wireguard_ip=10.0.0.8

[all:vars]
clamav_enabled=true
# clamav_fail_open=false
# clamav_scan_app_zips=true
# clamav_scan_ui_assets=true
# clamav_gateway_port=8081
# clamav_private_mirror=
```

Do not use `wireguard_ip=10.0.0.6`. That address is the default sysadmin
peer. When `wireguard_data_plane=true`, the clamav host must have its own
`wireguard_ip`.

## Variables

| Variable | Default | Notes |
| --- | --- | --- |
| `clamav_enabled` | `false` | Master gate |
| `clamav_fail_open` | `false` | Break-glass: allow uploads if clamd is down |
| `clamav_scan_app_zips` | `true` | `POST /api/apps` |
| `clamav_scan_ui_assets` | `true` | Custom JS/CSS and logos |
| `clamav_gateway_port` | `8081` | Bridge listen port |
| `clamav_private_mirror` | unset | Air-gapped freshclam mirror |

## Failure behaviour

- Infected upload: `403` JSON (`malware_detected` plus the signature name).
  Bytes are not forwarded to Tomcat.
- clamd or the gateway down: `503` (fail-closed). Set `clamav_fail_open=true`
  only as break-glass.
- Unknown or missing `X-DHIS2-Upstream`: `502`. The proxy overwrites that
  header; the gateway allowlists `[instances]` `service_ip` plus
  `tomcat_port` (default 8080). Adding or moving an instance refreshes
  that list during `create-instance` (and on `--tags clamav-configure`).
- Truncated upload bodies (client sent fewer bytes than `Content-Length`)
  are rejected with `400` and are not forwarded. The proxy is expected to
  buffer the request (`proxy_request_buffering` stays on) so the gateway
  sees `Content-Length`.

Stale signatures alert, they do not fail-closed. `/healthz` is a clamd
`PING` only. Signature age is exposed on `/metrics` so Prometheus can alert
without taking the scanner out of rotation.

Air-gapped hosts: set `clamav_private_mirror`, or copy `main.cvd`,
`daily.cvd`, and `bytecode.cvd` into `/var/lib/clamav` on the scanner.
Signature age over 48 hours is a freshness problem; scans still use the last
good database.

## Tags

```bash
ansible-playbook dhis2.yml --tags clamav
ansible-playbook dhis2.yml --tags clamav-install
ansible-playbook dhis2.yml --tags clamav-configure
```

Proxy location, Tomcat UFW, and the gateway upstream allowlist live in
`create-instance`. A full playbook run (or `--tags create-instance` after
the scanner is up) applies them.

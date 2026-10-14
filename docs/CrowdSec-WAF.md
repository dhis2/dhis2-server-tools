# CrowdSec WAF and IP banning

[CrowdSec](https://www.crowdsec.net/) runs on the `[web]` host next to the reverse
proxy. It gives two layers of protection, both off by default:

- **IP banning.** The Security Engine reads the proxy's access log and bans IPs
  whose traffic matches an attack scenario (scanners, probing, path traversal,
  brute force, bad user agents). With the Central API on, it also applies
  CrowdSec's community blocklist.
- **WAF (AppSec).** The OpenResty bouncer sends every request to the engine's
  AppSec listener, which blocks in-band on a virtual-patching rule (known CVEs)
  or a generic rule (for example template injection), before the request
  reaches DHIS2.

The bouncer enforces both in OpenResty's access phase: a banned IP or a blocked
request gets a 403.

## Requirements

- `ansible_connection=lxd` (the single-server architecture). SSH deployments are
  not supported.
- `proxy=openresty`. The bouncer is a lua module; the nginx.org packages the
  proxy role installs cannot load it, and apache2 has no bouncer. With another
  proxy, set `crowdsec_bouncer_enabled=false` to run the engine alone
  (detection only, nothing is blocked).
- Tested on Ubuntu 24.04 and 22.04.

## Enable

In `deploy/inventory/hosts`, under `[web:vars]`:

```
crowdsec_enabled=true
```

Then run the playbook. On an existing server:

```
sudo ansible-playbook dhis2.yml --tags proxy-install
```

The run fails before changing anything if the settings are inconsistent (wrong
proxy, captcha without keys).

### Check it works

Inside the proxy container (`lxc exec proxy -- bash`):

```
cscli metrics show acquisition      # access.log lines read and parsed
cscli bouncers list                 # one crowdsec-openresty-bouncer, last_pull a few seconds old
cscli decisions list                # current bans
curl -sI https://<fqdn>/.env | head -1   # from outside: HTTP/2 403 (AppSec)
```

To see a ban end to end:

```
cscli decisions add -i <your-ip> -d 1m
# a request from <your-ip> gets 403 within 10 s
cscli decisions delete -i <your-ip>
```

The playbook itself asserts that the bouncer has pulled decisions from the
local API after each run, so a bouncer that silently lets everything through
fails the deployment.

## Variables

All under `[web:vars]`. Defaults in `deploy/roles/crowdsec/defaults/main.yml`;
full descriptions in `deploy/roles/crowdsec/meta/argument_specs.yml`.

| Variable | Default | Notes |
| --- | --- | --- |
| `crowdsec_enabled` | `false` | Master switch. Setting it back to `false` removes CrowdSec from hosts this role set up. |
| `crowdsec_version` | `latest` | Pin to an exact package version to hold it across `apt upgrade`. |
| `crowdsec_online_api_enabled` | `true` | Central API: shares banned IPs and the scenarios they triggered with CrowdSec and pulls the community blocklist. See below. |
| `crowdsec_bouncer_enabled` | `true` | `false` keeps the engine (detection only). |
| `crowdsec_bouncer_mode` | `stream` | `stream` caches decisions, so bans hold while the engine restarts. `live` asks per request and fails open. |
| `crowdsec_bouncer_bouncing_on_type` | `ban` | `captcha` or `all` need the captcha keys. |
| `crowdsec_bouncer_captcha_provider` | `recaptcha` | `recaptcha`, `hcaptcha`, `turnstile`. |
| `crowdsec_bouncer_captcha_site_key` | `""` | |
| `crowdsec_bouncer_captcha_secret_key` | `""` | Put it in `host_vars/<web host>/vault.yml`. |
| `crowdsec_appsec_enabled` | `true` | The WAF. Needs the bouncer. |
| `crowdsec_appsec_failure_action` | `passthrough` | What the bouncer does when AppSec does not answer. `deny` blocks. |
| `crowdsec_appsec_max_body_size` | `10485760` | Bytes. See "What AppSec inspects". |
| `crowdsec_appsec_body_size_exceeded_action` | `partial` | `partial`, `allow`, or `drop`. `drop` blocks imports over the limit. |
| `crowdsec_allowlist` | `[]` | IPs/CIDRs never inspected or banned. |
| `crowdsec_metrics_enabled` | `true` | Prometheus endpoint, loopback only unless exposed. |
| `crowdsec_metrics_expose` | auto | `true` when `server_monitoring` is Prometheus-based and a `[monitoring]` host exists. |
| `crowdsec_memory_max` | `1G` | systemd `MemoryMax` for the engine. Empty removes the limit. |

## Central API and data sharing

With `crowdsec_online_api_enabled=true` (the default) the engine registers with
CrowdSec's Central API and sends it the IPs it bans together with the scenario
names that triggered the ban. Nothing else leaves the server: no request
contents, no DHIS2 data, no logs. In return it pulls the community blocklist,
which is most of the IP-banning value.

If that sharing is not acceptable, set:

```
crowdsec_online_api_enabled=false
```

Only locally detected attackers are banned then.

## Allowlist

Some networks put many legitimate users behind one address (a facility's
carrier-grade NAT, a national proxy). One user's behaviour must not ban them
all:

```
crowdsec_allowlist=["203.0.113.10", "198.51.100.0/24"]
```

Listed addresses are never inspected by AppSec and never banned, locally or by
the community blocklist. Adding an entry also lifts existing bans on it.

## What AppSec inspects

Requests are inspected in full up to `crowdsec_appsec_max_body_size`
(10 MiB). DHIS2 accepts imports up to 100 MB, so larger bodies are let through
rather than blocked:

- URI, query string and headers are always inspected.
- Form bodies are inspected up to the limit.
- JSON bodies over the limit are not body-inspected.

Raising the limit costs engine memory per in-flight request, and past about
50 MiB the bouncer's AppSec call times out and lets the request through
anyway. Keep the default unless you have a specific reason.

AppSec fails open (`passthrough`): if the engine is down, requests go through.
Stream-mode bans still hold in the bouncer during an engine restart.

## Prometheus and Grafana

With `server_monitoring=grafana`, `prometheus` or `grafana/prometheus` and a
`[monitoring]` host, the engine's metrics endpoint binds to the host's service
IP, ufw lets only the monitoring host(s) in, and Prometheus gets a
`crowdsec-<web host>` scrape job. The endpoint also serves Go's `/debug/pprof`,
which is why it is never exposed wider than that. The generic `InstanceDown`
alert covers the job; there is no CrowdSec dashboard yet.

With Munin (the default) there is no CrowdSec view; use `cscli metrics`.

## Switching off

| Setting | Effect |
| --- | --- |
| `crowdsec_bouncer_enabled=false` | Purges the bouncer and deletes its API registration. The engine keeps detecting; nothing is blocked. |
| `crowdsec_enabled=false` | Also removes the engine package, its apt repository, the metrics firewall rule and the proxy's CrowdSec log. Only on hosts this role set up. `/etc/crowdsec` and `/var/lib/crowdsec` are kept, so re-enabling reuses the registration. |

## Known limitations

- **Log rotation.** OpenResty's `access.log`, `error.log` and `perf.log` under
  `/usr/local/openresty/nginx/logs/` are not rotated. CrowdSec adds the
  combined `access.log`; watch the disk until rotation ships.
- **Patching.** `unattended-upgrades` only tracks Ubuntu repositories. CrowdSec
  and the bouncer upgrade when the playbook runs. Hub rules (scenarios,
  AppSec virtual patches) do update daily on their own, through the package's
  `crowdsec-hubupdate.timer`.
- **HTTP only.** The engine reads the proxy's logs; it does not watch SSH or
  other services on the host.

## Troubleshooting

**The run fails with "has not pulled decisions from the LAPI".** The bouncer
is installed but not enforcing. Check, in the proxy container:

```
dpkg --verify crowdsec-openresty-bouncer   # crowdsec_openresty.conf must not be listed
grep ^API_KEY /etc/crowdsec/bouncers/crowdsec-openresty-bouncer.conf
cscli bouncers list                        # the key must belong to a listed bouncer
tail /usr/local/openresty/nginx/logs/error.log
```

A hand-edited `conf.d/crowdsec_openresty.conf` is the usual cause; reinstall
the bouncer package or run once with `crowdsec_bouncer_enabled=false` and then
back on, which purges it and registers a fresh key.

**A legitimate user is banned.** `cscli decisions list` shows the reason.
`cscli decisions delete -i <ip>` lifts it; add the address to
`crowdsec_allowlist` if it is a shared egress.

**An import is blocked with 403.** `cscli alerts list` shows the AppSec rule.
Bodies over the limit are not blocked by default; a 403 on an import means a
rule matched the URI, a header or the first part of a form body.

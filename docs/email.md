# Email

DHIS2 sends transactional email for password resets, system alerts, and push
analysis. This toolset provides a dedicated `smtp` container that acts as a
send-only mail relay. All other containers and the LXD host route outgoing mail
through it. The smtp container does not accept mail from the internet and does
not deliver locally — it forwards everything to an external smarthost such as
[Brevo](https://www.brevo.com/) which handles actual delivery.

## Architecture

```
[dhis2 container]  ──┐
[postgres container] ├──► [smtp container :25] ──► [Brevo / smarthost] ──► internet
[proxy container]  ──┘
[LXD host]         ──┘
```

Each container and the LXD host has `msmtp-mta` installed, which provides a
`sendmail`-compatible binary. When any process on those hosts calls `sendmail`,
`msmtp` connects directly to the smtp container on port 25. The smtp container
runs Postfix, which authenticates to the smarthost over TLS and relays the
message. All outgoing mail has its `From:` address rewritten to
`no-reply@<fqdn>` regardless of what the originating process sent.

## Enabling the smtp container

Add a `[mail]` entry to `deploy/inventory/hosts`:

```ini
[mail]
smtp  ansible_host=172.19.2.5  mail_smarthost=smtp-relay.brevo.com  mail_smarthost_port=587  mail_smarthost_username=user@example.com  mail_smarthost_password=your_api_key
```

Choose an IP from your `lxd_network` range that is not already in use. The
`fqdn` variable set in `[all:vars]` determines the domain used in the rewritten
`From:` address, so ensure it is set correctly before deploying.

### Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `mail_smarthost` | yes | — | SMTP relay hostname |
| `mail_smarthost_port` | no | `587` | Relay port |
| `mail_smarthost_username` | yes | — | Relay account username |
| `mail_smarthost_password` | yes | — | Relay account password / API key |

### Deploying

```bash
sudo bash deploy/deploy.sh
```

Or to run only the mail-related roles on an existing deployment:

```bash
cd deploy && ansible-playbook dhis2.yml --tags mail,mail-client
```

## Securing credentials with Ansible Vault

The smarthost password should not be stored in plaintext in the hosts file.
Encrypt it with Ansible Vault:

```bash
ansible-vault create inventory/host_vars/smtp
```

Add the sensitive variable inside the vault:

```yaml
mail_smarthost_password: your_api_key
```

Then reference it from the hosts file without the value:

```ini
[mail]
smtp  ansible_host=172.19.2.5  mail_smarthost=smtp-relay.brevo.com  mail_smarthost_username=user@example.com
```

Run the playbook with `--ask-vault-password` to decrypt at runtime. See
[Ansible-Vault.md](Ansible-Vault.md) for full details.

## Configuring Brevo as the smarthost

1. Log in to [app.brevo.com](https://app.brevo.com/) and go to
   **SMTP & API → SMTP**.
2. Note the SMTP server (`smtp-relay.brevo.com`), port (`587`), and your login
   credentials or generate a dedicated SMTP key.
3. Set `mail_smarthost=smtp-relay.brevo.com`, `mail_smarthost_port=587`, and
   `mail_smarthost_username` / `mail_smarthost_password` accordingly in your
   inventory.
4. In Brevo, go to **Senders & IP → Domains** and add your `fqdn` domain.
   Brevo will provide DNS records (SPF, DKIM) to add to your domain — see the
   DNS section below.

Other providers (SendGrid, Mailgun, AWS SES) follow the same pattern: obtain
their SMTP relay hostname, port, and credentials and substitute them for the
Brevo values above.

## Testing

From the LXD host, exec into the smtp container and send a test message:

```bash
lxc exec smtp -- bash -c 'echo "Test from DHIS2 server" | sendmail -v you@example.com'
```

Watch the Postfix log to confirm relay to the smarthost succeeded:

```bash
lxc exec smtp -- tail -f /var/log/mail.log
```

A successful relay shows a `250 OK` status from the smarthost. The delivered
message should show `From: DHIS2 <no-reply@yourdomain.org>`.

To verify the mail client on another container is routing correctly:

```bash
lxc exec dhis -- bash -c 'echo "Test from dhis container" | sendmail -v you@example.com'
```

## DNS requirements for reliable delivery

Because the `From:` address uses your `fqdn` domain, receiving mail servers
will check DNS records for that domain to decide whether to accept or reject
the message. Misconfigured DNS is the most common cause of mail being silently
dropped or sent to spam.

> **Note:** Since you are using an external smarthost, it is the smarthost's
> IP address (not your server's) that actually sends mail to the internet. Your
> DNS records must authorise the smarthost's sending infrastructure for your
> domain, not your own server IP.

### SPF

An SPF record tells receiving servers which hosts are allowed to send mail for
your domain. Add a `TXT` record to your domain's DNS:

```
yourdomain.org.  TXT  "v=spf1 include:spf.brevo.com ~all"
```

Replace `spf.brevo.com` with the include directive your smarthost provider
specifies. The `~all` suffix (softfail) is a reasonable starting point; switch
to `-all` (hardfail) once you are confident no other sources send mail for the
domain.

### DKIM

DKIM adds a cryptographic signature to outgoing messages so receivers can
verify they have not been tampered with. Brevo and most providers generate a
DKIM key pair for you and provide a `CNAME` or `TXT` record to add to your
domain DNS. Follow your provider's domain authentication wizard to obtain and
publish the record.

Without DKIM, messages are more likely to be treated as spam even when SPF
passes.

### DMARC

DMARC builds on SPF and DKIM and tells receiving servers what to do when checks
fail. Add a `TXT` record at `_dmarc.yourdomain.org`:

```
_dmarc.yourdomain.org.  TXT  "v=DMARC1; p=none; rua=mailto:dmarc-reports@yourdomain.org"
```

Start with `p=none` (monitor only) and review the aggregate reports before
moving to `p=quarantine` or `p=reject`. This lets you catch any legitimate mail
sources you may have missed in your SPF record before enforcing a strict policy.

### Summary checklist

- [ ] SPF `TXT` record published for `fqdn` domain, including smarthost ranges
- [ ] DKIM key published (via your smarthost's domain authentication wizard)
- [ ] DMARC `TXT` record published at `_dmarc.<fqdn>`
- [ ] `fqdn` variable set in `inventory/hosts` `[all:vars]`
- [ ] Smarthost account credentials in Ansible Vault
- [ ] Test message delivered and `From:` shows `no-reply@<fqdn>`

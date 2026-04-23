# Reference Docker Compose Deployment

A minimal stack for running the Transcription app against any OIDC provider.

## What this includes

- `transcription` — the app (backend + pre-built frontend)
- `oauth2-proxy` — OIDC reverse-proxy terminator
- `caddy` — TLS termination and routing

## What this does NOT include

- **Keycloak.** Bring your own OIDC provider, or follow
  [`docs/keycloak-setup.md`](../../docs/keycloak-setup.md) to stand one up.
- Monitoring (node-exporter, Prometheus scrape config) — add your own if needed.
- Per-VM hardening (firewall, SELinux, auto-updates) — use your preferred tool.

## Quick start

1. Copy `.env.example` to `.env` and fill in the values.
2. Generate `cookie_secret` for oauth2-proxy:
   ```bash
   openssl rand -base64 32 | tr -d '\n' | tr -- '+/' '-_'
   ```
   Replace the placeholder in `oauth2-proxy.cfg`.
3. Fill in the four OIDC placeholders in `oauth2-proxy.cfg` (`client_id`,
   `client_secret`, `oidc_issuer_url`, `redirect_url`).
4. Point DNS at the host and run `docker compose up -d`.
5. Browse to `https://$APP_HOST`.

## Identity header contract

The app trusts two headers from oauth2-proxy:

- `X-Auth-Request-User` — stable user id (set via Caddy `copy_headers` from
  `X-Auth-Request-Preferred-Username`).
- `X-Auth-Request-Email` — user's email.

Any OIDC provider works as long as oauth2-proxy can emit these.

## Invitation mode (optional)

Set `INVITATION_MODE=true` in `.env` to require admin-issued invitations for
new users. This requires:

- `KEYCLOAK_ADMIN_URL` + an `admin-cli` client in Keycloak (see
  `docs/keycloak-setup.md`)
- A reachable SMTP server (or an internal relay — set `SMTP_STARTTLS=false`
  and leave the user/password empty)
- One or more `ADMIN_EMAILS` — the humans who can issue invitations from the
  app's Settings → Invitations page

Leaving `INVITATION_MODE=false` keeps the app open to anyone Keycloak lets in
(useful when Keycloak self-registration is enabled).

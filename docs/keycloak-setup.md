# Keycloak Setup Guide

This guide gets you from zero to a working Keycloak that can back a
self-hosted Transcription instance, with registration, login, password
reset, and optional social login.

The Transcription app does **not** require Keycloak specifically — any OIDC
provider that emits an email claim will work. Keycloak is documented here
because it's open-source, widely deployed in higher education, and supports
future federation (DFN-AAI / eduGAIN) without application changes.

## 1. Run Keycloak with Postgres

```bash
# Postgres data
docker run -d --name kc-postgres \
  -e POSTGRES_DB=keycloak \
  -e POSTGRES_USER=keycloak \
  -e POSTGRES_PASSWORD=REPLACE_ME \
  -v kc-postgres-data:/var/lib/postgresql/data \
  postgres:16

# Keycloak
docker run -d --name keycloak \
  --link kc-postgres:postgres \
  -e KC_DB=postgres \
  -e KC_DB_URL=jdbc:postgresql://postgres:5432/keycloak \
  -e KC_DB_USERNAME=keycloak \
  -e KC_DB_PASSWORD=REPLACE_ME \
  -e KC_HOSTNAME=auth.example.com \
  -e KC_PROXY=edge \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=REPLACE_ME \
  -p 8080:8080 \
  quay.io/keycloak/keycloak:26.0 start
```

Put a TLS-terminating reverse proxy in front (your Caddy is fine) and make
sure `auth.example.com` resolves to the Keycloak host.

## 2. Create the realm and client

1. Log in to the admin console at `https://auth.example.com`.
2. Create a realm: `transcription` (or whatever you want — set it as
   `KEYCLOAK_TARGET_REALM` in the app's `.env`).
3. In the realm, create an OIDC client:
   - Client ID: `transcription-app`
   - Client authentication: On
   - Valid redirect URIs: `https://transcription.example.com/oauth2/callback`
   - Save, then copy the client secret from the Credentials tab.
   - Put these in `oauth2-proxy.cfg` as `client_id` / `client_secret`.

## 3. Configure the realm

**Realm settings → Login tab:**
- User registration: **On** for open signup, or **Off** for invite-only.
- Verify email: **On** (always — prevents spam).
- Forgot password: **On**.

**Realm settings → Email tab:** configure SMTP. Keycloak uses this for
verification and password-reset emails. Share credentials with the app's
SMTP settings or use a different sender.

**Inside Uni Osnabrück:** use `Host=relay.rz.uni-osnabrueck.de`,
`Port=25`, leave *Username* and *Password* blank, and disable *Enable
StartTLS*. No RZ credentials are required for hosts inside the Uninetz.

**Authentication → Required actions:** ensure `UPDATE_PASSWORD` and
`VERIFY_EMAIL` are enabled.

## 4. Admin-CLI service account (for invitation mode)

If the app will run in `INVITATION_MODE=true`, it needs to call the Keycloak
Admin API to pre-create users.

1. In the `master` realm (or whichever realm owns admin access), create an
   OIDC client:
   - Client ID: `admin-cli`
   - Client authentication: On
   - Service accounts roles: On
2. Credentials tab → copy the client secret → put into the app's
   `KEYCLOAK_ADMIN_CLIENT_SECRET`.
3. Service accounts roles tab → assign `manage-users` (and `view-users`)
   of the *target* realm.
4. Set the app's `KEYCLOAK_ADMIN_URL` to the public base URL of Keycloak
   (e.g. `https://auth.example.com`) and `KEYCLOAK_TARGET_REALM` to the
   realm name from Section 2.

## 5. Social login (optional)

**Google:**
1. Google Cloud Console → APIs & Services → Credentials → Create OAuth
   client ID → Web application.
2. Add authorised redirect URI:
   `https://auth.example.com/realms/transcription/broker/google/endpoint`
3. Copy Client ID / Secret.
4. In Keycloak: Identity Providers → Add → Google → paste credentials.
5. Settings: "Trust email from provider" = On (Google verifies emails).

**Microsoft / Entra ID:**
1. Azure Portal → App registrations → New registration.
2. Redirect URI (web):
   `https://auth.example.com/realms/transcription/broker/microsoft/endpoint`
3. Certificates & secrets → New client secret → copy value.
4. In Keycloak: Identity Providers → Add → Microsoft → paste credentials.
5. Settings: "Trust email from provider" = On.

**Apple, GitHub, etc.** — same pattern. Skip Facebook/X unless you have a
reason; their email claims are unreliable.

**Account linking:** leave "First login flow" at the default
(`first broker login`). This prompts users with an existing password
account to confirm before linking a social login, preventing a class of
phishing-style account takeovers.

## 6. Break-glass: switch from open to invite-only

If abuse appears:

1. Keycloak admin UI → Realm settings → Login → User registration: **Off**
2. App `.env` → `INVITATION_MODE=true` → restart the app container.

Existing users keep their sessions. New unknown emails are rejected with
"No invitation found for this email." Invitations issued before the flip
stay valid.

## 7. Future: federated login via eduGAIN / DFN-AAI

Keycloak supports SAML identity providers. When/if you join DFN-AAI (the
German HE federation) and eduGAIN (the international inter-federation), you
will:

1. Publish your Keycloak SP metadata.
2. Sign the federation's onboarding agreement (legal + technical review,
   weeks-to-months process).
3. In Keycloak: Identity Providers → Add → SAML → import federation
   metadata.

No app-code change. Federated users appear to the app as any other
Keycloak-authenticated user with an email and a stable `sub` claim.

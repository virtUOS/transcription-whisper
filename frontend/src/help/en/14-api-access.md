# API Access

## What this is

When your deployment has API tokens enabled, you can generate a personal bearer token and use it to call the app's REST API directly from scripts, CI jobs, or any HTTP client. A token is scoped to your account — it can read and write your own files, transcriptions, and presets, but never anyone else's.

If your deployment has tokens disabled, the **Settings** link in the header won't appear and this feature isn't available.

## Creating a token

Open **Settings** from the header, then click **Create token**. Give the token a short name that helps you remember where you'll use it (for example, `my-laptop` or `ci-pipeline`), choose how long it should stay valid (30, 90, 365 days, or Never), and click **Create**.

The raw token appears **once** as a `tw_…` string. Copy it immediately — when you close the dialog, the full token is gone and cannot be retrieved. Only the short prefix stays visible in the list for identification.

## Using a token

Pass the token as a standard HTTP bearer header:

```
Authorization: Bearer tw_...
```

Example with curl:

```
curl -H "Authorization: Bearer tw_abc..." https://your-host/api/tokens
```

For the transcription-status WebSocket, pass the token as a query parameter (browsers don't allow custom headers on WebSocket requests):

```
wss://your-host/api/ws/status/{transcription_id}?token=tw_abc...
```

## Revoking a token

Click **Revoke** next to any active token. The token stops working immediately. Revoked tokens stay in the list (faded) so you can audit which ones you've rotated.

## Tips

- **Rotate tokens when machines change.** If a laptop is lost or a CI secret is rotated, revoke the matching token and create a new one.
- **One token per context.** Avoid sharing a single token across multiple tools or machines — naming them per usage makes revocation safer.
- **Capabilities match the UI.** A token inherits your access: if your deployment has no LLM configured, token-authenticated requests also can't run analysis, translation, or refinement (those endpoints return 503 regardless of how you authenticated).

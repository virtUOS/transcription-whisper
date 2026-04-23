import time
from typing import Any

import httpx


class KeycloakAdminError(Exception):
    """Raised for any non-success response from Keycloak Admin API."""


class KeycloakAdminClient:
    def __init__(
        self, *,
        base_url: str, admin_realm: str, target_realm: str,
        client_id: str, client_secret: str,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._admin_realm = admin_realm
        self._target_realm = target_realm
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    async def _get_admin_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at - 10:
            return self._token
        url = f"{self._base_url}/realms/{self._admin_realm}/protocol/openid-connect/token"
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if resp.status_code != 200:
            raise KeycloakAdminError(f"Token acquire failed: {resp.status_code} {resp.text}")
        payload = resp.json()
        self._token = payload["access_token"]
        self._token_expires_at = now + float(payload.get("expires_in", 60))
        return self._token

    async def create_user(self, *, email: str) -> str:
        """Create a user with emailVerified=False. Returns the Keycloak user id."""
        token = await self._get_admin_token()
        url = f"{self._base_url}/admin/realms/{self._target_realm}/users"
        body: dict[str, Any] = {
            "email": email,
            "username": email,
            "enabled": True,
            "emailVerified": False,
        }
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.post(
                url, json=body,
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code == 409:
            raise KeycloakAdminError(f"User already exists for {email}")
        if resp.status_code != 201:
            raise KeycloakAdminError(f"Create user failed: {resp.status_code} {resp.text}")
        location = resp.headers.get("Location", "")
        user_id = location.rstrip("/").rsplit("/", 1)[-1]
        if not user_id:
            raise KeycloakAdminError("Create user: no Location header in response")
        return user_id

    async def send_setup_email(
        self, *, user_id: str, actions: list[str], redirect_uri: str,
    ) -> None:
        token = await self._get_admin_token()
        url = (
            f"{self._base_url}/admin/realms/{self._target_realm}"
            f"/users/{user_id}/execute-actions-email"
        )
        params = {"redirect_uri": redirect_uri, "client_id": "account"}
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.put(
                url, json=actions, params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code not in (200, 204):
            raise KeycloakAdminError(f"execute-actions-email failed: {resp.status_code} {resp.text}")


def build_default_client() -> KeycloakAdminClient | None:
    """Build a client from settings. Returns None if KEYCLOAK_ADMIN_URL is unset."""
    from app.config import settings
    if not settings.KEYCLOAK_ADMIN_URL:
        return None
    return KeycloakAdminClient(
        base_url=settings.KEYCLOAK_ADMIN_URL,
        admin_realm=settings.KEYCLOAK_ADMIN_REALM,
        target_realm=settings.KEYCLOAK_TARGET_REALM,
        client_id=settings.KEYCLOAK_ADMIN_CLIENT_ID,
        client_secret=settings.KEYCLOAK_ADMIN_CLIENT_SECRET,
    )

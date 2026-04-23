import pytest
import respx
from httpx import Response

from app.services.idp_admin import KeycloakAdminClient, KeycloakAdminError


@pytest.mark.asyncio
@respx.mock
async def test_acquire_admin_token():
    respx.post("https://kc.example.com/realms/master/protocol/openid-connect/token").mock(
        return_value=Response(200, json={"access_token": "tok-123", "expires_in": 60})
    )
    client = KeycloakAdminClient(
        base_url="https://kc.example.com",
        admin_realm="master",
        target_realm="app",
        client_id="admin-cli",
        client_secret="s3cret",
    )
    token = await client._get_admin_token()
    assert token == "tok-123"


@pytest.mark.asyncio
@respx.mock
async def test_create_user_returns_user_id_from_location_header():
    respx.post("https://kc.example.com/realms/master/protocol/openid-connect/token").mock(
        return_value=Response(200, json={"access_token": "tok-123", "expires_in": 60})
    )
    respx.post("https://kc.example.com/admin/realms/app/users").mock(
        return_value=Response(
            201,
            headers={"Location": "https://kc.example.com/admin/realms/app/users/abc-uuid"},
        )
    )
    client = KeycloakAdminClient(
        base_url="https://kc.example.com",
        admin_realm="master",
        target_realm="app",
        client_id="admin-cli",
        client_secret="s3cret",
    )
    uid = await client.create_user(email="x@example.com")
    assert uid == "abc-uuid"


@pytest.mark.asyncio
@respx.mock
async def test_create_user_raises_on_409_conflict():
    respx.post("https://kc.example.com/realms/master/protocol/openid-connect/token").mock(
        return_value=Response(200, json={"access_token": "tok-123", "expires_in": 60})
    )
    respx.post("https://kc.example.com/admin/realms/app/users").mock(
        return_value=Response(409, json={"errorMessage": "User exists"})
    )
    client = KeycloakAdminClient(
        base_url="https://kc.example.com",
        admin_realm="master",
        target_realm="app",
        client_id="admin-cli",
        client_secret="s3cret",
    )
    with pytest.raises(KeycloakAdminError) as exc:
        await client.create_user(email="x@example.com")
    assert "exists" in str(exc.value).lower()


@pytest.mark.asyncio
@respx.mock
async def test_execute_actions_email_posts_required_actions():
    respx.post("https://kc.example.com/realms/master/protocol/openid-connect/token").mock(
        return_value=Response(200, json={"access_token": "tok-123", "expires_in": 60})
    )
    route = respx.put(
        "https://kc.example.com/admin/realms/app/users/abc-uuid/execute-actions-email"
    ).mock(return_value=Response(204))
    client = KeycloakAdminClient(
        base_url="https://kc.example.com",
        admin_realm="master",
        target_realm="app",
        client_id="admin-cli",
        client_secret="s3cret",
    )
    await client.send_setup_email(
        user_id="abc-uuid",
        actions=["UPDATE_PASSWORD", "VERIFY_EMAIL"],
        redirect_uri="https://app.example.com/",
    )
    assert route.called
    req = route.calls.last.request
    import json as _json
    body = _json.loads(req.content)
    assert body == ["UPDATE_PASSWORD", "VERIFY_EMAIL"]


@pytest.mark.asyncio
@respx.mock
async def test_acquire_admin_token_wraps_connect_error():
    import httpx
    respx.post(
        "https://kc.example.com/realms/master/protocol/openid-connect/token"
    ).mock(side_effect=httpx.ConnectError("boom"))
    client = KeycloakAdminClient(
        base_url="https://kc.example.com",
        admin_realm="master",
        target_realm="app",
        client_id="admin-cli",
        client_secret="s3cret",
    )
    with pytest.raises(KeycloakAdminError) as exc:
        await client._get_admin_token()
    assert "ConnectError" in str(exc.value) or "boom" in str(exc.value).lower()


@pytest.mark.asyncio
@respx.mock
async def test_acquire_admin_token_wraps_malformed_json():
    respx.post(
        "https://kc.example.com/realms/master/protocol/openid-connect/token"
    ).mock(return_value=Response(200, text="not json"))
    client = KeycloakAdminClient(
        base_url="https://kc.example.com",
        admin_realm="master",
        target_realm="app",
        client_id="admin-cli",
        client_secret="s3cret",
    )
    with pytest.raises(KeycloakAdminError):
        await client._get_admin_token()

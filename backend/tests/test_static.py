import asyncio
import os
from urllib.parse import unquote

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from app.main import app, mount_spa, safe_static_file


@pytest.mark.asyncio
async def test_health_still_works():
    """API routes take priority over SPA fallback."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_routes_not_caught_by_spa():
    """Non-existent API routes return 404, not index.html."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404


SECRET = b"SECRET-outside-static"
INDEX = '<!doctype html><div id="root"></div>'
FAVICON = '<svg xmlns="http://www.w3.org/2000/svg"/>'
NO_CACHE = "no-cache, no-store, must-revalidate"


@pytest.fixture
def spa(tmp_path):
    """An app serving a temporary static dir, with a secret file next to (outside) it."""
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "img").mkdir()
    (static / "index.html").write_text(INDEX)
    (static / "favicon.svg").write_text(FAVICON)
    (static / "assets" / "app.js").write_text("console.log(1)")
    secret = tmp_path / "secret.txt"
    secret.write_bytes(SECRET)
    # A sibling whose path shares the static dir's prefix ("static" vs "static2").
    (tmp_path / "static2").mkdir()
    (tmp_path / "static2" / "secret2.txt").write_bytes(SECRET)
    (static / "link.txt").symlink_to(secret)
    spa_app = FastAPI()
    mount_spa(spa_app, str(static))
    return spa_app, static, secret


async def _raw_get(asgi_app, raw_path: str):
    """GET ``raw_path`` as uvicorn delivers it: percent-decoded but not normalised.

    httpx collapses ``..`` segments client-side, which would hide traversal bugs,
    so the ASGI scope is built by hand.
    """
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "server": ("test", 80),
        "client": ("127.0.0.1", 12345),
        "root_path": "",
        "path": unquote(raw_path),
        "raw_path": raw_path.encode(),
        "query_string": b"",
        "headers": [(b"host", b"test")],
    }
    messages = []
    request_sent = False
    response_done = asyncio.Event()

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        # Like a real server: block until the response is complete, then disconnect.
        await response_done.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)
        if message["type"] == "http.response.body" and not message.get("more_body", False):
            response_done.set()

    await asyncio.wait_for(asgi_app(scope, receive, send), timeout=10)
    start = next(m for m in messages if m["type"] == "http.response.start")
    headers = {k.decode().lower(): v.decode() for k, v in start["headers"]}
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return start["status"], headers, body


# Request targets that resolve outside the static dir; {secret} is the secret's absolute path.
OUTSIDE_TARGETS = [
    "/{secret}",  # "//<abs>": the route param starts with "/"
    "/%2f{secret_rel_root}",  # encoded slash, decoded by the server
    "/../secret.txt",
    "/%2e%2e/secret.txt",
    "/img/../../secret.txt",
    "/img/%2e%2e/%2e%2e/secret.txt",
    "/link.txt",  # symlink inside static pointing outside
    "/../static2/secret2.txt",  # sibling dir sharing the static prefix
    "/%2e%2e/static2/secret2.txt",
]


def _target(template: str, secret) -> str:
    return template.format(secret=secret, secret_rel_root=str(secret).lstrip("/"))


@pytest.mark.asyncio
@pytest.mark.parametrize("template", OUTSIDE_TARGETS)
async def test_spa_never_serves_files_outside_static(spa, template):
    spa_app, _, secret = spa
    status, headers, body = await _raw_get(spa_app, _target(template, secret))
    assert SECRET not in body
    assert status == 200
    assert body.decode() == INDEX
    assert headers["cache-control"] == NO_CACHE


@pytest.mark.asyncio
@pytest.mark.parametrize("template", ["/assets/{secret}", "/assets/../../secret.txt"])
async def test_assets_mount_never_serves_files_outside_static(spa, template):
    spa_app, _, secret = spa
    status, _, body = await _raw_get(spa_app, _target(template, secret))
    assert SECRET not in body
    assert status == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("raw_path", ["/favicon.svg%00", "/%00", "/a%00/../../secret.txt"])
async def test_spa_nul_byte_falls_back_to_index(spa, raw_path):
    spa_app, _, _ = spa
    status, _, body = await _raw_get(spa_app, raw_path)
    assert status == 200
    assert body.decode() == INDEX


@pytest.mark.asyncio
async def test_spa_serves_root_static_file(spa):
    spa_app, _, _ = spa
    status, _, body = await _raw_get(spa_app, "/favicon.svg")
    assert status == 200
    assert body.decode() == FAVICON


@pytest.mark.asyncio
async def test_spa_serves_assets(spa):
    spa_app, _, _ = spa
    status, _, body = await _raw_get(spa_app, "/assets/app.js")
    assert status == 200
    assert body == b"console.log(1)"


@pytest.mark.asyncio
@pytest.mark.parametrize("raw_path", ["/", "/archive/123", "/assets", "/missing.png"])
async def test_spa_client_routes_get_uncached_index(spa, raw_path):
    spa_app, _, _ = spa
    status, headers, body = await _raw_get(spa_app, raw_path)
    assert status == 200
    assert body.decode() == INDEX
    assert headers["cache-control"] == NO_CACHE


@pytest.mark.asyncio
async def test_spa_unknown_api_route_is_404(spa):
    spa_app, _, _ = spa
    status, _, body = await _raw_get(spa_app, "/api/x")
    assert status == 404
    assert INDEX.encode() not in body


def test_safe_static_file_accepts_file_inside(spa):
    _, static, _ = spa
    assert os.path.samefile(safe_static_file(str(static), "favicon.svg"), static / "favicon.svg")
    assert os.path.samefile(safe_static_file(str(static), "assets/app.js"), static / "assets" / "app.js")


def test_safe_static_file_accepts_symlinked_static_dir(spa, tmp_path):
    _, static, _ = spa
    linked = tmp_path / "static-link"
    linked.symlink_to(static)
    assert os.path.samefile(safe_static_file(str(linked), "favicon.svg"), static / "favicon.svg")


@pytest.mark.parametrize("template", [
    "", "assets", "missing.txt", "favicon.svg\x00", "\x00",
    "{secret}", "../secret.txt", "img/../../secret.txt", "link.txt",
])
def test_safe_static_file_rejects(spa, template):
    _, static, secret = spa
    assert safe_static_file(str(static), _target(template, secret)) is None

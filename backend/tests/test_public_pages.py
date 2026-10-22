import logging

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.public_pages import (
    apply_features,
    fill_settings,
    format_days,
    load_privacy_notices,
    privacy_notice,
)
from app.routers import public_pages as router_mod

CSP = (
    "default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
    "font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)

GUIDE = """<!doctype html><html lang="{lang}"><body>
<ul><li>intro</li>
<!--tw-feature:llm--><li>llm toc</li><!--/tw-feature:llm-->
</ul>
<p>Mail <a href="mailto:__TW_SETTING_contact_email__">__TW_SETTING_contact_email__</a>
keep __TW_SETTING_retention_days__ days, v__TW_SETTING_app_version__</p>
<!--tw-feature:llm--><section>llm section</section><!--/tw-feature:llm-->
<!--tw-feature:privacy--><a href="/handbuch/datenschutz/">privacy</a><!--/tw-feature:privacy-->
</body></html>"""

SHELL = '<html lang="{lang}"><body><article class="notice" lang="__TW_NOTICE_LANG__">__TW_PRIVACY_NOTICE__</article></body></html>'


@pytest.fixture
def guide_dir(tmp_path, monkeypatch):
    for sub, lang in [("", "de"), ("en", "en")]:
        d = tmp_path / sub if sub else tmp_path
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(GUIDE.format(lang=lang), encoding="utf-8")
    for sub, lang in [("datenschutz", "de"), ("en/privacy", "en")]:
        d = tmp_path / sub
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(SHELL.format(lang=lang), encoding="utf-8")
    monkeypatch.setattr(router_mod, "GUIDE_DIR", tmp_path)
    monkeypatch.setattr(router_mod, "NOTICES", {})
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "CONTACT_EMAIL", "hilfe@example.org")
    return tmp_path


async def get(path):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        return await c.get(path)


def test_format_days():
    assert format_days(72, "de") == "3"
    assert format_days(4320, "en") == "180"
    assert format_days(36, "de") == "1,5"
    assert format_days(36, "en") == "1.5"
    assert format_days(25, "en") == "1"
    assert format_days(30, "en") == "1.3"  # 1.25 rounds half up like JS


def test_apply_features_off_and_on():
    html = "a<!--tw-feature:llm-->X<!--/tw-feature:llm-->b<!--tw-feature:api_tokens-->Y<!--/tw-feature:api_tokens-->"
    assert apply_features(html, {"llm": False, "api_tokens": True}) == "abY"
    assert apply_features(html, {"llm": True, "api_tokens": False}) == "aXb"


def test_fill_settings_escapes_and_blanks_unknown():
    out = fill_settings("__TW_SETTING_a__|__TW_SETTING_zzz__", {"a": 'a&b<c>"'})
    assert out == "a&amp;b&lt;c&gt;&quot;|"


@pytest.mark.asyncio
async def test_routing_and_headers(guide_dir):
    r = await get("/handbuch")
    assert r.status_code == 308
    assert r.headers["location"].endswith("/handbuch/")
    r = await get("/handbuch/en")
    assert r.status_code == 308
    assert r.headers["location"].endswith("/handbuch/en/")
    for p in ("/handbuch/", "/handbuch/en/"):
        r = await get(p)
        assert r.status_code == 200
        assert r.headers["content-security-policy"] == CSP
        assert r.headers["cache-control"] == "no-cache"
        assert "hilfe@example.org" in r.text
        assert "__TW_" not in r.text
        assert "llm section" in r.text
        assert "tw-feature" not in r.text


@pytest.mark.asyncio
async def test_llm_off_removes_blocks(guide_dir, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "")
    r = await get("/handbuch/")
    assert "llm" not in r.text.replace("tw-feature", "")


@pytest.mark.asyncio
async def test_escaping(guide_dir, monkeypatch):
    monkeypatch.setattr(settings, "CONTACT_EMAIL", "a&b<c>@x")
    r = await get("/handbuch/")
    assert "a&amp;b&lt;c&gt;@x" in r.text
    assert "a&b<c>" not in r.text
    assert "__TW_" not in r.text


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/handbuch/nope", "/handbuch/static/../index.html", "/handbuch/%2e%2e/index.html"])
async def test_no_spa_shell(guide_dir, path):
    r = await get(path)
    assert r.status_code == 404
    assert '<div id="root">' not in r.text


@pytest.mark.asyncio
async def test_no_notice(guide_dir):
    r = await get("/handbuch/datenschutz/")
    assert r.status_code == 404
    r = await get("/handbuch/")
    assert "datenschutz/" not in r.text


@pytest.mark.asyncio
async def test_notice_fallback_to_german(guide_dir, monkeypatch):
    monkeypatch.setattr(router_mod, "NOTICES", {"de": "<p>Deutscher Text</p>"})
    r = await get("/handbuch/en/privacy/")
    assert r.status_code == 200
    assert "Deutscher Text" in r.text
    assert 'lang="de"' in r.text
    assert r.headers["content-security-policy"] == CSP
    r = await get("/handbuch/")
    assert "datenschutz/" in r.text


def test_privacy_notice_helper():
    assert privacy_notice("en", {"de": "x"}) == ("x", "de")
    assert privacy_notice("en", {"de": "x", "en": "y"}) == ("y", "en")
    assert privacy_notice("de", {}) is None


@pytest.mark.asyncio
async def test_missing_file_logged_and_404(guide_dir, monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(settings, "PRIVACY_NOTICE_FILE_DE", str(tmp_path / "missing.html"))
    monkeypatch.setattr(settings, "PRIVACY_NOTICE_FILE_EN", "")
    with caplog.at_level(logging.ERROR):
        notices = load_privacy_notices()
    assert notices == {}
    assert any(rec.levelno == logging.ERROR for rec in caplog.records)
    monkeypatch.setattr(router_mod, "NOTICES", notices)
    assert (await get("/handbuch/datenschutz/")).status_code == 404


def test_load_notice_ok(monkeypatch, tmp_path):
    f = tmp_path / "p.html"
    f.write_text("<p>hi</p>", encoding="utf-8")
    monkeypatch.setattr(settings, "PRIVACY_NOTICE_FILE_DE", str(f))
    monkeypatch.setattr(settings, "PRIVACY_NOTICE_FILE_EN", "")
    assert load_privacy_notices() == {"de": "<p>hi</p>"}


@pytest.mark.asyncio
async def test_public_without_auth(guide_dir, monkeypatch):
    monkeypatch.setattr(settings, "DEV_MODE", False)
    r = await get("/handbuch/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_config_has_privacy_notice(monkeypatch):
    monkeypatch.setattr(router_mod, "NOTICES", {"en": "<p>x</p>"})
    r = await get("/api/config")
    assert r.status_code == 200
    assert r.json()["privacy_notice"] is True
    monkeypatch.setattr(router_mod, "NOTICES", {})
    assert (await get("/api/config")).json()["privacy_notice"] is False

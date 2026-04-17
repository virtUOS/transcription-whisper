import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db, get_db

DEV_HEADERS = {"X-Auth-Request-User": "test-user", "X-Auth-Request-Email": "test@test.com"}

TEST_USERS = ["test-user", "user-a", "user-b"]


@pytest_asyncio.fixture
async def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    await init_db(db_path)
    # Pre-insert users to satisfy the FK constraint on user_id columns
    async with get_db() as db:
        for user_id in TEST_USERS:
            await db.execute(
                "INSERT OR IGNORE INTO users (id, email) VALUES (?, ?)",
                (user_id, f"{user_id}@test.com"),
            )
        await db.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_transcription_preset_crud(client):
    # Create
    resp = await client.post("/api/presets/transcription", json={"name": "Lecture DE", "language": "de", "model": "large-v3"}, headers=DEV_HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Lecture DE"
    assert data["language"] == "de"
    preset_id = data["id"]

    # List
    resp = await client.get("/api/presets/transcription", headers=DEV_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Update
    resp = await client.put(f"/api/presets/transcription/{preset_id}", json={"name": "Lecture DE v2", "language": "de", "model": "large-v3-turbo"}, headers=DEV_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Lecture DE v2"

    # Delete
    resp = await client.delete(f"/api/presets/transcription/{preset_id}", headers=DEV_HEADERS)
    assert resp.status_code == 200

    # Verify deleted
    resp = await client.get("/api/presets/transcription", headers=DEV_HEADERS)
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_analysis_preset_crud(client):
    resp = await client.post("/api/presets/analysis", json={"name": "Summary EN", "template": "summary", "language": "en"}, headers=DEV_HEADERS)
    assert resp.status_code == 201
    preset_id = resp.json()["id"]

    resp = await client.get("/api/presets/analysis", headers=DEV_HEADERS)
    assert len(resp.json()) == 1

    resp = await client.delete(f"/api/presets/analysis/{preset_id}", headers=DEV_HEADERS)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_refinement_preset_crud(client):
    resp = await client.post("/api/presets/refinement", json={"name": "CS Lecture", "context": "Computer science lecture"}, headers=DEV_HEADERS)
    assert resp.status_code == 201
    preset_id = resp.json()["id"]

    resp = await client.get("/api/presets/refinement", headers=DEV_HEADERS)
    assert len(resp.json()) == 1

    resp = await client.delete(f"/api/presets/refinement/{preset_id}", headers=DEV_HEADERS)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_bundle_crud_and_default(client):
    # Create a transcription preset first
    resp = await client.post("/api/presets/transcription", json={"name": "T1"}, headers=DEV_HEADERS)
    t_id = resp.json()["id"]

    # Create bundle
    resp = await client.post("/api/presets/bundles", json={"name": "My Workflow", "transcription_preset_id": t_id}, headers=DEV_HEADERS)
    assert resp.status_code == 201
    bundle_id = resp.json()["id"]
    assert resp.json()["is_default"] is False

    # Set default
    resp = await client.put(f"/api/presets/bundles/{bundle_id}/default", headers=DEV_HEADERS)
    assert resp.status_code == 200

    # Get default (expanded)
    resp = await client.get("/api/presets/default", headers=DEV_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_default"] is True
    assert data["transcription_preset"]["name"] == "T1"

    # Clear default
    resp = await client.delete("/api/presets/default", headers=DEV_HEADERS)
    assert resp.status_code == 200

    resp = await client.get("/api/presets/default", headers=DEV_HEADERS)
    assert resp.json() is None

    # Delete bundle
    resp = await client.delete(f"/api/presets/bundles/{bundle_id}", headers=DEV_HEADERS)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_preset_nullifies_bundle_reference(client):
    # Create preset and bundle referencing it
    resp = await client.post("/api/presets/transcription", json={"name": "T1"}, headers=DEV_HEADERS)
    t_id = resp.json()["id"]
    resp = await client.post("/api/presets/bundles", json={"name": "Bundle", "transcription_preset_id": t_id}, headers=DEV_HEADERS)
    bundle_id = resp.json()["id"]

    # Delete the preset
    await client.delete(f"/api/presets/transcription/{t_id}", headers=DEV_HEADERS)

    # Bundle should still exist but with null reference
    resp = await client.get("/api/presets/bundles", headers=DEV_HEADERS)
    bundles = resp.json()
    assert len(bundles) == 1
    assert bundles[0]["transcription_preset_id"] is None


@pytest.mark.asyncio
async def test_user_isolation(client):
    # Create preset as user A
    resp = await client.post("/api/presets/transcription", json={"name": "A preset"}, headers={"X-Auth-Request-User": "user-a"})
    assert resp.status_code == 201

    # User B should not see it
    resp = await client.get("/api/presets/transcription", headers={"X-Auth-Request-User": "user-b"})
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_bundle_rejects_foreign_preset(client):
    # Each preset type, when referenced by another user's bundle, must 404.
    a = {"X-Auth-Request-User": "user-a"}
    b = {"X-Auth-Request-User": "user-b"}

    tp = (await client.post("/api/presets/transcription", json={"name": "A tp"}, headers=a)).json()["id"]
    ap = (await client.post("/api/presets/analysis", json={"name": "A ap", "template": "summary"}, headers=a)).json()["id"]
    rp = (await client.post("/api/presets/refinement", json={"name": "A rp"}, headers=a)).json()["id"]

    for field, value in [("transcription_preset_id", tp), ("analysis_preset_id", ap), ("refinement_preset_id", rp)]:
        resp = await client.post(
            "/api/presets/bundles",
            json={"name": "B bundle", field: value},
            headers=b,
        )
        assert resp.status_code == 404, f"{field} should be rejected across users"

    # Update must reject the same way.
    own_tp = (await client.post("/api/presets/transcription", json={"name": "B tp"}, headers=b)).json()["id"]
    bundle_id = (await client.post("/api/presets/bundles", json={"name": "B bundle", "transcription_preset_id": own_tp}, headers=b)).json()["id"]
    resp = await client.put(
        f"/api/presets/bundles/{bundle_id}",
        json={"name": "B bundle", "analysis_preset_id": ap},
        headers=b,
    )
    assert resp.status_code == 404

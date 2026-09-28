import time


def test_qr_create_and_join(client):
    s = client.post("/session", json={}).json()
    qr = client.post("/qr/create", json={"session_id": s["id"]}).json()
    assert "token" in qr and "join_url" in qr

    joined = client.post("/qr/join", json={"token": qr["token"]})
    assert joined.status_code == 200
    assert joined.json()["session"]["id"] == s["id"]


def test_qr_token_single_use(client):
    s = client.post("/session", json={}).json()
    qr = client.post("/qr/create", json={"session_id": s["id"]}).json()
    first = client.post("/qr/join", json={"token": qr["token"]})
    assert first.status_code == 200
    second = client.post("/qr/join", json={"token": qr["token"]})
    assert second.status_code == 410  # already consumed


def test_qr_token_expires(client):
    # conftest sets QR_TOKEN_TTL_SECONDS=1 for this test client
    s = client.post("/session", json={}).json()
    qr = client.post("/qr/create", json={"session_id": s["id"]}).json()
    time.sleep(1.5)
    r = client.post("/qr/join", json={"token": qr["token"]})
    assert r.status_code == 410


def test_invalid_token_rejected(client):
    r = client.post("/qr/join", json={"token": "not-a-real-token"})
    assert r.status_code == 410

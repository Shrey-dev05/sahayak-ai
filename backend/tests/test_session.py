def test_create_session(client):
    r = client.post("/session", json={"kiosk_id": "kiosk-1", "language": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["kiosk_id"] == "kiosk-1"
    assert body["status"] == "active"
    assert body["id"].startswith("sess_")


def test_get_session_context(client):
    s = client.post("/session", json={}).json()
    client.post("/chat", json={"session_id": s["id"], "text": "What is a cooperative society?"})
    r = client.get(f"/session/{s['id']}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["messages"]) == 2  # user + assistant
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"


def test_get_unknown_session_404(client):
    r = client.get("/session/does-not-exist")
    assert r.status_code == 404

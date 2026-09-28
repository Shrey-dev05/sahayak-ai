import io


def test_upload_rejects_unsupported_type(client):
    s = client.post("/session", json={}).json()
    r = client.post(
        "/upload",
        data={"session_id": s["id"]},
        files={"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 400


def test_upload_accepts_image_and_analyzes(client):
    s = client.post("/session", json={}).json()
    r = client.post(
        "/upload",
        data={"session_id": s["id"]},
        files={"file": ("doc.jpg", io.BytesIO(b"\xff\xd8\xff\xe0fake-jpeg-bytes"), "image/jpeg")},
    )
    assert r.status_code == 200
    up = r.json()
    assert up["processing_status"] == "pending"

    analyzed = client.post("/document/analyze", json={"upload_id": up["id"], "language": "en"})
    assert analyzed.status_code == 200
    # Mock OCR is honest about not having real text - the response must not
    # fabricate an answer as if it had read the document.
    assert analyzed.json()["response_mode"] == "HUMAN_ESCALATION"


def test_upload_rejects_unknown_session(client):
    r = client.post(
        "/upload",
        data={"session_id": "does-not-exist"},
        files={"file": ("doc.jpg", io.BytesIO(b"data"), "image/jpeg")},
    )
    assert r.status_code == 404

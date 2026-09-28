def test_complex_request_routes_to_mobile_handoff(client):
    s = client.post("/session", json={}).json()
    r = client.post("/chat", json={"session_id": s["id"], "text": "I need to scan a document"})
    assert r.json()["response_mode"] == "MOBILE_HANDOFF"


def test_short_definition_routes_speech_or_screen(client):
    s = client.post("/session", json={}).json()
    r = client.post("/chat", json={"session_id": s["id"], "text": "What is interest?"})
    assert r.json()["response_mode"] in ("SPEECH_ONLY", "SCREEN_SUMMARY")


def test_crop_insurance_question_generates_action_plan(client):
    s = client.post("/session", json={}).json()
    r = client.post("/chat", json={"session_id": s["id"], "text": "Tell me about crop insurance"}).json()
    assert r["action_plan"] is not None
    assert len(r["action_plan"]["steps"]) > 0

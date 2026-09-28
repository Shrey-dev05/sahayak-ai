def test_retrieval_finds_relevant_approved_doc(client):
    s = client.post("/session", json={}).json()
    r = client.post("/chat", json={"session_id": s["id"], "text": "What is a PACS?"})
    body = r.json()
    assert len(body["sources"]) >= 1
    assert any("PACS" in src["title"] for src in body["sources"])


def test_pending_document_not_retrieved(client):
    # The seeded "Sample scheme XYZ" doc is status=pending and must not be
    # searchable until an admin approves it.
    s = client.post("/session", json={}).json()
    r = client.post("/chat", json={"session_id": s["id"], "text": "Tell me about sample scheme XYZ"})
    body = r.json()
    titles = [src["title"] for src in body["sources"]]
    assert "Sample scheme XYZ - awaiting verification" not in titles


def test_no_evidence_fallback(client):
    s = client.post("/session", json={}).json()
    r = client.post("/chat", json={"session_id": s["id"], "text": "asdkjqwe nonsense gibberish xyz123"})
    body = r.json()
    assert body["response_mode"] == "HUMAN_ESCALATION"
    assert body["sources"] == []


def test_approving_document_makes_it_retrievable(client):
    created = client.post("/admin/documents", json={
        "title": "Test scheme ABC", "text": "Test scheme ABC gives farmers a subsidy for drip irrigation.",
        "issuer": "Test", "language": "en",
    }).json()
    assert created["status"] == "pending"

    s = client.post("/session", json={}).json()
    before = client.post("/chat", json={"session_id": s["id"], "text": "Tell me about scheme ABC"}).json()
    assert not any("Test scheme ABC" in src["title"] for src in before["sources"])

    client.post(f"/admin/documents/{created['id']}/approve")
    after = client.post("/chat", json={"session_id": s["id"], "text": "Tell me about scheme ABC"}).json()
    assert any("Test scheme ABC" in src["title"] for src in after["sources"])


def test_ambiguous_word_alone_does_not_retrieve(client):
    # "weather" appears in the crop-insurance doc ("damaged by weather..."),
    # but a weather-forecast question is not a crop-insurance question.
    # Regression test for the AMBIGUOUS_TERMS gate in rag/retrieval.py.
    s = client.post("/session", json={}).json()
    r = client.post("/chat", json={"session_id": s["id"], "text": "What's the weather today?"}).json()
    assert r["sources"] == []
    assert r["response_mode"] == "HUMAN_ESCALATION"


def test_specific_fact_not_in_evidence_is_not_answered(client):
    # The crop-insurance doc is topically relevant but contains no deadline
    # date - the system must not present its general text as if it answers
    # a date-specific question. Regression test for app/rag/fact_check.py.
    s = client.post("/session", json={}).json()
    r = client.post("/chat", json={
        "session_id": s["id"], "text": "What is the crop insurance application deadline this season?",
    }).json()
    assert r["response_mode"] == "HUMAN_ESCALATION"
    assert r["sources"] == []

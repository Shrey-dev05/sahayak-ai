import httpx
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://127.0.0.1:8008"

def test_live_workflow():
    with httpx.Client(base_url=BASE, timeout=90.0) as client:
        # 1. Health check
        h = client.get("/health")
        assert h.status_code == 200, f"Health failed: {h.text}"
        print("[OK] 1. Backend /health is OK")

        # 2. Start session
        sess = client.post("/session", json={"kiosk_id": "box-kiosk-test", "language": "hi"}).json()
        session_id = sess["id"]
        print(f"[OK] 2. Session created: {session_id}")

        # 3. Ask complex query in Hindi
        hi_query = "मेरी धान की फसल भारी बारिश से खराब हो गई है, मुझे क्लेम कैसे मिलेगा और क्या करना होगा?"
        r1 = client.post("/chat", json={"session_id": session_id, "text": hi_query, "language": "hi"})
        assert r1.status_code == 200, f"Chat failed: {r1.text}"
        d1 = r1.json()

        print("\n--- Hindi Complex Query Response ---")
        print(f"Intent: {d1.get('intent')}")
        print(f"Response mode: {d1.get('response_mode')}")
        print(f"Kiosk summary:\n{d1.get('kiosk_summary')}")
        print(f"QR Object: {d1.get('qr')}")
        print(f"Spoken text:\n{d1.get('spoken_text')}")

        # Assertions for Kiosk & Speech requirements
        assert d1.get("kiosk_summary") is not None, "Kiosk summary should be populated for complex crop query"
        assert d1.get("qr") is not None, "QR object should be generated for mobile handoff"
        assert "token" in d1["qr"], "QR must contain token"
        assert "join_url" in d1["qr"], "QR must contain join_url"

        # Verify TTS speech has NO markdown symbols
        spoken = d1.get("spoken_text", "")
        bad_symbols = ["*", "#", "•", "`", "[", "]", "{", "}"]
        for sym in bad_symbols:
            assert sym not in spoken, f"Spoken text contains forbidden symbol '{sym}': {spoken}"
        print("[OK] 3. Hindi complex response verified: Brief Kiosk summary, QR token present, clean symbol-free TTS")

        # 4. Test Mobile QR join
        qr_token = d1["qr"]["token"]
        join_res = client.post("/qr/join", json={"token": qr_token})
        assert join_res.status_code == 200, f"QR join failed: {join_res.text}"
        join_data = join_res.json()
        assert len(join_data["messages"]) >= 2, "Mobile join should contain prior kiosk messages"
        print(f"[OK] 4. Mobile QR join verified: Retrieved {len(join_data['messages'])} prior messages from kiosk session")

        # 5. Test PDF trigger request
        pdf_query = "iska pdf bana do"
        r2 = client.post("/chat", json={"session_id": session_id, "text": pdf_query, "language": "hi"})
        assert r2.status_code == 200
        d2 = r2.json()
        print("\n--- PDF Trigger Response ---")
        print(f"Answer: {d2.get('answer_text')}")
        print(f"Trigger PDF flag: {d2.get('trigger_pdf')}")
        assert d2.get("trigger_pdf") is True, "trigger_pdf flag must be True for 'pdf bana do'"
        print("[OK] 5. PDF generation intent recognized and trigger_pdf flag set to True")

        # 6. Test Romanized Hindi query maps automatically to Pure Hindi (hi)
        hing_query = "Mera fasal flood se doob gaya hai, PMFBY claim ka full step by step process batao"
        r3 = client.post("/chat", json={"session_id": session_id, "text": hing_query})
        assert r3.status_code == 200
        d3 = r3.json()
        print("\n--- Roman Hindi to Pure Hindi Response ---")
        print(f"Detected language: {d3.get('language')}")
        print(f"Kiosk summary: {d3.get('kiosk_summary')}")
        print(f"Spoken text: {d3.get('spoken_text')}")
        assert d3.get("language") == "hi", f"Expected language 'hi' but got {d3.get('language')}"
        spoken3 = d3.get("spoken_text", "")
        for sym in bad_symbols:
            assert sym not in spoken3, f"Hindi spoken text contains forbidden symbol '{sym}': {spoken3}"
        print("[OK] 6. Roman Hindi automatically detected and responded in pure Hindi (hi)")

        print("\n==========================================")
        print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
        print("==========================================")

if __name__ == "__main__":
    test_live_workflow()

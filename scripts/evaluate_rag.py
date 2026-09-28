"""
Runs data/eval/rag_evaluation.jsonl against the actual backend (via
FastAPI's TestClient, so no server needs to be running) and checks:
  - did retrieval surface the expected source document (when one exists)?
  - did the no-evidence fallback fire when no source should exist?
This is a real, executable check of the "don't fabricate" rule in
plan section 12 / pipeline section 26 - not just a written promise.

Run: python3 scripts/evaluate_rag.py
"""
import json
import sys
import tempfile
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

# isolate this run in its own temp database, same pattern as tests/conftest.py
tmp_db = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

EVAL_FILE = ROOT / "data" / "eval" / "rag_evaluation.jsonl"


def run():
    client = TestClient(app)
    session_id = client.post("/session", json={}).json()["id"]

    rows = [json.loads(l) for l in open(EVAL_FILE, encoding="utf-8") if l.strip()]
    passed, failed = 0, []

    for row in rows:
        r = client.post("/chat", json={"session_id": session_id, "text": row["question"]}).json()
        got_titles = {s["title"] for s in r.get("sources", [])}
        expected = set(row.get("expected_sources", []))

        if expected:
            ok = expected.issubset(got_titles)
        else:
            # no evidence should exist -> system must fall back, not answer confidently
            ok = (len(got_titles) == 0) or (r["response_mode"] == "HUMAN_ESCALATION")

        if ok:
            passed += 1
        else:
            failed.append({"question": row["question"], "expected": list(expected),
                            "got_sources": list(got_titles), "response_mode": r["response_mode"]})

    print(f"{passed}/{len(rows)} evaluation cases passed.\n")
    if failed:
        print("Failed cases:")
        for f in failed:
            print(f"  - {f}")
    return passed, len(rows), failed


if __name__ == "__main__":
    passed, total, failed = run()
    report_path = ROOT / "data" / "eval" / "evaluation_report.txt"
    lines = [f"{passed}/{total} evaluation cases passed.", ""]
    if failed:
        lines.append("Failed cases:")
        for f in failed:
            lines.append(f"  - {f}")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved report -> {report_path}")
    sys.exit(0 if not failed else 1)

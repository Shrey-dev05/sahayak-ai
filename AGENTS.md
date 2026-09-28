# Agent entry point

Read [`README.md`](./README.md) — specifically the section **"If you are an
AI agent picking this up"** near the top. It has the bootstrap commands,
the request-path walkthrough, the design conventions already in use, the
rules that must not be broken, and a prioritized task backlog with concrete
"done when" checks.

Fastest path in:
```bash
cd backend && pip install -r requirements.txt --break-system-packages && pytest -q
```
19 tests should pass. If they don't, that's the first thing to fix.

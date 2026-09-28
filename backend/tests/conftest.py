import sys
import os
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test.db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("QR_TOKEN_TTL_SECONDS", "1")  # short TTL to test expiry quickly

    # Import app modules AFTER env vars are set, and fresh each test, so
    # each test gets its own engine bound to its own temp database file.
    for mod in list(sys.modules):
        if mod.startswith("app"):
            del sys.modules[mod]

    from app.main import app
    with TestClient(app) as c:
        yield c

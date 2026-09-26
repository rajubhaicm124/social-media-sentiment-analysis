"""Shared pytest fixtures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Point the app at a throwaway database before any settings module is imported.
# The path is absolute because pytest may run from any working directory.
TEST_DB_DIR = PROJECT_DIR / "data"
TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_DB_DIR / 'test_socialscope.db').as_posix()}"
os.environ.setdefault("ENABLE_DEMO_MODE", "true")

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def demo_analysis(client: TestClient) -> dict:
    """One completed YouTube demo analysis, reused across the test module."""
    response = client.post("/api/demo", json={"platform": "youtube", "user_name": "Tester"})
    assert response.status_code == 200, response.text
    return response.json()

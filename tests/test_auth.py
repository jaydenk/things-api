import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from things_api.auth import require_token


def _make_app(token: str) -> FastAPI:
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint(
        _: None = require_token(token),
    ):
        return {"ok": True}

    return app


def test_valid_token():
    client = TestClient(_make_app("secret"))
    resp = client.get("/test", headers={"Authorization": "Bearer secret"})
    assert resp.status_code == 200


def test_missing_token():
    client = TestClient(_make_app("secret"))
    resp = client.get("/test")
    assert resp.status_code == 401


def test_wrong_token():
    client = TestClient(_make_app("secret"))
    resp = client.get("/test", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


def test_malformed_header():
    client = TestClient(_make_app("secret"))
    resp = client.get("/test", headers={"Authorization": "Token secret"})
    assert resp.status_code == 401

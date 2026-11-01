import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def make_link(client, url="https://example.com"):
    return client.post("/api/links", json={"url": url}).json()["code"]


def test_create_and_redirect(client):
    res = client.post("/api/links", json={"url": "https://example.com"})
    assert res.status_code == 201
    code = res.json()["code"]
    redirect = client.get(f"/{code}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com"


def test_click_counter(client):
    code = make_link(client)
    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)
    assert client.get("/api/links").json()[0]["clicks"] == 2


@pytest.mark.parametrize(
    "bad", ["example.com", "ftp://example.com", "javascript:alert(1)", ""]
)
def test_rejects_invalid_urls(client, bad):
    res = client.post("/api/links", json={"url": bad})
    assert res.status_code == 400


def test_unknown_code_returns_404(client):
    assert client.get("/nope123", follow_redirects=False).status_code == 404


def test_delete(client):
    code = make_link(client)
    assert client.delete(f"/api/links/{code}").status_code == 204
    assert client.delete(f"/api/links/{code}").status_code == 404

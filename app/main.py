import secrets
import sqlite3
import string
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from . import db

STATIC_DIR = Path(__file__).parent / "static"
ALPHABET = string.ascii_letters + string.digits


@asynccontextmanager
async def lifespan(app):
    db.init_db()
    yield


app = FastAPI(title="URL Shortener", lifespan=lifespan)


class LinkIn(BaseModel):
    url: str


def make_code(length=6):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/links", status_code=201)
def create_link(body: LinkIn):
    url = body.url.strip()
    if not is_valid_url(url):
        raise HTTPException(
            status_code=400, detail="URL must start with http:// or https://"
        )
    for _ in range(5):
        code = make_code()
        try:
            db.create_link(code, url)
            return {"code": code, "short_path": f"/{code}", "url": url}
        except sqlite3.IntegrityError:
            continue  # the code already existed, so try a new one
    raise HTTPException(status_code=500, detail="Could not generate a unique code")


@app.get("/api/links")
def list_links():
    return db.list_links()


@app.delete("/api/links/{code}", status_code=204)
def delete_link(code: str):
    if not db.delete_link(code):
        raise HTTPException(status_code=404, detail="Link not found")


@app.get("/{code}")
def follow(code: str):
    link = db.get_link(code)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    db.add_click(code)
    return RedirectResponse(link["url"], status_code=307)

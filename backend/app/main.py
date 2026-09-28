from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.seed import seed
from app.api import (
    routes_session, routes_chat, routes_voice, routes_qr,
    routes_upload, routes_grievance, routes_admin,
)

seed()

app = FastAPI(title="Sahayak AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_session.router, tags=["session"])
app.include_router(routes_chat.router, tags=["chat"])
app.include_router(routes_voice.router, tags=["voice"])
app.include_router(routes_qr.router, tags=["qr"])
app.include_router(routes_upload.router, tags=["upload"])
app.include_router(routes_grievance.router, tags=["grievance"])
app.include_router(routes_admin.router, tags=["admin"])

ROOT = Path(__file__).resolve().parent.parent.parent
app.mount("/kiosk", StaticFiles(directory=ROOT / "frontend-kiosk", html=True), name="kiosk")
app.mount("/mobile", StaticFiles(directory=ROOT / "frontend-mobile", html=True), name="mobile")
app.mount("/admin-ui", StaticFiles(directory=ROOT / "admin", html=True), name="admin-ui")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return RedirectResponse(url="/kiosk/")

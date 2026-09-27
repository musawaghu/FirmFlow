import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import NotConfigured
from app.routers import admin, baseline, chat, manuals, modules, quiz

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="FIRM FLOW API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(manuals.router)
app.include_router(modules.router)
app.include_router(modules.passages_router)
app.include_router(quiz.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(baseline.router)


@app.exception_handler(NotConfigured)
def not_configured(request: Request, exc: NotConfigured):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/api/health")
def health():
    return {"ok": True}

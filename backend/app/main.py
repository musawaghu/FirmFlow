import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import NotConfigured
from app.ratelimit import check_ip, too_many
from app.routers import account, admin, baseline, chat, manuals, modules, quiz

logging.basicConfig(level=logging.INFO)

settings = get_settings()
# The interactive docs are handy locally but map the whole API for anyone in production.
docs = {} if not settings.is_production else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(title="FIRM FLOW API", **docs)

app.include_router(account.router)
app.include_router(manuals.router)
app.include_router(modules.router)
app.include_router(modules.passages_router)
app.include_router(quiz.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(baseline.router)


# Middleware added later wraps middleware added earlier, so the order below is
# (outermost first): CORS, security headers, per-IP rate limit. CORS has to be
# outermost so the browser can read 429 responses too.

@app.middleware("http")
async def ip_rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.url.path != "/api/health" and request.method != "OPTIONS":
        ip = request.client.host if request.client else "unknown"
        if (wait := check_ip(ip)) is not None:
            error = too_many(wait)
            return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers=error.headers)
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    headers = response.headers
    headers.setdefault("X-Content-Type-Options", "nosniff")
    headers.setdefault("X-Frame-Options", "DENY")
    headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.path.startswith("/api/"):
        # JSON only: nothing here should be rendered, framed, or cached (responses hold personal data).
        headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        headers.setdefault("Cache-Control", "no-store")
    if settings.is_production:
        headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=False,  # the frontend sends a bearer token, not cookies
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Retry-After"],
)


@app.exception_handler(NotConfigured)
def not_configured(request: Request, exc: NotConfigured):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/api/health")
def health():
    return {"ok": True}

import re
from functools import lru_cache
from time import perf_counter

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.routing import Match

from app.config import settings
from app.routers import auth, chat, consent, documents, health
from app.services.metrics import (
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    RATE_LIMIT_REJECTIONS_TOTAL,
    REGISTRY,
)
from app.services.rate_limiter import get_client_identifier, rate_limiter

app = FastAPI(
    title=settings.APP_NAME,
    description="MediAssist general health-information platform",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

EXEMPT_PATHS = {"/", "/api/v1/health", "/docs", "/openapi.json", "/redoc", "/metrics"}


def _route_template(request: Request) -> str:
    """Resolve to a registered route template; never label metrics with raw URLs."""
    matched = request.scope.get("route")
    template = getattr(matched, "path", None)
    if template:
        return template
    for route in request.app.routes:
        try:
            match, _ = route.matches(request.scope)
        except (AttributeError, KeyError, TypeError):
            continue
        if match is Match.FULL:
            route_path = getattr(route, "path", None)
            if route_path:
                return route_path
    # Current FastAPI versions may keep included routers in lazy wrappers,
    # which cannot be matched directly until dispatch. Match against the
    # OpenAPI path templates for requests rejected by the limiter pre-dispatch.
    path = request.url.path
    for route_path in request.app.openapi().get("paths", {}):
        if _template_regex(route_path).fullmatch(path):
            return route_path
    return "__unmatched__"


@lru_cache(maxsize=256)
def _template_regex(route_path: str) -> re.Pattern[str]:
    parts = re.split(r"(\{[^{}]+\})", route_path)
    pattern = "^" + "".join("[^/]+" if part.startswith("{") else re.escape(part) for part in parts) + "$"
    return re.compile(pattern)


@app.middleware("http")
async def operational_and_rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    # The scrape endpoint is excluded to avoid self-observation feedback and
    # never passes through the limiter. Health/readiness and docs remain exempt
    # from rate limiting but are still measured.
    if path == "/metrics":
        return await call_next(request)

    method = request.method if request.method in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"} else "OTHER"
    route = _route_template(request)
    started = perf_counter()
    outcome_status = "500"
    HTTP_REQUESTS_IN_PROGRESS.labels(method=method, route=route).inc()

    try:
        if request.method != "OPTIONS" and settings.ENABLE_RATE_LIMIT and path not in EXEMPT_PATHS:
            client_id = get_client_identifier(request)
            limit_result = rate_limiter.check(client_id)
            if not limit_result.allowed:
                RATE_LIMIT_REJECTIONS_TOTAL.labels(route=route).inc()
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": (
                            f"Rate limit exceeded: maximum {limit_result.limit} requests per minute allowed. "
                            f"Please try again in {limit_result.retry_after} seconds."
                        )
                    },
                    headers={
                        "Retry-After": str(limit_result.retry_after),
                        "X-RateLimit-Limit": str(limit_result.limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(limit_result.reset_epoch),
                    },
                )
            else:
                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(limit_result.limit)
                response.headers["X-RateLimit-Remaining"] = str(limit_result.remaining)
                response.headers["X-RateLimit-Reset"] = str(limit_result.reset_epoch)
        else:
            response = await call_next(request)

        outcome_status = str(response.status_code)
        # Route resolution after dispatch handles routes that were initially unmatched.
        route = _route_template(request)
        return response
    except Exception:
        outcome_status = "500"
        raise
    finally:
        elapsed = perf_counter() - started
        HTTP_REQUESTS_TOTAL.labels(method=method, route=route, status_code=outcome_status).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, route=route).observe(elapsed)
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, route=route).dec()


for router in (auth.router, consent.router, chat.router, health.router, documents.router):
    app.include_router(router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Welcome to MediAssist API", "status": "running"}


@app.get("/api/v1/health", include_in_schema=False)
def health_check():
    return {"status": "healthy", "application": "MediAssist"}


@app.get("/metrics", include_in_schema=False)
def metrics_endpoint():
    if not settings.METRICS_ENABLED:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

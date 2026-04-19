import logging
import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import app_config
from app.core.logging_config import configure_logging, reset_request_id, set_request_id

configure_logging(log_level=app_config.log_level, log_format=app_config.log_format)

logger = logging.getLogger("app.request")

app = FastAPI(title=app_config.title)
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors_allow_origins,
    allow_origin_regex=app_config.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    token = set_request_id(request_id)
    started_at = time.perf_counter()
    path = request.url.path
    method = request.method
    client_ip = request.client.host if request.client else None

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.exception(
            "request_failed",
            extra={
                "http_method": method,
                "path": path,
                "status_code": 500,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            },
        )
        reset_request_id(token)
        raise

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    if app_config.log_requests_enabled:
        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            "request_completed",
            extra={
                "http_method": method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            },
        )

    reset_request_id(token)
    return response

app.include_router(api_router, prefix=app_config.api_v1_prefix)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)

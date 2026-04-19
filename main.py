from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import app_config

app = FastAPI(title=app_config.title)
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors_allow_origins,
    allow_origin_regex=app_config.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=app_config.api_v1_prefix)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)

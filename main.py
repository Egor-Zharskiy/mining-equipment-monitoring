from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import app_config

app = FastAPI(title=app_config.title)
app.include_router(api_router, prefix=app_config.api_v1_prefix)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)

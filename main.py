from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
import os
import logging
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend())
    yield

app = FastAPI(title="Ciphered Pattern API", lifespan=lifespan)

if os.getenv("DEBUG", False) or "--debug" in sys.argv:
    logger.info("Debug mode enabled")
    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.debug(f"Incoming request: {request.method} {request.url}")
        logger.debug(f"Request headers: {request.headers}")
        response = await call_next(request)
        logger.debug(f"Response headers: {response.headers}")
        return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://localhost:4321",
        "http://localhost:4322",
        "http://localhost:4323",
        "http://127.0.0.1:4321",
        "http://127.0.0.1:4322",
        "http://127.0.0.1:4323",
        "https://sahil.ink",
        "https://*.sahil.ink",
        "http://sahil.ink",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open(os.getenv("PATTERNS_FILE", "source/patterns.txt"), "r") as f:
    patterns = {pattern: words.split() for pattern, words in [line.strip().split(" ", 1) for line in f]}

@app.get("/")
async def root():
    return "view docs at /docs"

@app.get("/pattern/{pattern}")
@cache(expire=300) 
async def pattern(pattern: str):
    if patterns.get(pattern):
        return {"message": patterns[pattern]}
    else:
        return {"message": "pattern not found"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=("0.0.0.0" if "--host" in sys.argv else "localhost"), port=int(os.getenv("PORT", 0)), reload="--dev" in sys.argv)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
import sys
import os
import logging
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from contextlib import asynccontextmanager

DEBUG = os.getenv("DEBUG", False) or "--debug" in sys.argv

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend())
    yield

app = FastAPI(
    title="Ciphered Pattern API",
    description="An API that returns words matching specific patterns",
    version="1.0.1",
    lifespan=lifespan
)

if DEBUG:
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

class PatternResponse(BaseModel):
    message: List[str]

class PatternError(BaseModel):
    detail: str

def validate_pattern(pattern: str) -> bool:
    """
    Validates if the pattern follows the rules:
    1. Must be numeric
    2. Must not skip any integers (e.g., 1245 is invalid because it skips 3)
    3. Must be 20 characters or less
    4. Must be a valid pattern (e.g., 1123, 1221 are valid)
    """
    if not pattern.isdigit() or len(pattern) > 20:
        return False
    
    highest_digit = 0
    for digit in pattern:
        num = int(digit)
        if num > highest_digit + 1:
            return False
        highest_digit = max(highest_digit, num)
    
    return True

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    """
    return "view swagger docs at /docs"

@app.get("/pattern/{pattern}", 
         response_model=PatternResponse,
         tags=["Patterns"],
         summary="Get words matching a pattern",
         description="Returns a list of words that match the specified pattern.\n\n"
                    "Pattern Rules:\n"
                    "- Must be numeric\n"
                    "- Must not skip any integers (e.g., 1245 is invalid because it skips 3)\n"
                    "- Must be 20 characters or less\n\n"
                    "Examples:\n"
                    "- Valid patterns: 1123, 1221\n"
                    "- Invalid patterns: 1245, 234, AABBA",
         responses={
             200: {
                 "description": "Successfully found matching words",
                 "content": {
                     "application/json": {
                         "example": {"message": ["word1", "word2", "word3"]}
                     }
                 }
             },
             400: {
                 "description": "Invalid pattern format",
                 "model": PatternError,
                 "content": {
                     "application/json": {
                         "example": {"detail": "Invalid pattern format. Pattern must be numeric, not skip integers, and be 20 characters or less."}
                     }
                 }
             },
             404: {
                 "description": "Pattern not found",
                 "model": PatternError,
                 "content": {
                     "application/json": {
                         "example": {"detail": "Pattern not found"}
                     }
                 }
             }
         })
@cache(expire=300) 
async def pattern(pattern: str):
    """
    Get words matching a specific pattern.
    
    Args:
        pattern (str): The pattern to match against. Must follow the pattern rules.
        
    Returns:
        PatternResponse: A list of words matching the pattern
        
    Raises:
        HTTPException: If the pattern format is invalid or pattern is not found
    """
    if not validate_pattern(pattern):
        raise HTTPException(
            status_code=400,
            detail="Invalid pattern format. Pattern must be numeric, not skip integers, and be 20 characters or less."
        )
    
    if patterns.get(pattern):
        return {"message": patterns[pattern]}
    else:
        raise HTTPException(status_code=404, detail="Pattern not found")

if __name__ == "__main__":
    host = "0.0.0.0" if "--host" in sys.argv else "localhost"
    port = int(os.getenv("PORT", 0))
    logger.info(f"Starting server on {host}:{port} with reload={DEBUG}")
    uvicorn.run("main:app", host=host, port=port, reload=DEBUG)
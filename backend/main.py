import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.routers import auth, gamification, learning, modules, notion, social

logger = logging.getLogger(__name__)

app = FastAPI(title="MasterMind API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred."}},
    )


app.include_router(auth.router)
app.include_router(learning.router)
app.include_router(modules.router)
app.include_router(notion.router)
app.include_router(gamification.router)
app.include_router(social.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

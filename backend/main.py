from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, gamification, learning, modules, notion

app = FastAPI(title="MasterMind API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(learning.router)
app.include_router(modules.router)
app.include_router(notion.router)
app.include_router(gamification.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

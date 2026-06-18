from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers.trips import router as trips_router
from routers.stream import router as stream_router
from db import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Agentic Travel Planner",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trips_router, prefix="/api/trips", tags=["trips"])
app.include_router(stream_router, prefix="/api/trips", tags=["stream"])


@app.get("/health")
def health():
    return {"status": "ok"}

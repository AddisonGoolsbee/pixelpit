"""FastAPI application entry point — serves the frontend and REST API for the dashboard."""

import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
import os

from app.database import init_db
from app.routers import agents, artworks


connected_clients: list[WebSocket] = []


async def broadcast(data: dict):
    msg = json.dumps(data)
    for ws in connected_clients[:]:
        try:
            await ws.send_text(msg)
        except Exception:
            connected_clients.remove(ws)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="PixelPit", lifespan=lifespan)

app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(artworks.router, prefix="/api/artworks", tags=["artworks"])


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(ws)


# Serve React frontend in production
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = os.path.join(frontend_dist, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

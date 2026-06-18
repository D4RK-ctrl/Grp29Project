import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from routers.trips import get_or_create_queue

router = APIRouter()


@router.websocket("/{trip_id}/stream")
async def stream_trip(websocket: WebSocket, trip_id: str):
    await websocket.accept()
    queue = get_or_create_queue(trip_id)

    try:
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(msg)
                if msg.get("type") in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                # Heartbeat to keep the connection alive during long searches
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    # NOTE: we intentionally do NOT delete the queue here. The agent thread may
    # still be running and pushing messages; deleting it would break streaming.
    # Queues are small and cleared when the server restarts.

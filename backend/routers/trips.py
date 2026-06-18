import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from db import get_db, TripModel, ChangeModel
from models import TripCreate, ChangeRequest, TripResponse
from agent.orchestrator import run_planning_agent, run_change_agent
from stream_queue import StreamQueue

router = APIRouter()

# In-memory queues for WebSocket streaming (keyed by trip_id).
# StreamQueue is thread-safe, so the agent's background thread and the
# WebSocket's main event loop can share it safely.
_queues: dict[str, StreamQueue] = {}


def get_or_create_queue(trip_id: str) -> StreamQueue:
    if trip_id not in _queues:
        _queues[trip_id] = StreamQueue()
    return _queues[trip_id]


def _start_planning(trip_id: str, brief: str, db_url: str):
    """Background task entry point (run in asyncio event loop)."""
    import asyncio
    from db import SessionLocal, TripModel

    async def _run():
        queue = get_or_create_queue(trip_id)
        from agent.orchestrator import run_planning_agent
        itinerary = None
        try:
            itinerary = await run_planning_agent(brief, trip_id, queue)
        except Exception as e:
            import traceback
            traceback.print_exc()
            await queue.put({
                "type": "error",
                "message": f"Agent error: {type(e).__name__}: {e}",
            })

        db = SessionLocal()
        try:
            trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
            if trip:
                trip.status = "complete" if itinerary else "failed"
                trip.itinerary = itinerary
                db.commit()
        finally:
            db.close()

    asyncio.run(_run())


@router.post("", response_model=TripResponse)
def create_trip(body: TripCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    trip_id = str(uuid.uuid4())
    trip = TripModel(id=trip_id, brief=body.brief, status="planning")
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Ensure queue exists before background task starts
    get_or_create_queue(trip_id)

    import threading
    thread = threading.Thread(
        target=_start_planning, args=(trip_id, body.brief, ""), daemon=True
    )
    thread.start()

    return trip


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: str, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.get("", response_model=list[TripResponse])
def list_trips(db: Session = Depends(get_db)):
    return db.query(TripModel).order_by(TripModel.created_at.desc()).limit(20).all()


@router.post("/{trip_id}/change", response_model=TripResponse)
def request_change(trip_id: str, body: ChangeRequest, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if not trip.itinerary:
        raise HTTPException(status_code=400, detail="Trip has no itinerary yet")

    change_id = str(uuid.uuid4())
    change = ChangeModel(id=change_id, trip_id=trip_id, change_request=body.change_request)
    db.add(change)

    trip.status = "planning"
    db.commit()

    get_or_create_queue(trip_id)

    import threading

    def _run_change():
        import asyncio
        from db import SessionLocal, TripModel, ChangeModel
        from agent.orchestrator import run_change_agent

        async def _run():
            queue = get_or_create_queue(trip_id)
            revised = await run_change_agent(trip.itinerary, body.change_request, queue)
            db2 = SessionLocal()
            try:
                t = db2.query(TripModel).filter(TripModel.id == trip_id).first()
                c = db2.query(ChangeModel).filter(ChangeModel.id == change_id).first()
                if t:
                    t.status = "complete" if revised else "failed"
                    t.itinerary = revised or t.itinerary
                    db2.commit()
                if c:
                    c.revised_itinerary = revised
                    db2.commit()
            finally:
                db2.close()

        asyncio.run(_run())

    threading.Thread(target=_run_change, daemon=True).start()

    db.refresh(trip)
    return trip


@router.delete("/{trip_id}")
def delete_trip(trip_id: str, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    db.delete(trip)
    db.commit()
    return {"deleted": True}

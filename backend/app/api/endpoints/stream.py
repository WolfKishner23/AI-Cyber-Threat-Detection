import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.core.broadcaster import broadcaster

router = APIRouter()

async def event_generator(request: Request):
    queue = await broadcaster.subscribe()
    
    try:
        while True:
            # Wait for a message or timeout to send a ping
            try:
                # 20 second timeout for heartbeat
                message = await asyncio.wait_for(queue.get(), timeout=20.0)
                yield message
            except asyncio.TimeoutError:
                # Send heartbeat
                yield "event: ping\ndata: {}\n\n"
            
            # If the client disconnected, request.is_disconnected() will be true
            if await request.is_disconnected():
                break
    finally:
        broadcaster.unsubscribe(queue)

@router.get("/")
async def stream(request: Request):
    """
    Server-Sent Events endpoint.
    Sends real-time updates for new events, alerts, and investigations.
    """
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }
    return StreamingResponse(event_generator(request), media_type="text/event-stream", headers=headers)

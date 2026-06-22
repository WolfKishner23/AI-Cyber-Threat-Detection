import asyncio
import json
from typing import Set, Any, Dict
import logging

logger = logging.getLogger(__name__)

class EventBroadcaster:
    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        logger.info(f"New SSE subscriber connected. Total: {len(self.subscribers)}")
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            logger.info(f"SSE subscriber disconnected. Total: {len(self.subscribers)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients."""
        payload = {
            "type": event_type,
            "data": data
        }
        json_data = json.dumps(payload)
        # SSE format: event: <type>\ndata: <json>\n\n
        message = f"event: {event_type}\ndata: {json_data}\n\n"
        
        for queue in list(self.subscribers):
            try:
                # Use put_nowait so we don't block the broadcasting loop
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("Subscriber queue full, dropping message.")

broadcaster = EventBroadcaster()

import asyncio
import json
import logging
from typing import Callable, Dict, List, Any
import redis.asyncio as aioredis
from backend.app.core.config import settings

logger = logging.getLogger("EventBus")

class EventBus:
    """
    Event-driven bus supporting Redis pub/sub with an automatic in-memory 
    asyncio fallback so the application runs seamlessly offline and in testing.
    """
    def __init__(self):
        self._redis_client = None
        self._is_redis_connected = False
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}
        self._history: List[Dict[str, Any]] = []

    async def connect(self):
        try:
            self._redis_client = aioredis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1.0
            )
            await self._redis_client.ping()
            self._is_redis_connected = True
            logger.info("Successfully connected to Redis Event Bus.")
        except Exception as e:
            self._is_redis_connected = False
            logger.warning(f"Redis not available ({e}). Running in decoupled async in-memory mode.")

    async def disconnect(self):
        if self._redis_client and self._is_redis_connected:
            await self._redis_client.close()

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], Any]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler to event '{event_type}'")

    async def publish(self, event_type: str, data: Dict[str, Any]):
        event_payload = {
            "event_type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        self._history.append(event_payload)
        logger.info(f"Publishing event '{event_type}'")

        if self._is_redis_connected and self._redis_client:
            try:
                await self._redis_client.publish(event_type, json.dumps(event_payload))
            except Exception as e:
                logger.error(f"Redis publish error: {e}")

        # Local dispatch to registered async subscribers
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(data))
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Error handling event '{event_type}' in {handler}: {e}")

    def get_history(self) -> List[Dict[str, Any]]:
        return self._history[-50:]

    @property
    def is_connected(self) -> bool:
        return self._is_redis_connected

event_bus = EventBus()

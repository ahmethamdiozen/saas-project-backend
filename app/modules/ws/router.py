import json
import asyncio
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from app.core.config import settings
from app.core.security import decode_token
from app.core.ws_manager import manager
from app.core.logging import logger

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.cookies.get("access_token")

    if not token:
        await websocket.close(code=4001)
        return

    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket, user_id)
    logger.info(f"WebSocket connected: user={user_id}")

    redis_conn = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_conn.pubsub()
    await pubsub.subscribe(f"user:{user_id}:events")

    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await manager.send_to_user(user_id, data)
                    except Exception as e:
                        logger.error(f"WS forward error: {e}")
        except asyncio.CancelledError:
            pass

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: user={user_id} error={e}")
    finally:
        listener_task.cancel()
        await pubsub.unsubscribe(f"user:{user_id}:events")
        await redis_conn.aclose()
        manager.disconnect(websocket, user_id)

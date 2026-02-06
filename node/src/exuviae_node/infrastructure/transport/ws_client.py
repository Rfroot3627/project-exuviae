from __future__ import annotations
import asyncio
import logging
import websockets
import json

logger = logging.getLogger(__name__)

async def connect_and_loop(ws_url: str, node_id: str):
    """
    Minimal WS connection loop.
    Supports basic connection and stays alive.
    """
    uri = f"{ws_url}?node_id={node_id}"
    logger.info(f"Connecting to Hub WS: {uri}")
    
    async for websocket in websockets.connect(uri):
        try:
            logger.info("Connected to Hub WS.")
            while True:
                # v0.1: just wait for messages or send heartbeats if needed.
                # For now, let's just listen.
                message = await websocket.recv()
                logger.debug(f"Received message: {message}")
                
        except websockets.ConnectionClosed:
            logger.warning("WS connection closed, retrying...")
            continue
        except Exception as e:
            logger.error(f"WS error: {e}")
            break

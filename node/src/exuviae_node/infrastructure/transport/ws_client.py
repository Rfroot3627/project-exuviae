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
    
    # Initialize Dependencies
    # In a full DI container, this would be injected. For MVP, we compose here.
    # We need http_base from config, but func sig only has ws_url/node_id.
    # We can infer http_base from ws_url for MVP or pass it in. 
    # Let's simple infer: ws://host:port/ws... -> http://host:port
    
    # Simple heuristic to derive HTTP base for upload
    if "ws://" in ws_url:
        http_base = ws_url.replace("ws://", "http://").split("/ws")[0]
    elif "wss://" in ws_url:
        http_base = ws_url.replace("wss://", "https://").split("/ws")[0]
    else:
        logger.error("Cannot derive HTTP base from WS URL. Uploads will fail.")
        http_base = "http://localhost:8000" # fallback

    from exuviae_node.infrastructure.camera.pi_camera import LibcameraAdapter
    from exuviae_node.application.handlers.handle_capture_snapshot import CaptureSnapshotHandler

    camera = LibcameraAdapter()
    capture_handler = CaptureSnapshotHandler(camera, http_base, node_id)
    
    async for websocket in websockets.connect(uri):
        try:
            logger.info("Connected to Hub WS.")
            while True:
                message = await websocket.recv()
                try:
                    data = json.loads(message)
                    if data.get("type") == "command.capture_snapshot":
                        # Offload to handler (synchronous for now, but fast enough for MVP)
                        # In production, maybe run in executor if capture blocks loop too long.
                        capture_handler.handle(data)
                    else:
                        logger.debug(f"Received non-capture message: {data.get('type')}")
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON")
                except Exception as e:
                    logger.error(f"Handler error: {e}")
                
        except websockets.ConnectionClosed:
            logger.warning("WS connection closed, retrying...")
            await asyncio.sleep(2) # Backoff
            continue
        except Exception as e:
            logger.error(f"WS error: {e}")
            await asyncio.sleep(5) # Backoff
            continue

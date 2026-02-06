from __future__ import annotations
import asyncio
import logging
import requests
import sys
from .infrastructure.config.loader import load_config
from .infrastructure.transport.ws_client import connect_and_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("exuviae_node")

def register_node(config):
    """
    Perform HTTP registration with Hub.
    Minimal payload as per contracts/capabilities/node_register.schema.json
    """
    url = f"{config.hub.http_base}/api/v0/nodes/register"
    # Minimal stub payload following the contract
    payload = {
        "node_id": config.node_id,
        "kind": "node-runtime",
        "firmware": "0.1.0",
        "capabilities": {
            "video_in": {
                "modes": ["snapshot"],
                "formats": [config.features.camera.format],
                "resolutions": [config.features.camera.resolution],
                "fps_max": 1
            }
        }
    }
    
    logger.info(f"Registering node at {url}...")
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info(f"Registration successful: {resp.json()}")
        return True
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return False

async def main():
    try:
        # 1. Load config
        config = load_config()
        logger.info(f"Config loaded for node: {config.node_id}")
        
        # 2. Register
        if not register_node(config):
            logger.error("Failed to register with hub. Exiting.")
            sys.exit(1)
            
        # 3. WS connect and loop
        await connect_and_loop(config.hub.ws_url, config.node_id)
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

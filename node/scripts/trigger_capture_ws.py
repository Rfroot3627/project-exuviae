import json
import asyncio
import websockets
import os
import sys
from pathlib import Path

# --- SSOT Example Path ---
EXAMPLE_PATH = Path(__file__).parent.parent.parent / "hub" / "contracts" / "ws" / "examples" / "ws.command.capture_snapshot.json"

async def trigger():
    ws_url = os.getenv("HUB_WS_URL", "ws://127.0.0.1:8000/ws/v0?node_id=trigger-tool")
    
    if not EXAMPLE_PATH.exists():
        print(f"Error: Contract example not found at {EXAMPLE_PATH}")
        sys.exit(1)
        
    with open(EXAMPLE_PATH, "r") as f:
        payload = json.load(f)
        
    # Inject a fresh timestamp based ID for uniqueness if desired, 
    # but for smoke we can just use the example.
    print(f"Sending command to {ws_url}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps(payload))
            print("Sent successfully.")
    except Exception as e:
        print(f"Failed to send: {e}")

if __name__ == "__main__":
    asyncio.run(trigger())

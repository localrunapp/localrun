import asyncio
import websockets
import sys

async def test():
    uri = "ws://localhost:8000/ws/system/stats"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Successfully connected to {uri}")
            await websocket.close()
            sys.exit(0)
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test())

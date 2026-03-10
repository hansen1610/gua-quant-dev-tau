import asyncio
import websockets

async def test_ws():
    uri = "ws://localhost/ws/dashboard"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for messages...")
            for i in range(3):
                message = await websocket.recv()
                print(f"Received: {message}")
    except Exception as e:
        print(f"Error connecting: {e}")

asyncio.run(test_ws())

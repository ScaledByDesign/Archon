#!/usr/bin/env python3
"""
Simple WebSocket test client for the voice chat service.
Tests basic connectivity and message exchange.
"""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    """Test basic WebSocket connectivity and message exchange."""
    uri = "ws://localhost:8000/ws"
    
    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Send a test message
            test_message = {
                "type": "test",
                "message": "Hello from test client"
            }
            
            print(f"📤 Sending test message: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for a response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Received response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response received within 5 seconds (this is normal for this service)")
            
            # Send a clear history message
            clear_message = {
                "type": "clear_history"
            }
            
            print(f"📤 Sending clear history: {clear_message}")
            await websocket.send(json.dumps(clear_message))
            
            # Wait a bit more for any responses
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"📥 Received response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No additional responses")
            
            print("✅ WebSocket test completed successfully!")
            
    except ConnectionRefusedError:
        print("❌ Connection refused - is the server running on localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Error during WebSocket test: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing WebSocket connection to voice chat service...")
    success = asyncio.run(test_websocket())
    sys.exit(0 if success else 1)

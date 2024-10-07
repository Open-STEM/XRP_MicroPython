import asyncio
import websockets
import threading
import queue
import time

class WebsocketManager:
    def __init__(self, host='localhost', port=6780):
        self.host = host
        self.port = port
        self.data_queue = queue.Queue()
        self.loop = asyncio.new_event_loop()
        self.ws_thread = threading.Thread(target=self.start_websocket_server)
        self.ws_thread.start()

    def send_data(self, data: str):
        """Non-blocking function to send data to the WebSocket client."""
        #print(f"Sending data to WebSocket: {data}")
        self.data_queue.put(data)

    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections and send data from the queue."""
        print("Client connected")
        try:
            while True:
                try:
                    data_to_send = self.data_queue.get_nowait()
                    await websocket.send(data_to_send)
                    #print(f"Sent to browser: {data_to_send}")
                except queue.Empty:
                    pass
                await asyncio.sleep(0.1)  # Prevent busy-waiting
        except websockets.ConnectionClosed:
            print("Client disconnected")

    async def websocket_server(self):
        """Start the WebSocket server."""
        async with websockets.serve(self.websocket_handler, self.host, self.port):
            await asyncio.Future()  # Run forever

    def start_websocket_server(self):
        """Start WebSocket server in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.websocket_server())

# Usage example
if __name__ == "__main__":
    ws_manager = WebsocketManager()

    # Allow some time for WebSocket server to start
    time.sleep(1)

    # Example of sending data to the WebSocket from the main thread
    ws_manager.send_data("Hello from the main thread!")
    time.sleep(2)
    ws_manager.send_data("Another message from main thread!")

    # Keep the main program running for demonstration purposes
    while True:
        time.sleep(1)
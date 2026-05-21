from fastapi import WebSocket


class TrackingManager:
    def __init__(self):
        # Senders watching a delivery
        # { order_id: [websocket1, websocket2] }
        self.active_connections: dict[str, list[WebSocket]] = {}

        # Latest GPS per order — so if sender connects mid-delivery
        # they immediately get current position instead of waiting
        # { order_id: {lat, lng, ...} }
        self.latest_positions: dict[str, dict] = {}

    async def connect(self, order_id: str, websocket: WebSocket):
        await websocket.accept()

        if order_id not in self.active_connections:
            self.active_connections[order_id] = []
        self.active_connections[order_id].append(websocket)

        # Send current position immediately if driver already started
        if order_id in self.latest_positions:
            await websocket.send_json(self.latest_positions[order_id])

    def disconnect(self, order_id: str, websocket: WebSocket):
        if order_id in self.active_connections:
            self.active_connections[order_id].remove(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]

    async def broadcast(self, order_id: str, location: dict):
        # Store latest
        self.latest_positions[order_id] = location

        # Push to all senders watching this order
        dead = []
        for ws in self.active_connections.get(order_id, []):
            try:
                await ws.send_json(location)
            except Exception:
                dead.append(ws)

        # Clean up broken connections
        for ws in dead:
            self.active_connections[order_id].remove(ws)

    def clear(self, order_id: str):
        self.latest_positions.pop(order_id, None)
        self.active_connections.pop(order_id, None)


tracking_manager = TrackingManager()
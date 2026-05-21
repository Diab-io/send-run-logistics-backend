# api/tracking.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.models.user import User
from app.schemas.tracking import GPSUpdate
from app.services.tracking_service import update_driver_location, get_live_location, clear_tracking
from app.api.deps import require_verified_driver
from app.core.users import current_active_user
from app.core.ws_manager import tracking_manager

router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.post("/update")
async def push_gps(
    data: GPSUpdate,
    user: User = Depends(require_verified_driver()),
):
    return await update_driver_location(data, str(user.id))


@router.get("/live/{order_id}")
async def get_tracking(order_id: str, user: User = Depends(current_active_user)):
    return await get_live_location(order_id)


@router.delete("/live/{order_id}")
async def stop_tracking(order_id: str, user: User = Depends(require_verified_driver())):
    return await clear_tracking(order_id)


# --- ADD THIS ---
@router.websocket("/ws/{order_id}")
async def tracking_websocket(websocket: WebSocket, order_id: str):
    """
    Sender connects here to receive live driver location.
    No auth on WebSocket — waybill number is the access control.
    Anyone with the order_id can watch the delivery.
    """
    await tracking_manager.connect(order_id, websocket)
    try:
        while True:
            # We don't expect messages from sender
            # but we must keep listening to detect disconnection
            await websocket.receive_text()
    except WebSocketDisconnect:
        tracking_manager.disconnect(order_id, websocket)
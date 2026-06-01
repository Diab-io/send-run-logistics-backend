# api/tracking.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.schemas.tracking import GPSUpdate
from app.services.tracking_service import update_driver_location, get_live_location, clear_tracking
from app.api.deps import require_verified_driver
from app.core.users import current_active_user
from app.core.ws_manager import tracking_manager
from app.database import get_db

router = APIRouter(prefix="/tracking", tags=["tracking"])

CHAT_ALLOWED_STATUSES = {
    OrderStatus.ACCEPTED,
    OrderStatus.PICKED_UP,
    OrderStatus.IN_TRANSIT,
}


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


@router.websocket("/chat/{order_id}")
async def chat_websocket(
    websocket: WebSocket,
    order_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Sender and driver connect here to chat during active delivery.
    
    Auth via query param: /tracking/chat/{order_id}?token=JWT_TOKEN
    
    Message format sent by client:
    {"text": "I am at the park now"}
    
    Message format received by client:
    {"type": "message", "user_id": "...", "first_name": "...", 
     "role": "sender|driver", "text": "...", "timestamp": "..."}
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=401, reason="Missing token")
        return

    # Validate token and get user
    try:
        from app.core.users import get_jwt_strategy
        strategy = get_jwt_strategy()
        user = await strategy.read_token(token, None)
        if not user:
            await websocket.close(code=401, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=401, reason="Invalid token")
        return

    # Check order exists
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        await websocket.close(code=404, reason="Order not found")
        return

    # Check order is active
    if order.status not in CHAT_ALLOWED_STATUSES:
        await websocket.close(
            code=403,
            reason="Chat is only available during active delivery"
        )
        return

    # Check user is the sender or assigned driver
    from app.models.user import UserRole
    import uuid
    user_uuid = uuid.UUID(str(user.id))
    is_sender = order.sender_id == user_uuid
    is_driver = order.driver_id == user_uuid

    if not is_sender and not is_driver and user.role != UserRole.ADMIN:
        await websocket.close(code=403, reason="Not authorised for this order")
        return

    # Connect to chat
    await tracking_manager.chat_connect(
        order_id=str(order_id),
        websocket=websocket,
        user_id=str(user.id),
        role=user.role.value,
    )

    try:
        while True:
            # Wait for message from this client
            data = await websocket.receive_json()
            text = data.get("text", "").strip()

            if not text:
                continue

            if len(text) > 500:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message too long. Max 500 characters."
                })
                continue

            # Check order is still active before sending
            await db.refresh(order)
            if order.status not in CHAT_ALLOWED_STATUSES:
                await tracking_manager.close_chat(str(order_id))
                break

            # Broadcast message to all chat participants
            await tracking_manager.send_message(
                order_id=str(order_id),
                user_id=str(user.id),
                first_name=user.first_name,
                role=user.role.value,
                text=text,
            )

    except WebSocketDisconnect:
        tracking_manager.chat_disconnect(str(order_id), websocket)
    except Exception:
        tracking_manager.chat_disconnect(str(order_id), websocket)

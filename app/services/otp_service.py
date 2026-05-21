from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.otp import generate_otp, store_otp, verify_otp
from app.core.email import send_otp_email, send_driver_welcome_email


async def request_otp(email: str, db: AsyncSession) -> dict:
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != UserRole.DRIVER:
        raise HTTPException(status_code=400, detail="OTP verification is only for driver accounts")
    if user.otp_verified:
        raise HTTPException(status_code=400, detail="Account already verified")

    otp = generate_otp()
    await store_otp(email, otp)
    await send_otp_email(email, otp, user.first_name)

    return {"message": "OTP sent to your email"}


async def verify_driver_otp(email: str, otp: str, db: AsyncSession) -> dict:
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.otp_verified:
        raise HTTPException(status_code=400, detail="Account already verified")

    is_valid = await verify_otp(email, otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    await db.execute(
        update(User).where(User.id == user.id).values(otp_verified=True)
    )
    await db.commit()

    await send_driver_welcome_email(email, user.first_name)

    return {"message": "Driver account verified successfully"}
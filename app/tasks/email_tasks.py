from app.core.celery_app import celery_app
from app.core.email import fast_mail
from fastapi_mail import MessageSchema, MessageType
import asyncio


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="send_otp_email",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def send_otp_email_task(self, email: str, otp: str, first_name: str):
    try:
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1a73e8;">Ondo Logistics — Driver Verification</h2>
            <p>Hello {first_name},</p>
            <p>Your one-time verification code is:</p>
            <div style="background: #f0f4f8; padding: 20px; text-align: center;
                        border-radius: 8px; margin: 20px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px;
                             color: #1a73e8;">{otp}</span>
            </div>
            <p>This code expires in <strong>10 minutes</strong>.</p>
            <p>If you did not request this, ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">Ondo State Intelligent Logistics Platform</p>
        </div>
        """
        message = MessageSchema(
            subject="Your Verification Code — Ondo Logistics",
            recipients=[email],
            body=html,
            subtype=MessageType.html,
        )
        _run_async(fast_mail.send_message(message))

    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="send_order_notification_email",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def send_order_notification_task(
    self,
    email: str,
    first_name: str,
    waybill_number: str,
    status: str,
    origin: str,
    destination: str,
):
    try:
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1a73e8;">Order Update</h2>
            <p>Hello {first_name},</p>
            <p>Your order <strong>{waybill_number}</strong> has been updated:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr><td style="padding: 8px; color: #666;">Route</td>
                    <td style="padding: 8px; font-weight: bold;">{origin} → {destination}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Status</td>
                    <td style="padding: 8px; font-weight: bold; color: #1a73e8;">
                        {status.replace('_', ' ').title()}</td></tr>
            </table>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">Ondo State Intelligent Logistics Platform</p>
        </div>
        """
        message = MessageSchema(
            subject=f"Order {waybill_number} — {status.replace('_', ' ').title()}",
            recipients=[email],
            body=html,
            subtype=MessageType.html,
        )
        _run_async(fast_mail.send_message(message))

    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="send_driver_welcome_email",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def send_driver_welcome_task(self, email: str, first_name: str):
    try:
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1a73e8;">Welcome, {first_name}!</h2>
            <p>Your driver account has been verified successfully.</p>
            <p>You can now:</p>
            <ul>
                <li>View and accept delivery orders</li>
                <li>Enable GPS tracking for real-time delivery updates</li>
                <li>Manage your delivery history</li>
            </ul>
            <p>Open the driver dashboard in your browser to get started.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">Ondo State Intelligent Logistics Platform</p>
        </div>
        """
        message = MessageSchema(
            subject="Welcome to Ondo Logistics — Driver Verified",
            recipients=[email],
            body=html,
            subtype=MessageType.html,
        )
        _run_async(fast_mail.send_message(message))

    except Exception as exc:
        raise self.retry(exc=exc)
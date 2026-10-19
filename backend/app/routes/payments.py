"""Public website checkout endpoints for Razorpay one-time plan payments.

Secrets are read only from backend environment variables. The browser never
receives the Razorpay secret; payment signatures are verified server-side.
"""
import hashlib
import hmac
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request as URLRequest, urlopen

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import PaymentOrder

router = APIRouter(prefix="/api/payments", tags=["Website Payments"])

PLANS = {
    "orbit": {"name": "Orbit", "amount": 69 * 100},
    "nova": {"name": "Nova", "amount": 199 * 100},
    "galaxy": {"name": "Galaxy", "amount": 399 * 100},
}


class CreateOrderRequest(BaseModel):
    plan: str = Field(min_length=1, max_length=40)
    customer_name: str = Field(min_length=1, max_length=150)
    customer_email: EmailStr
    customer_phone: str | None = Field(default=None, max_length=30)


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str = Field(min_length=5, max_length=80)
    razorpay_payment_id: str = Field(min_length=5, max_length=80)
    razorpay_signature: str = Field(min_length=20, max_length=256)


def _razorpay_credentials() -> tuple[str, str]:
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    if not key_id or not key_secret:
        raise HTTPException(
            status_code=503,
            detail="Payments are not configured yet. Please contact Financial OS support.",
        )
    return key_id, key_secret


@router.post("/create-order")
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    plan_key = payload.plan.strip().lower()
    plan = PLANS.get(plan_key)
    if not plan:
        raise HTTPException(status_code=422, detail="Please select a valid subscription plan.")

    key_id, key_secret = _razorpay_credentials()
    order_payload = {
        "amount": plan["amount"],
        "currency": "INR",
        "receipt": "fos-" + os.urandom(12).hex(),
        "notes": {
            "plan": plan_key,
            "customer_name": payload.customer_name.strip(),
            "customer_email": str(payload.customer_email).strip().lower(),
        },
    }
    request = URLRequest(
        "https://api.razorpay.com/v1/orders",
        data=json.dumps(order_payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Basic " + __import__("base64").b64encode(
                f"{key_id}:{key_secret}".encode("utf-8")
            ).decode("ascii"),
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            order = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Do not expose provider response bodies or credentials to the browser.
        raise HTTPException(status_code=502, detail="Razorpay could not create the payment order. Please retry or contact support.") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not connect to Razorpay. Please retry.") from exc

    order_id = str(order.get("id", ""))
    if not order_id or int(order.get("amount", 0)) != plan["amount"] or order.get("currency") != "INR":
        raise HTTPException(status_code=502, detail="Razorpay returned an invalid order. Please contact support.")

    record = PaymentOrder(
        razorpay_order_id=order_id,
        plan=plan_key,
        amount_paise=plan["amount"],
        currency="INR",
        customer_name=payload.customer_name.strip(),
        customer_email=str(payload.customer_email).strip().lower(),
        customer_phone=(payload.customer_phone or "").strip() or None,
        status="created",
    )
    db.add(record)
    db.commit()
    return {
        "key_id": key_id,
        "order_id": order_id,
        "amount": plan["amount"],
        "currency": "INR",
        "plan": plan_key,
    }


@router.post("/verify")
def verify_payment(payload: VerifyPaymentRequest, db: Session = Depends(get_db)):
    _, key_secret = _razorpay_credentials()
    record = db.query(PaymentOrder).filter(
        PaymentOrder.razorpay_order_id == payload.razorpay_order_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Payment order was not found.")

    expected = hmac.new(
        key_secret.encode("utf-8"),
        f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment signature verification failed.")

    if record.status == "paid":
        if record.razorpay_payment_id != payload.razorpay_payment_id:
            raise HTTPException(status_code=409, detail="This order is already linked to a different payment.")
        return {"verified": True, "status": "paid", "plan": record.plan}

    record.razorpay_payment_id = payload.razorpay_payment_id
    record.status = "paid"
    db.commit()
    return {
        "verified": True,
        "status": "paid",
        "plan": record.plan,
        "payment_id": record.razorpay_payment_id,
        "message": "Payment signature verified. Subscription activation may require support confirmation.",
    }



@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Verify Razorpay webhook signatures and safely process payment/refund events."""
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Razorpay webhook secret is not configured.")

    signature = request.headers.get("X-Razorpay-Signature", "").strip()
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay webhook signature.")

    raw_body = await request.body()
    expected = hmac.new(
        webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid Razorpay webhook signature.")

    try:
        event = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload.") from exc

    event_name = event.get("event")
    payload = event.get("payload") or {}

    if event_name in ("payment.captured", "payment.failed"):
        payment = ((payload.get("payment") or {}).get("entity") or {})
        order_id = payment.get("order_id")
        if order_id:
            record = db.query(PaymentOrder).filter(
                PaymentOrder.razorpay_order_id == order_id
            ).first()
            if record:
                if event_name == "payment.captured":
                    # Do not downgrade a paid/refunded order on delayed events.
                    if record.status not in ("paid", "refunded"):
                        record.razorpay_payment_id = payment.get("id") or record.razorpay_payment_id
                        record.status = "paid"
                elif record.status == "created":
                    record.status = "failed"
                db.commit()

    elif event_name == "refund.processed":
        refund = ((payload.get("refund") or {}).get("entity") or {})
        payment_id = refund.get("payment_id")
        if payment_id:
            record = db.query(PaymentOrder).filter(
                PaymentOrder.razorpay_payment_id == payment_id
            ).first()
            if record and record.status != "refunded":
                record.status = "refunded"
                db.commit()

    # Acknowledge valid events, including events not used by this application.
    return {"received": True, "event": event_name}

from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import User
from app.schemas.subscription import SubscriptionStatus
from app.services.payment_service import PaymentService
from app.api.dependencies import get_current_user
from app.core.config import settings
import stripe

router = APIRouter()

@router.post("/subscribe/pro", status_code=status.HTTP_200_OK)
async def initiate_pro_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    payment_service = PaymentService(db)
    checkout_url = await payment_service.create_stripe_checkout_session(current_user)
    return {"checkout_url": checkout_url}

@router.post("/webhook/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    payment_service = PaymentService(db)
    await payment_service.handle_stripe_webhook_event(event)

    return {"status": "success"}

@router.get("/subscription/status", response_model=SubscriptionStatus, status_code=status.HTTP_200_OK)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    payment_service = PaymentService(db)
    subscription = await payment_service.get_user_subscription_status(current_user.id)

    if not subscription:
        return SubscriptionStatus(tier=current_user.role, status="no_subscription")
    
    return SubscriptionStatus(
        tier=subscription.tier,
        status=subscription.status,
        current_period_end=subscription.current_period_end
    )
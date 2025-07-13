import stripe
from app.core.config import settings
from app.db.models import User, Subscription, UserRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.exceptions import PaymentProcessingError
from datetime import datetime

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_stripe_checkout_session(self, user: User) -> str:
        try:
            
            user_subscription = await self._get_user_subscription(user.id)
            customer_id = user_subscription.stripe_customer_id if user_subscription else None

            if not customer_id:
                
                customer = stripe.Customer.create(
                    email=f"{user.mobile_number}@example.com", 
                    metadata={"user_id": user.id}
                )
                customer_id = customer.id
                if user_subscription:
                    user_subscription.stripe_customer_id = customer_id
                else:
                    
                    user_subscription = Subscription(user_id=user.id, stripe_customer_id=customer_id)
                    self.db.add(user_subscription)
                await self.db.commit()
                await self.db.refresh(user_subscription)

            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                line_items=[
                    {
                        'price': settings.STRIPE_PRO_PRICE_ID,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url='https://your-frontend.com/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://your-frontend.com/cancel',
                metadata={
                    "user_id": str(user.id)
                }
            )
            return checkout_session.url
        except stripe.error.StripeError as e:
            raise PaymentProcessingError(detail=f"Stripe error: {e.user_message}")
        except Exception as e:
            raise PaymentProcessingError(detail=f"An unexpected error occurred: {e}")

    async def handle_stripe_webhook_event(self, event: stripe.Event):
        event_type = event['type']
        data = event['data']['object']

        if event_type == 'checkout.session.completed':
            customer_id = data['customer']
            subscription_id = data.get('subscription')
            user_id = data['metadata'].get('user_id')

            if user_id and subscription_id:
                user_id = int(user_id)
                user_subscription = await self._get_user_subscription(user_id)
                if user_subscription:
                    user_subscription.stripe_customer_id = customer_id
                    user_subscription.stripe_subscription_id = subscription_id
                    user_subscription.tier = UserRole.PRO.value
                    user_subscription.status = "active"
                    
                    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                    user_subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                    await self.db.commit()
                    print(f"User {user_id} subscribed to Pro tier.")
                else:
                    
                    new_subscription = Subscription(
                        user_id=user_id,
                        stripe_customer_id=customer_id,
                        stripe_subscription_id=subscription_id,
                        tier=UserRole.PRO.value,
                        status="active"
                    )
                    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                    new_subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                    self.db.add(new_subscription)
                    await self.db.commit()
                    print(f"New subscription created for user {user_id} to Pro tier.")

        elif event_type == 'invoice.payment_succeeded':
            
            subscription_id = data.get('subscription')
            if subscription_id:
                user_subscription = await self._get_user_subscription_by_stripe_sub_id(subscription_id)
                if user_subscription:
                    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                    user_subscription.status = "active"
                    user_subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                    await self.db.commit()
                    print(f"Subscription {subscription_id} payment succeeded.")

        elif event_type == 'invoice.payment_failed' or event_type == 'customer.subscription.deleted':
            
            subscription_id = data.get('subscription') if 'subscription' in data else data.get('id')
            if subscription_id:
                user_subscription = await self._get_user_subscription_by_stripe_sub_id(subscription_id)
                if user_subscription:
                    user_subscription.status = "inactive" 
                    user_subscription.tier = UserRole.BASIC.value 
                    await self.db.commit()
                    print(f"Subscription {subscription_id} payment failed or cancelled. User {user_subscription.user_id} downgraded to Basic.")
        

    async def get_user_subscription_status(self, user_id: int) -> Subscription  :
        return await self._get_user_subscription(user_id)

    async def _get_user_subscription(self, user_id: int) -> Subscription  :
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _get_user_subscription_by_stripe_sub_id(self, stripe_subscription_id: str) -> Subscription  :
        stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
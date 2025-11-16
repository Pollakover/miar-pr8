import os
import asyncio
from uuid import UUID, uuid4
from datetime import datetime
from app.models.payment import Payment, PaymentStatus
from app.repositories.db_payment_repo import PaymentRepo
from app.clients.rabbitmq_client import RabbitMQClient
from pydantic import BaseModel

class CreatePaymentRequest(BaseModel):
    amount: float
    currency: str | None = "USD"

class PaymentService:
    def __init__(self):
        self.repo = PaymentRepo()
        self.rabbitmq_client = RabbitMQClient()

    def list_payments(self):
        return self.repo.get_payments()

    def create_payment(self, amount: float, currency: str = "USD"):
        payment = Payment(
            id=uuid4(),
            amount=amount,
            currency=currency,
            status=PaymentStatus.CREATED,
            created_at=datetime.utcnow()
        )
        return self.repo.create_payment(payment)

    async def process_payment(self, id: UUID, success: bool):
        payment = self.repo.get_payment_by_id(id)
        if payment.status != PaymentStatus.CREATED:
            raise ValueError("Payment already processed or not in CREATED state")

        payment.status = PaymentStatus.SUCCESS if success else PaymentStatus.FAILED
        updated_payment = self.repo.update_status(payment)

        # Отправляем уведомление в RabbitMQ только при успешном платеже
        if success and updated_payment.status == PaymentStatus.SUCCESS:
            # Запускаем отправку уведомления в фоне, не дожидаясь ответа
            await asyncio.create_task(
                self.rabbitmq_client.send_payment_notification(updated_payment.id)
            )

        return updated_payment

    def request_refund(self, id: UUID):
        payment = self.repo.get_payment_by_id(id)
        if payment.status != PaymentStatus.SUCCESS:
            raise ValueError("Can only request refund for successful payments")
        payment.status = PaymentStatus.REFUND_REQUESTED
        return self.repo.update_status(payment)

    def complete_refund(self, id: UUID, success: bool):
        payment = self.repo.get_payment_by_id(id)
        if payment.status != PaymentStatus.REFUND_REQUESTED:
            raise ValueError("Refund must be requested first")
        payment.status = PaymentStatus.REFUND_DONE if success else PaymentStatus.REFUND_DENIED
        return self.repo.update_status(payment)
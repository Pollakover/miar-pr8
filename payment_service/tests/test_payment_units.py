import pytest
from uuid import uuid4
from datetime import datetime

def test_payment_status_enum():
    from app.models.payment import PaymentStatus

    assert PaymentStatus.CREATED == "created"
    assert PaymentStatus.SUCCESS == "success"
    assert PaymentStatus.FAILED == "failed"
    assert PaymentStatus.REFUND_REQUESTED == "refund_requested"

def test_payment_model_creation():
    from app.models.payment import Payment, PaymentStatus

    payment_id = uuid4()
    payment = Payment(
        id=payment_id,
        amount=100.0,
        currency="USD"
    )

    assert payment.id == payment_id
    assert payment.amount == 100.0
    assert payment.currency == "USD"
    assert payment.status == PaymentStatus.CREATED
    assert isinstance(payment.created_at, datetime)

def test_payment_model_defaults():
    from app.models.payment import Payment

    payment = Payment(
        id=uuid4(),
        amount=50.0
    )

    assert payment.currency == "USD"
    assert payment.amount == 50.0
"""
Unit tests for Payment Service
"""
import pytest
from uuid import uuid4
from datetime import datetime

def test_payment_status_enum():
    """Test payment status values"""
    from app.models.payment import PaymentStatus

    assert PaymentStatus.CREATED == "created"
    assert PaymentStatus.SUCCESS == "success"
    assert PaymentStatus.FAILED == "failed"
    assert PaymentStatus.REFUND_REQUESTED == "refund_requested"

def test_payment_model_creation():
    """Test basic payment model creation"""
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

"""def test_payment_service_create():
    from app.services.payment_service import PaymentService

    service = PaymentService()
    payment = service.create_payment(amount=75.0, currency="EUR")

    assert payment.amount == 75.0
    assert payment.currency == "EUR"
    assert payment.status.value == "created"""

def test_payment_service_list():
    """Test payment service list method"""
    from app.services.payment_service import PaymentService

    service = PaymentService()

    # Should return list (may be empty)
    payments = service.list_payments()
    assert isinstance(payments, list)
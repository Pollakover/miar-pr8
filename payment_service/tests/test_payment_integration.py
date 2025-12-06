import pytest
import os
import sys
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.payment import Payment, PaymentStatus
from app.repositories.db_payment_repo import PaymentRepo
from app.database import Base, engine, SessionLocal


@pytest.fixture(scope='function')
def db_session():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope='function')
def payment_repo(db_session):
    return PaymentRepo()


@pytest.fixture(scope='function')
def sample_payment_data():
    return {
        "id": uuid4(),
        "amount": 100.0,
        "currency": "USD",
        "status": PaymentStatus.CREATED,
        "created_at": datetime.utcnow()
    }


@pytest.fixture(scope='function')
def sample_payment():
    return Payment(
        id=uuid4(),
        amount=150.0,
        currency="EUR",
        status=PaymentStatus.CREATED,
        created_at=datetime.utcnow()
    )


#Проверка инициализации репозитория
def test_payment_repo_initialization(payment_repo):
    assert payment_repo is not None
    assert hasattr(payment_repo, 'db')


# Проверяем, что платеж создался в базе данных
def test_create_payment(payment_repo, sample_payment):
    created_payment = payment_repo.create_payment(sample_payment)

    assert created_payment.id == sample_payment.id
    assert created_payment.amount == 150.0
    assert created_payment.currency == "EUR"
    assert created_payment.status == PaymentStatus.CREATED


# Получаем платеж по id
def test_get_payment_by_id(payment_repo, sample_payment):
    payment_repo.create_payment(sample_payment)

    retrieved_payment = payment_repo.get_payment_by_id(sample_payment.id)

    assert retrieved_payment.id == sample_payment.id
    assert retrieved_payment.amount == sample_payment.amount
    assert retrieved_payment.currency == sample_payment.currency
    assert retrieved_payment.status == sample_payment.status


# Пытаемся получить несуществующий платеж
def test_get_payment_by_id_not_found(payment_repo):
    non_existent_id = uuid4()

    with pytest.raises(KeyError):
        payment_repo.get_payment_by_id(non_existent_id)


# Проверка получения всех платежей
def test_get_all_payments(payment_repo):

    payments = payment_repo.get_payments()
    assert payments == []

    payment1 = Payment(
        id=uuid4(),
        amount=100.0,
        currency="USD",
        status=PaymentStatus.CREATED,
        created_at=datetime.utcnow()
    )

    payment2 = Payment(
        id=uuid4(),
        amount=200.0,
        currency="EUR",
        status=PaymentStatus.CREATED,
        created_at=datetime.utcnow()
    )

    payment_repo.create_payment(payment1)
    payment_repo.create_payment(payment2)

    payments = payment_repo.get_payments()

    assert len(payments) == 2
    assert any(p.id == payment1.id for p in payments)
    assert any(p.id == payment2.id for p in payments)


# Проверяем обновление статуса платежа
def test_update_payment_status(payment_repo, sample_payment):
    created_payment = payment_repo.create_payment(sample_payment)
    assert created_payment.status == PaymentStatus.CREATED

    created_payment.status = PaymentStatus.SUCCESS
    updated_payment = payment_repo.update_status(created_payment)

    assert updated_payment.status == PaymentStatus.SUCCESS
    assert updated_payment.id == sample_payment.id

    retrieved_payment = payment_repo.get_payment_by_id(sample_payment.id)
    assert retrieved_payment.status == PaymentStatus.SUCCESS


# Проверяем валюту по умолчанию (должна быть USD)
def test_payment_currency_default(payment_repo):
    payment = Payment(
        id=uuid4(),
        amount=300.0,
        status=PaymentStatus.CREATED,
        created_at=datetime.utcnow()
    )

    created_payment = payment_repo.create_payment(payment)
    assert created_payment.currency == "USD"


# Проверяем, что сохраняется временная метка при создании платежа
def test_payment_created_at_persistence(payment_repo):
    from datetime import datetime, timedelta

    specific_time = datetime(2024, 1, 1, 12, 0, 0)
    payment = Payment(
        id=uuid4(),
        amount=500.0,
        currency="USD",
        status=PaymentStatus.CREATED,
        created_at=specific_time
    )

    created_payment = payment_repo.create_payment(payment)

    # Проверяем, что время создания сохранилось
    retrieved_payment = payment_repo.get_payment_by_id(payment.id)
    assert retrieved_payment.created_at == specific_time

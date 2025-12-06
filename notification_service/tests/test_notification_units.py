import pytest
from uuid import uuid4
from datetime import datetime

def test_notification_type_enum():
    from app.models.notification import NotificationType

    assert NotificationType.ORDER_PLACED == "order_placed"
    assert NotificationType.BOOKING_CONFIRMED == "booking_confirmed"
    assert NotificationType.CLEANING_DONE == "cleaning_done"

def test_notification_status_enum():
    from app.models.notification import NotificationStatus

    assert NotificationStatus.SENT == "sent"
    assert NotificationStatus.FAILED == "failed"

def test_notification_model_creation():
    from app.models.notification import Notification, NotificationType, NotificationStatus

    notification_id = uuid4()
    notification = Notification(
        id=notification_id,
        type=NotificationType.ORDER_PLACED,
        message="Test notification message"
    )

    assert notification.id == notification_id
    assert notification.type == NotificationType.ORDER_PLACED
    assert notification.message == "Test notification message"
    assert notification.status == NotificationStatus.SENT
    assert notification.recipient is None
    assert isinstance(notification.created_at, datetime)

def test_notification_model_with_recipient():
    """Test notification model with recipient"""
    from app.models.notification import Notification, NotificationType

    notification = Notification(
        id=uuid4(),
        type=NotificationType.BOOKING_CONFIRMED,
        message="Booking confirmed",
        recipient="user@example.com"
    )

    assert notification.recipient == "user@example.com"
    assert notification.type == "booking_confirmed"

def test_notification_service_send():
    """Test notification service send method"""
    from app.services.notification_service import NotificationService
    from app.models.notification import NotificationType

    service = NotificationService()
    notification = service.send(
        n_type=NotificationType.ORDER_PLACED,
        message="Test message"
    )

    assert notification.type == NotificationType.ORDER_PLACED
    assert notification.message == "Test message"
    assert notification.status.value == "sent"

def test_notification_service_list():
    """Test notification service list method"""
    from app.services.notification_service import NotificationService

    service = NotificationService()

    notifications = service.list()
    assert isinstance(notifications, list)
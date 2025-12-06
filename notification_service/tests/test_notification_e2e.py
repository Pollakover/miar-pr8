"""
E2E tests for Notification Service API
"""
import pytest
import requests

BASE_URL = "http://localhost:8002/api/notifications"

def test_api_health():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200

def test_send_notification():
    notification_data = {
        "type": "order_placed",
        "message": "Test notification message",
        "recipient": "user@example.com"
    }

    response = requests.post(f"{BASE_URL}/", json=notification_data)

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["type"] == "order_placed"
    assert data["message"] == "Test notification message"
    assert data["recipient"] == "user@example.com"
    assert data["status"] == "sent"

    return data["id"]

def test_send_notification_no_recipient():
    notification_data = {
        "type": "cleaning_done",
        "message": "Cleaning completed"
    }

    response = requests.post(f"{BASE_URL}/", json=notification_data)

    assert response.status_code == 200
    data = response.json()
    assert data["recipient"] is None
    assert data["type"] == "cleaning_done"

def test_get_notifications():
    response = requests.get(f"{BASE_URL}/")

    assert response.status_code == 200
    notifications = response.json()
    assert isinstance(notifications, list)

def test_notification_not_found():
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = requests.get(f"{BASE_URL}/{fake_id}")

    assert response.status_code == 404
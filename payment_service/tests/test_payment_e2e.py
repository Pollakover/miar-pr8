"""
E2E tests for Payment Service API
"""
import pytest
import requests
import time

# Base URL for the payment service
BASE_URL = "http://localhost:8001/api/payments"

def test_api_health():
    """Test that API is responding"""
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200

def test_create_payment():
    """Test creating a payment via API"""
    payment_data = {
        "amount": 100.0,
        "currency": "USD"
    }

    response = requests.post(f"{BASE_URL}/", json=payment_data)

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["amount"] == 100.0
    assert data["currency"] == "USD"
    assert data["status"] == "created"

    return data["id"]

def test_get_payments():
    """Test retrieving payments list via API"""
    response = requests.get(f"{BASE_URL}/")

    assert response.status_code == 200
    payments = response.json()
    assert isinstance(payments, list)

def test_process_payment():
    payment_data = {"amount": 150.0}
    create_response = requests.post(f"{BASE_URL}/", json=payment_data)
    payment_id = create_response.json()["id"]

    process_data = {"success": True}
    process_response = requests.post(
        f"{BASE_URL}/{payment_id}/process",
        json=process_data
    )

    assert process_response.status_code == 200
    data = process_response.json()
    assert data["status"] in ["success", "failed"]

def test_payment_not_found():
    """Test error handling for non-existent payment"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = requests.get(f"{BASE_URL}/{fake_id}")

    # Should return 404 or 400
    assert response.status_code in [404, 400]
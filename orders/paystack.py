import requests
from django.conf import settings

# ----------------------------
# PAYSTACK CONFIGURATION
# ----------------------------
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
BASE_URL = "https://api.paystack.co"

def initialize_transaction(email, amount, metadata=None):
    """
    email    : customer email
    amount   : amount in pesewas (GHS * 100)
    metadata : a dictionary (e.g. {"order_id": 5})
    """
    url = f"{BASE_URL}/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": email,
        "amount": amount,
        "currency": "GHS", # Ensures GHS is used
    }

    if metadata:
        payload["metadata"] = metadata

    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        return {"status": False, "message": str(e)}

def verify_transaction(reference):
    url = f"{BASE_URL}/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        return {"status": False, "message": str(e)}
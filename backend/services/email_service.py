import os
import requests

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")  # ragchatbot1234@gmail.com


def send_otp_email(email: str, otp: str):
    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json",
            },
            json={
                "sender": {"name": "RAG Assistant", "email": SENDER_EMAIL},
                "to": [{"email": email}],
                "subject": "RAG Chatbot Verification",
                "textContent": f"Your OTP is: {otp}\nIt expires in 5 minutes.",
            },
            timeout=10,
        )
        response.raise_for_status()
        print("EMAIL SENT to", email, response.json())
    except Exception as e:
        print("EMAIL FAILED:", str(e))
        raise
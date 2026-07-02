import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

def send_otp_email(email: str, otp: str):
    try:
        resend.Emails.send({
            "from": "RAG Assistant <onboarding@resend.dev>",
            "to": email,
            "subject": "RAG Chatbot Verification",
            "text": f"Your OTP is: {otp}\nIt expires in 5 minutes.",
        })
    except Exception as e:
        print("EMAIL FAILED:", str(e))
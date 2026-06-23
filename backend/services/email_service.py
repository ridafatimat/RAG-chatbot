import os
import smtplib
from email.mime.text import MIMEText


def send_otp_email(email: str, otp: str):
    try:
        print("EMAIL DEBUG START")
        sender_email = os.getenv("EMAIL_ADDRESS")
        sender_password = os.getenv("EMAIL_PASSWORD")

        print("EMAIL DEBUG:", sender_email, sender_password)

        msg = MIMEText(f"Your OTP is: {otp}\nIt expires in 5 minutes.")
        msg["Subject"] = "RAG Chatbot Verification"
        msg["From"] = sender_email
        msg["To"] = email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print("EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        print("EMAIL FAILED:", str(e))
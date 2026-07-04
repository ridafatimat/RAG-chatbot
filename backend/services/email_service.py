import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_otp_email(email: str, otp: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = f"RAG Assistant <{GMAIL_ADDRESS}>"
        msg["To"] = email
        msg["Subject"] = "RAG Chatbot Verification"

        body = f"Your OTP is: {otp}\nIt expires in 5 minutes."
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, email, msg.as_string())

        print("EMAIL SENT to", email)
    except Exception as e:
        print("EMAIL FAILED:", str(e))
        raise
import random
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from services.mongo_service import (
    users_collection,
    email_verifications_collection
)

from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
)

from services.email_service import send_otp_email


router = APIRouter()


# -------------------------
# REQUEST MODELS
# -------------------------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendOTPRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


# -------------------------
# REGISTER (SEND OTP)
# -------------------------
@router.post("/register")
def register_user(user: RegisterRequest):
    email = user.email.lower().strip()

    if len(user.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long.",
        )

    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists. Please login.",
        )

    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    pending = email_verifications_collection.find_one({"email": email})

    if pending:
        email_verifications_collection.update_one(
            {"email": email},
            {"$set": {
                "otp": otp,
                "expires_at": expires_at
            }}
        )
    else:
        email_verifications_collection.insert_one({
            "name": user.name.strip(),
            "email": email,
            "password_hash": hash_password(user.password),
            "otp": otp,
            "expires_at": expires_at,
            "purpose": "register"
        })

    send_otp_email(email, otp)

    return {"message": "OTP sent successfully"}


# -------------------------
# RESEND OTP
# -------------------------
@router.post("/resend-otp")
def resend_otp(data: ResendOTPRequest):
    email = data.email.lower().strip()

    record = email_verifications_collection.find_one({"email": email})

    if not record:
        raise HTTPException(
            status_code=400,
            detail="No pending verification found."
        )

    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    email_verifications_collection.update_one(
        {"email": email},
        {"$set": {
            "otp": otp,
            "expires_at": expires_at
        }}
    )

    send_otp_email(email, otp)

    return {"message": "OTP resent successfully"}


# -------------------------
# VERIFY EMAIL (REGISTER COMPLETE)
# -------------------------
@router.post("/verify-email")
def verify_email(data: VerifyOTPRequest):

    record = email_verifications_collection.find_one({
        "email": data.email.lower().strip()
    })

    if not record:
        raise HTTPException(status_code=400, detail="No OTP found")

    expires_at = record["expires_at"]

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        email_verifications_collection.delete_one({"email": record["email"]})
        raise HTTPException(status_code=400, detail="OTP expired")

    if data.otp != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    result = users_collection.insert_one({
        "name": record["name"],
        "email": record["email"],
        "password_hash": record["password_hash"],
        "created_at": datetime.now(timezone.utc),
    })

    email_verifications_collection.delete_one({"email": record["email"]})

    access_token = create_access_token(
        data={
            "sub": str(result.inserted_id),
            "email": record["email"],
        }
    )

    return {
        "message": "Account verified successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "_id": str(result.inserted_id),
            "name": record["name"],
            "email": record["email"],
        },
    }


# -------------------------
# LOGIN
# -------------------------
@router.post("/login")
def login_user(user: LoginRequest):
    email = user.email.lower().strip()

    existing_user = users_collection.find_one({"email": email})

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not verify_password(user.password, existing_user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(
        data={
            "sub": str(existing_user["_id"]),
            "email": existing_user["email"],
        }
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "_id": str(existing_user["_id"]),
            "name": existing_user.get("name", ""),
            "email": existing_user["email"],
        },
    }


# -------------------------
# FORGOT PASSWORD (SEND OTP)
# -------------------------
@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):

    email = data.email.lower().strip()

    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    existing = email_verifications_collection.find_one({"email": email})

    if existing:
        email_verifications_collection.update_one(
            {"email": email},
            {"$set": {
                "otp": otp,
                "expires_at": expires_at,
                "purpose": "reset_password"
            }}
        )
    else:
        email_verifications_collection.insert_one({
            "email": email,
            "otp": otp,
            "expires_at": expires_at,
            "purpose": "reset_password"
        })

    send_otp_email(email, otp)

    return {
        "message": "Verification code sent to your email"
    }


# -------------------------
# RESET PASSWORD (VERIFY OTP + UPDATE PASSWORD)
# -------------------------
@router.post("/verify-reset-password")
def verify_reset_password(data: VerifyResetOTPRequest):

    record = email_verifications_collection.find_one({
        "email": data.email.lower().strip(),
        "purpose": "reset_password"
    })

    if not record:
        raise HTTPException(status_code=400, detail="No OTP found")

    expires_at = record["expires_at"]

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        email_verifications_collection.delete_one({"email": record["email"]})
        raise HTTPException(status_code=400, detail="OTP expired")

    if data.otp != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    hashed_password = hash_password(data.new_password)

    users_collection.update_one(
        {"email": record["email"]},
        {"$set": {"password_hash": hashed_password}}
    )

    email_verifications_collection.delete_one({"email": record["email"]})

    return {
        "message": "Password reset successful"
    }
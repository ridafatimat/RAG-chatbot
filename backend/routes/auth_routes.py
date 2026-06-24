import os
import random
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel, EmailStr

from services.mongo_service import (
    users_collection,
    email_verifications_collection,
)
from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
)
from services.rate_limiter import limiter
from services.email_service import send_otp_email


router = APIRouter()

ENV = os.getenv("ENV", "development")
IS_PRODUCTION = ENV == "production"

ACCESS_TOKEN_COOKIE_NAME = "access_token"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


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
# COOKIE HELPER
# -------------------------
def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


# -------------------------
# REGISTER (SEND OTP)
# -------------------------
@router.post("/register")
@limiter.limit("3/minute")
def register_user(
    request: Request,
    user: RegisterRequest,
):
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

    pending = email_verifications_collection.find_one({
        "email": email,
        "purpose": "register",
    })

    verification_data = {
        "name": user.name.strip(),
        "email": email,
        "password_hash": hash_password(user.password),
        "otp": otp,
        "expires_at": expires_at,
        "purpose": "register",
    }

    if pending:
        email_verifications_collection.update_one(
            {
                "email": email,
                "purpose": "register",
            },
            {"$set": verification_data},
        )
    else:
        email_verifications_collection.insert_one(verification_data)

    send_otp_email(email, otp)

    return {
        "message": "OTP sent successfully. Please verify your email."
    }


# -------------------------
# RESEND OTP
# -------------------------
@router.post("/resend-otp")
@limiter.limit("3/minute")
def resend_otp(
    request: Request,
    data: ResendOTPRequest,
):
    email = data.email.lower().strip()

    record = email_verifications_collection.find_one({"email": email})

    if not record:
        raise HTTPException(
            status_code=400,
            detail="No pending verification found.",
        )

    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    email_verifications_collection.update_one(
        {"email": email},
        {
            "$set": {
                "otp": otp,
                "expires_at": expires_at,
            }
        },
    )

    send_otp_email(email, otp)

    return {
        "message": "OTP resent successfully"
    }


# -------------------------
# VERIFY EMAIL (REGISTER COMPLETE)
# -------------------------
@router.post("/verify-email")
@limiter.limit("5/minute")
def verify_email(
    request: Request,
    data: VerifyOTPRequest,
    response: Response,
):
    email = data.email.lower().strip()

    record = email_verifications_collection.find_one({
        "email": email,
        "purpose": "register",
    })

    if not record:
        raise HTTPException(status_code=400, detail="No OTP found")

    expires_at = record["expires_at"]

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        email_verifications_collection.delete_one({
            "email": record["email"],
            "purpose": "register",
        })
        raise HTTPException(status_code=400, detail="OTP expired")

    if data.otp != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    existing_user = users_collection.find_one({"email": record["email"]})
    if existing_user:
        email_verifications_collection.delete_one({
            "email": record["email"],
            "purpose": "register",
        })
        raise HTTPException(
            status_code=400,
            detail="User already exists. Please login.",
        )

    result = users_collection.insert_one({
        "name": record["name"],
        "email": record["email"],
        "password_hash": record["password_hash"],
        "created_at": datetime.now(timezone.utc),
    })

    email_verifications_collection.delete_one({
        "email": record["email"],
        "purpose": "register",
    })

    access_token = create_access_token(
        data={
            "sub": str(result.inserted_id),
            "email": record["email"],
        }
    )

    set_auth_cookie(response, access_token)

    return {
        "message": "Account verified successfully",
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
@limiter.limit("5/minute")
def login_user(
    request: Request,
    user: LoginRequest,
    response: Response,
):
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

    set_auth_cookie(response, access_token)

    return {
        "message": "Login successful",
        "user": {
            "_id": str(existing_user["_id"]),
            "name": existing_user.get("name", ""),
            "email": existing_user["email"],
        },
    }


# -------------------------
# LOGOUT
# -------------------------
@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        path="/",
    )

    return {
        "message": "Logged out successfully"
    }


# -------------------------
# FORGOT PASSWORD (SEND OTP)
# -------------------------
@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
):
    email = data.email.lower().strip()

    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    existing = email_verifications_collection.find_one({
        "email": email,
        "purpose": "reset_password",
    })

    reset_data = {
        "email": email,
        "otp": otp,
        "expires_at": expires_at,
        "purpose": "reset_password",
    }

    if existing:
        email_verifications_collection.update_one(
            {
                "email": email,
                "purpose": "reset_password",
            },
            {"$set": reset_data},
        )
    else:
        email_verifications_collection.insert_one(reset_data)

    send_otp_email(email, otp)

    return {
        "message": "Verification code sent to your email"
    }


# -------------------------
# RESET PASSWORD (VERIFY OTP + UPDATE PASSWORD)
# -------------------------
@router.post("/verify-reset-password")
@limiter.limit("5/minute")
def verify_reset_password(
    request: Request,
    data: VerifyResetOTPRequest,
):
    email = data.email.lower().strip()

    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long.",
        )

    record = email_verifications_collection.find_one({
        "email": email,
        "purpose": "reset_password",
    })

    if not record:
        raise HTTPException(status_code=400, detail="No OTP found")

    expires_at = record["expires_at"]

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        email_verifications_collection.delete_one({
            "email": record["email"],
            "purpose": "reset_password",
        })
        raise HTTPException(status_code=400, detail="OTP expired")

    if data.otp != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    hashed_password = hash_password(data.new_password)

    users_collection.update_one(
        {"email": record["email"]},
        {"$set": {"password_hash": hashed_password}},
    )

    email_verifications_collection.delete_one({
        "email": record["email"],
        "purpose": "reset_password",
    })

    return {
        "message": "Password reset successful"
    }
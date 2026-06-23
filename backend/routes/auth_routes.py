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


# -------------------------
# REGISTER (OTP FLOW)
# -------------------------
@router.post("/register")
def register_user(user: RegisterRequest):
    email = user.email.lower().strip()

    if len(user.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long.",
        )

    # check if already a real user
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists. Please login.",
        )

    # check if OTP already pending
    pending = email_verifications_collection.find_one({"email": email})
    if pending:
        raise HTTPException(
            status_code=400,
            detail="OTP already sent. Please verify your email.",
        )

    # generate OTP
    otp = str(random.randint(100000, 999999))

    # FIXED: proper timezone-aware expiry
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    # store TEMP data
    email_verifications_collection.insert_one({
        "name": user.name.strip(),
        "email": email,
        "password_hash": hash_password(user.password),
        "otp": otp,
        "expires_at": expires_at,
    })

    # send email
    send_otp_email(email, otp)

    return {
        "message": "OTP sent to email. Please verify within 5 minutes."
    }


# -------------------------
# VERIFY OTP
# -------------------------
@router.post("/verify-email")
def verify_email(data: VerifyOTPRequest):

    record = email_verifications_collection.find_one({
        "email": data.email.lower().strip()
    })

    if not record:
        raise HTTPException(status_code=400, detail="No OTP found")

    expires_at = record["expires_at"]

    # FIXED: timezone-safe comparison
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        email_verifications_collection.delete_one({"email": record["email"]})
        raise HTTPException(status_code=400, detail="OTP expired")

    # otp check
    if data.otp != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # create actual user
    result = users_collection.insert_one({
        "name": record["name"],
        "email": record["email"],
        "password_hash": record["password_hash"],
        "created_at": datetime.now(timezone.utc),
    })

    # delete temp record
    email_verifications_collection.delete_one({"email": record["email"]})

    # generate token
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

    stored_password_hash = existing_user.get("password_hash")

    if not stored_password_hash:
        raise HTTPException(
            status_code=401,
            detail="This account uses an old password format. Please create a new account.",
        )

    if not verify_password(user.password, stored_password_hash):
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
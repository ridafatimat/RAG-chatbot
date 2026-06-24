import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel, EmailStr

from services.mongo_service import users_collection
from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
)
from services.rate_limiter import limiter

router = APIRouter()

ENV = os.getenv("ENV", "development")
IS_PRODUCTION = ENV == "production"

ACCESS_TOKEN_COOKIE_NAME = "access_token"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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


@router.post("/register")
@limiter.limit("3/minute")
def register_user(
    request: Request,
    user: RegisterRequest,
    response: Response,
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

    new_user = {
        "name": user.name.strip(),
        "email": email,
        "password_hash": hash_password(user.password),
        "created_at": datetime.now(timezone.utc),
    }

    result = users_collection.insert_one(new_user)

    access_token = create_access_token(
        data={
            "sub": str(result.inserted_id),
            "email": new_user["email"],
        }
    )

    set_auth_cookie(response, access_token)

    return {
        "message": "Account created successfully",
        "user": {
            "_id": str(result.inserted_id),
            "name": new_user["name"],
            "email": new_user["email"],
        },
    }


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

    set_auth_cookie(response, access_token)

    return {
        "message": "Login successful",
        "user": {
            "_id": str(existing_user["_id"]),
            "name": existing_user.get("name", ""),
            "email": existing_user["email"],
        },
    }


@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        path="/",
    )

    return {
        "message": "Logged out successfully"
    }
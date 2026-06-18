from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from passlib.context import CryptContext

from services.mongo_service import users_collection

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


@router.post("/register")
def register_user(user: RegisterRequest):
    email = user.email.lower().strip()

    if len(user.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long."
        )

    existing_user = users_collection.find_one({"email": email})

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists. Please login."
        )

    new_user = {
        "name": user.name.strip(),
        "email": email,
        "password_hash": hash_password(user.password),
        "created_at": datetime.now(timezone.utc),
    }

    result = users_collection.insert_one(new_user)

    return {
        "message": "Account created successfully",
        "user": {
            "_id": str(result.inserted_id),
            "name": new_user["name"],
            "email": new_user["email"],
        },
    }


@router.post("/login")
def login_user(user: LoginRequest):
    email = user.email.lower().strip()

    existing_user = users_collection.find_one({"email": email})

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    stored_password_hash = existing_user.get("password_hash")

    if not stored_password_hash:
        raise HTTPException(
            status_code=401,
            detail="This account uses an old password format. Please create a new account."
        )

    if not verify_password(user.password, stored_password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    return {
        "message": "Login successful",
        "user": {
            "_id": str(existing_user["_id"]),
            "name": existing_user["name"],
            "email": existing_user["email"],
        },
    }
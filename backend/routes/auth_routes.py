from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

from services.mongo_service import users_collection

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register_user(user: RegisterRequest):
    existing_user = users_collection.find_one({"email": user.email})

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists. Please login."
        )

    new_user = {
        "name": user.name,
        "email": user.email,
        "password": user.password,
        "created_at": datetime.now(timezone.utc),
    }

    result = users_collection.insert_one(new_user)

    return {
        "message": "Account created successfully",
        "user": {
            "_id": str(result.inserted_id),
            "name": user.name,
            "email": user.email,
        },
    }


@router.post("/login")
def login_user(user: LoginRequest):
    existing_user = users_collection.find_one({
        "email": user.email,
        "password": user.password,
    })

    if not existing_user:
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
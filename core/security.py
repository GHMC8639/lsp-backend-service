from fastapi import HTTPException
from passlib.context import CryptContext
from jose import jwt
import re
from datetime import datetime, timedelta
from core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hash password
def hash_password(text: str):
    return pwd_context.hash(text)


# Verify password
def verify_password(text: str, hash: str):
    return pwd_context.verify(text, hash)


def create_access_token(data: dict):
    to_encode = data.copy()
    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expires_at})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# Decode token
def decode_access_token(token: str):
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except Exception as e:
     print("TOKEN ERROR:", str(e))
     return None


def decode_refresh_token(token: str):
    return decode_access_token(token)


def validate_mobile(mobile_number: str):
    if not mobile_number:
        raise HTTPException(status_code=400, detail="Mobile number required")

    # Remove all spaces
    mobile_number = mobile_number.strip().replace(" ", "")

    # Normalize to +91
    if re.fullmatch(r"[6-9]\d{9}", mobile_number):
        mobile_number = "+91" + mobile_number

    # Final validation
    if not re.fullmatch(r"^\+91[6-9]\d{9}$", mobile_number):
        raise HTTPException(
            status_code=400,
            detail="Invalid Indian mobile number",
        )

    return mobile_number


def validate_password_length(password: str):
    if not password:
        raise HTTPException(status_code=400, detail="Password required")

    if len(password) < 6 or len(password) > 14:
        raise HTTPException(
            status_code=400,
            detail="Password length must be between 6 and 14 characters",
        )
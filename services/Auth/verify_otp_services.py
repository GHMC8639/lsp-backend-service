import random
from fastapi import HTTPException, status

from core.redis import redis_client
from core.security import hash_password, verify_password
from utils.twilio_service import send_sms


OTP_EXPIRY_SECONDS = 300
MAX_ATTEMPTS = 3
MAX_RESEND_ATTEMPTS = 2
BLOCK_DURATION_SECONDS = 86400


def _generate_otp():
    return str(random.randint(100000, 999999))


# =========================
# SEND OTP (Redis + Twilio)
# =========================
def send_otp(mobile_number: str):

    # Check if user is blocked
    if redis_client.exists(f"otp:block:{mobile_number}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Blocked for 24 hours"
        )
  
    
    otp = _generate_otp()
    print(f"OTP for {mobile_number}: {otp}")   ## Debug log, remove in production

    # Store OTP (hashed) in Redis
    redis_client.setex(
        f"otp:{mobile_number}",
        OTP_EXPIRY_SECONDS,
        hash_password(otp)
    )

    # Store metadata
    redis_client.hset(
        f"otp:meta:{mobile_number}",
        mapping={
            "attempts": 0,
            "resend_attempts": 0
        }
    )

    # Send SMS via Twilio
    try:
        send_sms(mobile_number, otp)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send OTP: {str(e)}"
        )

    return True, "OTP sent successfully"


# =========================
# VERIFY OTP
# =========================
def verify_otp(mobile_number: str, user_otp: str):

    if redis_client.exists(f"otp:block:{mobile_number}"):
        return False

    otp_hash = redis_client.get(f"otp:{mobile_number}")
    if not otp_hash:
        return False

    meta_key = f"otp:meta:{mobile_number}"
    attempts = int(redis_client.hget(meta_key, "attempts") or 0)

    # Check OTP
    if not verify_password(user_otp, otp_hash):

        attempts += 1
        redis_client.hset(meta_key, "attempts", attempts)

        if attempts >= MAX_ATTEMPTS:
            redis_client.setex(
                f"otp:block:{mobile_number}",
                BLOCK_DURATION_SECONDS,
                "1"
            )

        return False

    # OTP success
    redis_client.delete(f"otp:{mobile_number}")
    redis_client.delete(meta_key)

    return True


# =========================
# REMAINING ATTEMPTS
# =========================
def remaining_attempts(mobile_number: str):

    attempts = int(
        redis_client.hget(f"otp:meta:{mobile_number}", "attempts") or 0
    )

    return max(0, MAX_ATTEMPTS - attempts)


# =========================
# RESEND OTP
# =========================
def resend_otp(mobile_number: str):

    meta_key = f"otp:meta:{mobile_number}"

    resend_attempts = int(
        redis_client.hget(meta_key, "resend_attempts") or 0
    )

    if resend_attempts >= MAX_RESEND_ATTEMPTS:

        redis_client.setex(
            f"otp:block:{mobile_number}",
            BLOCK_DURATION_SECONDS,
            "1"
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Resend limit exceeded"
        )

    otp = _generate_otp()

    redis_client.setex(
        f"otp:{mobile_number}",
        OTP_EXPIRY_SECONDS,
        hash_password(otp)
    )

    redis_client.hset(
        meta_key,
        "resend_attempts",
        resend_attempts + 1
    )

    # Send SMS again
    try:
        send_sms(mobile_number, otp)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resend OTP: {str(e)}"
        )

    return {
        "message": "OTP resent successfully",
        "remaining_resend_attempts":
            MAX_RESEND_ATTEMPTS - (resend_attempts + 1)
    }


# =========================
# ADD OTP TO REDIS
# =========================
def add_otp(phone_number: str, ttl_seconds: int = 300):

    otp = str(random.randint(100000, 999999))

    key = f"otp:meta:{phone_number}"

    redis_client.hset(key, mapping={
        "otp": otp,
        "attempts": 0,
        "resend_attempts": 0
    })

    redis_client.expire(key, ttl_seconds)

    return otp
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):

    # ============================================================
    # Environment
    # ============================================================
    APP_ENV: str = "development"
    DEFAULT_CONSENT_VERSION: str = "v1.0"

    # ============================================================
    # Security
    # ============================================================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1000
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ============================================================
    # Super Admin Bootstrap
    # ============================================================
    SUPERADMIN_TOKEN: str
    SUPER_ADMIN_NAME: str
    SUPER_ADMIN_MOBILE: str
    SUPER_ADMIN_DEVICE_ID: str
    SUPER_ADMIN_PASSWORD: str

    # ============================================================
    # Database
    # ============================================================
    DATABASE_URL: str

    # ============================================================
    # Redis (OTP storage)
    # ============================================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # ============================================================
    # Twilio SMS Configuration
    # ============================================================
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    # ============================================================
    # Verification Mode
    # ============================================================
    VERIFICATION_MODE: str = "dummy"

    PAN_MAX_ATTEMPTS: int = 3
    AADHAAR_MAX_ATTEMPTS: int = 3
    BANK_MAX_ATTEMPTS: int = 3

    PAN_COOLDOWN_HOURS: int = 24
    AADHAAR_COOLDOWN_HOURS: int = 24
    BANK_COOLDOWN_HOURS: int = 24

    NAME_MATCH_THRESHOLD: float = 80.0

    # ============================================================
    # File Upload
    # ============================================================
    MAX_FILE_SIZE_MB: int = 2
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png"]
    ALLOWED_DOCUMENT_EXTENSIONS: List[str] = [".pdf"]
    UPLOAD_BASE_PATH: str = "uploads"

    DOC_MAX_ATTEMPTS: int = 3
    DOC_COOLDOWN_HOURS: int = 24
    DOC_MATCH_THRESHOLD: float = 75.0

    # ============================================================
    # Data Retention
    # ============================================================
    RETENTION_DAYS: int = 90
    TRACKER_CLEANUP_HOURS: int = 48
    REJECTED_DOCS_RETENTION_DAYS: int = 90

    # ============================================================
    # KARZA API
    # ============================================================
    KARZA_API_KEY: Optional[str] = None
    KARZA_PAN_URL: str = "https://api.karza.in/v3/sync/pan-verification"

    # ============================================================
    # DigiLocker
    # ============================================================
    DIGILOCKER_CLIENT_ID: Optional[str] = None
    DIGILOCKER_CLIENT_SECRET: Optional[str] = None
    DIGILOCKER_REDIRECT_URI: Optional[str] = None
    DIGILOCKER_AUTH_URL: str = "https://api.digitallocker.gov.in/public/oauth2/1/authorize"
    DIGILOCKER_TOKEN_URL: str = "https://api.digitallocker.gov.in/public/oauth2/1/token"
    DIGILOCKER_AADHAAR_URL: str = "https://api.digitallocker.gov.in/public/oauth2/1/xml/eaadhaar"

    # ============================================================
    # Cashfree
    # ============================================================
    CASHFREE_APP_ID: Optional[str] = None
    CASHFREE_SECRET_KEY: Optional[str] = None
    CASHFREE_BANK_URL: str = "https://api.cashfree.com/verification/bank-account/sync"

    # ============================================================
    # Hyperverge
    # ============================================================
    HYPERVERGE_APP_ID: Optional[str] = None
    HYPERVERGE_APP_KEY: Optional[str] = None
    HYPERVERGE_API_URL: str = "https://ind-docs.hyperverge.co/v2.0/readKYC"

    # ============================================================
    # Computed Fields
    # ============================================================
    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    # ============================================================
    # Pydantic Config
    # ============================================================
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
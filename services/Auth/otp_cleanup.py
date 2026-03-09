from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.Auth.otp_verification import OTPVerification
 
OTP_RETENTION_HOURS = 24  
 
 
def cleanup_otps(db: Session):
    cutoff_time = datetime.utcnow() - timedelta(hours=OTP_RETENTION_HOURS)
 
    db.query(OTPVerification).filter(
        OTPVerification.created_at < cutoff_time
    ).delete(synchronize_session=False)
 
    db.commit()
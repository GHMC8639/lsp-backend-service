import email
from sqlalchemy.orm import Session
from models.Auth.user import User
from core.security import hash_password

def create_default_super_admin(db: Session,username: str, mobile_number: str, password: str,device_id: str):
    existing = db.query(User).filter(
        User.mobile_number == mobile_number
    ).first()

    if existing:
        return 

    super_admin = User(
        username=username,
        mobile_number=mobile_number,
        password_hash=hash_password(password),
        device_id=device_id,
        role="SUPER_ADMIN"
    )

    db.add(super_admin)
    db.commit()
    
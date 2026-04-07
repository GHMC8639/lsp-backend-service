from sqlalchemy.orm import Session
from models.Auth.user import User


def update_user_profile(db: Session, user: User, data: dict):
    for key, value in data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user
def delete_user_account(db, user):
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
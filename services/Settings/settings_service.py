from sqlalchemy.orm import Session
from models.Settings.user_settings import UserSettings


# 🔹 GET SETTINGS
def get_user_settings(db: Session, user_id: int):
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == user_id
    ).first()

    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


# 🔹 UPDATE SETTINGS
def update_user_settings(db: Session, user_id: int, data: dict):
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == user_id
    ).first()

    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)

    for key, value in data.items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)

    return settings
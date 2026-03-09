from models.Auth.user import User

def seed_dummy_users(db):

    dummy_users = [
        {
            "id": 1,
            "username": "testuser1",
            "mobile_number": "9999999999",
            "password_hash": "hashedpassword",
            "device_id": "device_1",
            "role": "USER"
        },
        {
            "id": 2,
            "username": "testuser2",
            "mobile_number": "8888888888",
            "password_hash": "hashedpassword",
            "device_id": "device_2",
            "role": "USER"
        },
        {
            "id": 3,
            "username": "testuser3",
            "mobile_number": "7777777777",
            "password_hash": "hashedpassword",
            "device_id": "device_3",
            "role": "USER"
        },
        {
        "id": 4,
            "username": "testuser4",
            "mobile_number": "6666666666",
            "password_hash": "hashedpassword",
            "device_id": "device_4",
            "role": "USER"
        }
    ]

    for u in dummy_users:
        exists = db.query(User).filter_by(mobile_number=u["mobile_number"]).first()
        if exists:
            continue

        user = User(**u)
        db.add(user)

    db.commit()
    print("[SEED] Dummy users inserted successfully.")

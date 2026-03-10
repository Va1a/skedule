from pathlib import Path

from skedule import bcrypt, db
from skedule.models import User

from devtools.common import create_local_app


SEED_USERS = [
    {
        "id": 1,
        "external_id": "1",
        "name": "Vala Skedule",
        "email": "vala@skedule.net",
        "phone": "8185551234",
    },
    {
        "id": 2,
        "external_id": "2",
        "name": "Sam Sepiol",
        "email": "sam@skedule.net",
        "phone": "8183224172",
    },
    {
        "id": 3,
        "external_id": "3",
        "name": "Dolores Haze",
        "email": "haze@skedule.net",
        "phone": "8052123644",
    },
]


def main() -> int:
    app = create_local_app()
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    hashed_password = bcrypt.generate_password_hash("test").decode("utf-8")

    with app.app_context():
        db.create_all()
        created = 0

        for user_data in SEED_USERS:
            if User.query.filter_by(email=user_data["email"]).first():
                continue

            user = User(password=hashed_password, **user_data)
            db.session.add(user)
            created += 1

        db.session.commit()

    print(f"Inserted {created} development users. Default password: test")
    return 0

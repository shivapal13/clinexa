"""
Utility script to seed or promote an administrator account.
Usage:
    python -m app.scripts.seed_admin --name "Admin" --email "admin@clinexa.com" --password "AdminPassword123"
"""
import argparse
from app.core.database import SessionLocal
from app.models.user import User
from app.core.enums import UserRole
from app.core.password_hashing import hash_password


def seed_admin(name: str, email: str, password: str):
    db = SessionLocal()
    normalized_email = email.strip().lower()
    try:
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            existing.role = UserRole.ADMIN
            existing.is_admin = True
            existing.password = hash_password(password)
            existing.is_active = True
            db.commit()
            print(f"Successfully promoted existing user {normalized_email} to Administrator.")
        else:
            admin_user = User(
                name=name,
                email=normalized_email,
                password=hash_password(password),
                role=UserRole.ADMIN,
                is_admin=True,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            print(f"Successfully created new Administrator account for {normalized_email}.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed or promote an Admin account")
    parser.add_argument("--name", default="System Administrator", help="Admin name")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    args = parser.parse_args()

    seed_admin(args.name, args.email, args.password)


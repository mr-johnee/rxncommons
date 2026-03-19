import argparse

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User


def main():
    parser = argparse.ArgumentParser(description="Create or update an admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        by_email = db.query(User).filter(User.email == args.email).first()
        by_username = db.query(User).filter(User.username == args.username).first()

        user = by_email or by_username
        if user:
            user.email = args.email
            user.username = args.username
            user.password_hash = get_password_hash(args.password)
            user.role = "admin"
            user.is_active = True
            user.is_email_verified = True
            db.commit()
            print(f"updated admin user: {args.email}")
            return

        new_user = User(
            email=args.email,
            username=args.username,
            password_hash=get_password_hash(args.password),
            role="admin",
            is_active=True,
            is_email_verified=True,
        )
        db.add(new_user)
        db.commit()
        print(f"created admin user: {args.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

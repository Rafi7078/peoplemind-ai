from getpass import getpass
from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from backend.app.core.security import hash_password
from backend.app.db.database import Base, SessionLocal, engine
from backend.app.models.user import User
def request_email() -> str:
    while True:
        raw_email = input("Admin email: ").strip().lower()
        try:
            result = validate_email(
                raw_email,
                check_deliverability=False,
            )
            return result.normalized.lower()
        except EmailNotValidError as error:
            print(f"Invalid email: {error}")
def request_password() -> str:
    while True:
        password = getpass("Admin password: ")
        confirmation = getpass("Confirm password: ")
        if password != confirmation:
            print("Passwords did not match.")
            continue
        if len(password) < 12:
            print("Password must contain at least 12 characters.")
            continue
        if not any(character.isalpha() for character in password):
            print("Password must contain at least one letter.")
            continue
        if not any(character.isdigit() for character in password):
            print("Password must contain at least one number.")
            continue
        return password
def create_admin() -> None:
    Base.metadata.create_all(bind=engine)
    email = request_email()
    password = request_password()
    with SessionLocal() as database:
        existing_user = database.scalar(
            select(User).where(User.email == email)
        )
        if existing_user is not None:
            print("An account with this email already exists.")
            return
        admin = User(
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
            is_admin=True,
        )
        database.add(admin)
        database.commit()
    print("PeopleMind AI Admin account created successfully.")
if __name__ == "__main__":
    create_admin()

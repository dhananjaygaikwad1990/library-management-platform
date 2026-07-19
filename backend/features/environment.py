import os

# Set the isolated database before importing any application database modules.
os.environ["TEST_DATABASE_URL"] = "sqlite+pysqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "behave-test-secret"

from sqlalchemy import delete

from app.auth import get_password_hash
from app.db.session import Base, SessionLocal, engine
from app.models import Author, Book, BookCopy, BorrowRecord, Member, Role, User


def _seed_auth_data() -> None:
    with SessionLocal() as session:
        roles = {
            name: Role(name=name, description=f"Test {name} role")
            for name in ("student", "librarian", "admin", "visitor")
        }
        session.add_all(roles.values())
        session.flush()

        users = [
            User(
                email="student@example.com",
                password_hash=get_password_hash("StudentPass1!"),
                api_key="student-test-key",
                full_name="Test Student",
                roles=[roles["student"]],
            ),
            User(
                email="librarian@example.com",
                password_hash=get_password_hash("LibrarianPass1!"),
                api_key="librarian-test-key",
                full_name="Test Librarian",
                roles=[roles["librarian"]],
            ),
            User(
                email="visitor@example.com",
                password_hash=get_password_hash("VisitorPass1!"),
                api_key="visitor-test-key",
                full_name="Test Visitor",
                roles=[roles["visitor"]],
            ),
        ]
        session.add_all(users)
        session.commit()


def before_all(context):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _seed_auth_data()


def before_scenario(context, scenario):
    with SessionLocal() as session:
        for model in (BorrowRecord, BookCopy, Book, Member, Author):
            session.execute(delete(model))
        session.commit()
    context.failure = None
    context.response = None
    context.headers = {}


def after_all(context):
    Base.metadata.drop_all(bind=engine)

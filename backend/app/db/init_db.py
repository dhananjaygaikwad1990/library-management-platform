from pathlib import Path

from app.db.session import Base, engine
from app.models import Author, Book, BookCopy, Member, BorrowRecord, Role, User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    init_auth_roles()


def init_auth_roles() -> None:
    sql_file = Path(__file__).resolve().parent / "init_auth_roles.sql"
    if not sql_file.exists():
        raise FileNotFoundError(f"Auth role initialization script not found: {sql_file}")

    sql_text = sql_file.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.exec_driver_sql(sql_text)


if __name__ == "__main__":
    init_db()
    print("Database initialized")

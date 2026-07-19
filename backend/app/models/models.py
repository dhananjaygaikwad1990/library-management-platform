from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Table, Text, func
from sqlalchemy.orm import relationship
from app.db.session import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    users = relationship("User", secondary=user_roles, back_populates="roles")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(120), nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    api_key = Column(String(128), nullable=False, unique=True)
    full_name = Column(String(120), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Author(Base):
    __tablename__ = "authors"

    author_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    biography = Column(Text, nullable=True)

    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("authors.author_id"), nullable=False)
    isbn = Column(String(32), nullable=False, unique=True)
    title = Column(String(256), nullable=False)
    category = Column(String(80), nullable=True)
    publisher = Column(String(120), nullable=True)
    publish_year = Column(Integer, nullable=True)
    language = Column(String(40), nullable=True)
    pages = Column(Integer, nullable=True)

    author = relationship("Author", back_populates="books")
    copies = relationship("BookCopy", back_populates="book")


class BookCopy(Base):
    __tablename__ = "book_copies"

    copy_id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.book_id"), nullable=False)
    barcode = Column(String(80), nullable=False, unique=True)
    shelf_location = Column(String(120), nullable=True)
    status = Column(String(32), nullable=False, default="available")

    book = relationship("Book", back_populates="copies")
    borrows = relationship("BorrowRecord", back_populates="copy")


class Member(Base):
    __tablename__ = "members"

    member_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    phone = Column(String(40), nullable=True)
    address = Column(Text, nullable=True)
    membership_date = Column(Date, nullable=False)
    status = Column(String(32), nullable=False, default="active")

    borrows = relationship("BorrowRecord", back_populates="member")


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    borrow_id = Column(Integer, primary_key=True, autoincrement=True)
    copy_id = Column(Integer, ForeignKey("book_copies.copy_id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.member_id"), nullable=False)
    borrow_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    fine_amount = Column(Numeric(8, 2), nullable=True, default=0)
    remarks = Column(Text, nullable=True)

    copy = relationship("BookCopy", back_populates="borrows")
    member = relationship("Member", back_populates="borrows")

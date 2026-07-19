from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr


class ErrorResponse(BaseModel):
    error: Dict[str, object]


class TokenRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    roles: List[str]


class AuthorCreate(BaseModel):
    first_name: str
    last_name: str
    biography: Optional[str] = None


class AuthorRead(BaseModel):
    author_id: int
    first_name: str
    last_name: str
    biography: Optional[str] = None

    class Config:
        from_attributes = True


class BookCreate(BaseModel):
    author_id: int
    isbn: str
    title: str
    category: Optional[str] = None
    publisher: Optional[str] = None
    publish_year: Optional[int] = None
    language: Optional[str] = None
    pages: Optional[int] = None


class BookRead(BaseModel):
    book_id: int
    author_id: int
    isbn: str
    title: str
    category: Optional[str] = None
    publisher: Optional[str] = None
    publish_year: Optional[int] = None
    language: Optional[str] = None
    pages: Optional[int] = None

    class Config:
        from_attributes = True


class BookAvailabilityRead(BaseModel):
    book_id: int
    title: str
    isbn: str
    total_copies: int
    available_copies: int


class BookCopyCreate(BaseModel):
    book_id: int
    barcode: str
    shelf_location: Optional[str] = None
    status: Optional[str] = "available"


class BookCopyRead(BaseModel):
    copy_id: int
    book_id: int
    barcode: str
    shelf_location: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    membership_date: Optional[date] = None


class MemberRead(BaseModel):
    member_id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    membership_date: date
    status: str

    class Config:
        from_attributes = True


class BorrowRequest(BaseModel):
    book_id: Optional[int] = None
    copy_id: Optional[int] = None
    borrow_date: date
    due_date: date
    remarks: Optional[str] = None


class BorrowRead(BaseModel):
    borrow_id: int
    copy_id: int
    member_id: int
    borrow_date: date
    due_date: date
    return_date: Optional[date] = None
    fine_amount: Optional[float] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class BorrowHistoryItem(BaseModel):
    borrow_id: int
    copy_id: int
    member_id: int
    borrow_date: date
    due_date: date
    return_date: Optional[date] = None
    fine_amount: Optional[float] = None
    overdue_days: int = 0
    remarks: Optional[str] = None
    status: str
    book_title: str
    book_author: str

    class Config:
        from_attributes = True

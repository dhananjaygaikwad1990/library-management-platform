from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import case, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.exceptions import ConflictError, LibraryError, NotFoundError, ValidationError
from app.models import Author, Book, BookCopy, Member, BorrowRecord


class LibraryService:
    FINE_PER_OVERDUE_DAY = Decimal("1.00")

    def __init__(self) -> None:
        pass

    def _raise_not_found(self, message: str) -> None:
        raise NotFoundError(message)

    def _handle_integrity_error(self, error: IntegrityError) -> None:
        msg = str(error.orig) if error.orig is not None else str(error)
        raise ConflictError("Database integrity error", {"detail": msg})

    def create_author(self, first_name: str, last_name: str, biography: Optional[str] = None) -> Author:
        with SessionLocal() as session:
            author = Author(first_name=first_name, last_name=last_name, biography=biography)
            session.add(author)
            try:
                session.commit()
                session.refresh(author)
                return author
            except IntegrityError as error:
                session.rollback()
                self._handle_integrity_error(error)

    def get_author(self, author_id: int) -> Author:
        with SessionLocal() as session:
            author = session.get(Author, author_id)
            if not author:
                self._raise_not_found(f"Author {author_id} not found")
            return author

    def list_authors(self):
        with SessionLocal() as session:
            return session.query(Author).order_by(Author.last_name, Author.first_name).all()

    def create_book(
        self,
        author_id: int,
        isbn: str,
        title: str,
        category: Optional[str] = None,
        publisher: Optional[str] = None,
        publish_year: Optional[int] = None,
        language: Optional[str] = None,
        pages: Optional[int] = None,
    ) -> Book:
        with SessionLocal() as session:
            author = session.get(Author, author_id)
            if not author:
                self._raise_not_found(f"Author {author_id} not found")
            book = Book(
                author_id=author.author_id,
                isbn=isbn,
                title=title,
                category=category,
                publisher=publisher,
                publish_year=publish_year,
                language=language,
                pages=pages,
            )
            session.add(book)
            try:
                session.commit()
                session.refresh(book)
                return book
            except IntegrityError as error:
                session.rollback()
                self._handle_integrity_error(error)

    def create_book_copy(
        self,
        book_id: int,
        barcode: str,
        shelf_location: Optional[str] = None,
        status: str = "available",
    ) -> BookCopy:
        with SessionLocal() as session:
            book = session.get(Book, book_id)
            if not book:
                self._raise_not_found(f"Book {book_id} not found")
            copy = BookCopy(book_id=book_id, barcode=barcode, shelf_location=shelf_location, status=status)
            session.add(copy)
            try:
                session.commit()
                session.refresh(copy)
                return copy
            except IntegrityError as error:
                session.rollback()
                self._handle_integrity_error(error)

    def create_member(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        membership_date: Optional[date] = None,
    ) -> Member:
        with SessionLocal() as session:
            membership_date = membership_date or date.today()
            member = Member(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                membership_date=membership_date,
            )
            session.add(member)
            try:
                session.commit()
                session.refresh(member)
                return member
            except IntegrityError as error:
                session.rollback()
                self._handle_integrity_error(error)

    def borrow_copy(
        self,
        copy_id: Optional[int],
        member_id: int,
        borrow_date: date,
        due_date: date,
        remarks: Optional[str] = None,
        book_id: Optional[int] = None,
    ) -> BorrowRecord:
        with SessionLocal() as session:
            if copy_id is None and book_id is None:
                raise ValidationError("Either book_id or copy_id must be provided", {})
            if due_date < borrow_date:
                raise ValidationError(
                    "Due date cannot be before the borrow date",
                    {"borrow_date": borrow_date.isoformat(), "due_date": due_date.isoformat()},
                )

            copy = None
            if copy_id is not None:
                copy = session.get(BookCopy, copy_id)
                if not copy:
                    self._raise_not_found(f"Copy {copy_id} not found")
            elif book_id is not None:
                copy = (
                    session.query(BookCopy)
                    .filter(BookCopy.book_id == book_id, BookCopy.status == "available")
                    .order_by(BookCopy.copy_id)
                    .first()
                )
                if not copy:
                    raise ValidationError("No available copy found for the requested book", {"book_id": book_id})

            if copy.status != "available":
                raise ValidationError("Book copy is not available for borrow", {"copy_id": copy.copy_id})

            member = session.get(Member, member_id)
            if not member:
                self._raise_not_found(f"Member {member_id} not found")

            borrow = BorrowRecord(
                copy_id=copy.copy_id,
                member_id=member_id,
                borrow_date=borrow_date,
                due_date=due_date,
                remarks=remarks,
            )
            copy.status = "borrowed"
            session.add(borrow)
            try:
                session.commit()
                session.refresh(borrow)
                return borrow
            except IntegrityError as error:
                session.rollback()
                self._handle_integrity_error(error)

    def list_members(self, search: Optional[str] = None):
        with SessionLocal() as session:
            query = session.query(Member)
            term = search.strip() if search else ""
            if term:
                filters = [
                    Member.first_name.ilike(f"%{term}%"),
                    Member.last_name.ilike(f"%{term}%"),
                    (Member.first_name + " " + Member.last_name).ilike(f"%{term}%"),
                ]
                if term.isdigit():
                    filters.append(Member.member_id == int(term))
                query = query.filter(or_(*filters))
            return query.order_by(Member.last_name, Member.first_name).limit(100).all()

    def borrow_copy_for_member_email(
        self,
        email: str,
        copy_id: Optional[int],
        borrow_date: date,
        due_date: date,
        remarks: Optional[str] = None,
        book_id: Optional[int] = None,
        full_name: Optional[str] = None,
    ) -> BorrowRecord:
        with SessionLocal() as session:
            member = session.query(Member).filter(Member.email == email).one_or_none()
            if not member:
                name_parts = (full_name or email.split("@", 1)[0]).strip().split(maxsplit=1)
                first_name = name_parts[0] if name_parts else "Member"
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                member = Member(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    membership_date=date.today(),
                )
                session.add(member)
                try:
                    session.commit()
                    session.refresh(member)
                except IntegrityError as error:
                    session.rollback()
                    self._handle_integrity_error(error)
            member_id = member.member_id

        return self.borrow_copy(
            copy_id=copy_id,
            member_id=member_id,
            borrow_date=borrow_date,
            due_date=due_date,
            remarks=remarks,
            book_id=book_id,
        )

    def return_borrow_for_member_email(self, email: str, borrow_id: int) -> BorrowRecord:
        with SessionLocal() as session:
            member = session.query(Member).filter(Member.email == email).one_or_none()
            if not member:
                self._raise_not_found("Member record not found for the logged-in account")

            borrow = (
                session.query(BorrowRecord)
                .filter(
                    BorrowRecord.borrow_id == borrow_id,
                    BorrowRecord.member_id == member.member_id,
                )
                .one_or_none()
            )
            if not borrow:
                self._raise_not_found(f"Borrow record {borrow_id} not found")
            if borrow.return_date:
                raise ValidationError("This copy has already been returned", {"borrow_id": borrow_id})

            returned_on = date.today()
            overdue_days = max((returned_on - borrow.due_date).days, 0)
            borrow.return_date = returned_on
            borrow.fine_amount = self.FINE_PER_OVERDUE_DAY * overdue_days
            borrow.copy.status = "available"
            session.commit()
            session.refresh(borrow)
            return borrow

    def clear_fine_for_member_email(self, email: str, borrow_id: int) -> BorrowRecord:
        with SessionLocal() as session:
            member = session.query(Member).filter(Member.email == email).one_or_none()
            if not member:
                self._raise_not_found("Member record not found for the logged-in account")

            borrow = (
                session.query(BorrowRecord)
                .filter(
                    BorrowRecord.borrow_id == borrow_id,
                    BorrowRecord.member_id == member.member_id,
                )
                .one_or_none()
            )
            if not borrow:
                self._raise_not_found(f"Borrow record {borrow_id} not found")
            if not borrow.return_date:
                raise ValidationError(
                    "Fine can only be cleared after the copy is returned",
                    {"borrow_id": borrow_id},
                )

            borrow.fine_amount = Decimal("0.00")
            session.commit()
            session.refresh(borrow)
            return borrow

    def list_books(self, search: Optional[str] = None, author_id: Optional[int] = None):
        with SessionLocal() as session:
            query = session.query(Book)
            if search and search.strip():
                query = query.filter(Book.title.ilike(f"%{search.strip()}%"))
            if author_id is not None:
                query = query.filter(Book.author_id == author_id)
            return query.order_by(Book.title).limit(50).all()

    def list_book_availability(self, search: Optional[str] = None) -> list[dict]:
        with SessionLocal() as session:
            query = session.query(
                    Book.book_id,
                    Book.title,
                    Book.isbn,
                    func.count(BookCopy.copy_id).label("total_copies"),
                    func.sum(case((BookCopy.status == "available", 1), else_=0)).label("available_copies"),
                )
            if search and search.strip():
                query = query.filter(Book.title.ilike(f"%{search.strip()}%"))
            rows = (
                query.outerjoin(BookCopy, BookCopy.book_id == Book.book_id)
                .group_by(Book.book_id, Book.title, Book.isbn)
                .order_by(Book.title)
                .limit(50)
                .all()
            )
            return [
                {
                    "book_id": row.book_id,
                    "title": row.title,
                    "isbn": row.isbn,
                    "total_copies": row.total_copies,
                    "available_copies": row.available_copies,
                }
                for row in rows
            ]

    def get_borrow_history_for_member_email(self, email: str) -> list[dict]:
        with SessionLocal() as session:
            member = session.query(Member).filter(Member.email == email).one_or_none()
            if not member:
                return []

            borrows = (
                session.query(BorrowRecord)
                .filter(BorrowRecord.member_id == member.member_id)
                .order_by(BorrowRecord.borrow_date.desc(), BorrowRecord.borrow_id.desc())
                .all()
            )

            history = []
            today = date.today()
            for borrow in borrows:
                copy = borrow.copy
                book = copy.book
                author_name = ''
                if book and book.author:
                    author_name = f"{book.author.first_name} {book.author.last_name}"

                effective_end_date = borrow.return_date or today
                overdue_days = max((effective_end_date - borrow.due_date).days, 0)
                calculated_fine = self.FINE_PER_OVERDUE_DAY * overdue_days
                stored_fine = Decimal(borrow.fine_amount or 0)
                fine_amount = stored_fine if borrow.return_date else max(stored_fine, calculated_fine)

                if borrow.return_date:
                    status = "returned"
                elif overdue_days > 0:
                    status = "overdue"
                else:
                    status = "on loan"

                history.append(
                    {
                        'borrow_id': borrow.borrow_id,
                        'copy_id': borrow.copy_id,
                        'member_id': borrow.member_id,
                        'borrow_date': borrow.borrow_date,
                        'due_date': borrow.due_date,
                        'return_date': borrow.return_date,
                        'fine_amount': float(fine_amount),
                        'overdue_days': overdue_days,
                        'remarks': borrow.remarks,
                        'status': status,
                        'book_title': book.title if book else 'Unknown title',
                        'book_author': author_name,
                    }
                )

            return history

    def get_book(self, book_id: int) -> Book:
        with SessionLocal() as session:
            book = session.get(Book, book_id)
            if not book:
                self._raise_not_found(f"Book {book_id} not found")
            return book

from concurrent import futures
import logging
from datetime import datetime

import grpc
from google.protobuf import empty_pb2

from app.db.init_db import init_db
from app.services import LibraryService
from app.grpc import library_pb2, library_pb2_grpc
from app.exceptions import LibraryError
from app.auth import require_grpc_roles

service = LibraryService()


def to_author_record(author):
    return library_pb2.AuthorRecord(
        author_id=author.author_id,
        first_name=author.first_name,
        last_name=author.last_name,
        biography=author.biography or "",
    )


def to_book_record(book):
    return library_pb2.BookRecord(
        book_id=book.book_id,
        author_id=book.author_id,
        isbn=book.isbn,
        title=book.title,
        category=book.category or "",
        publisher=book.publisher or "",
        publish_year=book.publish_year or 0,
        language=book.language or "",
        pages=book.pages or 0,
    )


def to_book_copy_record(copy):
    return library_pb2.BookCopyRecord(
        copy_id=copy.copy_id,
        book_id=copy.book_id,
        barcode=copy.barcode,
        shelf_location=copy.shelf_location or "",
        status=copy.status,
    )


def to_member_record(member):
    return library_pb2.MemberRecord(
        member_id=member.member_id,
        first_name=member.first_name,
        last_name=member.last_name,
        email=member.email,
        phone=member.phone or "",
        address=member.address or "",
        membership_date=member.membership_date.isoformat(),
        status=member.status,
    )


def to_borrow_record(borrow):
    return library_pb2.BorrowRecordMessage(
        borrow_id=borrow.borrow_id,
        copy_id=borrow.copy_id,
        member_id=borrow.member_id,
        borrow_date=borrow.borrow_date.isoformat(),
        due_date=borrow.due_date.isoformat(),
        return_date=borrow.return_date.isoformat() if borrow.return_date else "",
        fine_amount=float(borrow.fine_amount or 0.0),
        remarks=borrow.remarks or "",
    )


from app.auth import get_grpc_auth_token, get_user_from_grpc_context, require_grpc_roles


class LibraryServicer(library_pb2_grpc.LibraryServiceServicer):
    def CreateAuthor(self, request, context):
        require_grpc_roles(context, "librarian", "admin")
        try:
            author = service.create_author(request.first_name, request.last_name, request.biography)
            return library_pb2.AuthorResponse(author=to_author_record(author))
        except LibraryError as err:
            context.set_details(err.message)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return library_pb2.AuthorResponse()

    def CreateBook(self, request, context):
        require_grpc_roles(context, "librarian", "admin")
        try:
            book = service.create_book(
                request.author_id,
                request.isbn,
                request.title,
                request.category or None,
                request.publisher or None,
                request.publish_year or None,
                request.language or None,
                request.pages or None,
            )
            return library_pb2.BookResponse(book=to_book_record(book))
        except LibraryError as err:
            context.set_details(err.message)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return library_pb2.BookResponse()

    def CreateBookCopy(self, request, context):
        require_grpc_roles(context, "librarian", "admin")
        try:
            copy = service.create_book_copy(
                request.book_id,
                request.barcode,
                request.shelf_location or None,
                request.status or "available",
            )
            return library_pb2.BookCopyResponse(book_copy=to_book_copy_record(copy))
        except LibraryError as err:
            context.set_details(err.message)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return library_pb2.BookCopyResponse()

    def CreateMember(self, request, context):
        require_grpc_roles(context, "librarian", "admin")
        try:
            member = service.create_member(
                request.first_name,
                request.last_name,
                request.email,
                request.phone or None,
                request.address or None,
                datetime.fromisoformat(request.membership_date).date() if request.membership_date else None,
            )
            return library_pb2.MemberResponse(member=to_member_record(member))
        except LibraryError as err:
            context.set_details(err.message)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return library_pb2.MemberResponse()

    def BorrowCopy(self, request, context):
        require_grpc_roles(context, "member", "librarian", "admin")
        try:
            borrow = service.borrow_copy(
                request.copy_id,
                request.member_id,
                datetime.fromisoformat(request.borrow_date).date(),
                datetime.fromisoformat(request.due_date).date(),
                request.remarks or None,
            )
            return library_pb2.BorrowResponse(borrow=to_borrow_record(borrow))
        except LibraryError as err:
            context.set_details(err.message)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return library_pb2.BorrowResponse()

    def ListBooks(self, request, context):
        require_grpc_roles(context)
        books = service.list_books()
        return library_pb2.BookListResponse(books=[to_book_record(book) for book in books])

    def GetBook(self, request, context):
        require_grpc_roles(context)
        try:
            book = service.get_book(request.book_id)
            return library_pb2.BookResponse(book=to_book_record(book))
        except LibraryError as err:
            context.set_details(err.message)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return library_pb2.BookResponse()


def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    library_pb2_grpc.add_LibraryServiceServicer_to_server(LibraryServicer(), server)
    server.add_insecure_port("[::]:50051")

    init_db()
    server.start()
    logging.info("gRPC server started on 0.0.0.0:50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()

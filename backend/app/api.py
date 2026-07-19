import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import create_access_token, get_db, authenticate_user, require_authenticated_user, require_roles

from app.exceptions import ConflictError, LibraryError, NotFoundError, ValidationError
from app.schemas import (
    AuthorCreate,
    AuthorRead,
    BookCopyCreate,
    BookCopyRead,
    BookAvailabilityRead,
    BookCreate,
    BookRead,
    BorrowHistoryItem,
    BorrowRead,
    BorrowRequest,
    MemberCreate,
    MemberRead,
    TokenRequest,
    TokenResponse,
)
from app.services import LibraryService

logger = logging.getLogger(__name__)
service = LibraryService()

app = FastAPI(
    title="Liberary Library Service",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(LibraryError)
async def library_error_handler(request, exc: LibraryError):
    if isinstance(exc, NotFoundError):
        status_code = 404
    elif isinstance(exc, ConflictError):
        status_code = 409
    elif isinstance(exc, ValidationError):
        status_code = 422
    else:
        status_code = 400
    return JSONResponse(status_code=status_code, content=exc.to_dict())


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": exc.detail, "details": {}}},
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/token", response_model=TokenResponse)
def login_for_access_token(payload: TokenRequest, db=Depends(get_db)):
    user = authenticate_user(payload.email, payload.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    roles = [role.name for role in user.roles]
    access_token = create_access_token({"sub": str(user.user_id), "roles": roles})
    return {"access_token": access_token, "token_type": "bearer", "roles": roles}


@app.post("/authors", response_model=AuthorRead)
def create_author(
    payload: AuthorCreate,
    current_user=Depends(require_roles("librarian", "admin")),
):
    return service.create_author(**payload.model_dump())


@app.get("/authors", response_model=list[AuthorRead])
def list_authors(current_user=Depends(require_authenticated_user)):
    return service.list_authors()


@app.post("/books", response_model=BookRead)
def create_book(
    payload: BookCreate,
    current_user=Depends(require_roles("librarian", "admin")),
):
    return service.create_book(**payload.model_dump())


@app.post("/copies", response_model=BookCopyRead)
def create_book_copy(
    payload: BookCopyCreate,
    current_user=Depends(require_roles("librarian", "admin")),
):
    return service.create_book_copy(**payload.model_dump())


@app.post("/members", response_model=MemberRead)
def create_member(
    payload: MemberCreate,
    current_user=Depends(require_roles("librarian", "admin")),
):
    return service.create_member(**payload.model_dump())


@app.get("/members", response_model=list[MemberRead])
def list_members(
    search: str | None = None,
    current_user=Depends(require_roles("librarian", "admin")),
):
    return service.list_members(search=search)


@app.post("/borrow", response_model=BorrowRead)
def borrow_copy(
    payload: BorrowRequest,
    current_user=Depends(require_roles("student", "librarian", "admin")),
):
    return service.borrow_copy_for_member_email(
        email=current_user.email,
        full_name=current_user.full_name,
        **payload.model_dump(),
    )


@app.get("/me/borrows", response_model=list[BorrowHistoryItem])
def get_my_borrow_history(current_user=Depends(require_roles("student", "librarian", "admin"))):
    return service.get_borrow_history_for_member_email(current_user.email)


@app.post("/me/borrows/{borrow_id}/return", response_model=BorrowRead)
def return_my_borrow(
    borrow_id: int,
    current_user=Depends(require_roles("student", "librarian", "admin")),
):
    return service.return_borrow_for_member_email(current_user.email, borrow_id)


@app.post("/me/borrows/{borrow_id}/clear-fine", response_model=BorrowRead)
def clear_my_fine(
    borrow_id: int,
    current_user=Depends(require_roles("student", "librarian", "admin")),
):
    return service.clear_fine_for_member_email(current_user.email, borrow_id)


@app.get("/books", response_model=list[BookRead])
def list_books(
    search: str | None = None,
    author_id: int | None = None,
    current_user=Depends(require_authenticated_user),
):
    return service.list_books(search=search, author_id=author_id)


@app.get("/books/availability", response_model=list[BookAvailabilityRead])
def list_book_availability(
    search: str | None = None,
    current_user=Depends(require_authenticated_user),
):
    return service.list_book_availability(search=search)


@app.get("/books/{book_id}", response_model=BookRead)
def get_book(book_id: int, current_user=Depends(require_authenticated_user)):
    return service.get_book(book_id)

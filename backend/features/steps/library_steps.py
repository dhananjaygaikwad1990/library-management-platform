from datetime import date, timedelta

from behave import given, then, when
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api import app
from app.db.session import SessionLocal
from app.exceptions import LibraryError
from app.models import Author, Book, BookCopy, BorrowRecord, Member
from app.services import LibraryService


service = LibraryService()
client = TestClient(app)


def _remember_failure(context, operation):
    try:
        operation()
    except LibraryError as error:
        context.failure = error


def _create_default_author():
    return service.create_author("Default", "Author", "Test author")


def _create_book(title: str, isbn: str, author_id=None):
    author_id = author_id or _create_default_author().author_id
    return service.create_book(author_id, isbn, title, "fiction", "Test Publisher", 2026, "English", 200)


def _copy_status(copy_id: int) -> str:
    with SessionLocal() as session:
        return session.get(BookCopy, copy_id).status


@given('an author named "{full_name}" exists')
def step_author_exists(context, full_name):
    first_name, last_name = full_name.split(maxsplit=1)
    context.author = service.create_author(first_name, last_name, "Test biography")


@given('a book titled "{title}" with ISBN "{isbn}" exists for that author')
def step_book_for_author(context, title, isbn):
    context.book = _create_book(title, isbn, context.author.author_id)


@given('a book titled "{title}" with ISBN "{isbn}" exists')
def step_book_exists(context, title, isbn):
    context.book = _create_book(title, isbn)


@given('the book has a copy "{barcode}" with status "{status}"')
def step_copy_exists(context, barcode, status):
    copy = service.create_book_copy(context.book.book_id, barcode, "A1", status)
    context.copy_id = copy.copy_id


@given('a member named "{full_name}" with email "{email}" exists')
def step_member_exists(context, full_name, email):
    first_name, last_name = full_name.split(maxsplit=1)
    member = service.create_member(first_name, last_name, email, membership_date=date.today())
    if not hasattr(context, "saved_member_id"):
        context.saved_member_id = member.member_id


@when('I search books for "{term}"')
def step_search_books(context, term):
    context.books = service.list_books(search=term)


@then('{count:d} book is returned with title "{title}"')
def step_book_result(context, count, title):
    assert len(context.books) == count
    assert context.books[0].title == title


@then('filtering books by the author returns {count:d} books')
def step_filter_author(context, count):
    assert len(service.list_books(author_id=context.author.author_id)) == count


@then('the author list contains "{full_name}"')
def step_author_list(context, full_name):
    names = {f"{author.first_name} {author.last_name}" for author in service.list_authors()}
    assert full_name in names


@when("I request book availability")
def step_availability(context):
    context.availability = service.list_book_availability()


@then('"{title}" has {total:d} total copies and {available:d} available copy')
def step_availability_counts(context, title, total, available):
    record = next(item for item in context.availability if item["title"] == title)
    assert record["total_copies"] == total
    assert record["available_copies"] == available


@then('availability search for "{term}" returns {count:d} book')
def step_availability_search(context, term, count):
    assert len(service.list_book_availability(search=term)) == count


@when('I search members for "{term}"')
def step_search_members(context, term):
    context.members = service.list_members(search=term)


@when("I search members using the saved member ID")
def step_search_member_id(context):
    context.members = service.list_members(search=str(context.saved_member_id))


@then('{count:d} member is returned with email "{email}"')
def step_member_result(context, count, email):
    assert len(context.members) == count
    assert context.members[0].email == email


@when('"{email}" borrows the book for {days:d} days')
def step_borrow_for_email(context, email, days):
    context.email = email
    context.borrow = service.borrow_copy_for_member_email(
        email=email,
        full_name="New Reader",
        copy_id=None,
        book_id=context.book.book_id,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=days),
    )


@then('a member record exists for "{email}"')
def step_member_linked(context, email):
    with SessionLocal() as session:
        assert session.scalar(select(Member).where(Member.email == email)) is not None


@then('the selected copy status is "{status}"')
def step_selected_copy_status(context, status):
    assert _copy_status(context.copy_id) == status


@then('that member has {count:d} loan with status "{status}"')
def step_member_history(context, count, status):
    history = service.get_borrow_history_for_member_email(context.email)
    assert len(history) == count
    assert history[0]["status"] == status


@when("I try to borrow with a due date before the borrow date")
def step_invalid_dates(context):
    _remember_failure(
        context,
        lambda: service.borrow_copy_for_member_email(
            "dates@test.local", None, date.today(), date.today() - timedelta(days=1), book_id=context.book.book_id
        ),
    )


@when("I try to borrow the unavailable book")
def step_unavailable(context):
    _remember_failure(
        context,
        lambda: service.borrow_copy_for_member_email(
            "unavailable@test.local", None, date.today(), date.today() + timedelta(days=7), book_id=context.book.book_id
        ),
    )


@then('the operation fails with "{message}"')
def step_failure(context, message):
    assert context.failure is not None, "Expected a LibraryError"
    assert message.lower() in context.failure.message.lower()


def _create_loan(context, email: str, due_days_ago=None):
    context.book = _create_book("Loan Book", f"ISBN-LOAN-{email}")
    copy = service.create_book_copy(context.book.book_id, f"COPY-{email}", "B1", "available")
    context.copy_id = copy.copy_id
    due_date = date.today() + timedelta(days=7) if due_days_ago is None else date.today() - timedelta(days=due_days_ago)
    context.email = email
    context.borrow = service.borrow_copy_for_member_email(
        email, copy.copy_id, date.today() - timedelta(days=10), due_date, full_name="Loan Owner"
    )


@given('an overdue loan for "{email}" that was due {days:d} days ago')
def step_overdue_loan(context, email, days):
    _create_loan(context, email, days)


@given('an active loan for "{email}"')
def step_active_loan(context, email):
    _create_loan(context, email)


@when('I request borrow history for "{email}"')
def step_request_history(context, email):
    context.history = service.get_borrow_history_for_member_email(email)


@then('the loan status is "{status}"')
def step_loan_status(context, status):
    assert context.history[0]["status"] == status


@then('the loan has {days:d} overdue days and a fine of {fine:f}')
def step_overdue_fine(context, days, fine):
    assert context.history[0]["overdue_days"] == days
    assert context.history[0]["fine_amount"] == fine


@when('"{email}" returns the loan')
def step_return(context, email):
    context.borrow = service.return_borrow_for_member_email(email, context.borrow.borrow_id)


@when('"{email}" clears the loan fine')
def step_clear_fine(context, email):
    context.borrow = service.clear_fine_for_member_email(email, context.borrow.borrow_id)


@then('the returned loan has a fine of {fine:f}')
def step_returned_fine(context, fine):
    history = service.get_borrow_history_for_member_email(context.email)
    assert history[0]["status"] == "returned"
    assert history[0]["fine_amount"] == fine


@when('"{email}" tries to return the loan')
def step_wrong_return(context, email):
    service.create_member("Other", "Member", email, membership_date=date.today())
    _remember_failure(context, lambda: service.return_borrow_for_member_email(email, context.borrow.borrow_id))


@given('I am logged in through HTTP as "{email}" with password "{password}"')
def step_http_login(context, email, password):
    response = client.post("/token", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    context.headers = {"Authorization": f"Bearer {response.json()['access_token']}"}


@when("I try to create an author through HTTP")
def step_http_create_author(context):
    context.response = client.post(
        "/authors", json={"first_name": "HTTP", "last_name": "Author"}, headers=context.headers
    )


@when("I request books through HTTP without a token")
def step_http_books_unauthorized(context):
    context.response = client.get("/books")


@then("the HTTP response status is {status:d}")
def step_http_status(context, status):
    assert context.response.status_code == status, context.response.text


@when("I borrow the saved book through HTTP")
def step_http_borrow(context):
    context.response = client.post(
        "/borrow",
        json={
            "book_id": context.book.book_id,
            "borrow_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
        },
        headers=context.headers,
    )
    if context.response.status_code == 200:
        context.http_borrow_id = context.response.json()["borrow_id"]


@then("my HTTP borrow history contains {count:d} loan")
def step_http_history(context, count):
    response = client.get("/me/borrows", headers=context.headers)
    assert response.status_code == 200, response.text
    assert len(response.json()) == count


@when("I return that loan through HTTP")
def step_http_return(context):
    context.response = client.post(
        f"/me/borrows/{context.http_borrow_id}/return", headers=context.headers
    )


@when('I try to create another book with ISBN "{isbn}"')
def step_duplicate_book(context, isbn):
    _remember_failure(context, lambda: _create_book("Duplicate Book", isbn, context.author.author_id))


@when("I request a missing book")
def step_missing_book(context):
    _remember_failure(context, lambda: service.get_book(999999))

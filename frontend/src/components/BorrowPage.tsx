import { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import RoleGuard from './RoleGuard';

interface BookSearchResult {
  book_id: number;
  title: string;
  isbn: string;
  total_copies: number;
  available_copies: number;
}

export default function BorrowPage() {
  const [bookId, setBookId] = useState<number>(0);
  const [bookSearch, setBookSearch] = useState('');
  const [bookResults, setBookResults] = useState<BookSearchResult[]>([]);
  const [searchingBooks, setSearchingBooks] = useState(false);
  const [bookSearchOpen, setBookSearchOpen] = useState(false);
  const [borrowDate, setBorrowDate] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [remarks, setRemarks] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const query = bookSearch.trim();
    if (bookId) {
      return;
    }
    if (query.length < 2) {
      setBookResults([]);
      setSearchingBooks(false);
      return;
    }

    let isActive = true;
    const timeoutId = window.setTimeout(async () => {
      setSearchingBooks(true);
      try {
        const results = await apiFetch<BookSearchResult[]>(`/books/availability?search=${encodeURIComponent(query)}`);
        if (isActive) {
          setBookResults(results);
          setBookSearchOpen(true);
        }
      } catch (err) {
        if (isActive) {
          setMessage(err instanceof Error ? err.message : 'Unable to search books.');
        }
      } finally {
        if (isActive) {
          setSearchingBooks(false);
        }
      }
    }, 300);

    return () => {
      isActive = false;
      window.clearTimeout(timeoutId);
    };
  }, [bookSearch, bookId]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);

    if (!bookId) {
      setMessage('Search for a title and select a matching book.');
      return;
    }

    try {
      await apiFetch('/borrow', {
        method: 'POST',
        body: JSON.stringify({
          book_id: bookId,
          borrow_date: borrowDate,
          due_date: dueDate,
          remarks,
        }),
      });
      setMessage('Borrow request submitted successfully.');
      setBookId(0);
      setBookSearch('');
      setBookResults([]);
      setBookSearchOpen(false);
      setBorrowDate('');
      setDueDate('');
      setRemarks('');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to borrow copy.');
    }
  };

  return (
    <RoleGuard allowedRoles={['member', 'librarian', 'admin']}>
      <main className="page-shell">
        <section className="page-header">
          <h1>Borrowing</h1>
          <p>Submit a borrow request using the library API.</p>
        </section>

        {message && <div className="error-panel">{message}</div>}

        <section className="table-card">
          <h2>Borrow a copy</h2>
          <form onSubmit={handleSubmit} className="form-grid">
            <label className="book-autocomplete">
              Search book by title
              <input
                type="search"
                value={bookSearch}
                placeholder="Enter at least 2 characters"
                autoComplete="off"
                role="combobox"
                aria-autocomplete="list"
                aria-expanded={bookSearchOpen}
                aria-controls="book-search-results"
                onChange={e => {
                  setBookSearch(e.target.value);
                  setBookId(0);
                  setBookSearchOpen(true);
                }}
                onFocus={() => {
                  if (bookSearch.trim().length >= 2 && !bookId) {
                    setBookSearchOpen(true);
                  }
                }}
                onBlur={() => window.setTimeout(() => setBookSearchOpen(false), 150)}
                required
              />
              {bookSearchOpen && bookSearch.trim().length >= 2 && (
                <div id="book-search-results" className="autocomplete-menu" role="listbox">
                  {searchingBooks ? (
                    <div className="autocomplete-message">Searching books…</div>
                  ) : bookResults.length > 0 ? (
                    bookResults.map(book => (
                      <button
                        key={book.book_id}
                        type="button"
                        className="autocomplete-option"
                        role="option"
                        aria-selected={book.book_id === bookId}
                        aria-disabled={book.available_copies === 0}
                        disabled={book.available_copies === 0}
                        onMouseDown={event => event.preventDefault()}
                        onClick={() => {
                          setBookId(book.book_id);
                          setBookSearch(book.title);
                          setBookSearchOpen(false);
                        }}
                      >
                        <span>{book.title}</span>
                        <small className="book-result-meta">
                          <span>ISBN: {book.isbn}</span>
                          <span className={book.available_copies > 0 ? 'result-availability' : 'result-availability none'}>
                            {book.available_copies} available
                          </span>
                        </small>
                      </button>
                    ))
                  ) : (
                    <div className="autocomplete-message">No matching books found.</div>
                  )}
                </div>
              )}
            </label>
            <label>
              Borrow date
              <input
                type="date"
                value={borrowDate}
                onChange={e => setBorrowDate(e.target.value)}
                required
              />
            </label>
            <label>
              Due date
              <input
                type="date"
                value={dueDate}
                onChange={e => setDueDate(e.target.value)}
                required
              />
            </label>
            <label>
              Remarks
              <input value={remarks} onChange={e => setRemarks(e.target.value)} />
            </label>
            <button type="submit" className="primary-button">
              Submit borrow
            </button>
          </form>
        </section>
      </main>
    </RoleGuard>
  );
}

import { useCallback, useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import RoleGuard from './RoleGuard';

interface BookSearchResult {
  book_id: number;
  title: string;
  isbn: string;
}

interface BookAvailability {
  book_id: number;
  title: string;
  isbn: string;
  total_copies: number;
  available_copies: number;
}

export default function CopiesPage() {
  const [bookId, setBookId] = useState<number>(0);
  const [bookSearch, setBookSearch] = useState('');
  const [bookResults, setBookResults] = useState<BookSearchResult[]>([]);
  const [searchingBooks, setSearchingBooks] = useState(false);
  const [bookSearchOpen, setBookSearchOpen] = useState(false);
  const [barcode, setBarcode] = useState('');
  const [shelfLocation, setShelfLocation] = useState('');
  const [status, setStatus] = useState('available');
  const [message, setMessage] = useState<string | null>(null);
  const [bookAvailability, setBookAvailability] = useState<BookAvailability[]>([]);
  const [loadingAvailability, setLoadingAvailability] = useState(true);

  const loadAvailability = useCallback(async () => {
    setLoadingAvailability(true);
    try {
      setBookAvailability(await apiFetch<BookAvailability[]>('/books/availability'));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load copy availability.');
    } finally {
      setLoadingAvailability(false);
    }
  }, []);

  useEffect(() => {
    void loadAvailability();
  }, [loadAvailability]);

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
        const results = await apiFetch<BookSearchResult[]>(`/books?search=${encodeURIComponent(query)}`);
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
      await apiFetch('/copies', {
        method: 'POST',
        body: JSON.stringify({ book_id: bookId, barcode, shelf_location: shelfLocation, status }),
      });
      setMessage('Book copy created successfully.');
      setBookId(0);
      setBookSearch('');
      setBookResults([]);
      setBookSearchOpen(false);
      setBarcode('');
      setShelfLocation('');
      setStatus('available');
      await loadAvailability();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to create copy.');
    }
  };

  return (
    <RoleGuard allowedRoles={['librarian', 'admin']}>
      <main className="page-shell">
        <section className="page-header">
          <h1>Book Copies</h1>
          <p>Register individual book copies for inventory tracking.</p>
        </section>

        {message && <div className="error-panel">{message}</div>}

        <section className="table-card">
          <h2>Create a new copy</h2>
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
                aria-controls="copy-book-search-results"
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
                <div id="copy-book-search-results" className="autocomplete-menu" role="listbox">
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
                        onMouseDown={event => event.preventDefault()}
                        onClick={() => {
                          setBookId(book.book_id);
                          setBookSearch(book.title);
                          setBookSearchOpen(false);
                        }}
                      >
                        <span>{book.title}</span>
                        <small>ISBN: {book.isbn}</small>
                      </button>
                    ))
                  ) : (
                    <div className="autocomplete-message">No matching books found.</div>
                  )}
                </div>
              )}
            </label>
            <label>
              Barcode
              <input
                value={barcode}
                onChange={e => setBarcode(e.target.value)}
                required
              />
            </label>
            <label>
              Shelf location
              <input
                value={shelfLocation}
                onChange={e => setShelfLocation(e.target.value)}
              />
            </label>
            <fieldset className="status-picker">
              <legend>Status</legend>
              <div className="status-options">
                {[
                  { value: 'available', label: 'Available' },
                  { value: 'checked_out', label: 'Checked out' },
                  { value: 'maintenance', label: 'Maintenance' },
                ].map(option => (
                  <button
                    key={option.value}
                    type="button"
                    className={`status-option status-option-${option.value} ${status === option.value ? 'selected' : ''}`}
                    aria-pressed={status === option.value}
                    onClick={() => setStatus(option.value)}
                  >
                    <span className="status-dot" />
                    {option.label}
                  </button>
                ))}
              </div>
            </fieldset>
            <button type="submit" className="primary-button">
              Create copy
            </button>
          </form>
        </section>

        <section className="table-card availability-section">
          <div className="section-heading-row">
            <div>
              <h2>Available copies by book</h2>
              <p>Current titles and the number of copies available for borrowing.</p>
            </div>
            <span className="record-count">{bookAvailability.length} books</span>
          </div>

          {loadingAvailability ? (
            <p className="dashboard-note">Loading availability…</p>
          ) : bookAvailability.length === 0 ? (
            <p className="dashboard-note">No books have been added yet.</p>
          ) : (
            <div className="availability-scroll-list">
              {bookAvailability.map(book => (
                <div key={book.book_id} className="availability-list-item">
                  <div>
                    <strong>
                      {book.title}
                      <span className="copy-counts-inline">
                        <span className="total-copy-count">Total: {book.total_copies}</span>
                        <span className={book.available_copies > 0 ? 'availability-count' : 'availability-count none'}>
                          Available: {book.available_copies}
                        </span>
                      </span>
                    </strong>
                    <small>ISBN: {book.isbn}</small>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </RoleGuard>
  );
}

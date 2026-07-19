import { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import RoleGuard from './RoleGuard';

interface BookRecord {
  book_id: number;
  title: string;
  isbn: string;
  category: string;
  publisher: string;
  publish_year: number;
}

interface AuthorRecord {
  author_id: number;
  first_name: string;
  last_name: string;
}

export default function BooksPage() {
  const [searchParams] = useSearchParams();
  const authorId = searchParams.get('author_id');
  const [books, setBooks] = useState<BookRecord[]>([]);
  const [authors, setAuthors] = useState<AuthorRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [selectedAuthorId, setSelectedAuthorId] = useState(0);
  const [authorSearch, setAuthorSearch] = useState('');
  const [authorSearchOpen, setAuthorSearchOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [isbn, setIsbn] = useState('');
  const [category, setCategory] = useState('');
  const [publisher, setPublisher] = useState('');
  const [publishYear, setPublishYear] = useState('');
  const [language, setLanguage] = useState('');
  const [pages, setPages] = useState('');
  const matchingAuthors = authorSearch.trim()
    ? authors.filter(author =>
        `${author.first_name} ${author.last_name}`.toLowerCase().includes(authorSearch.trim().toLowerCase())
      )
    : authors;

  const loadBooks = useCallback(async () => {
    const path = authorId ? `/books?author_id=${encodeURIComponent(authorId)}` : '/books';
    try {
      setBooks(await apiFetch<BookRecord[]>(path));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load books.');
    }
  }, [authorId]);

  useEffect(() => {
    void loadBooks();
    apiFetch<AuthorRecord[]>('/authors')
      .then(setAuthors)
      .catch(err => setError(err instanceof Error ? err.message : 'Unable to load authors.'));
  }, [loadBooks]);

  const handleCreateBook = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);

    if (!selectedAuthorId) {
      setMessage('Search for an author and select a matching result.');
      return;
    }

    try {
      await apiFetch('/books', {
        method: 'POST',
        body: JSON.stringify({
          author_id: selectedAuthorId,
          title,
          isbn,
          category: category || null,
          publisher: publisher || null,
          publish_year: publishYear ? Number(publishYear) : null,
          language: language || null,
          pages: pages ? Number(pages) : null,
        }),
      });
      setMessage('Book created successfully.');
      setSelectedAuthorId(0);
      setAuthorSearch('');
      setAuthorSearchOpen(false);
      setTitle('');
      setIsbn('');
      setCategory('');
      setPublisher('');
      setPublishYear('');
      setLanguage('');
      setPages('');
      await loadBooks();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to create book.');
    }
  };

  return (
    <main className="page-shell">
      <section className="page-header">
        <h1>Books</h1>
        <p>{authorId ? 'Showing books for the selected author.' : 'Browse the catalog or create a new book if your role allows it.'}</p>
        {authorId && <Link to="/books" className="clear-filter-link">View all books</Link>}
      </section>

      {error && <div className="error-panel">{error}</div>}

      <RoleGuard allowedRoles={['librarian', 'admin']} fallback={<></>}>
        <section className="table-card book-create-section">
          <h2>Create a new book</h2>
          <p>Add the catalog record first; physical copies can then be registered from the Copies screen.</p>
          {message && <div className="form-message">{message}</div>}
          <form onSubmit={handleCreateBook} className="form-grid book-form-grid">
            <label className="book-autocomplete">
              Search author by name
              <input
                type="search"
                value={authorSearch}
                placeholder="Enter author name"
                autoComplete="off"
                role="combobox"
                aria-autocomplete="list"
                aria-expanded={authorSearchOpen}
                aria-controls="author-search-results"
                onChange={event => {
                  setAuthorSearch(event.target.value);
                  setSelectedAuthorId(0);
                  setAuthorSearchOpen(true);
                }}
                onFocus={() => setAuthorSearchOpen(true)}
                onBlur={() => window.setTimeout(() => setAuthorSearchOpen(false), 150)}
                required
              />
              {authorSearchOpen && (
                <div id="author-search-results" className="autocomplete-menu" role="listbox">
                  {matchingAuthors.length > 0 ? (
                    matchingAuthors.map(author => (
                      <button
                        key={author.author_id}
                        type="button"
                        className="autocomplete-option"
                        role="option"
                        aria-selected={author.author_id === selectedAuthorId}
                        onMouseDown={event => event.preventDefault()}
                        onClick={() => {
                          setSelectedAuthorId(author.author_id);
                          setAuthorSearch(`${author.first_name} ${author.last_name}`);
                          setAuthorSearchOpen(false);
                        }}
                      >
                        <span>{author.first_name} {author.last_name}</span>
                        <small>Author ID: {author.author_id}</small>
                      </button>
                    ))
                  ) : (
                    <div className="autocomplete-message">No matching authors found.</div>
                  )}
                </div>
              )}
            </label>
            <label>
              Title
              <input value={title} onChange={event => setTitle(event.target.value)} required />
            </label>
            <label>
              ISBN
              <input value={isbn} onChange={event => setIsbn(event.target.value)} required />
            </label>
            <label>
              Category
              <input value={category} onChange={event => setCategory(event.target.value)} />
            </label>
            <label>
              Publisher
              <input value={publisher} onChange={event => setPublisher(event.target.value)} />
            </label>
            <label>
              Publication year
              <input type="number" min="0" value={publishYear} onChange={event => setPublishYear(event.target.value)} />
            </label>
            <label>
              Language
              <input value={language} onChange={event => setLanguage(event.target.value)} />
            </label>
            <label>
              Pages
              <input type="number" min="1" value={pages} onChange={event => setPages(event.target.value)} />
            </label>
            <button type="submit" className="primary-button">Create book</button>
          </form>
        </section>
      </RoleGuard>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>ISBN</th>
              <th>Category</th>
              <th>Publisher</th>
              <th>Year</th>
            </tr>
          </thead>
          <tbody>
            {books.length === 0 && (
              <tr>
                <td colSpan={6}>No books found for this author.</td>
              </tr>
            )}
            {books.map(book => (
              <tr key={book.book_id}>
                <td>{book.book_id}</td>
                <td>{book.title}</td>
                <td>{book.isbn}</td>
                <td>{book.category}</td>
                <td>{book.publisher}</td>
                <td>{book.publish_year}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

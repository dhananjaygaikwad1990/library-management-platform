import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import RoleGuard from './RoleGuard';

interface AuthorRecord {
  author_id: number;
  first_name: string;
  last_name: string;
  biography: string | null;
}

interface BookRecord {
  book_id: number;
  author_id: number;
  title: string;
}

export default function AuthorsPage() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [biography, setBiography] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [authors, setAuthors] = useState<AuthorRecord[]>([]);
  const [books, setBooks] = useState<BookRecord[]>([]);
  const [loadingList, setLoadingList] = useState(true);

  const loadAuthorsAndBooks = useCallback(async () => {
    setLoadingList(true);
    try {
      const [authorResults, bookResults] = await Promise.all([
        apiFetch<AuthorRecord[]>('/authors'),
        apiFetch<BookRecord[]>('/books'),
      ]);
      setAuthors(authorResults);
      setBooks(bookResults);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Unable to load authors.');
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => {
    void loadAuthorsAndBooks();
  }, [loadAuthorsAndBooks]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setStatus(null);

    try {
      await apiFetch('/authors', {
        method: 'POST',
        body: JSON.stringify({ first_name: firstName, last_name: lastName, biography }),
      });
      setStatus('Author created successfully.');
      setFirstName('');
      setLastName('');
      setBiography('');
      await loadAuthorsAndBooks();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Unable to create author.');
    }
  };

  return (
    <RoleGuard allowedRoles={['librarian', 'admin']}>
      <main className="page-shell">
        <section className="page-header">
          <h1>Authors</h1>
          <p>Only librarians and administrators may create and manage authors.</p>
        </section>

        {status && <div className="error-panel">{status}</div>}

        <section className="table-card">
          <h2>Create a new author</h2>
          <form onSubmit={handleSubmit} className="form-grid">
            <label>
              First name
              <input value={firstName} onChange={e => setFirstName(e.target.value)} required />
            </label>
            <label>
              Last name
              <input value={lastName} onChange={e => setLastName(e.target.value)} required />
            </label>
            <label>
              Biography
              <textarea value={biography} onChange={e => setBiography(e.target.value)} rows={4} />
            </label>
            <button type="submit" className="primary-button">
              Create author
            </button>
          </form>
        </section>

        <section className="table-card author-list-section">
          <div className="section-heading-row">
            <div>
              <h2>Authors and books</h2>
              <p>Browse registered authors and titles currently linked to them.</p>
            </div>
            <span className="record-count">{authors.length} authors</span>
          </div>

          {loadingList ? (
            <p className="dashboard-note">Loading authors…</p>
          ) : authors.length === 0 ? (
            <p className="dashboard-note">No authors have been added yet.</p>
          ) : (
            <div className="author-scroll-list">
              {authors.map(author => {
                const authorBooks = books.filter(book => book.author_id === author.author_id);
                return (
                  <article key={author.author_id} className="author-list-item">
                    <div className="author-details">
                      <h3>{author.first_name} {author.last_name}</h3>
                      {author.biography && <p>{author.biography}</p>}
                    </div>
                    <div className="author-books">
                      <Link
                        to={`/books?author_id=${author.author_id}`}
                        className="author-books-label author-books-link"
                      >
                        Books ({authorBooks.length})
                      </Link>
                      {authorBooks.length > 0 ? (
                        <ul>
                          {authorBooks.map(book => <li key={book.book_id}>{book.title}</li>)}
                        </ul>
                      ) : (
                        <span className="empty-value">No books linked</span>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </RoleGuard>
  );
}

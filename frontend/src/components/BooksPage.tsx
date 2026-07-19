import { useEffect, useState } from 'react';
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

export default function BooksPage() {
  const [searchParams] = useSearchParams();
  const authorId = searchParams.get('author_id');
  const [books, setBooks] = useState<BookRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const path = authorId ? `/books?author_id=${encodeURIComponent(authorId)}` : '/books';
    apiFetch<BookRecord[]>(path)
      .then(setBooks)
      .catch(err => setError(err.message));
  }, [authorId]);

  return (
    <main className="page-shell">
      <section className="page-header">
        <h1>Books</h1>
        <p>{authorId ? 'Showing books for the selected author.' : 'Browse the catalog or create a new book if your role allows it.'}</p>
        {authorId && <Link to="/books" className="clear-filter-link">View all books</Link>}
      </section>

      {error && <div className="error-panel">{error}</div>}

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

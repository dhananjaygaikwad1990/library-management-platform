import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getSession } from '../lib/auth';
import { apiFetch } from '../lib/api';

interface BorrowSummary {
  borrow_id: number;
  book_title: string;
  book_author: string;
  borrow_date: string;
  due_date: string;
  return_date: string | null;
  fine_amount: number;
  overdue_days: number;
  status: string;
}

export default function DashboardPage() {
  const session = getSession();
  const isStudent = session?.roles.includes('student') ?? false;
  const canViewLoans = session !== null;
  const [borrows, setBorrows] = useState<BorrowSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingBorrowId, setProcessingBorrowId] = useState<number | null>(null);
  const [refreshVersion, setRefreshVersion] = useState(0);
  const activeBorrows = borrows.filter(item => item.status !== 'returned');
  const overdueBorrows = activeBorrows.filter(item => item.status === 'overdue');
  const totalFines = borrows.reduce((total, item) => total + item.fine_amount, 0);

  useEffect(() => {
    if (!canViewLoans) {
      return;
    }

    let isActive = true;

    const loadBorrows = async () => {
      setLoading(true);
      try {
        const result = await apiFetch<BorrowSummary[]>('/me/borrows');
        if (isActive) {
          setBorrows(result);
          setError(null);
        }
      } catch (err) {
        if (isActive) {
          setError(err instanceof Error ? err.message : 'Unable to load borrow records.');
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    };

    void loadBorrows();
    const intervalId = window.setInterval(() => {
      void loadBorrows();
    }, 60_000);

    return () => {
      isActive = false;
      window.clearInterval(intervalId);
    };
  }, [canViewLoans, refreshVersion]);

  const runBorrowAction = async (borrowId: number, action: 'return' | 'clear-fine') => {
    setProcessingBorrowId(borrowId);
    setError(null);
    try {
      await apiFetch(`/me/borrows/${borrowId}/${action}`, { method: 'POST' });
      setRefreshVersion(version => version + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update the borrow record.');
    } finally {
      setProcessingBorrowId(null);
    }
  };


  return (
    <main className="page-shell">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Welcome back</p>
          <h1>Library Dashboard</h1>
          <p className="intro">
            {isStudent
              ? 'Review your current loans and due dates. Keep your account in good standing by returning books on time.'
              : 'Track library activity, manage resources, and stay on top of key actions for your role.'}
          </p>

          <div className="dashboard-summary">
            {canViewLoans ? (
              <>
                <div className="summary-card-grid">
                  <div className="summary-card">
                    <span className="summary-label">Current loans</span>
                    <span className="summary-value">{activeBorrows.length}</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Overdue</span>
                    <span className="summary-value">{overdueBorrows.length}</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Total fines</span>
                    <span className="summary-value">{totalFines.toFixed(2)}</span>
                  </div>
                </div>
                {loading && <p className="dashboard-note">Loading your current loans…</p>}
                {error && <div className="error-panel">{error}</div>}
                {!loading && !error && borrows.length === 0 && (
                  <p className="dashboard-note">You have no active borrow records at this time.</p>
                )}
                {borrows.length > 0 && (
                  <div className="dashboard-table-card">
                    <table className="dashboard-table">
                      <thead>
                        <tr>
                          <th>Title</th>
                          <th>Author</th>
                          <th>Borrowed</th>
                          <th>Due</th>
                          <th>Status</th>
                          <th>Overdue</th>
                          <th>Fine</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {borrows.map(item => (
                          <tr key={item.borrow_id}>
                            <td>{item.book_title}</td>
                            <td>{item.book_author}</td>
                            <td>{item.borrow_date}</td>
                            <td>{item.due_date}</td>
                            <td><span className={`loan-status loan-status-${item.status.replace(' ', '-')}`}>{item.status}</span></td>
                            <td>{item.overdue_days > 0 ? `${item.overdue_days} day${item.overdue_days === 1 ? '' : 's'}` : '—'}</td>
                            <td>{item.fine_amount.toFixed(2)}</td>
                            <td>
                              {item.status !== 'returned' && (
                                <button
                                  type="button"
                                  className="table-action-button"
                                  disabled={processingBorrowId === item.borrow_id}
                                  onClick={() => void runBorrowAction(item.borrow_id, 'return')}
                                >
                                  {processingBorrowId === item.borrow_id ? 'Returning…' : 'Return copy'}
                                </button>
                              )}
                              {item.status === 'returned' && item.fine_amount > 0 && (
                                <button
                                  type="button"
                                  className="table-action-button fine-button"
                                  disabled={processingBorrowId === item.borrow_id}
                                  onClick={() => void runBorrowAction(item.borrow_id, 'clear-fine')}
                                >
                                  {processingBorrowId === item.borrow_id ? 'Clearing…' : 'Clear fine'}
                                </button>
                              )}
                              {item.status === 'returned' && item.fine_amount === 0 && '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            ) : (
              <p className="dashboard-note">
                The library system is ready for your next action. Use the navigation on the left to manage books, members, copies, and borrowing.
              </p>
            )}
          </div>
        </div>

      </section>

      <section className="grid-panel">
        <Link to="/authors" className="nav-card">
          <h2>Authors</h2>
          <p>Create and manage library authors.</p>
        </Link>

        <Link to="/books" className="nav-card">
          <h2>Books</h2>
          <p>View the book catalog or add new titles.</p>
        </Link>

        <Link to="/copies" className="nav-card">
          <h2>Book Copies</h2>
          <p>Track individual book copies and availability.</p>
        </Link>

        <Link to="/members" className="nav-card">
          <h2>Members</h2>
          <p>Manage library members and memberships.</p>
        </Link>

        <Link to="/borrow" className="nav-card">
          <h2>Borrowing</h2>
          <p>Borrow a copy or review loan status.</p>
        </Link>
      </section>
    </main>
  );
}

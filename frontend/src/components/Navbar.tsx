import { Link } from 'react-router-dom';
import { getSession } from '../lib/auth';

export default function Navbar() {
  const session = getSession();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo">📚</div>
        <div>
          <div className="brand-title">Library Portal</div>
          <div className="brand-tag">Secure access</div>
        </div>
      </div>

      {session ? (
        <nav className="sidebar-nav">
          <Link to="/dashboard" className="sidebar-link">
            <span className="menu-icon">🏠</span>
            Dashboard
          </Link>
          <Link to="/authors" className="sidebar-link">
            <span className="menu-icon">🖊️</span>
            Authors
          </Link>
          <Link to="/books" className="sidebar-link">
            <span className="menu-icon">📚</span>
            Books
          </Link>
          <Link to="/copies" className="sidebar-link">
            <span className="menu-icon">📦</span>
            Copies
          </Link>
          <Link to="/members" className="sidebar-link">
            <span className="menu-icon">👥</span>
            Members
          </Link>
          <Link to="/borrow" className="sidebar-link">
            <span className="menu-icon">🔄</span>
            Borrow
          </Link>
        </nav>
      ) : null}
    </aside>
  );
}

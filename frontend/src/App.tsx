import { useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import DashboardPage from './components/DashboardPage';
import AuthorsPage from './components/AuthorsPage';
import BooksPage from './components/BooksPage';
import CopiesPage from './components/CopiesPage';
import MembersPage from './components/MembersPage';
import BorrowPage from './components/BorrowPage';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import { getSession, logout } from './lib/auth';
import './styles.css';

export default function App() {
  const session = getSession();
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    setProfileOpen(false);
    navigate('/login');
  };

  return (
    <div className="app-shell">
      <Navbar />
      <div className="content-area">
        {session && (
          <header className="topbar">
            <div>
              <p className="topbar-title">Library operations</p>
              <p className="topbar-subtitle">Welcome to your secure library workspace.</p>
            </div>
            <div className="user-menu">
              <button
                type="button"
                className="user-avatar-button"
                onClick={() => setProfileOpen(value => !value)}
              >
                <span className="user-avatar">👤</span>
              </button>
              <div className={`user-menu-panel ${profileOpen ? 'open' : ''}`}>
                <div className="user-menu-header">
                  <div className="user-menu-label">Signed in as</div>
                  <div className="user-menu-email">{session.email}</div>
                </div>
                <div className="user-menu-info">Roles: {session.roles.join(', ')}</div>
                <button onClick={handleLogout} className="secondary-button logout-button">
                  Sign out
                </button>
              </div>
            </div>
          </header>
        )}

        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/authors" element={<ProtectedRoute><AuthorsPage /></ProtectedRoute>} />
          <Route path="/books" element={<ProtectedRoute><BooksPage /></ProtectedRoute>} />
          <Route path="/copies" element={<ProtectedRoute><CopiesPage /></ProtectedRoute>} />
          <Route path="/members" element={<ProtectedRoute><MembersPage /></ProtectedRoute>} />
          <Route path="/borrow" element={<ProtectedRoute><BorrowPage /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </div>
  );
}

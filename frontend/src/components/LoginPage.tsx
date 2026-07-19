import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../lib/auth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    try {
      await login({ email, password });
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <main className="page-shell">
      <section className="card auth-card">
        <h1>Library Portal</h1>
        <p>Sign in with your credentials to access the library dashboard.</p>

        <form onSubmit={handleSubmit} className="form-grid">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoFocus
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </label>

          {error && <div className="error-panel">{error}</div>}

          <button type="submit" className="primary-button">
            Sign in
          </button>
        </form>
      </section>
    </main>
  );
}

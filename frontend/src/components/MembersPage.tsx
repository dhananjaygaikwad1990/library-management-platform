import { useCallback, useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';
import RoleGuard from './RoleGuard';

interface MemberRecord {
  member_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  membership_date: string;
  status: string;
}

export default function MembersPage() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [membershipDate, setMembershipDate] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [members, setMembers] = useState<MemberRecord[]>([]);
  const [memberSearch, setMemberSearch] = useState('');
  const [loadingMembers, setLoadingMembers] = useState(false);

  const loadMembers = useCallback(async (search: string) => {
    setLoadingMembers(true);
    try {
      const query = search.trim();
      const path = query ? `/members?search=${encodeURIComponent(query)}` : '/members';
      setMembers(await apiFetch<MemberRecord[]>(path));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load members.');
    } finally {
      setLoadingMembers(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadMembers(memberSearch);
    }, 300);
    return () => window.clearTimeout(timeoutId);
  }, [memberSearch, loadMembers]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);

    try {
      await apiFetch('/members', {
        method: 'POST',
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email,
          phone,
          address,
          membership_date: membershipDate,
        }),
      });
      setMessage('Member created successfully.');
      setFirstName('');
      setLastName('');
      setEmail('');
      setPhone('');
      setAddress('');
      setMembershipDate('');
      await loadMembers(memberSearch);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to create member.');
    }
  };

  return (
    <RoleGuard allowedRoles={['librarian', 'admin']}>
      <main className="page-shell">
        <section className="page-header">
          <h1>Members</h1>
          <p>Create and manage member records for the library.</p>
        </section>

        {message && <div className="error-panel">{message}</div>}

        <section className="table-card">
          <h2>Create a new member</h2>
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
              Email
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
            </label>
            <label>
              Phone
              <input value={phone} onChange={e => setPhone(e.target.value)} />
            </label>
            <label>
              Address
              <input value={address} onChange={e => setAddress(e.target.value)} />
            </label>
            <label>
              Membership date
              <input
                type="date"
                value={membershipDate}
                onChange={e => setMembershipDate(e.target.value)}
              />
            </label>
            <button type="submit" className="primary-button">
              Create member
            </button>
          </form>
        </section>

        <section className="table-card member-directory">
          <div className="section-heading-row">
            <div>
              <h2>Member directory</h2>
              <p>Search by member name or exact member ID.</p>
            </div>
            <span className="record-count">{members.length} members</span>
          </div>

          <label className="member-search-field">
            Search members
            <input
              type="search"
              value={memberSearch}
              placeholder="Enter a name or member ID"
              onChange={event => setMemberSearch(event.target.value)}
            />
          </label>

          {loadingMembers ? (
            <p className="dashboard-note">Searching members…</p>
          ) : (
            <div className="member-scroll-list">
              <table>
                <thead>
                  <tr>
                    <th>Member ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Joined</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {members.length === 0 && (
                    <tr><td colSpan={6}>No matching members found.</td></tr>
                  )}
                  {members.map(member => (
                    <tr key={member.member_id}>
                      <td>{member.member_id}</td>
                      <td>{member.first_name} {member.last_name}</td>
                      <td>{member.email}</td>
                      <td>{member.phone || '—'}</td>
                      <td>{member.membership_date}</td>
                      <td>{member.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </RoleGuard>
  );
}

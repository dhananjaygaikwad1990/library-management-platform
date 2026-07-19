import { ReactNode } from 'react';
import { getSession } from '../lib/auth';

interface RoleGuardProps {
  allowedRoles: string[];
  fallback?: ReactNode;
  children: ReactNode;
}

export default function RoleGuard({ allowedRoles, fallback, children }: RoleGuardProps) {
  const session = getSession();
  const isAllowed = session?.roles.some(role => allowedRoles.includes(role));

  if (!session) {
    return <>{fallback ?? <p className="error">Please log in to view this page.</p>}</>;
  }

  if (!isAllowed) {
    return <div className="error-panel">
      <h2>Access denied</h2>
      <p>You do not have permission to view this page.</p>
    </div>;
  }

  return <>{children}</>;
}

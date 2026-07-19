import { Navigate } from 'react-router-dom';
import { getSession } from '../lib/auth';

interface ProtectedRouteProps {
  children: JSX.Element;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const session = getSession();
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

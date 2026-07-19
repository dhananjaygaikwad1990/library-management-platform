export type RoleName = 'admin' | 'librarian' | 'student' | 'visitor';

export interface UserSession {
  accessToken: string;
  roles: RoleName[];
  email: string;
}

export interface LoginForm {
  email: string;
  password: string;
}

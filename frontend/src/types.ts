export type RoleName = 'admin' | 'librarian' | 'member' | 'visitor';

export interface UserSession {
  accessToken: string;
  roles: RoleName[];
  email: string;
}

export interface LoginForm {
  email: string;
  password: string;
}

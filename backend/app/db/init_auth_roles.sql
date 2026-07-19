-- app/db/init_auth_roles.sql
-- Initial PostgreSQL auth schema and seed data for users, roles, and role assignments.

-- Enable pgcrypto for password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Role definitions used by the application
CREATE TABLE IF NOT EXISTS roles (
  role_id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT
);

-- Application users (login/authentication records)
CREATE TABLE IF NOT EXISTS users (
  user_id SERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  api_key TEXT NOT NULL UNIQUE,
  full_name TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure legacy database tables get the api_key column when it was not present.
ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS users_api_key_key ON users(api_key);

-- Many-to-many mapping between users and roles
CREATE TABLE IF NOT EXISTS user_roles (
  user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  role_id INTEGER NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

-- Seed core roles
INSERT INTO roles (name, description)
VALUES
  ('librarian', 'Library staff with permissions to manage inventory and members'),
  ('member', 'Library member with borrowing privileges'),
  ('admin', 'Administrator with full access to system operations'),
  ('visitor', 'Read-only visitor role for browsing available books')
ON CONFLICT (name) DO NOTHING;

-- Seed initial users and assign roles
INSERT INTO users (email, password_hash, api_key, full_name, is_active)
VALUES
  ('lib1@example.com', crypt('LibrarianPass1!', gen_salt('bf')), 'lib1-api-key-0001', 'Librarian One', TRUE),
  ('member1@example.com', crypt('MemberPass1!', gen_salt('bf')), 'member1-api-key-0001', 'Member One', TRUE),
  ('admin1@example.com', crypt('AdminPass1!', gen_salt('bf')), 'admin1-api-key-0001', 'Administrator One', TRUE),
  ('visitor1@example.com', crypt('VisitorPass1!', gen_salt('bf')), 'visitor1-api-key-0001', 'Visitor One', TRUE)
ON CONFLICT (email) DO UPDATE SET api_key = EXCLUDED.api_key;

-- Assign roles to seeded users
INSERT INTO user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM users u
JOIN roles r ON r.name = 'librarian'
WHERE u.email = 'lib1@example.com'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM users u
JOIN roles r ON r.name = 'member'
WHERE u.email = 'member1@example.com'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM users u
JOIN roles r ON r.name = 'admin'
WHERE u.email = 'admin1@example.com'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM users u
JOIN roles r ON r.name = 'visitor'
WHERE u.email = 'visitor1@example.com'
ON CONFLICT DO NOTHING;

-- Migrate legacy student assignments to the member role.
INSERT INTO user_roles (user_id, role_id)
SELECT ur.user_id, member_role.role_id
FROM user_roles ur
JOIN roles legacy_role ON legacy_role.role_id = ur.role_id AND legacy_role.name = 'student'
CROSS JOIN roles member_role
WHERE member_role.name = 'member'
ON CONFLICT DO NOTHING;

DELETE FROM user_roles
WHERE role_id IN (SELECT role_id FROM roles WHERE name = 'student');

DELETE FROM roles WHERE name = 'student';

-- Example query to verify seeded data
-- SELECT u.email, r.name AS role_name
-- FROM users u
-- JOIN user_roles ur ON ur.user_id = u.user_id
-- JOIN roles r ON r.role_id = ur.role_id
-- ORDER BY u.user_id, r.role_id;

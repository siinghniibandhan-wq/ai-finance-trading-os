-- Add a unique optional phone number for authenticated account login.
-- Review and apply through the normal deployment migration process; this file does not run itself.
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(25);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_number ON users (phone_number);

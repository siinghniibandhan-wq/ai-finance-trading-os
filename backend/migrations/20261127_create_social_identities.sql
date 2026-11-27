-- Social sign-in (Google, GitHub): links a provider account to a Financial OS user.
-- Optional: the backend creates this table by itself on start-up (create_all).
-- Run this only if you prefer to create it by hand first. Safe to run twice.
CREATE TABLE IF NOT EXISTS social_identities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL,
    provider_user_id VARCHAR(128) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_social_identity_provider_user UNIQUE (provider, provider_user_id)
);
CREATE INDEX IF NOT EXISTS ix_social_identities_user_id ON social_identities (user_id);

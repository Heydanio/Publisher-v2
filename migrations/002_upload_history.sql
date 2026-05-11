-- Table pour le rate limiting anti-shadowban
CREATE TABLE IF NOT EXISTS upload_history (
    id BIGSERIAL PRIMARY KEY,
    account_name TEXT NOT NULL,
    platform TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_upload_history_account_time
ON upload_history(account_name, uploaded_at DESC);

CREATE INDEX IF NOT EXISTS idx_upload_history_platform_time
ON upload_history(platform, uploaded_at DESC);

-- Optionnel: cleanup des vieux records (>30 jours)
-- DELETE FROM upload_history WHERE uploaded_at < NOW() - INTERVAL '30 days';

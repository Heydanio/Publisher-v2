-- Table principale: tracking des publications
CREATE TABLE IF NOT EXISTS published_videos (
    id BIGSERIAL PRIMARY KEY,
    account_name TEXT NOT NULL,
    drive_file_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    published_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pub_videos_unique
ON published_videos(account_name, drive_file_id, platform);

CREATE INDEX IF NOT EXISTS idx_pub_videos_account
ON published_videos(account_name);

CREATE INDEX IF NOT EXISTS idx_pub_videos_platform
ON published_videos(platform);

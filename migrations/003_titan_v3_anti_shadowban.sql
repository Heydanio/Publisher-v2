-- =============================================================================
-- TITAN V3 - Anti-Shadowban 2026 Migration
-- =============================================================================
-- À exécuter dans Supabase SQL Editor

-- Table pour tracker l'âge des comptes (warming period)
CREATE TABLE IF NOT EXISTS account_metadata (
    id BIGSERIAL PRIMARY KEY,
    account_name TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    first_upload_at TIMESTAMPTZ,
    warming_started_at TIMESTAMPTZ DEFAULT NOW(),
    is_warming_complete BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- Table pour les validations (audit log)
CREATE TABLE IF NOT EXISTS validation_log (
    id BIGSERIAL PRIMARY KEY,
    account_name TEXT NOT NULL,
    video_id TEXT,
    platform TEXT NOT NULL,
    validation_score INT,
    is_valid BOOLEAN,
    errors JSONB,
    warnings JSONB,
    validated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_validation_log_account_time
ON validation_log(account_name, validated_at DESC);

-- Table pour tracker les IPs utilisées (anti-IP-linking)
CREATE TABLE IF NOT EXISTS ip_usage_log (
    id BIGSERIAL PRIMARY KEY,
    account_name TEXT NOT NULL,
    ip_address TEXT,
    is_datacenter BOOLEAN,
    isp TEXT,
    country TEXT,
    used_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ip_usage_account
ON ip_usage_log(account_name, used_at DESC);

-- View pour analyse facile
CREATE OR REPLACE VIEW account_health_2026 AS
SELECT 
    am.account_name,
    am.platform,
    EXTRACT(DAY FROM NOW() - am.warming_started_at)::INT as warming_days,
    am.is_warming_complete,
    (SELECT COUNT(*) FROM upload_history 
     WHERE account_name = am.account_name 
     AND uploaded_at > NOW() - INTERVAL '24 hours') as uploads_24h,
    (SELECT COUNT(*) FROM upload_history 
     WHERE account_name = am.account_name 
     AND uploaded_at > NOW() - INTERVAL '7 days') as uploads_7d,
    (SELECT COUNT(*) FROM validation_log 
     WHERE account_name = am.account_name 
     AND NOT is_valid 
     AND validated_at > NOW() - INTERVAL '30 days') as failed_validations_30d
FROM account_metadata am;

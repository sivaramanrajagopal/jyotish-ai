-- Anonymous AI daily quotas (IP hash tracked by backend service role only)
-- Run once in Supabase SQL Editor alongside schema_steps_4_5_7.sql

CREATE TABLE IF NOT EXISTS anon_ai_usage (
    ip_hash         TEXT NOT NULL,
    usage_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    chat_count      INTEGER NOT NULL DEFAULT 0,
    forecast_count  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (ip_hash, usage_date)
);

ALTER TABLE anon_ai_usage ENABLE ROW LEVEL SECURITY;
-- No client policies — backend service role reads/writes only

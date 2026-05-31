-- ============================================================
-- Jyotish AI — Supabase Schema
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor)
-- ============================================================

-- Enable pgvector extension (needed for future embedding features)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 1. LOCATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS locations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,
    lat         DOUBLE PRECISION NOT NULL,
    lon         DOUBLE PRECISION NOT NULL,
    timezone    TEXT NOT NULL,
    country     TEXT NOT NULL DEFAULT 'India',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed default locations
INSERT INTO locations (name, lat, lon, timezone, country) VALUES
    ('Chennai',    13.0827,  80.2707, 'Asia/Kolkata',    'India'),
    ('Bangalore',  12.9716,  77.5946, 'Asia/Kolkata',    'India'),
    ('Mumbai',     19.0760,  72.8777, 'Asia/Kolkata',    'India'),
    ('Delhi',      28.6139,  77.2090, 'Asia/Kolkata',    'India'),
    ('Hyderabad',  17.3850,  78.4867, 'Asia/Kolkata',    'India'),
    ('Coimbatore', 11.0168,  76.9558, 'Asia/Kolkata',    'India'),
    ('Erlangen',   49.5897,  11.0078, 'Europe/Berlin',   'Germany')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- 2. USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                   TEXT NOT NULL UNIQUE,
    name                    TEXT,
    dob                     DATE,                           -- date of birth
    tob                     TIME,                           -- time of birth (local)
    place_of_birth          TEXT,
    lat                     DOUBLE PRECISION,
    lon                     DOUBLE PRECISION,
    timezone                TEXT DEFAULT 'Asia/Kolkata',
    subscription_tier       TEXT NOT NULL DEFAULT 'free'
                                CHECK (subscription_tier IN ('free','starter','premium','developer')),
    razorpay_subscription_id TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- 3. NATAL CHARTS
-- ============================================================
CREATE TABLE IF NOT EXISTS natal_charts (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID REFERENCES users(id) ON DELETE CASCADE,
    sun_sign         TEXT,
    moon_sign        TEXT,
    ascendant        TEXT,
    planet_positions JSONB NOT NULL DEFAULT '{}',
    -- Structure: { "Sun": {"lon": 45.2, "sign": "Taurus", "house": 1,
    --              "nakshatra": "Rohini", "pada": 2, "retro": false}, ... }
    yogas            JSONB NOT NULL DEFAULT '[]',
    -- Structure: [{ "name": "Gaja Kesari Yoga", "description": "..." }, ...]
    ayanamsa         TEXT NOT NULL DEFAULT 'Lahiri',
    ayanamsa_value   DOUBLE PRECISION,
    calculated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Each user has one active natal chart (upsert on user_id)
    UNIQUE(user_id)
);

-- ============================================================
-- 4. PANCHANGAM DAILY
-- ============================================================
CREATE TABLE IF NOT EXISTS panchangam_daily (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    date                  DATE NOT NULL,
    location_name         TEXT NOT NULL REFERENCES locations(name),
    lat                   DOUBLE PRECISION NOT NULL,
    lon                   DOUBLE PRECISION NOT NULL,
    timezone              TEXT NOT NULL,

    -- Sun timings
    sunrise               TIMESTAMPTZ,
    sunset                TIMESTAMPTZ,

    -- Vaaram (weekday)
    vaaram_name           TEXT NOT NULL,
    vaaram_lord           TEXT NOT NULL,

    -- Tithi
    tithi_name            TEXT NOT NULL,
    tithi_paksha          TEXT NOT NULL,        -- 'Shukla' or 'Krishna'
    tithi_index           INTEGER NOT NULL,     -- 1–30
    tithi_end_time        TIMESTAMPTZ,          -- NULL if lasts all day
    next_tithi_name       TEXT,
    next_tithi_end        TIMESTAMPTZ,

    -- Nakshatra
    nakshatra_name        TEXT NOT NULL,
    nakshatra_lord        TEXT NOT NULL,
    nakshatra_index       INTEGER NOT NULL,     -- 1–27
    nakshatra_pada        INTEGER NOT NULL,     -- 1–4
    nakshatra_end_time    TIMESTAMPTZ,
    next_nakshatra_name   TEXT,
    next_nakshatra_end    TIMESTAMPTZ,

    -- Yogam
    yogam_name            TEXT NOT NULL,
    yogam_index           INTEGER NOT NULL,     -- 1–27
    yogam_end_time        TIMESTAMPTZ,
    next_yogam_name       TEXT,
    next_yogam_end        TIMESTAMPTZ,

    -- Karanam
    karanam_name          TEXT NOT NULL,
    karanam_index         INTEGER NOT NULL,     -- 1–11
    karanam_end_time      TIMESTAMPTZ,
    next_karanam_name     TEXT,
    next_karanam_end      TIMESTAMPTZ,

    -- Inauspicious periods
    rahu_kalam_start      TIMESTAMPTZ,
    rahu_kalam_end        TIMESTAMPTZ,
    gulikai_kalam_start   TIMESTAMPTZ,
    gulikai_kalam_end     TIMESTAMPTZ,
    yamaganda_start       TIMESTAMPTZ,
    yamaganda_end         TIMESTAMPTZ,

    -- Metadata
    validated             BOOLEAN NOT NULL DEFAULT FALSE,
    calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(date, location_name)
);

CREATE INDEX IF NOT EXISTS panchangam_date_loc_idx
    ON panchangam_daily(date, location_name);

-- ============================================================
-- 5. FORECASTS
-- ============================================================
CREATE TABLE IF NOT EXISTS forecasts (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID REFERENCES users(id) ON DELETE CASCADE,
    date                 DATE NOT NULL,

    -- Claude narrated sections
    career_forecast      TEXT,
    love_forecast        TEXT,
    health_forecast      TEXT,
    spiritual_forecast   TEXT,
    finance_forecast     TEXT,
    timing_advice        TEXT,
    panchapakshi_summary TEXT,
    dasha_context        TEXT,

    -- Raw agent outputs (for debugging / re-narration)
    raw_context          JSONB DEFAULT '{}',

    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS forecasts_user_date_idx
    ON forecasts(user_id, date);

-- ============================================================
-- 6. CHAT HISTORY
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_history (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    message    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chat_history_user_idx
    ON chat_history(user_id, created_at DESC);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- Enable after connecting Supabase Auth
-- ============================================================

ALTER TABLE users         ENABLE ROW LEVEL SECURITY;
ALTER TABLE natal_charts  ENABLE ROW LEVEL SECURITY;
ALTER TABLE forecasts     ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history  ENABLE ROW LEVEL SECURITY;

-- Users can only read/write their own rows
CREATE POLICY "users_self" ON users
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "natal_charts_self" ON natal_charts
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "forecasts_self" ON forecasts
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "chat_history_self" ON chat_history
    FOR ALL USING (auth.uid() = user_id);

-- Panchangam and locations are public read
ALTER TABLE panchangam_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations        ENABLE ROW LEVEL SECURITY;

CREATE POLICY "panchangam_public_read" ON panchangam_daily
    FOR SELECT USING (true);

CREATE POLICY "locations_public_read" ON locations
    FOR SELECT USING (true);

-- Service role can write panchangam (backend inserts)
CREATE POLICY "panchangam_service_write" ON panchangam_daily
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "locations_service_write" ON locations
    FOR ALL USING (auth.role() = 'service_role');

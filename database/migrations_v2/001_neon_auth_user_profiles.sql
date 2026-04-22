-- Neon / standalone Postgres: allow app-managed auth (no auth.users FK).
-- Run once on your Neon branch after importing schema from Supabase.

ALTER TABLE IF EXISTS public.user_profiles
  DROP CONSTRAINT IF EXISTS user_profiles_id_fkey;

ALTER TABLE IF EXISTS public.user_profiles
  ADD COLUMN IF NOT EXISTS password_hash TEXT;

COMMENT ON COLUMN public.user_profiles.password_hash IS 'bcrypt hash for Auth.js Credentials (nullable for legacy Supabase-only users).';

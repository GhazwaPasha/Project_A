-- Agent proposals awaiting a person's decision, and tokens that let outside AI apps connect over MCP.
-- Additive only: no existing table is changed. Idempotent: safe to re-run.

CREATE TABLE IF NOT EXISTS public.agent_proposals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  proposed_by uuid NOT NULL REFERENCES public.user_profiles (id) ON DELETE CASCADE,
  source text NOT NULL CHECK (source IN ('app', 'mcp')),
  source_name text,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'recorded', 'discarded')),
  entry_date date NOT NULL,
  description text NOT NULL,
  explanation text NOT NULL,
  confidence text NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
  lines jsonb NOT NULL,
  decided_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  decided_at timestamptz,
  journal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS agent_proposals_org_status
  ON public.agent_proposals (organization_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS public.mcp_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.user_profiles (id) ON DELETE CASCADE,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  name text NOT NULL,
  token_hash text NOT NULL UNIQUE,
  token_hint text NOT NULL,
  can_record boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  last_used_at timestamptz,
  revoked_at timestamptz
);
CREATE INDEX IF NOT EXISTS mcp_tokens_user_org
  ON public.mcp_tokens (user_id, organization_id);

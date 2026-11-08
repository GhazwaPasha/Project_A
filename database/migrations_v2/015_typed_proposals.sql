-- Agent proposals with a type. A payment or a document to post runs through the same service as the screens when
-- approved, so invoices, bills and their balances stay in step with the books. Run after 014.
-- Additive: existing proposals become journal proposals. Idempotent: safe to re-run.

ALTER TABLE public.agent_proposals ADD COLUMN IF NOT EXISTS kind text NOT NULL DEFAULT 'journal';
ALTER TABLE public.agent_proposals ADD COLUMN IF NOT EXISTS payload jsonb;
ALTER TABLE public.agent_proposals ADD COLUMN IF NOT EXISTS warnings jsonb NOT NULL DEFAULT '[]'::jsonb;

DO $$
BEGIN
  ALTER TABLE public.agent_proposals ADD CONSTRAINT agent_proposals_kind_valid CHECK (kind IN ('journal', 'payment', 'post_document'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- An entry an outside AI app recorded directly also leaves a proposal row, marked recorded, so every AI entry
-- can be traced the same way.
CREATE INDEX IF NOT EXISTS agent_proposals_entry ON public.agent_proposals (journal_entry_id) WHERE journal_entry_id IS NOT NULL;

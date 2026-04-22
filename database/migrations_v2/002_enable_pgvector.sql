-- Optional: enable pgvector on Neon when supported (Phase 3 / AI retrieval).
-- Verify in Neon dashboard before applying to production.

CREATE EXTENSION IF NOT EXISTS vector;

-- Tenant-scoped embedding store (minimal stub; tune dimensions to your model)
CREATE TABLE IF NOT EXISTS public.tenant_document_embeddings (
  id                BIGSERIAL PRIMARY KEY,
  organization_id   UUID NOT NULL,
  source_kind       TEXT NOT NULL,
  source_id         TEXT NOT NULL,
  content           TEXT,
  embedding         vector(384),
  metadata          JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS tenant_doc_emb_org_idx
  ON public.tenant_document_embeddings (organization_id);

-- Add ivfflat / hnsw after you have representative embedding rows (Neon docs).

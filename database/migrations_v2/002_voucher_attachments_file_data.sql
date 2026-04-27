-- Store voucher attachment bytes in Neon (replaces Supabase storage bucket)
ALTER TABLE public.voucher_attachments
  ADD COLUMN IF NOT EXISTS file_data bytea;

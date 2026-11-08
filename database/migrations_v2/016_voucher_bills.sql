-- A purchase voucher bought on credit raises a bill for what's owed, linked here, so what you owe suppliers
-- always has a bill behind it. Such a bill shares the voucher's entry and is undone from the voucher, not voided.
-- Run after 015. Additive, idempotent.

ALTER TABLE public.trade_documents ADD COLUMN IF NOT EXISTS voucher_id bigint REFERENCES public.inventory_vouchers (id) ON DELETE RESTRICT;
CREATE UNIQUE INDEX IF NOT EXISTS trade_documents_voucher_once ON public.trade_documents (voucher_id) WHERE voucher_id IS NOT NULL;

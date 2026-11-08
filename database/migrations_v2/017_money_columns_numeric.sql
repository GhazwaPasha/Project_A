-- The last money columns stored as floating point become exact decimals, like every other amount. Run after 016.
-- Values are rounded to the cent, which is how they were always shown. Idempotent: a column already numeric is left alone.

DO $$
DECLARE c record;
BEGIN
  FOR c IN SELECT * FROM (VALUES
    ('inventory_vouchers', 'deposit_amount'),
    ('inventory_vouchers', 'total_estimated_cost'),
    ('inventory_vouchers', 'total_actual_cost'),
    ('voucher_expiration_log', 'total_value'),
    ('suppliers', 'credit_limit'),
    ('suppliers', 'current_balance')
  ) AS t(tbl, col) LOOP
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = c.tbl AND column_name = c.col AND data_type = 'double precision') THEN
      EXECUTE format('ALTER TABLE public.%I ALTER COLUMN %I TYPE numeric(20, 2) USING round(%I::numeric, 2)', c.tbl, c.col, c.col);
    END IF;
  END LOOP;
END $$;

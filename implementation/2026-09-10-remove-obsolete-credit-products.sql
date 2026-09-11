BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
LOCK TABLE migrations IN SHARE ROW EXCLUSIVE MODE;
DO $$
BEGIN
  IF current_database() <> 'clipper_admin_prod' THEN
    RAISE EXCEPTION 'WRONG_DATABASE';
  END IF;
  IF EXISTS (SELECT 1 FROM migrations WHERE timestamp = 1789100000000
    OR name = 'RemoveObsoleteCreditProducts1789100000000') THEN
    RAISE EXCEPTION 'MIGRATION_ALREADY_RECORDED: check state before retrying';
  END IF;
END $$;
DO $$
BEGIN
  PERFORM id FROM credit_products
    WHERE code IN ('credits_100', 'credits_500') FOR UPDATE;
  IF EXISTS (
    SELECT 1 FROM credit_products
    WHERE code IN ('credits_100', 'credits_500') AND (
      is_active IS DISTINCT FROM false OR
      (code = 'credits_100' AND (name IS DISTINCT FROM '100 Credits' OR credits IS DISTINCT FROM 100 OR price_krw IS DISTINCT FROM 5900)) OR
      (code = 'credits_500' AND (name IS DISTINCT FROM '500 Credits' OR credits IS DISTINCT FROM 500 OR price_krw IS DISTINCT FROM 27900))
    )
  ) THEN
    RAISE EXCEPTION 'OBSOLETE_CREDIT_PRODUCTS_CHANGED: review catalog before deleting';
  END IF;
  IF EXISTS (
    SELECT 1 FROM payment_orders orders
    JOIN credit_products product ON product.id = orders.credit_product_id
    WHERE product.code IN ('credits_100', 'credits_500')
  ) THEN
    RAISE EXCEPTION 'OBSOLETE_CREDIT_PRODUCTS_REFERENCED: preserve historical orders';
  END IF;
  DELETE FROM credit_products
    WHERE code IN ('credits_100', 'credits_500') AND is_active = false;
END $$;
INSERT INTO migrations(timestamp, name)
VALUES (1789100000000, 'RemoveObsoleteCreditProducts1789100000000');
COMMIT;
SELECT count(*) AS obsolete_products_remaining
FROM credit_products WHERE code IN ('credits_100', 'credits_500');
SELECT timestamp, name FROM migrations WHERE timestamp = 1789100000000;
SELECT code, name, credits, price_krw, validity_days, is_active
FROM credit_products ORDER BY code;

-- ============================================================
-- TDDQ: Schema Validation Tests
-- Asserts structural integrity of the CRIS database.
-- Each test prints PASS or FAIL.
-- ============================================================

USE CRIS;
GO

-- ============================================================
-- TEST 1: Primary Key uniqueness — customers
-- ============================================================
DECLARE @dup_customers INT;
SELECT @dup_customers = COUNT(*)
FROM (
    SELECT customer_id, COUNT(*) AS cnt
    FROM dbo.customers
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) dupes;

IF @dup_customers = 0
    PRINT '[PASS] customers.customer_id is unique.'
ELSE
    PRINT '[FAIL] customers.customer_id has duplicates: ' + CAST(@dup_customers AS VARCHAR);
GO

-- ============================================================
-- TEST 2: Primary Key uniqueness — orders
-- ============================================================
DECLARE @dup_orders INT;
SELECT @dup_orders = COUNT(*)
FROM (
    SELECT order_id, COUNT(*) AS cnt
    FROM dbo.orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
) dupes;

IF @dup_orders = 0
    PRINT '[PASS] orders.order_id is unique.'
ELSE
    PRINT '[FAIL] orders.order_id has duplicates: ' + CAST(@dup_orders AS VARCHAR);
GO

-- ============================================================
-- TEST 3: Primary Key uniqueness — order_items
-- ============================================================
DECLARE @dup_items INT;
SELECT @dup_items = COUNT(*)
FROM (
    SELECT item_id, COUNT(*) AS cnt
    FROM dbo.order_items
    GROUP BY item_id
    HAVING COUNT(*) > 1
) dupes;

IF @dup_items = 0
    PRINT '[PASS] order_items.item_id is unique.'
ELSE
    PRINT '[FAIL] order_items.item_id has duplicates: ' + CAST(@dup_items AS VARCHAR);
GO

-- ============================================================
-- TEST 4: NOT NULL — critical columns
-- ============================================================
DECLARE @null_count INT;

SELECT @null_count = COUNT(*)
FROM dbo.customers
WHERE name IS NULL OR email IS NULL OR signup_date IS NULL;

IF @null_count = 0
    PRINT '[PASS] customers: no NULL values in critical columns.'
ELSE
    PRINT '[FAIL] customers: ' + CAST(@null_count AS VARCHAR) + ' rows with NULL critical columns.';
GO

-- ============================================================
-- TEST 5: FK integrity — all orders reference valid customers
-- ============================================================
DECLARE @orphan_orders INT;
SELECT @orphan_orders = COUNT(*)
FROM dbo.orders o
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.customers c WHERE c.customer_id = o.customer_id
);

IF @orphan_orders = 0
    PRINT '[PASS] orders: all customer_id references are valid.'
ELSE
    PRINT '[FAIL] orders: ' + CAST(@orphan_orders AS VARCHAR) + ' orphan rows found.';
GO

-- ============================================================
-- TEST 6: FK integrity — all order_items reference valid orders
-- ============================================================
DECLARE @orphan_items INT;
SELECT @orphan_items = COUNT(*)
FROM dbo.order_items oi
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.orders o WHERE o.order_id = oi.order_id
);

IF @orphan_items = 0
    PRINT '[PASS] order_items: all order_id references are valid.'
ELSE
    PRINT '[FAIL] order_items: ' + CAST(@orphan_items AS VARCHAR) + ' orphan rows found.';
GO

PRINT '>>> Schema tests complete.';
GO

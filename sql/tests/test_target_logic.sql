-- ============================================================
-- TDDQ: Target Logic Validation
-- Verifies that is_churned labels are calculated correctly.
-- ============================================================

USE CRIS;
GO

-- ============================================================
-- TEST 1: Churned customers have ZERO orders in prediction window
-- ============================================================
DECLARE @bad_churned INT;
SELECT @bad_churned = COUNT(*)
FROM dbo.customer_labels cl
WHERE cl.is_churned = 1
AND EXISTS (
    SELECT 1
    FROM dbo.orders o
    WHERE o.customer_id = cl.customer_id
    AND o.order_date BETWEEN '2024-07-01' AND '2024-08-31'
);

IF @bad_churned = 0
    PRINT '[PASS] All is_churned=1 customers have zero prediction-window orders.'
ELSE
    PRINT '[FAIL] ' + CAST(@bad_churned AS VARCHAR) + ' churned customers have prediction-window orders!';
GO

-- ============================================================
-- TEST 2: Safe customers have at least ONE order in prediction window
-- ============================================================
DECLARE @bad_safe INT;
SELECT @bad_safe = COUNT(*)
FROM dbo.customer_labels cl
WHERE cl.is_churned = 0
AND NOT EXISTS (
    SELECT 1
    FROM dbo.orders o
    WHERE o.customer_id = cl.customer_id
    AND o.order_date BETWEEN '2024-07-01' AND '2024-08-31'
);

IF @bad_safe = 0
    PRINT '[PASS] All is_churned=0 customers have prediction-window orders.'
ELSE
    PRINT '[FAIL] ' + CAST(@bad_safe AS VARCHAR) + ' safe customers lack prediction-window orders!';
GO

-- ============================================================
-- TEST 3: All labeled customers had orders in observation window
-- ============================================================
DECLARE @no_obs INT;
SELECT @no_obs = COUNT(*)
FROM dbo.customer_labels cl
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.orders o
    WHERE o.customer_id = cl.customer_id
    AND o.order_date BETWEEN '2024-01-01' AND '2024-06-30'
);

IF @no_obs = 0
    PRINT '[PASS] All labeled customers have observation-window activity.'
ELSE
    PRINT '[FAIL] ' + CAST(@no_obs AS VARCHAR) + ' labeled customers lack observation-window orders!';
GO

-- ============================================================
-- TEST 4: Label is binary (0 or 1 only)
-- ============================================================
DECLARE @bad_label INT;
SELECT @bad_label = COUNT(*)
FROM dbo.customer_labels
WHERE is_churned NOT IN (0, 1);

IF @bad_label = 0
    PRINT '[PASS] is_churned contains only 0 and 1.'
ELSE
    PRINT '[FAIL] is_churned has non-binary values: ' + CAST(@bad_label AS VARCHAR);
GO

PRINT '>>> Target logic tests complete.';
GO

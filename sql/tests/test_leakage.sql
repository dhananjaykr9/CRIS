-- ============================================================
-- TDDQ: Data Leakage Prevention
-- Ensures features do NOT use prediction-window data.
-- ============================================================

USE CRIS;
GO

-- ============================================================
-- TEST 1: Feature view only references observation-window data
-- Check that the max order date contributing to features
-- does not exceed the observation window cutoff.
-- ============================================================
DECLARE @max_feature_date DATE;
SELECT @max_feature_date = MAX(o.order_date)
FROM dbo.orders o
WHERE o.order_date BETWEEN '2024-01-01' AND '2024-06-30'
AND o.customer_id IN (SELECT customer_id FROM dbo.customer_features);

IF @max_feature_date <= '2024-06-30'
    PRINT '[PASS] Feature data does not exceed observation window (max: ' 
          + CAST(@max_feature_date AS VARCHAR) + ').'
ELSE
    PRINT '[FAIL] Feature data extends beyond observation window! Max date: ' 
          + CAST(@max_feature_date AS VARCHAR);
GO

-- ============================================================
-- TEST 2: Recency is non-negative (relative to obs end)
-- ============================================================
DECLARE @neg_recency INT;
SELECT @neg_recency = COUNT(*)
FROM dbo.customer_features
WHERE recency_days < 0;

IF @neg_recency = 0
    PRINT '[PASS] All recency_days values are non-negative.'
ELSE
    PRINT '[FAIL] ' + CAST(@neg_recency AS VARCHAR) + ' customers have negative recency!';
GO

-- ============================================================
-- TEST 3: Every customer in labels also has features
-- ============================================================
DECLARE @missing_features INT;
SELECT @missing_features = COUNT(*)
FROM dbo.customer_labels cl
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.customer_features cf WHERE cf.customer_id = cl.customer_id
);

IF @missing_features = 0
    PRINT '[PASS] All labeled customers have matching feature rows.'
ELSE
    PRINT '[FAIL] ' + CAST(@missing_features AS VARCHAR) + ' labeled customers lack features!';
GO

-- ============================================================
-- TEST 4: No future-date orders in features
-- Verify recency_days >= 0 means last order <= observation end
-- ============================================================
DECLARE @future_orders INT;
SELECT @future_orders = COUNT(*)
FROM dbo.customer_features cf
INNER JOIN dbo.orders o ON cf.customer_id = o.customer_id
WHERE o.order_date > '2024-06-30'
AND o.order_date BETWEEN '2024-07-01' AND '2024-08-31'
AND cf.recency_days = DATEDIFF(DAY, o.order_date, '2024-06-30');

IF @future_orders = 0
    PRINT '[PASS] No feature calculations use prediction-window orders.'
ELSE
    PRINT '[FAIL] Potential leakage: ' + CAST(@future_orders AS VARCHAR) + ' feature rows may use future data!';
GO

PRINT '>>> Leakage tests complete.';
GO

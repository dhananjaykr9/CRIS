-- ============================================================
-- CRIS: Target Engineering
-- Time-Aware churn label generation.
--
-- Observation Window : 2024-01-01 to 2024-06-30  (features)
-- Prediction Window  : 2024-07-01 to 2024-08-31  (target)
--
-- is_churned = 1  →  NO orders in prediction window  (High Risk)
-- is_churned = 0  →  HAS orders in prediction window (Safe)
-- ============================================================

USE CRIS;
GO

-- Drop existing objects
IF OBJECT_ID('dbo.customer_labels', 'U') IS NOT NULL DROP TABLE dbo.customer_labels;
GO

-- ============================================================
-- Parameters (adjust these to change the time windows)
-- ============================================================
DECLARE @obs_start    DATE = '2024-01-01';
DECLARE @obs_end      DATE = '2024-06-30';
DECLARE @pred_start   DATE = '2024-07-01';
DECLARE @pred_end     DATE = '2024-08-31';

-- ============================================================
-- Build labels: only include customers who placed at least
-- one order in the observation window (known customers).
-- ============================================================
SELECT
    c.customer_id,
    c.name,
    c.region,
    c.segment,
    -- Count of orders in observation window
    COUNT(DISTINCT CASE
        WHEN o.order_date BETWEEN @obs_start AND @obs_end
        THEN o.order_id END) AS obs_order_count,
    -- Count of orders in prediction window
    COUNT(DISTINCT CASE
        WHEN o.order_date BETWEEN @pred_start AND @pred_end
        THEN o.order_id END) AS pred_order_count,
    -- Churn label
    CASE
        WHEN COUNT(DISTINCT CASE
            WHEN o.order_date BETWEEN @pred_start AND @pred_end
            THEN o.order_id END) = 0
        THEN 1  -- CHURNED (no orders in prediction window)
        ELSE 0  -- SAFE
    END AS is_churned
INTO dbo.customer_labels
FROM dbo.customers c
LEFT JOIN dbo.orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.region, c.segment
-- Only consider customers active in the observation window
HAVING COUNT(DISTINCT CASE
    WHEN o.order_date BETWEEN @obs_start AND @obs_end
    THEN o.order_id END) > 0;

DECLARE @churned_count INT;
DECLARE @safe_count INT;

SELECT @churned_count = COUNT(*) FROM dbo.customer_labels WHERE is_churned = 1;
SELECT @safe_count = COUNT(*) FROM dbo.customer_labels WHERE is_churned = 0;

PRINT '>>> Target engineering complete.';
PRINT '>>> Churned customers: ' + CAST(@churned_count AS VARCHAR);
PRINT '>>> Safe customers: ' + CAST(@safe_count AS VARCHAR);
GO

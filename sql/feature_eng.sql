-- ============================================================
-- CRIS: SQL-First Feature Engineering
-- Computes RFM, behavioral trends, and ratios using the
-- OBSERVATION WINDOW ONLY (2024-01-01 to 2024-06-30).
--
-- This ensures NO data leakage from the prediction window.
-- ============================================================

USE CRIS;
GO

-- Drop existing view/table
IF OBJECT_ID('dbo.customer_features', 'V') IS NOT NULL DROP VIEW dbo.customer_features;
GO

CREATE VIEW dbo.customer_features AS
WITH
-- ============================================================
-- Base: only observation window orders
-- ============================================================
obs_orders AS (
    SELECT *
    FROM dbo.orders
    WHERE order_date BETWEEN '2024-01-01' AND '2024-06-30'
),

-- ============================================================
-- RFM Metrics
-- ============================================================
rfm AS (
    SELECT
        o.customer_id,
        -- Recency: days since last order (relative to observation end)
        DATEDIFF(DAY, MAX(o.order_date), '2024-06-30') AS recency_days,
        -- Frequency: number of completed orders
        COUNT(DISTINCT o.order_id) AS frequency,
        -- Monetary: total spend
        SUM(o.total_amount) AS monetary
    FROM obs_orders o
    GROUP BY o.customer_id
),

-- ============================================================
-- Trend Metrics (last 3 months vs lifetime within observation)
-- ============================================================
trends AS (
    SELECT
        o.customer_id,
        -- Average order value over entire observation window
        AVG(o.total_amount) AS avg_order_value_lifetime,
        -- Average order value in the last 3 months of observation (Apr-Jun)
        AVG(CASE
            WHEN o.order_date >= '2024-04-01'
            THEN o.total_amount END) AS avg_order_value_last_3m,
        -- Order count in last 3 months
        COUNT(DISTINCT CASE
            WHEN o.order_date >= '2024-04-01'
            THEN o.order_id END) AS orders_last_3m,
        -- Order count in first 3 months
        COUNT(DISTINCT CASE
            WHEN o.order_date < '2024-04-01'
            THEN o.order_id END) AS orders_first_3m
    FROM obs_orders o
    GROUP BY o.customer_id
),

-- ============================================================
-- Status Ratios & Item Diversity
-- ============================================================
ratios AS (
    SELECT
        o.customer_id,
        -- Cancellation rate
        CAST(SUM(CASE WHEN o.status = 'Cancelled' THEN 1 ELSE 0 END) AS FLOAT)
            / NULLIF(COUNT(*), 0) AS cancel_rate,
        -- Return rate
        CAST(SUM(CASE WHEN o.status = 'Returned' THEN 1 ELSE 0 END) AS FLOAT)
            / NULLIF(COUNT(*), 0) AS return_rate
    FROM obs_orders o
    GROUP BY o.customer_id
),

item_diversity AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT oi.category) AS unique_categories,
        AVG(CAST(oi.quantity AS FLOAT)) AS avg_items_per_order,
        COUNT(DISTINCT oi.product_name) AS unique_products
    FROM obs_orders o
    INNER JOIN dbo.order_items oi ON o.order_id = oi.order_id
    GROUP BY o.customer_id
),

-- ============================================================
-- Days Between Orders (order regularity)
-- ============================================================
order_gaps AS (
    SELECT
        customer_id,
        AVG(day_gap) AS avg_days_between_orders
    FROM (
        SELECT
            customer_id,
            DATEDIFF(DAY,
                LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date),
                order_date
            ) AS day_gap
        FROM obs_orders
    ) gaps
    WHERE day_gap IS NOT NULL
    GROUP BY customer_id
)

-- ============================================================
-- Final Feature Vector
-- ============================================================
SELECT
    r.customer_id,
    -- RFM
    r.recency_days,
    r.frequency,
    r.monetary,
    -- Trends
    t.avg_order_value_lifetime,
    t.avg_order_value_last_3m,
    CASE
        WHEN t.avg_order_value_lifetime > 0
        THEN t.avg_order_value_last_3m / t.avg_order_value_lifetime
        ELSE 0
    END AS trend_ratio,
    t.orders_last_3m,
    t.orders_first_3m,
    -- Ratios
    ISNULL(rat.cancel_rate, 0) AS cancel_rate,
    ISNULL(rat.return_rate, 0) AS return_rate,
    -- Item Diversity
    ISNULL(id.unique_categories, 0) AS unique_categories,
    ISNULL(id.avg_items_per_order, 0) AS avg_items_per_order,
    ISNULL(id.unique_products, 0) AS unique_products,
    -- Order Regularity
    ISNULL(og.avg_days_between_orders, 0) AS avg_days_between_orders

FROM rfm r
LEFT JOIN trends t   ON r.customer_id = t.customer_id
LEFT JOIN ratios rat ON r.customer_id = rat.customer_id
LEFT JOIN item_diversity id ON r.customer_id = id.customer_id
LEFT JOIN order_gaps og ON r.customer_id = og.customer_id;
GO

PRINT '>>> Feature engineering view created.';
GO

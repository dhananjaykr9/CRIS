-- ============================================================
-- CRIS: Schema Creation
-- Creates normalized relational tables for the CRIS database.
-- ============================================================

-- Create database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'CRIS')
BEGIN
    CREATE DATABASE CRIS;
END
GO

USE CRIS;
GO

-- ============================================================
-- Drop existing tables (in FK-safe order)
-- ============================================================
IF OBJECT_ID('dbo.order_items', 'U') IS NOT NULL DROP TABLE dbo.order_items;
IF OBJECT_ID('dbo.orders', 'U')      IS NOT NULL DROP TABLE dbo.orders;
IF OBJECT_ID('dbo.customers', 'U')   IS NOT NULL DROP TABLE dbo.customers;
GO

-- ============================================================
-- 1. Customers
-- ============================================================
CREATE TABLE dbo.customers (
    customer_id   INT          NOT NULL  PRIMARY KEY,
    name          NVARCHAR(100) NOT NULL,
    email         NVARCHAR(150) NOT NULL,
    signup_date   DATE          NOT NULL,
    region        NVARCHAR(50)  NOT NULL,
    segment       NVARCHAR(50)  NOT NULL
);
GO

-- ============================================================
-- 2. Orders
-- ============================================================
CREATE TABLE dbo.orders (
    order_id      INT          NOT NULL  PRIMARY KEY,
    customer_id   INT          NOT NULL,
    order_date    DATE          NOT NULL,
    total_amount  DECIMAL(12,2) NOT NULL,
    status        NVARCHAR(20)  NOT NULL,
    CONSTRAINT FK_orders_customers
        FOREIGN KEY (customer_id) REFERENCES dbo.customers(customer_id)
);
GO

CREATE INDEX IX_orders_customer_id ON dbo.orders(customer_id);
CREATE INDEX IX_orders_order_date  ON dbo.orders(order_date);
GO

-- ============================================================
-- 3. Order Items
-- ============================================================
CREATE TABLE dbo.order_items (
    item_id       INT           NOT NULL  PRIMARY KEY,
    order_id      INT           NOT NULL,
    product_name  NVARCHAR(100) NOT NULL,
    category      NVARCHAR(50)  NOT NULL,
    quantity      INT           NOT NULL,
    unit_price    DECIMAL(10,2) NOT NULL,
    CONSTRAINT FK_items_orders
        FOREIGN KEY (order_id) REFERENCES dbo.orders(order_id)
);
GO

CREATE INDEX IX_order_items_order_id ON dbo.order_items(order_id);
GO

PRINT '>>> Schema creation complete.';
GO

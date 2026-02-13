-- PostgreSQL

-- Customer orders table
CREATE TABLE IF NOT EXISTS orders (
    id            SERIAL PRIMARY KEY,                       -- unique order ID
    customer      VARCHAR(255) NOT NULL,                    -- customer name or ID
    amount        NUMERIC(12,2) NOT NULL,                   -- order amount
    status        VARCHAR(20) NOT NULL DEFAULT 'NEW'        -- order status
                  CHECK (status IN ('NEW', 'PAID', 'SHIPPED', 'CANCELLED')),
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT now(),   -- creation timestamp
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT now()    -- last update timestamp
);

-- Seed data
INSERT INTO orders (customer, amount, status) VALUES
    ('Alice', 100.00, 'NEW'),
    ('Bob',   250.50, 'PAID'),
    ('Carol', 75.00,  'SHIPPED');
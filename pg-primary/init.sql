-- PostgreSQL

CREATE TABLE IF NOT EXISTS orders (
    id            SERIAL PRIMARY KEY,
    customer      VARCHAR(255) NOT NULL,
    amount        NUMERIC(12,2) NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'NEW'
                  CHECK (status IN ('NEW', 'PAID', 'SHIPPED', 'CANCELLED')),
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Seed data
INSERT INTO orders (customer, amount, status) VALUES
    ('Alice', 100.00, 'NEW'),
    ('Bob',   250.50, 'PAID'),
    ('Carol', 75.00,  'SHIPPED');
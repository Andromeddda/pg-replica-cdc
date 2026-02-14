CREATE TABLE IF NOT EXISTS orders_read (
    id            INT PRIMARY KEY,
    customer      VARCHAR(255),
    amount        NUMERIC(12,2),
    status        VARCHAR(20),
    created_at    TIMESTAMP WITH TIME ZONE,
    updated_at    TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS orders_read_2 (
    id            INT PRIMARY KEY,
    customer      VARCHAR(255),
    status        VARCHAR(20)
);
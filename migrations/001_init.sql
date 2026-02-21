CREATE TABLE IF NOT EXISTS servers (
    id SERIAL PRIMARY KEY,
    hoster VARCHAR(255) NOT NULL,
    server_name VARCHAR(255) NOT NULL,
    payment_day INTEGER NOT NULL CHECK (payment_day BETWEEN 1 AND 31),
    payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('invoice', 'auto')),
    monthly_cost DECIMAL(10, 2),
    currency VARCHAR(10) NOT NULL DEFAULT 'RUB',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    server_id INTEGER NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    due_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'confirmed', 'problem')),
    paid_at TIMESTAMP,
    notified_3d BOOLEAN NOT NULL DEFAULT FALSE,
    notified_1d BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (server_id, due_date)
);

CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL,
    value TEXT NOT NULL
);

-- Production Control System Database Schema
-- Initialize database and create tables

-- Create database (run as postgres user)
-- CREATE DATABASE prodcontrol;

-- Connect to database
\c prodcontrol;

-- Enable TimescaleDB extension (optional, for time-series optimization)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Equipment Master Table
CREATE TABLE IF NOT EXISTS equipment (
    id SERIAL PRIMARY KEY,
    equipment_id VARCHAR(50) UNIQUE NOT NULL,
    equipment_type VARCHAR(50) NOT NULL,
    description TEXT,
    location VARCHAR(100),
    installation_date TIMESTAMP,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_equipment_id ON equipment(equipment_id);
CREATE INDEX idx_equipment_type ON equipment(equipment_type);

-- Telemetry Table (Time-Series Data)
CREATE TABLE IF NOT EXISTS telemetry (
    id SERIAL,
    time TIMESTAMPTZ NOT NULL,
    equipment_id VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION,
    unit VARCHAR(20),
    status VARCHAR(20),
    PRIMARY KEY (id, time)
);

CREATE INDEX idx_telemetry_equipment ON telemetry(equipment_id, time DESC);
CREATE INDEX idx_telemetry_metric ON telemetry(metric_name);

-- Convert to hypertable if TimescaleDB is available
SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    equipment_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_alerts_equipment ON alerts(equipment_id, created_at DESC);
CREATE INDEX idx_alerts_severity ON alerts(severity, acknowledged);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_log(action);

-- Insert default admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash generated with bcrypt
INSERT INTO users (username, email, password_hash, role, active)
VALUES (
    'admin',
    'admin@prodcontrol.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5rnboKlbYdHsO',
    'admin',
    true
) ON CONFLICT (username) DO NOTHING;

-- Insert sample equipment
INSERT INTO equipment (equipment_id, equipment_type, description, location, installation_date, active)
VALUES
    ('IMM-01', 'IMM', 'Injection Molding Machine 1', 'Cell-01', '2023-01-15', true),
    ('IMM-02', 'IMM', 'Injection Molding Machine 2', 'Cell-02', '2023-01-15', true),
    ('IMM-03', 'IMM', 'Injection Molding Machine 3', 'Cell-03', '2023-02-20', true),
    ('IMM-04', 'IMM', 'Injection Molding Machine 4', 'Cell-04', '2023-02-20', true),
    ('IMM-05', 'IMM', 'Injection Molding Machine 5', 'Cell-05', '2023-03-10', true),
    ('IMM-06', 'IMM', 'Injection Molding Machine 6', 'Cell-06', '2023-03-10', true),
    ('IMM-07', 'IMM', 'Injection Molding Machine 7', 'Cell-07', '2023-04-05', true),
    ('IMM-08', 'IMM', 'Injection Molding Machine 8', 'Cell-08', '2023-04-05', true),
    ('TCM-01', 'TCM', 'Tear Cutting Machine 1', 'Airbag-Line', '2023-05-01', true),
    ('TCM-02', 'TCM', 'Tear Cutting Machine 2', 'Airbag-Line', '2023-05-01', true),
    ('VWM-01', 'VWM', 'Vibration Welding Machine 1', 'Airbag-Line', '2023-06-15', true),
    ('VWM-02', 'VWM', 'Vibration Welding Machine 2', 'Airbag-Line', '2023-06-15', true)
ON CONFLICT (equipment_id) DO NOTHING;

-- Data retention policy (keep 180 days using TimescaleDB)
SELECT add_retention_policy('telemetry', INTERVAL '180 days', if_not_exists => TRUE);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prodcontrol;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO prodcontrol;

-- Success message
\echo '✅ Database schema created successfully!'
\echo '✅ Default admin user: admin / admin123 (CHANGE PASSWORD!)'
\echo '✅ Equipment records inserted'

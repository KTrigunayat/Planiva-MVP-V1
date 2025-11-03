-- Database initialization script for Event Planning Agent v2
-- This script sets up the initial database schema and extensions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create database user if not exists (for development)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'eventuser') THEN
        CREATE ROLE eventuser WITH LOGIN PASSWORD 'eventpass';
    END IF;
END
$$;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE eventdb TO eventuser;
GRANT ALL ON SCHEMA public TO eventuser;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO eventuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO eventuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO eventuser;

-- Create initial tables (basic structure)
-- Note: Full schema will be created by migration scripts

-- Event plans table (enhanced from original)
CREATE TABLE IF NOT EXISTS event_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    plan_data JSONB,
    workflow_state JSONB,
    beam_history JSONB,
    agent_logs JSONB,
    final_blueprint TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent performance tracking
CREATE TABLE IF NOT EXISTS agent_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES event_plans(plan_id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    task_name VARCHAR(100) NOT NULL,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow metrics
CREATE TABLE IF NOT EXISTS workflow_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES event_plans(plan_id) ON DELETE CASCADE,
    total_iterations INTEGER DEFAULT 0,
    total_execution_time_ms INTEGER DEFAULT 0,
    combinations_evaluated INTEGER DEFAULT 0,
    final_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vendor data tables (preserved from original system)
CREATE TABLE IF NOT EXISTS venues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    capacity INTEGER,
    cost_per_person DECIMAL(10,2),
    amenities JSONB,
    availability JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS caterers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cuisine_type VARCHAR(100),
    cost_per_person DECIMAL(10,2),
    menu_options JSONB,
    dietary_restrictions JSONB,
    availability JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS photographers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    style VARCHAR(100),
    hourly_rate DECIMAL(10,2),
    package_options JSONB,
    portfolio_url VARCHAR(500),
    availability JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS makeup_artists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    specialties JSONB,
    hourly_rate DECIMAL(10,2),
    travel_radius INTEGER,
    availability JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_event_plans_status ON event_plans(status);
CREATE INDEX IF NOT EXISTS idx_event_plans_client_id ON event_plans(client_id);
CREATE INDEX IF NOT EXISTS idx_event_plans_created_at ON event_plans(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_performance_plan_id ON agent_performance(plan_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_name ON agent_performance(agent_name);
CREATE INDEX IF NOT EXISTS idx_workflow_metrics_plan_id ON workflow_metrics(plan_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to event_plans
CREATE TRIGGER update_event_plans_updated_at 
    BEFORE UPDATE ON event_plans 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for development
INSERT INTO venues (name, location, capacity, cost_per_person, amenities) VALUES
('Grand Ballroom', 'Downtown', 200, 150.00, '{"parking": true, "catering_kitchen": true, "av_equipment": true}'),
('Garden Pavilion', 'Suburbs', 100, 120.00, '{"outdoor_space": true, "garden_view": true, "weather_backup": true}'),
('Rooftop Terrace', 'City Center', 80, 180.00, '{"city_view": true, "bar_area": true, "elevator_access": true}')
ON CONFLICT DO NOTHING;

INSERT INTO caterers (name, cuisine_type, cost_per_person, menu_options) VALUES
('Elegant Eats', 'International', 85.00, '{"appetizers": ["bruschetta", "shrimp cocktail"], "mains": ["salmon", "beef tenderloin"], "desserts": ["tiramisu", "chocolate cake"]}'),
('Farm Fresh Catering', 'Organic', 75.00, '{"appetizers": ["seasonal salad", "cheese board"], "mains": ["herb chicken", "vegetarian pasta"], "desserts": ["fruit tart", "organic ice cream"]}'),
('Gourmet Delights', 'Fine Dining', 120.00, '{"appetizers": ["foie gras", "caviar service"], "mains": ["wagyu beef", "lobster thermidor"], "desserts": ["crème brûlée", "chocolate soufflé"]}')
ON CONFLICT DO NOTHING;

-- Log initialization completion
INSERT INTO agent_performance (agent_name, task_name, execution_time_ms, success) VALUES
('system', 'database_initialization', 0, true);
-- ============================================================================
-- CRM Communication Engine - Complete Database Schema Migration
-- ============================================================================
-- This migration creates all tables, indexes, views, and functions required
-- for the CRM Communication Engine integration.
--
-- Requirements: PostgreSQL 13+, pgcrypto extension
-- Version: 1.0.0
-- Date: 2025-10-27
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TABLE: crm_communications
-- ============================================================================
-- Stores all communication records sent to clients
-- ============================================================================

CREATE TABLE IF NOT EXISTS crm_communications (
    communication_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    client_id UUID NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    subject TEXT,
    content TEXT,
    context JSONB,
    urgency VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_crm_communications_plan_id ON crm_communications(plan_id);
CREATE INDEX IF NOT EXISTS idx_crm_communications_client_id ON crm_communications(client_id);
CREATE INDEX IF NOT EXISTS idx_crm_communications_status ON crm_communications(status);
CREATE INDEX IF NOT EXISTS idx_crm_communications_created_at ON crm_communications(created_at);
CREATE INDEX IF NOT EXISTS idx_crm_communications_channel ON crm_communications(channel);
CREATE INDEX IF NOT EXISTS idx_crm_communications_message_type ON crm_communications(message_type);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_crm_communications_plan_status ON crm_communications(plan_id, status);
CREATE INDEX IF NOT EXISTS idx_crm_communications_client_channel ON crm_communications(client_id, channel);

-- ============================================================================
-- TABLE: crm_client_preferences
-- ============================================================================
-- Stores client communication preferences and opt-out settings
-- ============================================================================

CREATE TABLE IF NOT EXISTS crm_client_preferences (
    client_id UUID PRIMARY KEY,
    preferred_channels JSONB DEFAULT '["email"]',
    timezone VARCHAR(50) DEFAULT 'UTC',
    quiet_hours_start TIME DEFAULT '22:00:00',
    quiet_hours_end TIME DEFAULT '08:00:00',
    opt_out_email BOOLEAN DEFAULT FALSE,
    opt_out_sms BOOLEAN DEFAULT FALSE,
    opt_out_whatsapp BOOLEAN DEFAULT FALSE,
    language_preference VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for timezone-based queries
CREATE INDEX IF NOT EXISTS idx_crm_client_preferences_timezone ON crm_client_preferences(timezone);

-- ============================================================================
-- TABLE: crm_communication_templates
-- ============================================================================
-- Stores message templates for different channels and message types
-- ============================================================================

CREATE TABLE IF NOT EXISTS crm_communication_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) UNIQUE NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    subject_template TEXT,
    body_template TEXT NOT NULL,
    variables JSONB,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for template lookups
CREATE INDEX IF NOT EXISTS idx_crm_templates_name ON crm_communication_templates(template_name);
CREATE INDEX IF NOT EXISTS idx_crm_templates_channel ON crm_communication_templates(channel);
CREATE INDEX IF NOT EXISTS idx_crm_templates_message_type ON crm_communication_templates(message_type);
CREATE INDEX IF NOT EXISTS idx_crm_templates_active ON crm_communication_templates(is_active);

-- Composite index for template selection
CREATE INDEX IF NOT EXISTS idx_crm_templates_lookup ON crm_communication_templates(message_type, channel, is_active);

-- ============================================================================
-- TABLE: crm_delivery_logs
-- ============================================================================
-- Detailed logs of delivery attempts and API responses
-- ============================================================================

CREATE TABLE IF NOT EXISTS crm_delivery_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    communication_id UUID NOT NULL REFERENCES crm_communications(communication_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivery_status VARCHAR(50),
    provider_response JSONB,
    error_details TEXT,
    attempt_number INTEGER DEFAULT 1,
    api_provider VARCHAR(50),
    status_code INTEGER,
    delivery_time_ms INTEGER
);

-- Indexes for log queries
CREATE INDEX IF NOT EXISTS idx_crm_delivery_logs_communication_id ON crm_delivery_logs(communication_id);
CREATE INDEX IF NOT EXISTS idx_crm_delivery_logs_event_type ON crm_delivery_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_crm_delivery_logs_event_timestamp ON crm_delivery_logs(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_crm_delivery_logs_delivery_status ON crm_delivery_logs(delivery_status);

-- ============================================================================
-- VIEW: crm_communication_analytics
-- ============================================================================
-- Aggregated analytics for communication effectiveness
-- ============================================================================

CREATE OR REPLACE VIEW crm_communication_analytics AS
SELECT 
    message_type,
    channel,
    DATE(created_at) as date,
    COUNT(*) as total_sent,
    SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_count,
    SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened_count,
    SUM(CASE WHEN clicked_at IS NOT NULL THEN 1 ELSE 0 END) as clicked_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
    AVG(EXTRACT(EPOCH FROM (delivered_at - sent_at))) as avg_delivery_time_seconds,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        2
    ) as delivery_rate_percent,
    ROUND(
        100.0 * SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) / 
        NULLIF(SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END), 0),
        2
    ) as open_rate_percent
FROM crm_communications
GROUP BY message_type, channel, DATE(created_at);

-- ============================================================================
-- FUNCTION: update_crm_client_preferences_timestamp
-- ============================================================================
-- Automatically update updated_at timestamp on preference changes
-- ============================================================================

CREATE OR REPLACE FUNCTION update_crm_client_preferences_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic timestamp updates
DROP TRIGGER IF EXISTS trigger_update_crm_client_preferences_timestamp ON crm_client_preferences;
CREATE TRIGGER trigger_update_crm_client_preferences_timestamp
    BEFORE UPDATE ON crm_client_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_crm_client_preferences_timestamp();

-- ============================================================================
-- FUNCTION: update_crm_template_timestamp
-- ============================================================================
-- Automatically update updated_at timestamp on template changes
-- ============================================================================

CREATE OR REPLACE FUNCTION update_crm_template_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic timestamp updates
DROP TRIGGER IF EXISTS trigger_update_crm_template_timestamp ON crm_communication_templates;
CREATE TRIGGER trigger_update_crm_template_timestamp
    BEFORE UPDATE ON crm_communication_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_crm_template_timestamp();

-- ============================================================================
-- COMMENTS: Table and column documentation
-- ============================================================================

COMMENT ON TABLE crm_communications IS 'Stores all communication records sent to clients through various channels';
COMMENT ON TABLE crm_client_preferences IS 'Client communication preferences including channels, timezone, and opt-outs';
COMMENT ON TABLE crm_communication_templates IS 'Message templates for different channels and message types';
COMMENT ON TABLE crm_delivery_logs IS 'Detailed logs of delivery attempts and API responses for debugging';

COMMENT ON COLUMN crm_communications.communication_id IS 'Unique identifier for the communication';
COMMENT ON COLUMN crm_communications.plan_id IS 'Reference to the event plan';
COMMENT ON COLUMN crm_communications.client_id IS 'Reference to the client';
COMMENT ON COLUMN crm_communications.message_type IS 'Type of message: welcome, budget_summary, vendor_options, etc.';
COMMENT ON COLUMN crm_communications.channel IS 'Communication channel: email, sms, whatsapp';
COMMENT ON COLUMN crm_communications.status IS 'Current status: pending, sent, delivered, opened, clicked, failed';
COMMENT ON COLUMN crm_communications.context IS 'JSONB context data used for template rendering';
COMMENT ON COLUMN crm_communications.urgency IS 'Message urgency: critical, high, normal, low';
COMMENT ON COLUMN crm_communications.retry_count IS 'Number of retry attempts made';

-- ============================================================================
-- GRANTS: Set appropriate permissions
-- ============================================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON crm_communications TO eventuser;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON crm_client_preferences TO eventuser;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON crm_communication_templates TO eventuser;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON crm_delivery_logs TO eventuser;
-- GRANT SELECT ON crm_communication_analytics TO eventuser;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

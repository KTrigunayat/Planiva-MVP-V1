-- Migration: CRM Communication Engine Tables
-- Version: 001
-- Description: Create tables for CRM communication tracking and client preferences

-- CRM Communications Table
CREATE TABLE IF NOT EXISTS crm_communications (
    communication_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES event_plans(plan_id) ON DELETE CASCADE,
    client_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    urgency VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    subject TEXT,
    body TEXT NOT NULL,
    template_name VARCHAR(100),
    context_data JSONB,
    metadata JSONB,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- CRM Client Preferences Table
CREATE TABLE IF NOT EXISTS crm_client_preferences (
    client_id VARCHAR(255) PRIMARY KEY,
    preferred_channels JSONB DEFAULT '["email"]'::jsonb,
    timezone VARCHAR(50) DEFAULT 'UTC',
    quiet_hours_start TIME DEFAULT '22:00:00',
    quiet_hours_end TIME DEFAULT '08:00:00',
    opt_out_email BOOLEAN DEFAULT FALSE,
    opt_out_sms BOOLEAN DEFAULT FALSE,
    opt_out_whatsapp BOOLEAN DEFAULT FALSE,
    language_preference VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- CRM Communication Templates Table
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- CRM Delivery Logs Table
CREATE TABLE IF NOT EXISTS crm_delivery_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    communication_id UUID NOT NULL REFERENCES crm_communications(communication_id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL,
    attempt_number INTEGER NOT NULL,
    api_provider VARCHAR(50) NOT NULL,
    api_request JSONB,
    api_response JSONB,
    status_code INTEGER,
    success BOOLEAN NOT NULL,
    error_details TEXT,
    delivery_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_crm_communications_plan_id ON crm_communications(plan_id);
CREATE INDEX IF NOT EXISTS idx_crm_communications_client_id ON crm_communications(client_id);
CREATE INDEX IF NOT EXISTS idx_crm_communications_status ON crm_communications(status);
CREATE INDEX IF NOT EXISTS idx_crm_communications_channel ON crm_communications(channel);
CREATE INDEX IF NOT EXISTS idx_crm_communications_message_type ON crm_communications(message_type);
CREATE INDEX IF NOT EXISTS idx_crm_communications_created_at ON crm_communications(created_at);
CREATE INDEX IF NOT EXISTS idx_crm_communications_sent_at ON crm_communications(sent_at);

CREATE INDEX IF NOT EXISTS idx_crm_client_preferences_client_id ON crm_client_preferences(client_id);

CREATE INDEX IF NOT EXISTS idx_crm_templates_name ON crm_communication_templates(template_name);
CREATE INDEX IF NOT EXISTS idx_crm_templates_channel ON crm_communication_templates(channel);
CREATE INDEX IF NOT EXISTS idx_crm_templates_message_type ON crm_communication_templates(message_type);
CREATE INDEX IF NOT EXISTS idx_crm_templates_active ON crm_communication_templates(is_active);

CREATE INDEX IF NOT EXISTS idx_crm_delivery_logs_communication_id ON crm_delivery_logs(communication_id);
CREATE INDEX IF NOT EXISTS idx_crm_delivery_logs_channel ON crm_delivery_logs(channel);
CREATE INDEX IF NOT EXISTS idx_crm_delivery_logs_created_at ON crm_delivery_logs(created_at);

-- Apply updated_at trigger to CRM tables
CREATE TRIGGER update_crm_communications_updated_at 
    BEFORE UPDATE ON crm_communications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crm_client_preferences_updated_at 
    BEFORE UPDATE ON crm_client_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crm_templates_updated_at 
    BEFORE UPDATE ON crm_communication_templates 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create analytics view for communication effectiveness
CREATE OR REPLACE VIEW crm_communication_analytics AS
SELECT 
    message_type,
    channel,
    DATE(created_at) as date,
    COUNT(*) as total_sent,
    SUM(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 ELSE 0 END) as delivered_count,
    SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened_count,
    SUM(CASE WHEN clicked_at IS NOT NULL THEN 1 ELSE 0 END) as clicked_count,
    SUM(CASE WHEN status IN ('failed', 'bounced') THEN 1 ELSE 0 END) as failed_count,
    AVG(EXTRACT(EPOCH FROM (delivered_at - sent_at))) as avg_delivery_time_seconds,
    ROUND(
        (SUM(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 ELSE 0 END)::DECIMAL / 
         NULLIF(COUNT(*), 0)) * 100, 
        2
    ) as delivery_rate_percent,
    ROUND(
        (SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END)::DECIMAL / 
         NULLIF(SUM(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 ELSE 0 END), 0)) * 100, 
        2
    ) as open_rate_percent
FROM crm_communications
WHERE sent_at IS NOT NULL
GROUP BY message_type, channel, DATE(created_at);

-- Insert default communication templates
INSERT INTO crm_communication_templates (template_name, message_type, channel, subject_template, body_template, variables) VALUES
(
    'welcome_email',
    'welcome',
    'email',
    'Welcome to Event Planning - Plan {{plan_id}}',
    '<h1>Welcome {{client_name}}!</h1><p>Your event plan <strong>{{plan_id}}</strong> has been created. We''re excited to help you plan your {{event_type}}!</p><p>Next steps: We''ll analyze your requirements and present vendor options within 24 hours.</p>',
    '{"client_name": "string", "plan_id": "string", "event_type": "string"}'::jsonb
),
(
    'budget_summary_email',
    'budget_summary',
    'email',
    'Your Budget Strategies - Plan {{plan_id}}',
    '<h1>Budget Strategies Ready</h1><p>Hi {{client_name}},</p><p>We''ve prepared three budget allocation strategies for your {{event_type}}:</p>{{budget_table}}<p>Review and let us know your preference!</p>',
    '{"client_name": "string", "plan_id": "string", "event_type": "string", "budget_table": "html"}'::jsonb
),
(
    'vendor_options_email',
    'vendor_options',
    'email',
    'Vendor Combinations Ready - Plan {{plan_id}}',
    '<h1>Your Vendor Options</h1><p>Hi {{client_name}},</p><p>We found {{combination_count}} great vendor combinations for your {{event_type}}!</p>{{vendor_cards}}<p><a href="{{selection_link}}">Click here to review and select</a></p>',
    '{"client_name": "string", "plan_id": "string", "event_type": "string", "combination_count": "number", "vendor_cards": "html", "selection_link": "url"}'::jsonb
),
(
    'welcome_sms',
    'welcome',
    'sms',
    NULL,
    'Welcome to Planiva! Your event plan #{{plan_id}} is being created. We''ll notify you when ready.',
    '{"plan_id": "string"}'::jsonb
),
(
    'vendors_ready_whatsapp',
    'vendor_options',
    'whatsapp',
    NULL,
    '🎉 We found {{count}} vendor combinations for your {{event_type}}! Check them out: {{link}}',
    '{"count": "number", "event_type": "string", "link": "url"}'::jsonb
),
(
    'blueprint_ready_whatsapp',
    'blueprint_delivery',
    'whatsapp',
    NULL,
    '✅ Your event blueprint is ready! Download: {{link}}',
    '{"link": "url"}'::jsonb
)
ON CONFLICT (template_name) DO NOTHING;

-- Log migration completion
INSERT INTO agent_performance (agent_name, task_name, execution_time_ms, success) VALUES
('system', 'crm_tables_migration', 0, true);

-- Migration complete
COMMENT ON TABLE crm_communications IS 'Stores all client communications sent through the CRM engine';
COMMENT ON TABLE crm_client_preferences IS 'Stores client communication preferences and opt-out settings';
COMMENT ON TABLE crm_communication_templates IS 'Stores message templates for different channels and message types';
COMMENT ON TABLE crm_delivery_logs IS 'Detailed logs of delivery attempts and API responses';

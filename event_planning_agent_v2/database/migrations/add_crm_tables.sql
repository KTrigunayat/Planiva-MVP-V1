-- Migration v1.3.0: Add CRM Communication Engine tables
-- This migration creates tables for multi-channel client communication tracking

-- Create enum types for CRM
DO $$ BEGIN
    CREATE TYPE message_type AS ENUM (
        'welcome',
        'budget_summary',
        'vendor_options',
        'selection_confirmation',
        'blueprint_delivery',
        'error_notification',
        'reminder'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE message_channel AS ENUM (
        'email',
        'sms',
        'whatsapp'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE urgency_level AS ENUM (
        'critical',
        'high',
        'normal',
        'low'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE communication_status AS ENUM (
        'pending',
        'queued',
        'sent',
        'delivered',
        'opened',
        'clicked',
        'failed',
        'bounced'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Table: crm_communications
-- Stores all communication records sent to clients
CREATE TABLE IF NOT EXISTS crm_communications (
    communication_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES event_plans(plan_id) ON DELETE CASCADE,
    client_id VARCHAR(255) NOT NULL,
    message_type message_type NOT NULL,
    channel message_channel NOT NULL,
    urgency urgency_level NOT NULL DEFAULT 'normal',
    status communication_status NOT NULL DEFAULT 'pending',
    subject VARCHAR(500),
    body TEXT NOT NULL,
    template_name VARCHAR(255),
    context_data JSONB,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: crm_client_preferences
-- Stores client communication preferences and opt-out settings
CREATE TABLE IF NOT EXISTS crm_client_preferences (
    client_id VARCHAR(255) PRIMARY KEY,
    preferred_channels message_channel[] DEFAULT ARRAY['email']::message_channel[],
    timezone VARCHAR(100) DEFAULT 'UTC',
    quiet_hours_start TIME DEFAULT '22:00',
    quiet_hours_end TIME DEFAULT '08:00',
    opt_out_email BOOLEAN DEFAULT FALSE,
    opt_out_sms BOOLEAN DEFAULT FALSE,
    opt_out_whatsapp BOOLEAN DEFAULT FALSE,
    language_preference VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: crm_communication_templates
-- Stores message templates for different channels and message types
CREATE TABLE IF NOT EXISTS crm_communication_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(255) UNIQUE NOT NULL,
    message_type message_type NOT NULL,
    channel message_channel NOT NULL,
    subject_template VARCHAR(500),
    body_template TEXT NOT NULL,
    variables JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: crm_delivery_logs
-- Detailed logs of delivery attempts and API responses
CREATE TABLE IF NOT EXISTS crm_delivery_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    communication_id UUID REFERENCES crm_communications(communication_id) ON DELETE CASCADE,
    channel message_channel NOT NULL,
    attempt_number INTEGER NOT NULL,
    api_provider VARCHAR(100),
    api_request JSONB,
    api_response JSONB,
    status_code INTEGER,
    success BOOLEAN NOT NULL,
    error_details TEXT,
    delivery_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance optimization

-- crm_communications indexes
CREATE INDEX IF NOT EXISTS idx_crm_comm_plan_id ON crm_communications(plan_id);
CREATE INDEX IF NOT EXISTS idx_crm_comm_client_id ON crm_communications(client_id);
CREATE INDEX IF NOT EXISTS idx_crm_comm_status ON crm_communications(status);
CREATE INDEX IF NOT EXISTS idx_crm_comm_message_type ON crm_communications(message_type);
CREATE INDEX IF NOT EXISTS idx_crm_comm_channel ON crm_communications(channel);
CREATE INDEX IF NOT EXISTS idx_crm_comm_urgency ON crm_communications(urgency);
CREATE INDEX IF NOT EXISTS idx_crm_comm_sent_at ON crm_communications(sent_at);
CREATE INDEX IF NOT EXISTS idx_crm_comm_created_at ON crm_communications(created_at);
CREATE INDEX IF NOT EXISTS idx_crm_comm_context_data_gin ON crm_communications USING GIN (context_data);
CREATE INDEX IF NOT EXISTS idx_crm_comm_metadata_gin ON crm_communications USING GIN (metadata);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_crm_comm_client_status ON crm_communications(client_id, status);
CREATE INDEX IF NOT EXISTS idx_crm_comm_plan_status ON crm_communications(plan_id, status);
CREATE INDEX IF NOT EXISTS idx_crm_comm_type_channel ON crm_communications(message_type, channel);

-- crm_client_preferences indexes
CREATE INDEX IF NOT EXISTS idx_crm_prefs_updated_at ON crm_client_preferences(updated_at);

-- crm_communication_templates indexes
CREATE INDEX IF NOT EXISTS idx_crm_templates_name ON crm_communication_templates(template_name);
CREATE INDEX IF NOT EXISTS idx_crm_templates_type ON crm_communication_templates(message_type);
CREATE INDEX IF NOT EXISTS idx_crm_templates_channel ON crm_communication_templates(channel);
CREATE INDEX IF NOT EXISTS idx_crm_templates_active ON crm_communication_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_crm_templates_type_channel ON crm_communication_templates(message_type, channel);

-- crm_delivery_logs indexes
CREATE INDEX IF NOT EXISTS idx_crm_logs_comm_id ON crm_delivery_logs(communication_id);
CREATE INDEX IF NOT EXISTS idx_crm_logs_channel ON crm_delivery_logs(channel);
CREATE INDEX IF NOT EXISTS idx_crm_logs_success ON crm_delivery_logs(success);
CREATE INDEX IF NOT EXISTS idx_crm_logs_created_at ON crm_delivery_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_crm_logs_api_provider ON crm_delivery_logs(api_provider);

-- Create trigger for updated_at on crm_communications
CREATE TRIGGER update_crm_communications_updated_at
    BEFORE UPDATE ON crm_communications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for updated_at on crm_client_preferences
CREATE TRIGGER update_crm_client_preferences_updated_at
    BEFORE UPDATE ON crm_client_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for updated_at on crm_communication_templates
CREATE TRIGGER update_crm_communication_templates_updated_at
    BEFORE UPDATE ON crm_communication_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default templates for email channel
INSERT INTO crm_communication_templates (template_name, message_type, channel, subject_template, body_template, variables) VALUES
(
    'welcome_email',
    'welcome',
    'email',
    'Welcome to Event Planning - Let''s Create Your Perfect Event!',
    'Hi {{client_name}},

Welcome to our Event Planning service! We''re excited to help you create an unforgettable event.

Your event planning journey has begun, and our AI-powered system is ready to assist you every step of the way.

What happens next:
1. We''ll analyze your requirements and preferences
2. Our agents will source the best vendors for your needs
3. You''ll receive personalized recommendations
4. We''ll help you finalize your perfect event plan

If you have any questions, feel free to reach out anytime.

Best regards,
The Event Planning Team',
    '{"client_name": "string"}'::jsonb
),
(
    'budget_summary_email',
    'budget_summary',
    'email',
    'Your Event Budget Summary - {{event_type}}',
    'Hi {{client_name}},

Great news! We''ve prepared a comprehensive budget summary for your {{event_type}}.

Budget Overview:
- Total Budget: {{total_budget}}
- Estimated Cost: {{estimated_cost}}
- Remaining: {{remaining_budget}}

Budget Breakdown:
{{budget_breakdown}}

You can review the detailed breakdown and make adjustments in your planning dashboard.

Next Steps:
{{next_steps}}

Best regards,
The Event Planning Team',
    '{"client_name": "string", "event_type": "string", "total_budget": "string", "estimated_cost": "string", "remaining_budget": "string", "budget_breakdown": "string", "next_steps": "string"}'::jsonb
),
(
    'vendor_options_email',
    'vendor_options',
    'email',
    'Vendor Recommendations for Your {{event_type}}',
    'Hi {{client_name}},

We''ve found some excellent vendor options for your {{event_type}}!

{{vendor_summary}}

All vendors have been carefully selected based on your preferences, budget, and requirements.

Review Options:
{{review_link}}

Please review these options at your convenience. Our system will help you compare and select the best combination.

Best regards,
The Event Planning Team',
    '{"client_name": "string", "event_type": "string", "vendor_summary": "string", "review_link": "string"}'::jsonb
),
(
    'blueprint_delivery_email',
    'blueprint_delivery',
    'email',
    'Your Event Blueprint is Ready! 🎉',
    'Hi {{client_name}},

Exciting news! Your complete event blueprint is ready for review.

Event Details:
- Event Type: {{event_type}}
- Date: {{event_date}}
- Guest Count: {{guest_count}}

Your blueprint includes:
✓ Complete vendor lineup
✓ Detailed timeline
✓ Budget breakdown
✓ Coordination plan

View Your Blueprint:
{{blueprint_link}}

This is your comprehensive guide to making your event a success. Review it carefully and let us know if you need any adjustments.

Best regards,
The Event Planning Team',
    '{"client_name": "string", "event_type": "string", "event_date": "string", "guest_count": "string", "blueprint_link": "string"}'::jsonb
)
ON CONFLICT (template_name) DO NOTHING;

-- Insert default templates for SMS channel
INSERT INTO crm_communication_templates (template_name, message_type, channel, body_template, variables) VALUES
(
    'welcome_sms',
    'welcome',
    'sms',
    'Welcome {{client_name}}! Your event planning journey starts now. We''ll keep you updated every step of the way. Reply STOP to opt out.',
    '{"client_name": "string"}'::jsonb
),
(
    'budget_summary_sms',
    'budget_summary',
    'sms',
    'Hi {{client_name}}, your event budget summary is ready! Total: {{total_budget}}, Estimated: {{estimated_cost}}. Check your email for details.',
    '{"client_name": "string", "total_budget": "string", "estimated_cost": "string"}'::jsonb
),
(
    'blueprint_delivery_sms',
    'blueprint_delivery',
    'sms',
    '🎉 {{client_name}}, your event blueprint is ready! Check your email for the complete plan. Exciting times ahead!',
    '{"client_name": "string"}'::jsonb
)
ON CONFLICT (template_name) DO NOTHING;

-- Insert default templates for WhatsApp channel
INSERT INTO crm_communication_templates (template_name, message_type, channel, body_template, variables) VALUES
(
    'welcome_whatsapp',
    'welcome',
    'whatsapp',
    'Hi {{client_name}}! 👋

Welcome to Event Planning! We''re thrilled to help you create an amazing event.

Your AI-powered planning assistant is ready to work its magic. You''ll receive updates throughout the planning process.

Let''s make this event unforgettable! 🎉',
    '{"client_name": "string"}'::jsonb
),
(
    'budget_summary_whatsapp',
    'budget_summary',
    'whatsapp',
    'Hi {{client_name}}! 💰

Your event budget summary is ready:

📊 Total Budget: {{total_budget}}
💵 Estimated Cost: {{estimated_cost}}
✅ Status: {{budget_status}}

Check your email for the detailed breakdown!',
    '{"client_name": "string", "total_budget": "string", "estimated_cost": "string", "budget_status": "string"}'::jsonb
),
(
    'blueprint_delivery_whatsapp',
    'blueprint_delivery',
    'whatsapp',
    '🎉 Exciting news, {{client_name}}!

Your complete event blueprint is ready! 📋

✨ Everything is planned and ready to go
📧 Check your email for the full details
🎯 Your perfect event awaits!

Let us know if you need any changes!',
    '{"client_name": "string"}'::jsonb
)
ON CONFLICT (template_name) DO NOTHING;

-- Create view for communication analytics
CREATE OR REPLACE VIEW crm_communication_analytics AS
SELECT
    message_type,
    channel,
    status,
    COUNT(*) as total_count,
    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_count,
    COUNT(CASE WHEN status = 'opened' THEN 1 END) as opened_count,
    COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked_count,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
    ROUND(AVG(EXTRACT(EPOCH FROM (delivered_at - sent_at))), 2) as avg_delivery_time_seconds,
    ROUND(AVG(EXTRACT(EPOCH FROM (opened_at - delivered_at))), 2) as avg_open_time_seconds
FROM crm_communications
WHERE sent_at IS NOT NULL
GROUP BY message_type, channel, status;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO eventuser;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO eventuser;

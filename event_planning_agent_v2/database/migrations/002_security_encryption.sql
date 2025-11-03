-- Migration: Security and Encryption
-- Version: 002
-- Description: Add pgcrypto extension for field-level encryption and security enhancements

-- Enable pgcrypto extension for encryption functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT, encryption_key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, encryption_key);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data BYTEA, encryption_key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(encrypted_data, encryption_key);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add encrypted columns to crm_client_preferences table
-- Store encrypted email and phone number for GDPR compliance
ALTER TABLE crm_client_preferences 
ADD COLUMN IF NOT EXISTS email_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS phone_number_encrypted BYTEA,
ADD COLUMN IF NOT EXISTS full_name_encrypted BYTEA;

-- Add audit columns for GDPR compliance
ALTER TABLE crm_client_preferences
ADD COLUMN IF NOT EXISTS data_retention_until TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deletion_reason TEXT;

-- Add opt-out tracking columns for CAN-SPAM compliance
ALTER TABLE crm_client_preferences
ADD COLUMN IF NOT EXISTS opt_out_timestamp TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS opt_out_ip_address INET,
ADD COLUMN IF NOT EXISTS opt_out_user_agent TEXT;

-- Create audit log table for data access tracking (GDPR requirement)
CREATE TABLE IF NOT EXISTS crm_data_access_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(255) NOT NULL,
    access_type VARCHAR(50) NOT NULL, -- 'read', 'write', 'delete', 'export'
    accessed_by VARCHAR(255) NOT NULL, -- user or system identifier
    access_timestamp TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    data_fields JSONB, -- which fields were accessed
    purpose TEXT, -- reason for access
    INDEX idx_data_access_client_id (client_id),
    INDEX idx_data_access_timestamp (access_timestamp),
    INDEX idx_data_access_type (access_type)
);

-- Create table for tracking credential rotations
CREATE TABLE IF NOT EXISTS security_credential_rotations (
    rotation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    credential_type VARCHAR(100) NOT NULL, -- 'whatsapp_token', 'twilio_token', 'smtp_password', 'db_encryption_key'
    rotated_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_by VARCHAR(255) NOT NULL,
    previous_key_hash VARCHAR(255), -- SHA256 hash of previous key for audit
    rotation_reason TEXT,
    next_rotation_due TIMESTAMPTZ,
    INDEX idx_credential_type (credential_type),
    INDEX idx_rotated_at (rotated_at)
);

-- Create table for API credential management
CREATE TABLE IF NOT EXISTS security_api_credentials (
    credential_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) UNIQUE NOT NULL, -- 'whatsapp', 'twilio', 'smtp'
    credential_key_encrypted BYTEA NOT NULL, -- encrypted API key/token
    credential_metadata JSONB, -- additional metadata (endpoints, account IDs, etc.)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    rotation_interval_days INTEGER DEFAULT 90,
    INDEX idx_service_name (service_name),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at)
);

-- Create trigger for credential rotation tracking
CREATE OR REPLACE FUNCTION track_credential_rotation()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.credential_key_encrypted IS DISTINCT FROM NEW.credential_key_encrypted THEN
        INSERT INTO security_credential_rotations (
            credential_type,
            rotated_by,
            previous_key_hash,
            rotation_reason,
            next_rotation_due
        ) VALUES (
            NEW.service_name,
            current_user,
            encode(digest(OLD.credential_key_encrypted, 'sha256'), 'hex'),
            'Credential updated',
            NOW() + (NEW.rotation_interval_days || ' days')::INTERVAL
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_track_credential_rotation
    AFTER UPDATE ON security_api_credentials
    FOR EACH ROW
    EXECUTE FUNCTION track_credential_rotation();

-- Create function for GDPR-compliant data deletion
CREATE OR REPLACE FUNCTION gdpr_delete_client_data(
    p_client_id VARCHAR(255),
    p_deletion_reason TEXT DEFAULT 'Client request - Right to be forgotten'
)
RETURNS BOOLEAN AS $$
DECLARE
    v_deleted_count INTEGER := 0;
BEGIN
    -- Mark deletion request timestamp
    UPDATE crm_client_preferences
    SET 
        deletion_requested_at = NOW(),
        deletion_reason = p_deletion_reason
    WHERE client_id = p_client_id
    AND deleted_at IS NULL;
    
    -- Anonymize communication records (keep for analytics but remove PII)
    UPDATE crm_communications
    SET 
        client_id = 'DELETED_' || encode(digest(client_id, 'sha256'), 'hex'),
        subject = '[REDACTED]',
        body = '[REDACTED - GDPR Deletion]',
        context_data = '{}'::jsonb,
        metadata = jsonb_build_object('gdpr_deleted', true, 'deleted_at', NOW())
    WHERE client_id = p_client_id;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    -- Delete client preferences (soft delete)
    UPDATE crm_client_preferences
    SET 
        deleted_at = NOW(),
        email_encrypted = NULL,
        phone_number_encrypted = NULL,
        full_name_encrypted = NULL,
        preferred_channels = '[]'::jsonb
    WHERE client_id = p_client_id
    AND deleted_at IS NULL;
    
    -- Log the deletion for audit trail
    INSERT INTO crm_data_access_log (
        client_id,
        access_type,
        accessed_by,
        purpose,
        data_fields
    ) VALUES (
        p_client_id,
        'delete',
        current_user,
        p_deletion_reason,
        jsonb_build_object(
            'communications_anonymized', v_deleted_count,
            'preferences_deleted', true
        )
    );
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error deleting client data: %', SQLERRM;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Create function for data export (GDPR right to data portability)
CREATE OR REPLACE FUNCTION gdpr_export_client_data(p_client_id VARCHAR(255))
RETURNS JSONB AS $$
DECLARE
    v_export_data JSONB;
BEGIN
    -- Compile all client data into a single JSON object
    SELECT jsonb_build_object(
        'client_id', p_client_id,
        'export_timestamp', NOW(),
        'preferences', (
            SELECT jsonb_build_object(
                'preferred_channels', preferred_channels,
                'timezone', timezone,
                'quiet_hours_start', quiet_hours_start,
                'quiet_hours_end', quiet_hours_end,
                'opt_out_email', opt_out_email,
                'opt_out_sms', opt_out_sms,
                'opt_out_whatsapp', opt_out_whatsapp,
                'language_preference', language_preference,
                'created_at', created_at,
                'updated_at', updated_at
            )
            FROM crm_client_preferences
            WHERE client_id = p_client_id
        ),
        'communications', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'communication_id', communication_id,
                    'message_type', message_type,
                    'channel', channel,
                    'status', status,
                    'sent_at', sent_at,
                    'delivered_at', delivered_at,
                    'created_at', created_at
                )
            )
            FROM crm_communications
            WHERE client_id = p_client_id
        )
    ) INTO v_export_data;
    
    -- Log the export for audit trail
    INSERT INTO crm_data_access_log (
        client_id,
        access_type,
        accessed_by,
        purpose
    ) VALUES (
        p_client_id,
        'export',
        current_user,
        'GDPR data portability request'
    );
    
    RETURN v_export_data;
END;
$$ LANGUAGE plpgsql;

-- Create view for credential rotation monitoring
CREATE OR REPLACE VIEW security_credential_status AS
SELECT 
    c.service_name,
    c.is_active,
    c.created_at,
    c.updated_at,
    c.expires_at,
    c.last_used_at,
    c.rotation_interval_days,
    c.updated_at + (c.rotation_interval_days || ' days')::INTERVAL as next_rotation_due,
    CASE 
        WHEN c.expires_at < NOW() THEN 'EXPIRED'
        WHEN c.updated_at + (c.rotation_interval_days || ' days')::INTERVAL < NOW() THEN 'OVERDUE'
        WHEN c.updated_at + (c.rotation_interval_days || ' days')::INTERVAL < NOW() + INTERVAL '7 days' THEN 'DUE_SOON'
        ELSE 'CURRENT'
    END as rotation_status,
    (SELECT COUNT(*) FROM security_credential_rotations WHERE credential_type = c.service_name) as rotation_count,
    (SELECT MAX(rotated_at) FROM security_credential_rotations WHERE credential_type = c.service_name) as last_rotation_at
FROM security_api_credentials c;

-- Create indexes for audit log performance
CREATE INDEX IF NOT EXISTS idx_data_access_log_client_timestamp 
ON crm_data_access_log(client_id, access_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_data_access_log_type_timestamp 
ON crm_data_access_log(access_type, access_timestamp DESC);

-- Add comments for documentation
COMMENT ON TABLE crm_data_access_log IS 'Audit log for tracking all access to client data (GDPR compliance)';
COMMENT ON TABLE security_credential_rotations IS 'Tracks history of API credential rotations for security audit';
COMMENT ON TABLE security_api_credentials IS 'Encrypted storage for external API credentials';
COMMENT ON FUNCTION gdpr_delete_client_data IS 'GDPR-compliant function to delete/anonymize client data (Right to be forgotten)';
COMMENT ON FUNCTION gdpr_export_client_data IS 'GDPR-compliant function to export all client data (Right to data portability)';
COMMENT ON COLUMN crm_client_preferences.email_encrypted IS 'Encrypted email address using pgcrypto';
COMMENT ON COLUMN crm_client_preferences.phone_number_encrypted IS 'Encrypted phone number using pgcrypto';
COMMENT ON COLUMN crm_client_preferences.deletion_requested_at IS 'Timestamp when client requested data deletion (GDPR)';

-- Grant necessary permissions (adjust based on your user setup)
-- GRANT EXECUTE ON FUNCTION encrypt_sensitive_data TO eventuser;
-- GRANT EXECUTE ON FUNCTION decrypt_sensitive_data TO eventuser;
-- GRANT EXECUTE ON FUNCTION gdpr_delete_client_data TO eventuser;
-- GRANT EXECUTE ON FUNCTION gdpr_export_client_data TO eventuser;

-- Migration complete
SELECT 'Security and encryption migration completed successfully' as status;

# Implementation Plan - CRM Communication Engine Integration

- [x] 1. Set up database schema and core data models










  - Create PostgreSQL migration script for all CRM tables (crm_communications, crm_client_preferences, crm_communication_templates, crm_delivery_logs)
  - Implement data models (MessageType, MessageChannel, UrgencyLevel, CommunicationStatus enums)
  - Create dataclasses (CommunicationRequest, CommunicationStrategy, CommunicationResult, ClientPreferences)
  - Add database indexes for performance optimization
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 2. Implement Communication Repository









  - Create CommunicationRepository class with database connection management
  - Implement save_communication() method to persist communication records
  - Implement update_status() method to update communication status and timestamps
  - Implement get_history() method with filtering by plan_id, client_id, channel, date_range, status
  - Implement get_analytics() method to query communication effectiveness metrics
  - _Requirements: 5.1, 5.2, 5.3, 5.5, 10.1, 10.2_

- [x] 2.1 Write unit tests for CommunicationRepository



  - Test database CRUD operations
  - Test query filtering and analytics aggregation
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [x] 3. Implement Communication Strategy Tool





  - Create CommunicationStrategyTool class with strategy determination logic
  - Implement determine_strategy() method with channel selection priority logic
  - Implement calculate_optimal_send_time() method with timezone and quiet hours handling
  - Implement should_batch() method for message batching logic
  - Add client preference analysis and timezone checking
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 9.4, 9.5_

- [x] 3.1 Write unit tests for Communication Strategy Tool



  - Test channel selection logic for different urgency levels
  - Test timezone calculations and quiet hours handling
  - Test batching rules
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 4. Implement Email Template System





  - Create EmailTemplateSystem class with template loading and caching
  - Implement load_template() method with filesystem access and caching
  - Implement render() method with variable substitution using Jinja2
  - Implement validate_html() method for HTML structure validation
  - Create HTML email templates (welcome, budget_summary, vendor_options, selection_confirmation, blueprint_delivery, error_notification, reminder)
  - Add responsive CSS styling for mobile and desktop
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 4.1 Write unit tests for Email Template System




  - Test template loading and caching
  - Test variable substitution
  - Test HTML validation
  - _Requirements: 7.1, 7.2, 7.5_

- [x] 5. Implement Email Sub-Agent









  - Create EmailSubAgent class with SMTP configuration
  - Implement compose_and_send() method integrating template system
  - Implement AttachmentHandler for PDF and image attachments
  - Add SMTP connection management with connection pooling
  - Implement track_engagement() method for open and click tracking
  - Add delivery status logging to database
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_
-


- [x] 5.1 Write unit tests for Email Sub-Agent




  - Test email composition with templates
  - Test attachment handling
  - Test SMTP sending with mocks
  - _Requirements: 2.8, 2.9, 2.10_

- [x] 6. Implement API Connector for messaging services






  - Create APIConnector class with WhatsApp and Twilio configuration
  - Implement send_whatsapp_message() method with WhatsApp Business API integration
  - Implement send_sms_message() method with Twilio API integration
  - Implement handle_webhook() method for delivery receipts and status updates
  - Add authentication and request signing for both APIs
  - Implement rate limiting checks before API calls
  - Add error parsing and categorization (transient, permanent, rate_limit, auth_failure)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 6.1 Write unit tests for API Connector


  - Test WhatsApp API integration with mocks
  - Test Twilio API integration with mocks
  - Test webhook handling
  - Test rate limiting logic
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 7. Implement Messaging Sub-Agent







  - Create MessagingSubAgent class with API connector integration
  - Implement ConciseTextGenerator for SMS message composition (< 160 chars)
  - Implement send_whatsapp() method with message formatting
  - Implement send_sms() method with message formatting
  - Implement handle_incoming_message() method for client responses
  - Create message templates (welcome_sms, budget_ready_sms, vendors_ready_whatsapp, selection_needed_sms, blueprint_ready_whatsapp, reminder_sms)
  - Add delivery status tracking and database logging
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

- [x] 7.1 Write unit tests for Messaging Sub-Agent




  - Test message composition and length constraints
  - Test WhatsApp and SMS sending
  - Test incoming message handling
  - _Requirements: 3.7, 3.8, 3.9_

- [x] 8. Implement CRM Agent Orchestrator




  - Create CRMAgentOrchestrator class with sub-agent coordination
  - Implement process_communication_request() method as main entry point
  - Implement route_to_sub_agent() method with channel-based routing
  - Implement handle_client_response() method for workflow state updates
  - Add retry_with_backoff() method with exponential backoff and jitter
  - Add fallback_to_alternative() method for multi-channel fallback
  - Implement communication logging to database with metadata
  - Add error categorization and handling logic
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 8.1 Write unit tests for CRM Agent Orchestrator




  - Test communication request processing
  - Test routing logic
  - Test retry mechanism with exponential backoff
  - Test fallback channel logic
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [x] 9. Integrate CRM engine with LangGraph workflow






  - Add CRM orchestrator initialization in workflow setup
  - Implement communication trigger in initialize_planning node (welcome message)
  - Implement communication trigger in budget_allocation_node (budget summary)
  - Implement communication trigger in beam_search_node with present_options (vendor options)
  - Implement communication trigger in client_selection node (selection confirmation)
  - Implement communication trigger in blueprint_generation node (blueprint delivery)
  - Implement communication trigger in error_handler (error notification)
  - Update WorkflowState to include communications list and last_communication_at
  - Add communication status to workflow state metadata
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [x] 9.1 Write integration tests for workflow triggers


  - Test end-to-end communication flow from each workflow node
  - Test workflow state updates after communication
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 10. Implement client preference management





  - Create API endpoint POST /api/crm/preferences for preference updates
  - Implement preference validation and persistence to crm_client_preferences table
  - Add default preference initialization for new clients
  - Implement preference caching in Redis with 1-hour TTL
  - Add cache invalidation on preference updates
  - Create Streamlit GUI components for preference management (channel selection, timezone, quiet hours, opt-outs)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 10.1 Write unit tests for preference management



  - Test preference validation
  - Test database persistence
  - Test cache operations
  - _Requirements: 9.1, 9.2, 9.3, 9.6_

- [x] 11. Implement security and encryption









  - Add pgcrypto extension to PostgreSQL for field-level encryption
  - Implement encryption for email and phone_number fields in database
  - Add environment variable loading for API credentials (WHATSAPP_ACCESS_TOKEN, TWILIO_AUTH_TOKEN, SMTP_PASSWORD, DB_ENCRYPTION_KEY)
  - Implement HTTPS/TLS validation for all external API calls
  - Add credential rotation documentation and procedures
  - Implement data deletion functionality for GDPR compliance (right to be forgotten)
  - Add opt-out handling for CAN-SPAM compliance
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 12. Implement monitoring and observability





  - Add Prometheus metrics (crm_communications_total, crm_delivery_time_seconds, crm_open_rate, crm_api_errors_total)
  - Implement structured logging with JSON format for all CRM components
  - Add log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) throughout codebase
  - Create health check endpoint for load balancer monitoring
  - Configure alerting rules for critical conditions (auth failure, all channels failed, delivery rate < 90%)
  - _Requirements: 1.4, 11.1, 11.2, 11.3, 11.4_

- [x] 13. Implement analytics and reporting









  - Create analytics query methods for delivery rate, open rate, click-through rate, response rate
  - Implement channel performance comparison queries
  - Implement message type performance queries
  - Create Streamlit dashboard components (overview panel, channel comparison, timeline chart, engagement funnel, preference distribution)
  - Add CSV export functionality for detailed analysis
  - Add PDF report generation for stakeholders
  - Create API endpoint GET /api/crm/analytics for programmatic access
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 13.1 Write unit tests for analytics queries









  - Test metric calculations
  - Test filtering and aggregation
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 14. Implement Redis caching layer









  - Set up Redis connection with connection pooling
  - Implement cache operations for client preferences (1-hour TTL)
  - Implement cache operations for email templates (indefinite TTL with manual invalidation)
  - Implement rate limit counters in Redis for API quota tracking
  - Add cache hit/miss logging for monitoring
  - _Requirements: 4.1, 4.2, 8.6, 9.4_

- [x] 15. Create configuration and environment setup





  - Create .env.template file with all required environment variables
  - Add configuration classes (WhatsAppConfig, TwilioConfig, SMTPConfig, RetryConfig, BatchConfig)
  - Implement configuration validation on startup
  - Add configuration documentation in README
  - Create database migration scripts for schema setup
  - _Requirements: 8.1, 8.2, 11.2, 12.6_

- [x] 16. End-to-end integration testing







  - Test complete workflow from plan creation to blueprint delivery with all communication touchpoints
  - Test multi-channel fallback scenarios
  - Test retry and error handling scenarios
  - Test client preference respect (opt-outs, quiet hours, timezone)
  - Test webhook handling for delivery receipts
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 17. Documentation and deployment preparation





  - Write API documentation for CRM endpoints
  - Create deployment guide with prerequisites and setup steps
  - Document external service setup (WhatsApp Business API, Twilio, SMTP)
  - Create troubleshooting guide for common issues
  - Add code comments and docstrings throughout codebase
  - Create architecture diagram and data flow documentation
  - _Requirements: All requirements_

# CRM Communication Engine - Architecture Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagrams](#architecture-diagrams)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Integration Points](#integration-points)
6. [Technology Stack](#technology-stack)
7. [Design Decisions](#design-decisions)

---

## System Overview

The CRM Communication Engine is a multi-channel communication orchestration system that manages all client interactions throughout the event planning lifecycle. It provides intelligent routing, retry mechanisms, and comprehensive tracking of communications across email, SMS, and WhatsApp channels.

### Key Features

- **Multi-Channel Support**: Email, SMS, WhatsApp
- **Intelligent Routing**: Context-aware channel selection
- **Retry Logic**: Exponential backoff with jitter
- **Fallback Mechanisms**: Multi-channel fallback on failure
- **Template System**: Dynamic content generation
- **Analytics**: Comprehensive communication metrics
- **Compliance**: GDPR, CAN-SPAM compliant

### Design Principles

1. **Stateless Design**: Enables horizontal scaling
2. **Async-First**: Non-blocking I/O for high throughput
3. **Fail-Safe**: Graceful degradation and fallback
4. **Observable**: Comprehensive logging and metrics
5. **Secure**: Encryption at rest and in transit

---

## Architecture Diagrams

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Event Planning Workflow                          │
│                        (LangGraph)                                   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Communication Requests
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CRM Agent Orchestrator                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • Request Processing                                         │  │
│  │  • Strategy Determination                                     │  │
│  │  • Sub-Agent Routing                                          │  │
│  │  • Retry & Fallback Logic                                     │  │
│  │  • State Management                                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────┬────────────────────────────────────────┬───────────────────┘
         │                                        │
         │                                        │
         ▼                                        ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│   Email Sub-Agent       │          │  Messaging Sub-Agent    │
│  ┌──────────────────┐   │          │  ┌──────────────────┐   │
│  │ Template System  │   │          │  │ Text Generator   │   │
│  │ Attachment       │   │          │  │ API Connector    │   │
│  │ SMTP Client      │   │          │  │ Webhook Handler  │   │
│  └──────────────────┘   │          │  └──────────────────┘   │
└────────┬────────────────┘          └────────┬────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│    SMTP Server          │          │  WhatsApp API           │
│  • Gmail                │          │  • Business API         │
│  • SendGrid             │          │  Twilio SMS API         │
│  • AWS SES              │          │  • SMS Gateway          │
└─────────────────────────┘          └─────────────────────────┘

         ┌────────────────────────────────────┐
         │        Data Layer                  │
         │  ┌──────────────┐  ┌────────────┐ │
         │  │ PostgreSQL   │  │   Redis    │ │
         │  │ • Comms Log  │  │ • Cache    │ │
         │  │ • Preferences│  │ • Rate     │ │
         │  │ • Templates  │  │   Limits   │ │
         │  └──────────────┘  └────────────┘ │
         └────────────────────────────────────┘

         ┌────────────────────────────────────┐
         │     Monitoring & Observability     │
         │  ┌──────────────┐  ┌────────────┐ │
         │  │ Prometheus   │  │  Grafana   │ │
         │  │ • Metrics    │  │ • Dashboards│ │
         │  └──────────────┘  └────────────┘ │
         └────────────────────────────────────┘
```

### Component Interaction Diagram

```
┌──────────────┐
│   Workflow   │
│     Node     │
└──────┬───────┘
       │
       │ 1. process_communication_request()
       ▼
┌──────────────────────────────────────────────────────────┐
│              CRM Agent Orchestrator                       │
│                                                           │
│  2. determine_strategy()                                  │
│     ┌─────────────────────────────────────┐             │
│     │  Communication Strategy Tool         │             │
│     │  • Analyze context & preferences     │             │
│     │  • Select primary channel            │             │
│     │  • Calculate send time               │             │
│     │  • Determine fallback channels       │             │
│     └─────────────────────────────────────┘             │
│                                                           │
│  3. route_to_sub_agent()                                 │
│     ┌──────────────┐              ┌──────────────┐      │
│     │ Email Agent  │              │ Messaging    │      │
│     │              │              │ Agent        │      │
│     └──────┬───────┘              └──────┬───────┘      │
│            │                             │               │
└────────────┼─────────────────────────────┼───────────────┘
             │                             │
             │ 4. compose_and_send()       │ 4. send_whatsapp/sms()
             ▼                             ▼
    ┌─────────────────┐          ┌─────────────────┐
    │ Template System │          │  API Connector  │
    │ • Load template │          │ • Format request│
    │ • Render HTML   │          │ • Send API call │
    │ • Validate      │          │ • Parse response│
    └────────┬────────┘          └────────┬────────┘
             │                            │
             │ 5. SMTP send               │ 5. HTTP POST
             ▼                            ▼
    ┌─────────────────┐          ┌─────────────────┐
    │  SMTP Server    │          │  External API   │
    └─────────────────┘          └─────────────────┘
             │                            │
             │ 6. Delivery receipt        │ 6. Webhook callback
             ▼                            ▼
    ┌──────────────────────────────────────────────┐
    │         Communication Repository              │
    │  • Save communication record                  │
    │  • Update delivery status                     │
    │  • Log delivery events                        │
    └──────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Communication Request Flow                    │
└─────────────────────────────────────────────────────────────────┘

1. Workflow Trigger
   ┌──────────────────────────────────────────────────────────┐
   │ budget_allocation_node completes                          │
   │ ↓                                                         │
   │ Create CommunicationRequest:                              │
   │   - plan_id: "abc-123"                                    │
   │   - message_type: "budget_summary"                        │
   │   - context: {budget_strategies: [...]}                   │
   │   - urgency: "normal"                                     │
   └──────────────────────────────────────────────────────────┘
                              ↓
2. Strategy Determination
   ┌──────────────────────────────────────────────────────────┐
   │ CommunicationStrategyTool.determine_strategy()            │
   │ ↓                                                         │
   │ Input:                                                    │
   │   - message_type: "budget_summary"                        │
   │   - urgency: "normal"                                     │
   │   - client_preferences: {channels: ["email", "whatsapp"]} │
   │   - current_time: "2025-10-27T10:30:00Z"                 │
   │ ↓                                                         │
   │ Output:                                                   │
   │   - primary_channel: "email"                              │
   │   - fallback_channels: ["whatsapp", "sms"]                │
   │   - send_time: "2025-10-27T10:30:00Z"                    │
   │   - priority: 2                                           │
   └──────────────────────────────────────────────────────────┘
                              ↓
3. Channel Routing
   ┌──────────────────────────────────────────────────────────┐
   │ CRMAgentOrchestrator.route_to_sub_agent()                 │
   │ ↓                                                         │
   │ if channel == "email":                                    │
   │     EmailSubAgent.compose_and_send()                      │
   │ elif channel in ["sms", "whatsapp"]:                      │
   │     MessagingSubAgent.send_whatsapp/sms()                 │
   └──────────────────────────────────────────────────────────┘
                              ↓
4. Email Composition (if email channel)
   ┌──────────────────────────────────────────────────────────┐
   │ EmailTemplateSystem.render()                              │
   │ ↓                                                         │
   │ Load template: "budget_summary.html"                      │
   │ ↓                                                         │
   │ Substitute variables:                                     │
   │   {{client_name}} → "Priya Sharma"                        │
   │   {{budget_strategies}} → [...]                           │
   │ ↓                                                         │
   │ Validate HTML structure                                   │
   │ ↓                                                         │
   │ Output: Rendered HTML email                               │
   └──────────────────────────────────────────────────────────┘
                              ↓
5. Delivery
   ┌──────────────────────────────────────────────────────────┐
   │ SMTP/API send                                             │
   │ ↓                                                         │
   │ Status: "sent"                                            │
   │ ↓                                                         │
   │ Save to database:                                         │
   │   - communication_id: "comm-456"                          │
   │   - status: "sent"                                        │
   │   - sent_at: "2025-10-27T10:30:05Z"                      │
   └──────────────────────────────────────────────────────────┘
                              ↓
6. Delivery Receipt (async)
   ┌──────────────────────────────────────────────────────────┐
   │ Webhook receives delivery status                          │
   │ ↓                                                         │
   │ Update database:                                          │
   │   - status: "delivered"                                   │
   │   - delivered_at: "2025-10-27T10:30:12Z"                 │
   │ ↓                                                         │
   │ Log delivery event                                        │
   └──────────────────────────────────────────────────────────┘
                              ↓
7. Engagement Tracking (async)
   ┌──────────────────────────────────────────────────────────┐
   │ Client opens email                                        │
   │ ↓                                                         │
   │ Tracking pixel loaded                                     │
   │ ↓                                                         │
   │ Update database:                                          │
   │   - status: "opened"                                      │
   │   - opened_at: "2025-10-27T11:15:30Z"                    │
   │ ↓                                                         │
   │ Client clicks link                                        │
   │ ↓                                                         │
   │ Update database:                                          │
   │   - status: "clicked"                                     │
   │   - clicked_at: "2025-10-27T11:16:45Z"                   │
   └──────────────────────────────────────────────────────────┘
```

### Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Handling & Retry Flow                   │
└─────────────────────────────────────────────────────────────────┘

1. Communication Attempt
   ┌──────────────────────────────────────────────────────────┐
   │ EmailSubAgent.compose_and_send()                          │
   │ ↓                                                         │
   │ Try: SMTP send                                            │
   └──────────────────────────────────────────────────────────┘
                              ↓
                         ┌────┴────┐
                         │ Success?│
                         └────┬────┘
                    Yes ←────┘└────→ No
                    │                │
                    ▼                ▼
   ┌────────────────────────┐  ┌────────────────────────┐
   │ Return success result  │  │ Categorize error       │
   │ Update status: "sent"  │  │ • TRANSIENT            │
   └────────────────────────┘  │ • PERMANENT            │
                               │ • RATE_LIMIT           │
                               │ • AUTH_FAILURE         │
                               └────────┬───────────────┘
                                        │
                                        ▼
                               ┌────────────────────────┐
                               │ Error category?        │
                               └────┬───────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │ TRANSIENT    │  │ RATE_LIMIT   │  │ PERMANENT    │
         │ or           │  │              │  │ or           │
         │ AUTH_FAILURE │  │              │  │ INVALID      │
         └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                │                 │                  │
                ▼                 ▼                  ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │ Retry with   │  │ Retry with   │  │ Don't retry  │
         │ exponential  │  │ longer delay │  │ Mark failed  │
         │ backoff      │  │              │  │ Log error    │
         └──────┬───────┘  └──────┬───────┘  └──────────────┘
                │                 │
                ▼                 ▼
         ┌──────────────────────────────┐
         │ Retry count < max_retries?   │
         └──────┬───────────────────────┘
                │
         Yes ←──┴──→ No
         │            │
         ▼            ▼
┌────────────────┐  ┌────────────────────────┐
│ Wait delay     │  │ Try fallback channel   │
│ • 1st: 1 min   │  │ • Email → WhatsApp     │
│ • 2nd: 5 min   │  │ • WhatsApp → SMS       │
│ • 3rd: 15 min  │  │ • SMS → Email          │
└────────┬───────┘  └────────┬───────────────┘
         │                   │
         │                   ▼
         │          ┌────────────────────────┐
         │          │ Fallback successful?   │
         │          └────────┬───────────────┘
         │                   │
         │            Yes ←──┴──→ No
         │            │            │
         │            ▼            ▼
         │   ┌────────────────┐  ┌────────────────┐
         │   │ Return success │  │ All channels   │
         │   │ with metadata  │  │ failed         │
         │   └────────────────┘  │ • Log critical │
         │                       │ • Alert admin  │
         │                       └────────────────┘
         │
         └──→ Retry attempt
```

---

## Component Details

### 1. CRM Agent Orchestrator

**Purpose**: Central coordinator for all communications

**Key Responsibilities**:
- Process communication requests from workflow
- Determine optimal communication strategy
- Route to appropriate sub-agent
- Implement retry logic with exponential backoff
- Handle fallback to alternative channels
- Log all interactions to database

**Key Methods**:
```python
async def process_communication_request(
    plan_id: str,
    message_type: MessageType,
    context: Dict[str, Any],
    urgency: UrgencyLevel
) -> CommunicationResult

async def route_to_sub_agent(
    strategy: CommunicationStrategy,
    context: Dict[str, Any]
) -> CommunicationResult

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3
) -> Any

async def fallback_to_alternative(
    original_channel: MessageChannel,
    context: Dict[str, Any]
) -> CommunicationResult
```

**State Management**:
- Stateless design (no instance state)
- All state stored in database
- Enables horizontal scaling

---

### 2. Communication Strategy Tool

**Purpose**: Intelligent decision-making for communication routing

**Key Responsibilities**:
- Analyze message type and urgency
- Consider client preferences
- Respect timezone and quiet hours
- Determine channel priority
- Calculate optimal send time
- Decide on message batching

**Decision Matrix**:

| Message Type | Urgency | Primary Channel | Fallback |
|--------------|---------|-----------------|----------|
| welcome | normal | email | sms |
| budget_summary | normal | email | whatsapp |
| vendor_options | high | email | whatsapp, sms |
| selection_confirmation | normal | email | sms |
| blueprint_delivery | high | email (PDF) | whatsapp (link) |
| error_notification | critical | sms | email, whatsapp |
| reminder | low | email | - |

**Timing Rules**:
- CRITICAL: Send immediately
- HIGH: Send within 1 hour
- NORMAL: Send during business hours (9 AM - 6 PM local)
- LOW: Batch and send once daily

---

### 3. Email Sub-Agent

**Purpose**: Handle all email communications

**Components**:
- **Email Template System**: Load and render HTML templates
- **Attachment Handler**: Manage file attachments
- **SMTP Client**: Send emails via SMTP

**Template Variables**:
- `{{client_name}}`: Client's name
- `{{event_type}}`: Type of event
- `{{event_date}}`: Event date
- `{{plan_id}}`: Plan identifier
- Custom variables per template

**Tracking**:
- Delivery status via SMTP response
- Open tracking via 1x1 pixel
- Click tracking via redirect URLs

---

### 4. Messaging Sub-Agent

**Purpose**: Handle SMS and WhatsApp communications

**Components**:
- **Concise Text Generator**: Create brief messages (< 160 chars for SMS)
- **API Connector**: Interface with WhatsApp and Twilio APIs
- **Webhook Handler**: Process delivery receipts

**Message Templates**:
- welcome_sms
- budget_ready_sms
- vendors_ready_whatsapp
- selection_needed_sms
- blueprint_ready_whatsapp
- reminder_sms

---

### 5. Communication Repository

**Purpose**: Database persistence layer

**Key Methods**:
```python
async def save_communication(comm: Communication) -> str
async def update_status(comm_id: str, status: CommunicationStatus) -> None
async def get_history(filters: Dict) -> List[Communication]
async def get_analytics(date_range: Tuple) -> Dict
```

**Database Tables**:
- `crm_communications`: Main communication log
- `crm_client_preferences`: Client preferences
- `crm_communication_templates`: Template metadata
- `crm_delivery_logs`: Detailed delivery events

---

## Integration Points

### 1. LangGraph Workflow Integration

**Trigger Points**:
```python
# In workflow node
async def budget_allocation_node(state: WorkflowState):
    # ... budget calculation logic ...
    
    # Trigger CRM communication
    crm_result = await crm_orchestrator.process_communication_request(
        plan_id=state.plan_id,
        message_type=MessageType.BUDGET_SUMMARY,
        context={
            "client_name": state.client_name,
            "budget_strategies": budget_strategies
        },
        urgency=UrgencyLevel.NORMAL
    )
    
    # Update workflow state
    state.communications.append(crm_result)
    return state
```

**Workflow Nodes with CRM Integration**:
1. `initialize_planning` → Welcome message
2. `budget_allocation_node` → Budget summary
3. `beam_search_node` → Vendor options
4. `client_selection` → Selection confirmation
5. `blueprint_generation` → Blueprint delivery
6. `error_handler` → Error notification

---

### 2. API Integration

**REST Endpoints**:
```
POST   /api/crm/communications          # Send communication
GET    /api/crm/communications          # Get history
GET    /api/crm/communications/{id}     # Get details
POST   /api/crm/preferences              # Update preferences
GET    /api/crm/preferences/{client_id} # Get preferences
GET    /api/crm/analytics                # Get analytics
POST   /api/crm/webhooks/whatsapp       # WhatsApp webhook
POST   /api/crm/webhooks/twilio         # Twilio webhook
GET    /api/crm/health                   # Health check
```

---

### 3. External Service Integration

**WhatsApp Business API**:
```
Endpoint: https://graph.facebook.com/v18.0/{phone_number_id}/messages
Method: POST
Auth: Bearer token
```

**Twilio SMS API**:
```
Endpoint: https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json
Method: POST
Auth: Basic (Account SID + Auth Token)
```

**SMTP Servers**:
- Gmail: smtp.gmail.com:587 (TLS)
- SendGrid: smtp.sendgrid.net:587 (TLS)
- AWS SES: email-smtp.{region}.amazonaws.com:587 (TLS)

---

## Technology Stack

### Backend
- **Language**: Python 3.9+
- **Framework**: FastAPI (async web framework)
- **Workflow**: LangGraph (state machine)
- **Database**: PostgreSQL 13+ (relational data)
- **Cache**: Redis 6+ (caching, rate limiting)
- **ORM**: SQLAlchemy (database abstraction)

### External Services
- **Email**: SMTP (Gmail, SendGrid, AWS SES)
- **SMS**: Twilio API
- **WhatsApp**: WhatsApp Business API (Meta)

### Monitoring
- **Metrics**: Prometheus (time-series metrics)
- **Visualization**: Grafana (dashboards)
- **Logging**: Structured JSON logging
- **Tracing**: OpenTelemetry (distributed tracing)

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose / Kubernetes
- **Web Server**: Uvicorn (ASGI server)
- **Reverse Proxy**: Nginx
- **Process Manager**: Systemd

---

## Design Decisions

### 1. Stateless Orchestrator

**Decision**: CRM Orchestrator maintains no instance state

**Rationale**:
- Enables horizontal scaling
- Simplifies deployment
- Improves fault tolerance
- All state in database/cache

**Trade-offs**:
- Slightly higher database load
- Need for efficient caching

---

### 2. Async/Await Pattern

**Decision**: Use async/await for all I/O operations

**Rationale**:
- Non-blocking I/O improves throughput
- Handle multiple communications concurrently
- Better resource utilization

**Trade-offs**:
- More complex code
- Requires async-compatible libraries

---

### 3. Multi-Channel Fallback

**Decision**: Implement automatic fallback to alternative channels

**Rationale**:
- Ensures critical communications reach clients
- Improves reliability
- Better user experience

**Trade-offs**:
- Increased complexity
- Potential for duplicate messages if timing is off

---

### 4. Template-Based Content

**Decision**: Use Jinja2 templates for email content

**Rationale**:
- Separation of content and logic
- Easy to update templates
- Supports dynamic content
- Reusable across messages

**Trade-offs**:
- Template management overhead
- Need for template versioning

---

### 5. Exponential Backoff with Jitter

**Decision**: Retry with exponential backoff and random jitter

**Rationale**:
- Gives transient issues time to resolve
- Prevents thundering herd
- Industry best practice

**Trade-offs**:
- Delayed delivery on failures
- More complex retry logic

---

### 6. Redis for Caching

**Decision**: Use Redis for caching and rate limiting

**Rationale**:
- Fast in-memory access
- Built-in TTL support
- Atomic operations for rate limiting
- Distributed caching support

**Trade-offs**:
- Additional infrastructure component
- Data loss on Redis failure (acceptable for cache)

---

### 7. PostgreSQL for Persistence

**Decision**: Use PostgreSQL for all persistent data

**Rationale**:
- ACID compliance
- Rich query capabilities
- JSON support (JSONB)
- Mature and reliable

**Trade-offs**:
- Vertical scaling limits
- Need for read replicas at scale

---

## Scalability Considerations

### Horizontal Scaling

**Current Capacity** (single instance):
- 100 communications/minute
- 6,000 communications/hour
- 144,000 communications/day

**Scaling Strategy**:
1. Deploy multiple orchestrator instances
2. Use load balancer (Nginx/ALB)
3. Shared PostgreSQL and Redis
4. No session affinity required (stateless)

**Bottlenecks**:
- Database connections (use connection pooling)
- External API rate limits (implement queuing)
- SMTP rate limits (use multiple SMTP servers)

### Vertical Scaling

**Database**:
- Read replicas for analytics queries
- Connection pooling (max 20 per instance)
- Indexes on frequently queried columns

**Redis**:
- Increase memory allocation
- Use Redis Cluster for sharding
- Separate cache and rate limit instances

---

## Security Architecture

### Data Protection

**At Rest**:
- PostgreSQL field-level encryption (pgcrypto)
- Encrypted fields: email, phone_number
- Encryption key in environment variable

**In Transit**:
- TLS 1.2+ for all external connections
- HTTPS for API endpoints
- Secure WebSocket for real-time updates

### Authentication & Authorization

**API Authentication**:
- JWT Bearer tokens
- Token expiration: 60 minutes
- Refresh token support

**External Service Auth**:
- API keys in environment variables
- Credential rotation quarterly
- Secrets management (AWS Secrets Manager)

### Compliance

**GDPR**:
- Right to access (export API)
- Right to be forgotten (deletion API)
- Consent management
- Data retention policies

**CAN-SPAM**:
- Unsubscribe link in emails
- Honor opt-outs within 10 days
- Physical address in footer
- Accurate subject lines

---

## Performance Metrics

### Target SLAs

- **Availability**: 99.9% uptime
- **Latency**: < 2 seconds (p95)
- **Delivery Rate**: > 95%
- **Email Open Rate**: > 60%
- **SMS Delivery Rate**: > 98%

### Monitoring Metrics

**Application Metrics**:
- `crm_communications_total`: Total communications sent
- `crm_delivery_time_seconds`: Time from send to delivery
- `crm_open_rate`: Email open rate
- `crm_api_errors_total`: API error count

**System Metrics**:
- CPU usage
- Memory usage
- Database connections
- Redis memory usage
- Network I/O

---

## Future Enhancements

1. **Voice Calls**: Integrate with Twilio Voice API
2. **Live Chat**: Real-time chat support
3. **Social Media**: Facebook, Instagram messaging
4. **AI Personalization**: ML-based content optimization
5. **A/B Testing**: Template and timing experiments
6. **Multi-Language**: Internationalization support
7. **Advanced Analytics**: Predictive engagement models

---

## References

- [Design Document](./design.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING_GUIDE.md)

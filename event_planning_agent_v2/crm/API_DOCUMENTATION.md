# CRM Communication Engine - API Documentation

## Overview

The CRM Communication Engine provides RESTful API endpoints for managing client communications, preferences, and analytics. All endpoints use JSON for request and response bodies.

**Base URL**: `http://localhost:8000/api/crm` (development)  
**Authentication**: Bearer token (JWT) required for all endpoints  
**Content-Type**: `application/json`

---

## Table of Contents

1. [Communication Endpoints](#communication-endpoints)
2. [Preference Management](#preference-management)
3. [Analytics and Reporting](#analytics-and-reporting)
4. [Webhook Endpoints](#webhook-endpoints)
5. [Health Check](#health-check)
6. [Error Responses](#error-responses)
7. [Rate Limiting](#rate-limiting)

---

## Communication Endpoints

### Send Communication

Trigger a communication to a client through the CRM engine.

**Endpoint**: `POST /api/crm/communications`

**Request Body**:
```json
{
  "plan_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "660e8400-e29b-41d4-a716-446655440001",
  "message_type": "budget_summary",
  "context": {
    "client_name": "Priya Sharma",
    "event_type": "wedding",
    "event_date": "2025-12-15",
    "budget_strategies": [
      {
        "name": "Conservative",
        "total": 500000,
        "breakdown": {...}
      }
    ]
  },
  "urgency": "normal",
  "preferred_channel": "email"
}
```

**Request Parameters**:
- `plan_id` (string, required): Event plan UUID
- `client_id` (string, required): Client UUID
- `message_type` (string, required): One of: `welcome`, `budget_summary`, `vendor_options`, `selection_confirmation`, `blueprint_delivery`, `error_notification`, `reminder`
- `context` (object, required): Message-specific context data
- `urgency` (string, optional): One of: `critical`, `high`, `normal`, `low`. Default: `normal`
- `preferred_channel` (string, optional): One of: `email`, `sms`, `whatsapp`. Default: determined by strategy

**Response** (200 OK):
```json
{
  "communication_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "sent",
  "channel_used": "email",
  "sent_at": "2025-10-27T10:30:00Z",
  "delivered_at": null,
  "metadata": {
    "subject": "Your Budget Strategies are Ready!",
    "recipient": "priya.sharma@example.com"
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Plan or client not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Communication failed

---

### Get Communication History

Retrieve communication history for a plan or client.

**Endpoint**: `GET /api/crm/communications`

**Query Parameters**:
- `plan_id` (string, optional): Filter by plan ID
- `client_id` (string, optional): Filter by client ID
- `channel` (string, optional): Filter by channel (`email`, `sms`, `whatsapp`)
- `status` (string, optional): Filter by status
- `start_date` (string, optional): ISO 8601 date (e.g., `2025-10-01`)
- `end_date` (string, optional): ISO 8601 date
- `limit` (integer, optional): Max results (default: 50, max: 200)
- `offset` (integer, optional): Pagination offset (default: 0)

**Example Request**:
```
GET /api/crm/communications?plan_id=550e8400-e29b-41d4-a716-446655440000&limit=10
```

**Response** (200 OK):
```json
{
  "total": 15,
  "limit": 10,
  "offset": 0,
  "communications": [
    {
      "communication_id": "770e8400-e29b-41d4-a716-446655440002",
      "plan_id": "550e8400-e29b-41d4-a716-446655440000",
      "client_id": "660e8400-e29b-41d4-a716-446655440001",
      "message_type": "budget_summary",
      "channel": "email",
      "status": "delivered",
      "subject": "Your Budget Strategies are Ready!",
      "created_at": "2025-10-27T10:30:00Z",
      "sent_at": "2025-10-27T10:30:05Z",
      "delivered_at": "2025-10-27T10:30:12Z",
      "opened_at": "2025-10-27T11:15:30Z",
      "clicked_at": null,
      "urgency": "normal",
      "retry_count": 0
    }
  ]
}
```

---

### Get Communication Details

Retrieve detailed information about a specific communication.

**Endpoint**: `GET /api/crm/communications/{communication_id}`

**Path Parameters**:
- `communication_id` (string, required): Communication UUID

**Response** (200 OK):
```json
{
  "communication_id": "770e8400-e29b-41d4-a716-446655440002",
  "plan_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "660e8400-e29b-41d4-a716-446655440001",
  "message_type": "budget_summary",
  "channel": "email",
  "status": "opened",
  "subject": "Your Budget Strategies are Ready!",
  "content": "Dear Priya, your budget strategies are ready...",
  "context": {...},
  "urgency": "normal",
  "created_at": "2025-10-27T10:30:00Z",
  "sent_at": "2025-10-27T10:30:05Z",
  "delivered_at": "2025-10-27T10:30:12Z",
  "opened_at": "2025-10-27T11:15:30Z",
  "clicked_at": null,
  "failed_at": null,
  "error_message": null,
  "retry_count": 0,
  "metadata": {
    "recipient": "priya.sharma@example.com",
    "attachments": [],
    "tracking_enabled": true
  },
  "delivery_logs": [
    {
      "event_type": "sent",
      "event_timestamp": "2025-10-27T10:30:05Z",
      "delivery_status": "accepted"
    },
    {
      "event_type": "delivered",
      "event_timestamp": "2025-10-27T10:30:12Z",
      "delivery_status": "delivered"
    },
    {
      "event_type": "opened",
      "event_timestamp": "2025-10-27T11:15:30Z",
      "delivery_status": "opened"
    }
  ]
}
```

**Error Responses**:
- `404 Not Found`: Communication not found

---

## Preference Management

### Get Client Preferences

Retrieve communication preferences for a client.

**Endpoint**: `GET /api/crm/preferences/{client_id}`

**Path Parameters**:
- `client_id` (string, required): Client UUID

**Response** (200 OK):
```json
{
  "client_id": "660e8400-e29b-41d4-a716-446655440001",
  "preferred_channels": ["email", "whatsapp"],
  "timezone": "Asia/Kolkata",
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "opt_out_email": false,
  "opt_out_sms": false,
  "opt_out_whatsapp": false,
  "created_at": "2025-10-20T09:00:00Z",
  "updated_at": "2025-10-27T10:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Client preferences not found (returns default preferences)

---

### Update Client Preferences

Update communication preferences for a client.

**Endpoint**: `POST /api/crm/preferences`

**Request Body**:
```json
{
  "client_id": "660e8400-e29b-41d4-a716-446655440001",
  "preferred_channels": ["email", "whatsapp"],
  "timezone": "Asia/Kolkata",
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "opt_out_email": false,
  "opt_out_sms": false,
  "opt_out_whatsapp": false
}
```

**Request Parameters**:
- `client_id` (string, required): Client UUID
- `preferred_channels` (array, optional): Array of preferred channels
- `timezone` (string, optional): IANA timezone (e.g., `Asia/Kolkata`)
- `quiet_hours_start` (string, optional): Time in HH:MM format (24-hour)
- `quiet_hours_end` (string, optional): Time in HH:MM format (24-hour)
- `opt_out_email` (boolean, optional): Opt out of email communications
- `opt_out_sms` (boolean, optional): Opt out of SMS communications
- `opt_out_whatsapp` (boolean, optional): Opt out of WhatsApp communications

**Response** (200 OK):
```json
{
  "client_id": "660e8400-e29b-41d4-a716-446655440001",
  "preferred_channels": ["email", "whatsapp"],
  "timezone": "Asia/Kolkata",
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "opt_out_email": false,
  "opt_out_sms": false,
  "opt_out_whatsapp": false,
  "updated_at": "2025-10-27T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid preference values
- `404 Not Found`: Client not found

---

## Analytics and Reporting

### Get Communication Analytics

Retrieve analytics and metrics for communications.

**Endpoint**: `GET /api/crm/analytics`

**Query Parameters**:
- `start_date` (string, optional): ISO 8601 date (default: 30 days ago)
- `end_date` (string, optional): ISO 8601 date (default: today)
- `group_by` (string, optional): Group by `day`, `week`, `month`, `channel`, `message_type` (default: `day`)
- `plan_id` (string, optional): Filter by specific plan
- `client_id` (string, optional): Filter by specific client

**Example Request**:
```
GET /api/crm/analytics?start_date=2025-10-01&end_date=2025-10-27&group_by=channel
```

**Response** (200 OK):
```json
{
  "period": {
    "start_date": "2025-10-01",
    "end_date": "2025-10-27"
  },
  "summary": {
    "total_sent": 1250,
    "total_delivered": 1198,
    "total_opened": 720,
    "total_clicked": 340,
    "total_failed": 52,
    "delivery_rate": 95.84,
    "open_rate": 60.10,
    "click_through_rate": 47.22,
    "avg_delivery_time_seconds": 8.5
  },
  "by_channel": [
    {
      "channel": "email",
      "total_sent": 800,
      "delivered": 770,
      "opened": 480,
      "clicked": 230,
      "failed": 30,
      "delivery_rate": 96.25,
      "open_rate": 62.34,
      "click_through_rate": 47.92
    },
    {
      "channel": "sms",
      "total_sent": 250,
      "delivered": 245,
      "opened": 0,
      "clicked": 0,
      "failed": 5,
      "delivery_rate": 98.00,
      "open_rate": 0,
      "click_through_rate": 0
    },
    {
      "channel": "whatsapp",
      "total_sent": 200,
      "delivered": 183,
      "opened": 240,
      "clicked": 110,
      "failed": 17,
      "delivery_rate": 91.50,
      "open_rate": 131.15,
      "click_through_rate": 45.83
    }
  ],
  "by_message_type": [
    {
      "message_type": "welcome",
      "total_sent": 200,
      "delivered": 195,
      "opened": 140,
      "clicked": 80,
      "open_rate": 71.79,
      "click_through_rate": 57.14
    },
    {
      "message_type": "budget_summary",
      "total_sent": 200,
      "delivered": 192,
      "opened": 130,
      "clicked": 70,
      "open_rate": 67.71,
      "click_through_rate": 53.85
    }
  ]
}
```

---

### Export Analytics

Export analytics data in CSV or PDF format.

**Endpoint**: `GET /api/crm/analytics/export`

**Query Parameters**:
- `format` (string, required): `csv` or `pdf`
- `start_date` (string, optional): ISO 8601 date
- `end_date` (string, optional): ISO 8601 date
- `plan_id` (string, optional): Filter by specific plan
- `client_id` (string, optional): Filter by specific client

**Example Request**:
```
GET /api/crm/analytics/export?format=csv&start_date=2025-10-01&end_date=2025-10-27
```

**Response** (200 OK):
- Content-Type: `text/csv` or `application/pdf`
- Content-Disposition: `attachment; filename="crm_analytics_2025-10-01_2025-10-27.csv"`

---

## Webhook Endpoints

### WhatsApp Webhook

Receive delivery receipts and incoming messages from WhatsApp Business API.

**Endpoint**: `POST /api/crm/webhooks/whatsapp`

**Request Body** (Delivery Receipt):
```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "statuses": [
              {
                "id": "wamid.HBgNMTIzNDU2Nzg5MAA=",
                "status": "delivered",
                "timestamp": "1698412800",
                "recipient_id": "919876543210"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "status": "processed"
}
```

---

### Twilio SMS Webhook

Receive delivery receipts from Twilio SMS API.

**Endpoint**: `POST /api/crm/webhooks/twilio`

**Request Body**:
```
MessageSid=SM1234567890abcdef&
MessageStatus=delivered&
To=%2B919876543210&
From=%2B11234567890&
Timestamp=2025-10-27T10:30:00Z
```

**Response** (200 OK):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

---

## Health Check

### CRM Health Check

Check the health status of the CRM communication engine.

**Endpoint**: `GET /api/crm/health`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-27T10:30:00Z",
  "components": {
    "orchestrator": "healthy",
    "email_agent": "healthy",
    "messaging_agent": "healthy",
    "database": "healthy",
    "redis_cache": "healthy",
    "smtp_server": "healthy",
    "whatsapp_api": "healthy",
    "twilio_api": "healthy"
  },
  "metrics": {
    "pending_communications": 5,
    "failed_communications_last_hour": 2,
    "avg_delivery_time_seconds": 8.5
  }
}
```

**Status Values**:
- `healthy`: All systems operational
- `degraded`: Some non-critical issues detected
- `unhealthy`: Critical issues requiring attention

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid message_type: invalid_type",
    "details": {
      "field": "message_type",
      "allowed_values": ["welcome", "budget_summary", "vendor_options", "selection_confirmation", "blueprint_delivery", "error_notification", "reminder"]
    },
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

| Endpoint | Rate Limit |
|----------|------------|
| `POST /api/crm/communications` | 100 requests/minute per client |
| `GET /api/crm/communications` | 300 requests/minute per client |
| `POST /api/crm/preferences` | 20 requests/minute per client |
| `GET /api/crm/analytics` | 60 requests/minute per client |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698412860
```

When rate limit is exceeded:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "details": {
      "retry_after": 45
    }
  }
}
```

---

## Authentication

All API endpoints require authentication using JWT Bearer tokens.

**Header**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Payload**:
```json
{
  "sub": "client_id",
  "exp": 1698412800,
  "iat": 1698409200,
  "scope": ["crm:read", "crm:write"]
}
```

**Scopes**:
- `crm:read`: Read access to communications and analytics
- `crm:write`: Create and update communications
- `crm:admin`: Full administrative access

---

## Code Examples

### Python

```python
import requests

# Send a communication
response = requests.post(
    "http://localhost:8000/api/crm/communications",
    headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "Content-Type": "application/json"
    },
    json={
        "plan_id": "550e8400-e29b-41d4-a716-446655440000",
        "client_id": "660e8400-e29b-41d4-a716-446655440001",
        "message_type": "budget_summary",
        "context": {
            "client_name": "Priya Sharma",
            "event_type": "wedding"
        },
        "urgency": "normal"
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Communication sent: {result['communication_id']}")
else:
    print(f"Error: {response.json()}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

async function sendCommunication() {
  try {
    const response = await axios.post(
      'http://localhost:8000/api/crm/communications',
      {
        plan_id: '550e8400-e29b-41d4-a716-446655440000',
        client_id: '660e8400-e29b-41d4-a716-446655440001',
        message_type: 'budget_summary',
        context: {
          client_name: 'Priya Sharma',
          event_type: 'wedding'
        },
        urgency: 'normal'
      },
      {
        headers: {
          'Authorization': 'Bearer YOUR_TOKEN',
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('Communication sent:', response.data.communication_id);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

sendCommunication();
```

### cURL

```bash
curl -X POST http://localhost:8000/api/crm/communications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_id": "660e8400-e29b-41d4-a716-446655440001",
    "message_type": "budget_summary",
    "context": {
      "client_name": "Priya Sharma",
      "event_type": "wedding"
    },
    "urgency": "normal"
  }'
```

---

## Support

For API support and questions:
- Email: api-support@planiva.com
- Documentation: https://docs.planiva.com/crm-api
- Status Page: https://status.planiva.com

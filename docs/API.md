# Kea Research Engine - API Documentation

## Overview

Kea is a distributed autonomous research engine with multi-user support.

**Base URL:** `https://api.kea.example.com` or `http://localhost:8000`

**Authentication:** API Key, JWT, or Session Cookie

---

## Authentication

### Register

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

---

## Authentication Headers

```http
# Option 1: API Key
X-API-Key: kea_xxxxxxxxxxxxx

# Option 2: JWT Token
Authorization: Bearer eyJhbG...

# Option 3: Session Cookie (automatic from login)
Cookie: session_id=sess_xxx
```

---

## Conversations

### List Conversations

```http
GET /api/v1/conversations
Authorization: Bearer <token>

Query params:
  - include_archived: bool (default: false)
  - limit: int (default: 50, max: 200)
  - offset: int (default: 0)
```

**Response:**
```json
{
  "conversations": [
    {
      "conversation_id": "uuid",
      "title": "AI Research",
      "message_count": 5,
      "is_archived": false,
      "is_pinned": true,
      "created_at": "2026-01-16T00:00:00Z",
      "updated_at": "2026-01-16T01:00:00Z"
    }
  ],
  "total": 1
}
```

### Create Conversation

```http
POST /api/v1/conversations
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Optional Title"
}
```

### Get Conversation

```http
GET /api/v1/conversations/{id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "conversation": {...},
  "messages": [
    {
      "message_id": "uuid",
      "role": "user",
      "content": "What is AI?",
      "created_at": "2026-01-16T00:00:00Z"
    },
    {
      "message_id": "uuid",
      "role": "assistant",
      "content": "AI is...",
      "sources": [...],
      "created_at": "2026-01-16T00:00:01Z"
    }
  ]
}
```

### Send Message

```http
POST /api/v1/conversations/{id}/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "What is quantum computing?"
}
```

**Response:**
```json
{
  "user_message": {...},
  "assistant_message": {
    "message_id": "uuid",
    "role": "assistant",
    "content": "Quantum computing is...",
    "sources": [
      {"url": "...", "title": "...", "snippet": "..."}
    ]
  },
  "meta": {
    "query_type": "research",
    "confidence": 0.85,
    "sources_count": 5,
    "duration_ms": 1234,
    "was_cached": false
  }
}
```

### Update Conversation

```http
PUT /api/v1/conversations/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "New Title",
  "is_archived": false,
  "is_pinned": true
}
```

### Delete Conversation

```http
DELETE /api/v1/conversations/{id}
Authorization: Bearer <token>
```

### Search Conversations

```http
GET /api/v1/conversations/search?q=quantum
Authorization: Bearer <token>
```

---

## API Keys

### Create API Key

```http
POST /api/v1/users/me/keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Production Key"
}
```

**Response:**
```json
{
  "key_id": "uuid",
  "name": "Production Key",
  "raw_key": "kea_xxxxxxxxxxxx",  // Only shown ONCE
  "created_at": "2026-01-16T00:00:00Z"
}
```

### List API Keys

```http
GET /api/v1/users/me/keys
Authorization: Bearer <token>
```

### Delete API Key

```http
DELETE /api/v1/users/me/keys/{key_id}
Authorization: Bearer <token>
```

---

## Health Checks

### Basic Health

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "api_gateway"
}
```

### Full Health

```http
GET /health/full
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-16T00:00:00Z",
  "checks": {
    "database": {"status": "healthy", "latency_ms": 5},
    "redis": {"status": "healthy", "latency_ms": 2},
    "qdrant": {"status": "healthy", "latency_ms": 10},
    "memory": {"status": "healthy", "used_percent": 45}
  }
}
```

---

## Rate Limiting

Response headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
```

When exceeded (429):
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## Error Responses

```json
{
  "detail": "Error message"
}
```

| Code | Meaning |
|------|---------|
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 422 | Validation error |
| 429 | Rate limited |
| 500 | Server error |

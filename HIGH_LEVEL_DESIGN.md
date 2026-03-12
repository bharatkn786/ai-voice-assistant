# Connect.AI - High-Level Design (HLD)
## System Architecture & Component Interaction

**Created for Interview Presentation**  
**Date:** February 2026  
**Version:** 1.0

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Diagram](#component-diagram)
3. [Data Flow Architecture](#data-flow-architecture)
4. [API Design](#api-design)
5. [Database Design](#database-design)
6. [External Service Integration](#external-service-integration)
7. [State Management](#state-management)
8. [Error Handling Strategy](#error-handling-strategy)
9. [Deployment Architecture](#deployment-architecture)
10. [Capacity Planning](#capacity-planning)

---

## 🏗️ Architecture Overview

### Architectural Pattern
**Hybrid Microservices Architecture** with Event-driven processing

### Key Principles
1. **Separation of Concerns**: Each component has single responsibility
2. **Loose Coupling**: Services communicate via well-defined interfaces
3. **High Cohesion**: Related functionality grouped together
4. **Stateless Design**: Application layer is stateless (state in DB/Cache)
5. **Async First**: Non-blocking I/O for high concurrency

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Phone Device │  │  Web Browser │  │ Twilio Cloud │         │
│  │  (User Call) │  │  (Dashboard) │  │  (Webhooks)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EDGE LAYER                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Cloudflare Tunnel (Reverse Proxy)                │  │
│  │         - SSL/TLS Termination                            │  │
│  │         - DDoS Protection                                │  │
│  │         - CDN Caching                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                             │
│  ┌────────────────────────────┐  ┌────────────────────────┐    │
│  │  Main API Gateway          │  │  Dashboard API         │    │
│  │  (FastAPI - Port 8000)     │  │  (FastAPI - Port 8001) │    │
│  │                            │  │                        │    │
│  │  - Request Validation      │  │  - Analytics APIs      │    │
│  │  - Auth/Security           │  │  - Document Upload     │    │
│  │  - Rate Limiting           │  │  - CORS Handling       │    │
│  │  - Logging                 │  │  - Report Generation   │    │
│  └────────────────────────────┘  └────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Call         │  │ Stream       │  │ Query        │         │
│  │ Orchestrator │  │ Manager      │  │ Processor    │         │
│  │              │  │              │  │              │         │
│  │ - Lifecycle  │  │ - WebSocket  │  │ - RAG Query  │         │
│  │ - State Mgmt │  │ - Audio Flow │  │ - Translation│         │
│  │ - Webhooks   │  │ - Transcripts│  │ - Intent     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │  Twilio    │ │  Deepgram  │ │   Gemini   │ │  Google    │  │
│  │  Client    │ │  Client    │ │   Client   │ │ Translate  │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                             │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │  Repository        │  │  Vector Store      │                │
│  │  - CallRepository  │  │  - Embeddings      │                │
│  │  - DocRepository   │  │  - Index Manager   │                │
│  └────────────────────┘  └────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER                             │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │  MongoDB Atlas     │  │  File System       │                │
│  │  - calls           │  │  - index_storage/  │                │
│  │  - documents       │  │  - pdf/            │                │
│  └────────────────────┘  └────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Diagram

### Main Application Components

```
┌────────────────────────────────────────────────────────┐
│                   Main Application                     │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │            FastAPI Application                   │ │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────┐  │ │
│  │  │  Endpoint  │  │  Endpoint  │  │ WebSocket │  │ │
│  │  │ /start-call│  │  /twiml    │  │  /stream  │  │ │
│  │  └────────────┘  └────────────┘  └───────────┘  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │         Core Business Logic                      │ │
│  │                                                  │ │
│  │  ┌─────────────────────────────────────────┐    │ │
│  │  │  StateManager (Singleton)              │    │ │
│  │  │  ┌──────────────┐  ┌──────────────┐   │    │ │
│  │  │  │  call_states │  │ conversation │   │    │ │
│  │  │  │              │  │   _history   │   │    │ │
│  │  │  └──────────────┘  └──────────────┘   │    │ │
│  │  │  ┌──────────────┐  ┌──────────────┐   │    │ │
│  │  │  │   active_ws  │  │    locks     │   │    │ │
│  │  │  └──────────────┘  └──────────────┘   │    │ │
│  │  └─────────────────────────────────────────┘    │ │
│  │                                                  │ │
│  │  ┌─────────────────────────────────────────┐    │ │
│  │  │  StreamHandler                         │    │ │
│  │  │  ┌──────────────────────────────────┐  │    │ │
│  │  │  │  forward_audio_to_deepgram()    │  │    │ │
│  │  │  │  process_deepgram_transcripts() │  │    │ │
│  │  │  │  keep_deepgram_alive()          │  │    │ │
│  │  │  └──────────────────────────────────┘  │    │ │
│  │  └─────────────────────────────────────────┘    │ │
│  │                                                  │ │
│  │  ┌─────────────────────────────────────────┐    │ │
│  │  │  LLMHandler                            │    │ │
│  │  │  ┌──────────────────────────────────┐  │    │ │
│  │  │  │  process_university_query()      │  │    │ │
│  │  │  │  - detect_language               │  │    │ │
│  │  │  │  - translate_input               │  │    │ │
│  │  │  │  - query_rag                     │  │    │ │
│  │  │  │  - detect_intent                 │  │    │ │
│  │  │  │  - translate_response            │  │    │ │
│  │  │  └──────────────────────────────────┘  │    │ │
│  │  └─────────────────────────────────────────┘    │ │
│  │                                                  │ │
│  │  ┌─────────────────────────────────────────┐    │ │
│  │  │  RAGSystem                             │    │ │
│  │  │  ┌──────────────────────────────────┐  │    │ │
│  │  │  │  create_rag_system()             │  │    │ │
│  │  │  │  - load_index                    │  │    │ │
│  │  │  │  - create_retriever              │  │    │ │
│  │  │  │  - create_reranker               │  │    │ │
│  │  │  │  - build_query_engine            │  │    │ │
│  │  │  └──────────────────────────────────┘  │    │ │
│  │  └─────────────────────────────────────────┘    │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │         Utility Services                         │ │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────┐  │ │
│  │  │    TTS     │  │ Translator │  │ Database │  │ │
│  │  │  Service   │  │  Service   │  │ Service  │  │ │
│  │  └────────────┘  └────────────┘  └──────────┘  │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Key Methods |
|-----------|---------------|-------------|
| **FastAPI App** | HTTP request handling | `start_call()`, `generate_twiml()`, `speech_complete()` |
| **StateManager** | Centralized state | `register_call()`, `update_call_state()`, `end_call()` |
| **StreamHandler** | WebSocket processing | `twilio_stream_websocket()`, audio forwarding |
| **LLMHandler** | Query processing | `process_university_query()`, translation |
| **RAGSystem** | Document retrieval | `create_rag_system()`, `query_llm_with_data()` |
| **TTSService** | Text-to-speech | `speak_async()`, TwiML generation |
| **DatabaseService** | Data persistence | `save_call_to_db()`, `save_conversation()` |

---

## 🔄 Data Flow Architecture

### Request-Response Flow

```
┌───────────┐
│  Client   │
└─────┬─────┘
      │ 1. HTTP POST /start-call
      ▼
┌─────────────────┐
│  FastAPI Server │
└─────┬───────────┘
      │ 2. Validate request
      │ 3. Create call record (DB)
      ▼
┌─────────────────┐
│  Twilio API     │
└─────┬───────────┘
      │ 4. Initiate call
      │ 5. Request TwiML
      ▼
┌─────────────────┐
│  /twiml         │
└─────┬───────────┘
      │ 6. Return greeting + WebSocket URL
      ▼
┌─────────────────┐
│  WebSocket      │
│  Connection     │
└─────┬───────────┘
      │ 7. Bi-directional stream
      │
      ├─→ [Audio Out] → Twilio → User
      │
      └─→ [Audio In] → Deepgram → Text
                           │
                           ▼
                    ┌──────────────┐
                    │ LLM Pipeline │
                    │              │
                    │ Translation  │
                    │      ↓       │
                    │    RAG       │
                    │      ↓       │
                    │   Gemini     │
                    │      ↓       │
                    │ Translation  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  TTS Service │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Twilio Speak │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Webhook    │
                    │ /speech-     │
                    │  complete    │
                    └──────────────┘
```

### Event-Driven Flow

```
Event Bus (In-Memory)
┌────────────────────────────────────────────────────┐
│                                                    │
│  Event: CALL_STARTED                              │
│  ├─→ Handler: StateManager.register_call()        │
│  └─→ Handler: Database.save_call_to_db()          │
│                                                    │
│  Event: SPEECH_DETECTED                           │
│  ├─→ Handler: LLMHandler.process_query()          │
│  └─→ Handler: StateManager.update_state()         │
│                                                    │
│  Event: RESPONSE_GENERATED                        │
│  ├─→ Handler: TTSService.speak_async()            │
│  └─→ Handler: Database.save_conversation()        │
│                                                    │
│  Event: CALL_ENDED                                │
│  ├─→ Handler: StateManager.end_call()             │
│  ├─→ Handler: WebSocket.close()                   │
│  └─→ Handler: Database.update_call_status()       │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 🌐 API Design

### REST API Endpoints

#### Main Application API (Port 8000)

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/` | Home page | - | HTML template |
| `POST` | `/start-call` | Initiate call | `name`, `phone`, `country_code` | HTML template with status |
| `POST` | `/twiml` | Generate TwiML | Twilio form data | TwiML XML |
| `POST` | `/speech-complete/{call_sid}` | Speech webhook | Twilio form data | TwiML XML |
| `POST` | `/call-status` | Status update | Twilio form data | `"OK"` |
| `WS` | `/twilio-stream` | WebSocket stream | WebSocket messages | WebSocket messages |
| `POST` | `/api/process-documents` | Trigger RAG update | - | `{"message": "Processing started"}` |

#### Dashboard API (Port 8001)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/` | Health check | `{"message": "Backend running"}` |
| `GET` | `/api/calls` | Get all calls | `{"success": true, "data": [...]}` |
| `GET` | `/api/calls/status-summary` | Call statistics | `{"success": true, "data": [...]}` |
| `GET` | `/api/calls/active` | Active calls only | `{"success": true, "data": [...]}` |
| `GET` | `/api/calls/{call_sid}` | Single call details | `{"success": true, "data": {...}}` |
| `POST` | `/api/upload/document` | Upload PDF/TXT | `{"success": true, "message": "..."}` |
| `GET` | `/api/upload/status` | Upload stats | `{"pending": 0, "processed": 5}` |

### WebSocket Protocol

#### Client → Server Messages

```json
{
  "event": "start",
  "start": {
    "callSid": "CA1234567890abcdef",
    "streamSid": "MZ1234567890abcdef",
    "customParameters": {}
  }
}
```

```json
{
  "event": "media",
  "media": {
    "payload": "base64_encoded_audio",
    "timestamp": "1234567890"
  }
}
```

```json
{
  "event": "stop",
  "stop": {
    "callSid": "CA1234567890abcdef"
  }
}
```

#### Server → Client Messages

```json
{
  "event": "connected",
  "protocol": "Call",
  "version": "1.0.0"
}
```

---

## 💾 Database Design

### MongoDB Schema Design

#### Collection: `calls`

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "call_sid": "CA1234567890abcdef",
  "phone_number": "+919876543210",
  "caller_name": "John Doe",
  "status": "completed",
  "created_at": "2026-02-08T10:30:00.000Z",
  "updated_at": "2026-02-08T10:35:00.000Z",
  "conversation": [
    {
      "question": "What is the fee structure?",
      "answer": "The annual fee is one lakh fifty thousand rupees...",
      "timestamp": "2026-02-08T10:31:00.000Z"
    },
    {
      "question": "Tell me about placements",
      "answer": "Our placement rate is 95% with average package...",
      "timestamp": "2026-02-08T10:32:30.000Z"
    }
  ]
}
```

**Indexes:**
```javascript
db.calls.createIndex({ "call_sid": 1 }, { unique: true })
db.calls.createIndex({ "status": 1 })
db.calls.createIndex({ "created_at": -1 })
db.calls.createIndex({ "phone_number": 1 })
```

#### Collection: `uploaded_documents`

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "filename": "university_prospectus.pdf",
  "file_data": BinData(0, "base64_encoded_pdf_content"),
  "file_size": 2457600,
  "uploaded_at": "2026-02-08T09:00:00.000Z",
  "processed": true,
  "processed_at": "2026-02-08T09:05:00.000Z"
}
```

**Indexes:**
```javascript
db.uploaded_documents.createIndex({ "processed": 1 })
db.uploaded_documents.createIndex({ "uploaded_at": -1 })
```

### Vector Store Structure

```
index_storage/
├── docstore.json           # Document chunks with metadata
├── index_store.json        # Index configuration
├── default__vector_store.json  # 384-dim embeddings
└── graph_store.json        # Document relationships
```

**docstore.json structure:**
```json
{
  "docstore/data": {
    "node_id_1": {
      "text": "Chitkara University offers B.Tech programs in...",
      "metadata": {
        "file_name": "courses.pdf",
        "page": 5
      }
    }
  }
}
```

### Data Retention Policy

| Data Type | Retention Period | Action |
|-----------|-----------------|--------|
| Call Records | 90 days | Archive to S3, delete from MongoDB |
| Conversations | 90 days | Archive with call records |
| Uploaded Documents | Permanent | Keep in MongoDB |
| Vector Embeddings | Until document deleted | Delete when doc removed |
| Application Logs | 30 days | Rotate and compress |

---

## 🔌 External Service Integration

### 1. Twilio Integration

**Purpose**: Cloud telephony and voice streaming

**API Endpoints Used:**
```python
# Initiate call
client.calls.create(
    to="+919876543210",
    from_="+18884990559",
    url="https://domain.com/twiml",
    status_callback="https://domain.com/call-status"
)

# Update ongoing call with TwiML
client.calls(call_sid).update(twiml=twiml_string)
```

**WebSocket URL**: 
```
wss://api.twilio.com/2010-04-01/Streams/{stream_sid}
```

**Authentication**: Account SID + Auth Token (HTTP Basic Auth)

### 2. Deepgram Integration

**Purpose**: Real-time speech-to-text

**WebSocket URL:**
```
wss://api.deepgram.com/v1/listen?
  encoding=mulaw&
  sample_rate=8000&
  channels=1&
  model=nova-2&
  punctuate=true&
  interim_results=false&
  language=hi
```

**Authentication**: Token-based (Authorization header)

**Message Format:**
```json
{
  "channel": {
    "alternatives": [{
      "transcript": "मुझे फीस के बारे में बताइए",
      "confidence": 0.94
    }]
  },
  "is_final": true
}
```

### 3. Google Gemini Integration

**Purpose**: Large Language Model for responses

**API Configuration:**
```python
from llama_index.llms.gemini import Gemini

llm = Gemini(
    api_key="GOOGLE_API_KEY",
    model_name="gemini-2.5-flash",
    temperature=0.0,
    streaming=True
)
```

**Rate Limits:**
- 60 requests per minute
- 1M tokens per day (free tier)

**Retry Strategy:**
```python
for attempt in range(3):
    try:
        response = llm.query(prompt)
        break
    except Exception as e:
        if "503" in str(e):
            time.sleep((attempt + 1) * 3)
```

### 4. Google Translate Integration

**Purpose**: Multi-language support

**Library**: deep-translator

**Fallback Chain:**
```
Google Translate (Primary)
    ↓ (if fails)
MyMemory Translation
    ↓ (if fails)
Use original text
```

**Chunking Strategy** (for long texts):
```python
if len(text) > 450:
    chunks = split_by_sentences(text, max_length=450)
    translated = [translate(chunk) for chunk in chunks]
    result = join(translated)
```

### Service Health Monitoring

```python
# Health check matrix
services = {
    "twilio": {"status": "healthy", "latency_ms": 120},
    "deepgram": {"status": "healthy", "latency_ms": 450},
    "gemini": {"status": "degraded", "latency_ms": 3200},
    "mongodb": {"status": "healthy", "latency_ms": 25}
}
```

---

## 🎛️ State Management

### State Machine Diagram

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  ┌─────────┐                                   │
│  │ INITIAL │ ─────────────────┐                │
│  └─────────┘                  │                │
│       │                       │                │
│       │ register_call()       │                │
│       ▼                       │                │
│  ┌──────────┐                 │                │
│  │ SPEAKING │◄────────────────┤                │
│  └──────────┘                 │                │
│       │                       │                │
│       │ speech_complete       │                │
│       ▼                       │                │
│  ┌──────────────┐             │                │
│  │WAITING_INPUT │             │                │
│  └──────────────┘             │                │
│       │                       │                │
│       │ user speaks           │                │
│       ▼                       │                │
│  ┌────────────┐               │                │
│  │PROCESSING  │               │                │
│  └────────────┘               │                │
│       │                       │                │
│       │ response ready        │                │
│       └───────────────────────┘                │
│                                                 │
│  ┌──────────────┐                              │
│  │SILENCE_CHECK │                              │
│  └──────────────┘                              │
│       │                                         │
│       │ 3 silences                              │
│       ▼                                         │
│  ┌─────────┐                                   │
│  │ GOODBYE │                                   │
│  └─────────┘                                   │
│       │                                         │
│       │ cleanup()                               │
│       ▼                                         │
│  ┌───────────┐                                 │
│  │ COMPLETED │                                 │
│  └───────────┘                                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

### State Storage

**In-Memory (StateManager):**
```python
_call_states = {
    "CA123": {
        "status": "WAITING_INPUT",
        "start_time": 1707390000.123,
        "last_update": 1707390015.456,
        "should_hangup": False,
        "is_followup": False
    }
}
```

**Distributed (Redis - for scaling):**
```python
redis.hset("call:CA123", mapping={
    "status": "WAITING_INPUT",
    "start_time": "1707390000.123",
    "detected_lang": "hi"
})
```

### State Transitions

| From State | Event | To State | Action |
|------------|-------|----------|--------|
| INITIAL | register_call() | SPEAKING | Play greeting |
| SPEAKING | speech_complete | WAITING_INPUT | Start silence timer |
| WAITING_INPUT | user_speech | PROCESSING | Query LLM |
| PROCESSING | response_ready | SPEAKING | Speak response |
| WAITING_INPUT | 3_silences | GOODBYE | Farewell message |
| ANY | call_ended | COMPLETED | Cleanup resources |

---

## ⚠️ Error Handling Strategy

### Error Categories

#### 1. Network Errors
```python
class NetworkError:
    - ConnectionTimeout
    - ConnectionRefused
    - SocketError
    
Action: Retry with exponential backoff (3 attempts)
```

#### 2. API Errors
```python
class APIError:
    - RateLimitExceeded (429)
    - ServiceUnavailable (503)
    - Unauthorized (401)
    
Action: 
- 429: Wait and retry
- 503: Exponential backoff
- 401: Log and alert (configuration issue)
```

####3. Business Logic Errors
```python
class BusinessError:
    - InvalidPhoneNumber
    - CallAlreadyActive
    - DocumentNotFound
    
Action: Return user-friendly error message
```

### Retry Strategies

**Exponential Backoff:**
```python
def exponential_backoff(attempt):
    wait_time = (2 ** attempt) + random.uniform(0, 1)
    return min(wait_time, 60)  # Max 60 seconds

# Usage
for attempt in range(3):
    try:
        result = api_call()
        break
    except RetryableError:
        if attempt < 2:
            time.sleep(exponential_backoff(attempt))
```

**Circuit Breaker Pattern:**
```python
class CircuitBreaker:
    CLOSED: Normal operation
    OPEN: Stop calls after 5 failures
    HALF_OPEN: Try 1 request after 30s
    
    if state == OPEN and time_since_open > 30:
        state = HALF_OPEN
        try_one_request()
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "DEEPGRAM_CONNECTION_FAILED",
    "message": "Unable to connect to speech service",
    "timestamp": "2026-02-08T10:30:00Z",
    "call_sid": "CA123",
    "retryable": true
  }
}
```

---

## 🚀 Deployment Architecture

### Production Deployment

```
┌─────────────────────────────────────────────────┐
│           Internet (Users)                      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│       Cloudflare CDN & DDoS Protection          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│       Cloudflare Tunnel (SSL Termination)       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│       Nginx Load Balancer                       │
│       (Round-robin to app servers)              │
└───────┬──────────────────────┬──────────────────┘
        │                      │
   ┌────▼─────┐           ┌────▼─────┐
   │  App     │           │  App     │
   │ Server 1 │           │ Server 2 │
   │ (8000)   │           │ (8000)   │
   └────┬─────┘           └────┬─────┘
        │                      │
        └──────────┬───────────┘
                   │
        ┌──────────▼──────────┐
        │  Redis (State)      │
        │  - Session Data     │
        │  - Cache            │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  MongoDB Atlas      │
        │  (3-node replica)   │
        └─────────────────────┘
```

### Container Architecture (Docker)

```dockerfile
# Main application
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "hello:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  main-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=${MONGODB_URL}
    depends_on:
      - redis
  
  dashboard:
    build: ./Dashboard
    ports:
      - "8001:8001"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: connect-ai-app
spec:
  replicas: 5
  selector:
    matchLabels:
      app: connect-ai
  template:
    spec:
      containers:
      - name: app
        image: connect-ai:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## 📊 Capacity Planning

### Current Capacity (Single Server)

| Resource | Capacity | Utilization |
|----------|----------|-------------|
| **CPU** | 4 cores | 60% avg |
| **Memory** | 8 GB | 4.5 GB used |
| **Network** | 1 Gbps | 200 Mbps avg |
| **Concurrent Calls** | 50 | - |
| **Database Connections** | 100 | 30 active |

### Scaling Thresholds

| Metric | Warning (Scale Up at) | Critical |
|--------|----------------------|----------|
| CPU Usage | > 70% for 5 min | > 85% |
| Memory Usage | > 80% | > 90% |
| Active Calls | > 40 | > 45 |
| Response Time | > 6 seconds | > 10 seconds |
| Error Rate | > 2% | > 5% |

### Projected Capacity (10x Scale)

```
Traffic Estimation:
- Peak hours: 500 concurrent calls
- Daily calls: 50,000
- Monthly calls: 1.5M

Infrastructure Need:
- App Servers: 10 instances (50 calls each)
- MongoDB: M30 cluster (3 nodes)
- Redis: 16 GB cluster
- Network: 10 Gbps
- Estimated Cost: $5,700/month
```

---

## 📝 Summary

The High-Level Design demonstrates:

✅ **Layered Architecture** with clear separation of concerns  
✅ **Scalable Components** designed for horizontal scaling  
✅ **Robust API Design** following REST best practices  
✅ **Efficient Database Schema** optimized for query patterns  
✅ **External Service Integration** with proper error handling  
✅ **State Management** supporting concurrent operations  
✅ **Production-Ready Deployment** with containerization support  

This HLD serves as a blueprint for implementation and provides clear interfaces between components.

---

**Document Version**: 1.0  
**Last Updated**: February 8, 2026  
**Next**: See LOW_LEVEL_DESIGN.md for implementation details

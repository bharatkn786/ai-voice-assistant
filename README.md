# 🤖 Connect.AI - AI-Powered Voice Assistant for University Admissions

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115.6-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18.x-61DAFB.svg" alt="React">
  <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248.svg" alt="MongoDB">
  <img src="https://img.shields.io/badge/LLM-Gemini%202.5-orange.svg" alt="Gemini">
</p>

> **An intelligent, multilingual voice assistant** that handles university admission inquiries via phone calls using real-time speech recognition, RAG-powered responses, and natural language processing.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
  - [High-Level Design](#high-level-design-hld)
  - [Low-Level Design](#low-level-design-lld)
- [Core Components](#-core-components)
- [Data Flow](#-data-flow)
- [API Documentation](#-api-documentation)
- [Database Schema](#-database-schema)
- [Installation & Setup](#-installation--setup)
- [Project Structure](#-project-structure)
- [Performance Optimizations](#-performance-optimizations)
- [Future Enhancements](#-future-enhancements)

---

## 🎯 Overview

**Connect.AI** is a production-ready AI voice assistant designed for **Chitkara University's admissions department**. It automates phone-based inquiries by:

1. **Receiving phone calls** via Twilio's programmable voice
2. **Converting speech to text** in real-time using Deepgram's Nova-2 model
3. **Understanding queries** using RAG (Retrieval-Augmented Generation) with LlamaIndex
4. **Generating contextual responses** via Google Gemini 2.5 Flash
5. **Speaking responses** back to callers in Hindi or English
6. **Logging all conversations** to MongoDB for analytics

### 🎬 Demo Flow
```
User calls → Twilio → WebSocket Stream → Deepgram STT → RAG Query → Gemini LLM → TTS → User hears response
```

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Voice Processing** | Bi-directional WebSocket streaming with Twilio |
| **Multilingual Support** | Hindi & English with automatic language detection |
| **RAG-Powered Knowledge** | Context-aware answers from university documents |
| **Intelligent State Management** | Thread-safe call state tracking with minimal locking |
| **Progressive Silence Detection** | Adaptive timeouts (6s → 8s → 10s) with 3-strike system |
| **Auto Follow-up Questions** | Gemini generates contextual follow-ups to keep conversation flowing |
| **Conversation Persistence** | Full call transcripts saved to MongoDB Atlas |
| **Admin Dashboard** | React-based UI for monitoring calls and uploading documents |
| **Document Hot-Reload** | Upload PDFs → Auto-rebuild vector index → Immediate availability |

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | Async web framework with WebSocket support |
| **Python 3.10+** | Core language |
| **Twilio SDK** | Voice calls & media streaming |
| **Deepgram** | Real-time speech-to-text (Nova-2 model) |
| **LlamaIndex** | RAG orchestration & vector retrieval |
| **Google Gemini 2.5** | LLM for response generation |
| **HuggingFace Embeddings** | BAAI/bge-small-en-v1.5 for semantic search |
| **MongoDB Atlas** | Cloud database for call logs |
| **Cloudflare Tunnel** | Secure webhook exposure |

### Frontend (Dashboard)
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **TailwindCSS** | Styling |
| **Chart.js** | Call analytics visualization |

### External Services
| Service | Function |
|---------|----------|
| **Twilio** | Telephony infrastructure |
| **Deepgram** | Speech recognition |
| **Google AI** | Gemini LLM + Translation |
| **MongoDB Atlas** | Database hosting |

---

## 🏗 System Architecture

### High-Level Design (HLD)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│   │   Phone     │    │   Browser   │    │   Twilio    │                    │
│   │   (User)    │    │ (Dashboard) │    │   Cloud     │                    │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                    │
└──────────┼──────────────────┼──────────────────┼────────────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EDGE LAYER (Cloudflare)                            │
│              SSL/TLS Termination │ DDoS Protection │ CDN                    │
└─────────────────────────────────────────────────────────────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                                    │
│   ┌─────────────────────────────┐    ┌─────────────────────────────┐        │
│   │    Main API (Port 8000)     │    │  Dashboard API (Port 8001)  │        │
│   │    FastAPI + WebSocket      │    │      FastAPI REST           │        │
│   └─────────────────────────────┘    └─────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ORCHESTRATION LAYER                                    │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                   │
│   │ StateManager  │  │ StreamHandler │  │  LLMHandler   │                   │
│   │ (Call States) │  │  (WebSocket)  │  │ (RAG Query)   │                   │
│   └───────────────┘  └───────────────┘  └───────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                                        │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│   │  Twilio  │  │ Deepgram │  │  Gemini  │  │ Translate│  │   TTS    │     │
│   │  Client  │  │  Client  │  │   LLM    │  │  Service │  │ Service  │     │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PERSISTENCE LAYER                                      │
│   ┌─────────────────────────────┐    ┌─────────────────────────────┐        │
│   │      MongoDB Atlas          │    │    Vector Store (Local)     │        │
│   │   - calls collection        │    │   - docstore.json           │        │
│   │   - documents collection    │    │   - vector_store.json       │        │
│   └─────────────────────────────┘    └─────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Low-Level Design (LLD)

#### State Machine - Call Lifecycle

```
                    ┌─────────────┐
                    │   INITIAL   │
                    └──────┬──────┘
                           │ register_call()
                           ▼
                    ┌─────────────┐
         ┌─────────│  SPEAKING   │◄────────────┐
         │         └──────┬──────┘             │
         │                │ speech_complete    │ speak_async()
         │                │ webhook            │
         │                ▼                    │
         │         ┌─────────────┐             │
         │         │WAITING_INPUT│─────────────┤
         │         └──────┬──────┘             │
         │                │ transcript         │
         │                │ received           │
         │                ▼                    │
         │         ┌─────────────┐             │
         │         │ PROCESSING  │─────────────┘
         │         └──────┬──────┘
         │                │ goodbye detected
         │                ▼
         │         ┌─────────────┐
         └────────►│    ENDED    │
    (3 silences)   └─────────────┘
```

#### Class Diagram - StateManager

```
┌─────────────────────────────────────────────────────────┐
│                    StateManager                         │
├─────────────────────────────────────────────────────────┤
│ - _write_lock: threading.Lock                           │
│ - _webhook_lock: threading.Lock                         │
│ - _call_states: Dict[str, Dict]                         │
│ - _conversation_states: DefaultDict[str, Dict]          │
│ - _conversation_history: DefaultDict[str, List]         │
│ - _active_websockets: Dict[str, WebSocket]              │
│ - _webhook_processing: Set[str]                         │
├─────────────────────────────────────────────────────────┤
│ + register_call(call_sid, initial_state) → bool         │
│ + update_call_state(call_sid, new_state) → bool         │
│ + is_call_active(call_sid) → bool       [Lock-free]     │
│ + end_call(call_sid) → bool                             │
│ + add_to_conversation_history(...)  → bool              │
│ + get_conversation_context(call_sid) → str              │
│ + start_webhook_processing(call_sid) → bool             │
│ + end_webhook_processing(call_sid)                      │
└─────────────────────────────────────────────────────────┘
```

#### RAG Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RAG QUERY PIPELINE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   User Query                                                        │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  STAGE 1: Language Detection & Translation              │      │
│   │  langdetect → detect(text) → 'hi' or 'en'               │      │
│   │  deep_translator → translate_to_english()               │      │
│   └─────────────────────────────────────────────────────────┘      │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  STAGE 2: Embedding Generation                          │      │
│   │  HuggingFace BGE-small-en-v1.5 → 384-dim vector         │      │
│   │  Complexity: O(d) where d=384                           │      │
│   └─────────────────────────────────────────────────────────┘      │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  STAGE 3: Vector Retrieval                              │      │
│   │  Cosine Similarity Search → Top-3 chunks                │      │
│   │  Complexity: O(log n) with index                        │      │
│   └─────────────────────────────────────────────────────────┘      │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  STAGE 4: Cross-Encoder Reranking                       │      │
│   │  ms-marco-MiniLM-L-6-v2 → Re-score & select top-3       │      │
│   │  Complexity: O(k×m) where k=candidates, m=model         │      │
│   └─────────────────────────────────────────────────────────┘      │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  STAGE 5: LLM Generation (Gemini 2.5 Flash)             │      │
│   │  Prompt: Context + History + Query                       │      │
│   │  Output: CONTINUE:[answer] FOLLOWUP:[question]          │      │
│   │          or GOODBYE:[farewell]                          │      │
│   └─────────────────────────────────────────────────────────┘      │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  STAGE 6: Response Translation (if Hindi)               │      │
│   │  GoogleTranslator → Hindi output                        │      │
│   └─────────────────────────────────────────────────────────┘      │
│       │                                                             │
│       ▼                                                             │
│   Final Response → TTS → User                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. **hello.py** - Main Application Entry
- FastAPI server with REST endpoints and WebSocket
- Call initiation via Twilio API
- TwiML generation for voice interaction
- Webhook handlers for call status and speech completion

### 2. **state_manager.py** - Centralized State Management
- Thread-safe state tracking with minimal locking
- Lock-free reads for high performance
- Conversation history management (last 3 exchanges)
- Webhook duplicate prevention

### 3. **stream_handler_simple.py** - WebSocket Handler
- Bi-directional audio streaming (Twilio ↔ Deepgram)
- Progressive silence detection algorithm
- Transcript accumulation and processing
- Deepgram keepalive management

### 4. **llm_handler.py** - Query Processor
- Language detection and translation
- RAG system invocation
- Response parsing (CONTINUE/GOODBYE/FOLLOWUP)
- TTS integration

### 5. **simple_rag.py** - RAG System
- LlamaIndex-based retrieval
- HuggingFace embeddings
- Cross-encoder reranking
- Custom prompt engineering for short responses

### 6. **tts.py** - Text-to-Speech
- Twilio TwiML generation
- Voice selection (Polly.Aditi for Hindi/English)
- Webhook callback coordination

### 7. **Dashboard/** - Admin Interface
- React frontend for call monitoring
- FastAPI backend for analytics
- Document upload for RAG updates

---

## 🔄 Data Flow

### Complete Call Flow Sequence

```
┌──────┐    ┌───────┐    ┌──────────┐    ┌──────────┐    ┌───────┐    ┌───────┐
│ User │    │Twilio │    │ FastAPI  │    │ Deepgram │    │Gemini │    │MongoDB│
└──┬───┘    └───┬───┘    └────┬─────┘    └────┬─────┘    └───┬───┘    └───┬───┘
   │            │             │               │              │            │
   │  Dial In   │             │               │              │            │
   │───────────►│             │               │              │            │
   │            │  POST /twiml│               │              │            │
   │            │────────────►│               │              │            │
   │            │   TwiML     │  save_call()  │              │            │
   │            │◄────────────│──────────────────────────────────────────►│
   │  Greeting  │             │               │              │            │
   │◄───────────│             │               │              │            │
   │            │  WebSocket  │               │              │            │
   │            │  Connect    │               │              │            │
   │            │────────────►│  Connect      │              │            │
   │            │             │──────────────►│              │            │
   │   Speak    │  Audio      │   Audio       │              │            │
   │───────────►│────────────►│──────────────►│              │            │
   │            │             │   Transcript  │              │            │
   │            │             │◄──────────────│              │            │
   │            │             │               │  RAG Query   │            │
   │            │             │───────────────────────────────►            │
   │            │             │               │  Response    │            │
   │            │             │◄──────────────────────────────            │
   │            │             │  save_conversation()         │            │
   │            │             │────────────────────────────────────────────►
   │            │  TTS TwiML  │               │              │            │
   │            │◄────────────│               │              │            │
   │  Response  │             │               │              │            │
   │◄───────────│             │               │              │            │
   │            │             │               │              │            │
   │            │  Webhook    │               │              │            │
   │            │  /speech-   │               │              │            │
   │            │  complete   │               │              │            │
   │            │────────────►│               │              │            │
   │            │             │ Set WAITING   │              │            │
   │            │             │ _INPUT        │              │            │
   │            │             │               │              │            │
```

---

## 📡 API Documentation

### Main Application (Port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve call initiation form |
| `POST` | `/start-call` | Initiate outbound call |
| `POST` | `/twiml` | Generate TwiML for Twilio |
| `POST` | `/speech-complete/{call_sid}` | Speech completion webhook |
| `POST` | `/call-status` | Twilio status callback |
| `WS` | `/twilio-stream` | Bi-directional audio stream |
| `POST` | `/api/process-documents` | Trigger RAG index rebuild |

### Dashboard API (Port 8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/calls` | List all calls |
| `GET` | `/api/calls/status-summary` | Call statistics |
| `GET` | `/api/calls/active` | Active calls only |
| `GET` | `/api/calls/{call_sid}` | Single call details |
| `POST` | `/api/upload/document` | Upload PDF/TXT for RAG |
| `GET` | `/api/upload/status` | Upload processing status |

---

## 💾 Database Schema

### MongoDB Collection: `calls`

```json
{
  "_id": "ObjectId",
  "call_sid": "CA1234567890abcdef",
  "phone_number": "+919876543210",
  "caller_name": "John Doe",
  "status": "completed", 
  "created_at": "2026-02-22T10:30:00.000Z",
  "updated_at": "2026-02-22T10:35:00.000Z",
  "conversation": [
    {
      "question": "What is the fee structure?",
      "answer": "The annual fee is one lakh fifty thousand rupees...",
      "timestamp": "2026-02-22T10:31:00.000Z"
    }
  ]
}
```

**Indexes:**
- `call_sid` (unique)
- `status`
- `created_at` (descending)

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ (for dashboard)
- MongoDB Atlas account
- Twilio account
- Deepgram API key
- Google AI API key

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/your-repo/Connect.Ai-main.git
cd Connect.Ai-main

# Backend
pip install -r requirements.txt

# Dashboard Frontend
cd Dashboard/frontend
npm install
```

### 2. Configure Environment Variables

Create `.env` file:
```env
# Twilio
twilio_sid=YOUR_ACCOUNT_SID
twilio_token=YOUR_AUTH_TOKEN
YOUR_TWILIO_PHONE_NUMBER=+18884990559

# APIs
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_API_KEY=your_google_ai_key

# Database
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DATABASE_NAME=connect_ai_db
```

### 3. Build RAG Index

```bash
# Add PDFs to ./pdf/ folder
python update_llamaindex.py
```

### 4. Start Services

```bash
# Terminal 1: Main Application
python hello.py  # Runs on port 8000

# Terminal 2: Dashboard Backend
cd Dashboard/backend
python main.py  # Runs on port 8001

# Terminal 3: Dashboard Frontend
cd Dashboard/frontend
npm start  # Runs on port 3000

# Terminal 4: Cloudflare Tunnel (for webhooks)
cloudflared tunnel --url http://localhost:8000
```

---

## 📁 Project Structure

```
Connect.Ai-main/
├── hello.py                    # Main FastAPI application
├── config.py                   # Configuration & initialization
├── state_manager.py            # Thread-safe state management
├── stream_handler_simple.py    # WebSocket audio handler
├── llm_handler.py              # Query processing pipeline
├── simple_rag.py               # RAG system implementation
├── tts.py                      # Text-to-speech service
├── translator_utils.py         # Translation utilities
├── database.py                 # MongoDB operations
├── security.py                 # Twilio signature verification
├── update_llamaindex.py        # RAG index builder
├── requirements.txt            # Python dependencies
│
├── HIGH_LEVEL_DESIGN.md        # System architecture documentation
├── LOW_LEVEL_DESIGN.md         # Implementation details
│
├── templates/
│   └── index.html              # Call initiation web form
│
├── pdf/                        # University documents for RAG
│
├── index_storage/              # Vector store persistence
│   ├── docstore.json
│   ├── default__vector_store.json
│   └── index_store.json
│
└── Dashboard/
    ├── backend/
    │   ├── main.py             # Dashboard API server
    │   ├── db.py               # Database connection
    │   └── routes/
    │       ├── calls.py        # Call analytics endpoints
    │       └── upload.py       # Document upload endpoint
    └── frontend/
        └── src/
            ├── App.js          # Main React component
            └── components/     # UI components
```

---

## ⚡ Performance Optimizations

| Optimization | Implementation | Impact |
|--------------|----------------|--------|
| **Lock-free reads** | `is_call_active()` has no locking | 10x faster state checks |
| **Async I/O** | All network calls are non-blocking | High concurrency |
| **Connection pooling** | Reuse Twilio/Deepgram clients | Reduced latency |
| **RAG caching** | `_RAG_COMPONENTS` global cache | Instant retrieval after first load |
| **Webhook deduplication** | `_webhook_processing` set | Prevents race conditions |
| **Conversation history limit** | Max 6 items (3 exchanges) | Bounded memory |
| **Background preloading** | RAG loads on server startup | Eliminates cold start |

---

## 🔮 Future Enhancements

- [ ] **Multi-tenant support** - Handle multiple universities
- [ ] **Voice cloning** - Custom TTS voices
- [ ] **Sentiment analysis** - Track caller satisfaction
- [ ] **Call recording** - Store audio for quality assurance
- [ ] **A/B testing** - Compare response strategies
- [ ] **Kubernetes deployment** - Auto-scaling infrastructure
- [ ] **Real-time analytics** - WebSocket dashboard updates

---

## 📚 Additional Documentation

- [High-Level Design (HLD)](./HIGH_LEVEL_DESIGN.md) - Complete system architecture
- [Low-Level Design (LLD)](./LOW_LEVEL_DESIGN.md) - Implementation details with code examples

---

## 👤 Author

**Built for Technical Interview Demonstration**

This project showcases:
- ✅ System design skills (HLD/LLD)
- ✅ Real-time streaming architectures
- ✅ LLM/RAG integration
- ✅ Production-grade Python development
- ✅ Full-stack capabilities (FastAPI + React)
- ✅ Cloud service integration (Twilio, Deepgram, Google AI, MongoDB)

---

<p align="center">
  <i>Connect.AI - Transforming university admissions with conversational AI</i>
</p>

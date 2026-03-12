# Connect.AI - Low-Level Design (LLD)
## Implementation Details & Code Structure

**Created for Interview Presentation**  
**Date:** February 2026  
**Version:** 1.0

---

## 📋 Table of Contents

1. [Module Structure](#module-structure)
2. [Class Diagrams](#class-diagrams)
3. [Detailed Algorithms](#detailed-algorithms)
4. [Code Examples](#code-examples)
5. [Sequence Diagrams](#sequence-diagrams)
6. [Data Structures](#data-structures)
7. [Concurrency & Threading](#concurrency--threading)
8. [Performance Optimization](#performance-optimization)
9. [Testing Strategy](#testing-strategy)
10. [Code Quality Standards](#code-quality-standards)

---

## 📁 Module Structure

### Project Directory Layout

```
Connect.Ai-main/
├── hello.py                    # Main FastAPI application
├── config.py                   # Configuration & client initialization
├── state_manager.py            # Centralized state management
├── stream_handler_simple.py    # WebSocket handler
├── llm_handler.py              # LLM query processor
├── simple_rag.py               # RAG system implementation
├── tts.py                      # Text-to-speech service
├── translator_utils.py         # Translation utilities
├── database.py                 # MongoDB operations
├── security.py                 # Authentication & validation
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not committed)
│
├── templates/
│   └── index.html              # Web form template
│
├── pdf/                        # Document storage
│   └── university_docs.pdf
│
├── index_storage/              # Vector store
│   ├── docstore.json
│   ├── default__vector_store.json
│   └── index_store.json
│
└── Dashboard/
    ├── backend/
    │   ├── main.py             # Dashboard API server
    │   ├── db.py               # Database connection
    │   └── routes/
    │       ├── calls.py        # Call endpoints
    │       └── upload.py       # Upload endpoints
    └── frontend/
        ├── package.json
        └── src/
            ├── App.js          # Main React component
            ├── api.js          # API client
            └── components/
                ├── StatsCards.jsx
                ├── CallsChart.jsx
                ├── ActiveCallsTable.jsx
                └── ConversationModal.jsx
```

### Module Dependencies

```
┌─────────────────────────────────────────────────┐
│              hello.py (Main Entry)              │
└────┬────────────────────────────────────────────┘
     │
     ├─→ config.py (Import configurations)
     │   ├─→ twilio_client
     │   ├─→ state_manager
     │   ├─→ llm (Gemini)
     │   └─→ DEEPGRAM_URL
     │
     ├─→ stream_handler_simple.py
     │   ├─→ llm_handler
     │   ├─→ state_manager
     │   └─→ database
     │
     ├─→ security.py
     │   └─→ verify_twilio_request()
     │
     └─→ database.py
         └─→ MongoDB operations

stream_handler_simple.py
     ├─→ llm_handler
     │   ├─→ translator_utils
     │   ├─→ simple_rag
     │   ├─→ tts
     │   └─→ database
     │
     └─→ state_manager

simple_rag.py
     ├─→ llama_index.core
     ├─→ llama_index.llms.gemini
     └─→ llama_index.embeddings.huggingface
```

---

## 🏛️ Class Diagrams

### 1. StateManager Class

```python
┌─────────────────────────────────────────────────────┐
│              StateManager                           │
├─────────────────────────────────────────────────────┤
│ - _write_lock: threading.Lock                       │
│ - _webhook_lock: threading.Lock                     │
│ - _call_states: Dict[str, Dict]                     │
│ - _conversation_states: DefaultDict[str, Dict]      │
│ - _conversation_history: DefaultDict[str, List]     │
│ - _active_websockets: Dict[str, WebSocket]          │
│ - _webhook_processing: Set[str]                     │
│ - _twilio_client: Client                            │
├─────────────────────────────────────────────────────┤
│ + __init__(twilio_client)                           │
│ + register_call(call_sid, initial_state) -> bool    │
│ + update_call_state(call_sid, new_state) -> bool    │
│ + is_call_active(call_sid) -> bool                  │
│ + get_call_state(call_sid) -> Dict                  │
│ + end_call(call_sid) -> bool                        │
│ + add_to_conversation_history(...) -> bool          │
│ + get_conversation_context(call_sid) -> str         │
│ + get_conversation_count(call_sid) -> int           │
│ + increment_conversation_count(call_sid) -> int     │
│ + update_language(call_sid, lang_code) -> bool      │
│ + get_language(call_sid) -> str                     │
│ + start_webhook_processing(call_sid) -> bool        │
│ + end_webhook_processing(call_sid)                  │
│ + register_websocket(call_sid, websocket) -> bool   │
│ + set_input_start_time(call_sid, timestamp) -> bool │
│ + get_input_start_time(call_sid) -> float           │
└─────────────────────────────────────────────────────┘
```

**Implementation Details:**

```python
class StateManager:
    """Thread-safe state management for concurrent calls"""
    
    def __init__(self, twilio_client=None):
        # Minimal locking for performance
        self._write_lock = threading.Lock()
        self._webhook_lock = threading.Lock()
        
        # Core state storage
        self._call_states = {}  # {call_sid: {status, start_time, ...}}
        self._conversation_states = defaultdict(
            lambda: {'conversation_count': 0}
        )
        self._conversation_history = defaultdict(list)
        self._active_websockets = {}
        self._webhook_processing = set()
        
        self._twilio_client = twilio_client
    
    def register_call(self, call_sid: str, initial_state: str = 'INITIAL') -> bool:
        """Register new call with atomic operation"""
        with self._write_lock:
            if call_sid in self._call_states:
                return False
            
            current_time = asyncio.get_event_loop().time()
            self._call_states[call_sid] = {
                'status': initial_state,
                'start_time': current_time,
                'last_update': current_time
            }
        return True
    
    def is_call_active(self, call_sid: str) -> bool:
        """Lock-free read for maximum performance"""
        return call_sid in self._call_states
```

### 2. StreamHandler (Functional Design)

```python
┌─────────────────────────────────────────────────────┐
│         twilio_stream_websocket(websocket)         │
├─────────────────────────────────────────────────────┤
│ Variables:                                          │
│ - call_sid: str                                     │
│ - deepgram_ws: WebSocket                            │
│ - current_transcript: str                           │
│ - input_timer: asyncio.Task                         │
│ - silence_timer: asyncio.Task                       │
│ - silence_count: int                                │
│ - cleanup_done: bool                                │
├─────────────────────────────────────────────────────┤
│ Nested Functions:                                   │
│ + ask_followup_question() -> None                   │
│ + start_complete_silence_timer() -> None            │
│ + process_user_input() -> None                      │
│ + start_silence_timer() -> None                     │
│ + forward_audio_to_deepgram() -> None               │
│ + process_deepgram_transcripts() -> None            │
│ + keep_deepgram_alive() -> None                     │
│ + cleanup() -> None                                 │
│ + close_deepgram() -> None                          │
└─────────────────────────────────────────────────────┘
```

### 3. RAGSystem Class Structure

```python
┌─────────────────────────────────────────────────────┐
│              RAGSystem (Module)                     │
├─────────────────────────────────────────────────────┤
│ Global Variables:                                   │
│ - llm: Gemini                                       │
│ - embed_model: HuggingFaceEmbedding                 │
│ - _RAG_COMPONENTS: Dict (cache)                     │
│ - _INDEX_STORAGE_PATH: str                          │
├─────────────────────────────────────────────────────┤
│ Functions:                                          │
│ + create_rag_system() -> Dict                       │
│ + query_rag_system(query, context) -> str           │
│ + query_llm_with_data(...) -> str                   │
│ + safe_query_with_retry(...) -> str                 │
└─────────────────────────────────────────────────────┘

RAG Components Dictionary:
┌─────────────────────────────────────────────────────┐
│ {                                                   │
│   "index": VectorStoreIndex,                        │
│   "retriever": VectorIndexRetriever,                │
│   "reranker": SentenceTransformerRerank,            │
│   "query_engine": RetrieverQueryEngine              │
│ }                                                   │
└─────────────────────────────────────────────────────┘
```

---

## 🔢 Detailed Algorithms

### Algorithm 1: Call Lifecycle Management

```python
def handle_call_lifecycle(call_sid, phone_number, name):
    """
    Complete call management from initiation to termination
    
    Complexity: O(1) for state operations, O(n) for conversation (n=turns)
    Space: O(k) where k = conversation history size (max 6 entries)
    """
    
    # Phase 1: Initialization - O(1)
    call_record = {
        'call_sid': call_sid,
        'phone_number': phone_number,
        'caller_name': name,
        'status': 'initiated',
        'created_at': datetime.now()
    }
    database.save_call_to_db(call_record)  # O(1) MongoDB insert
    
    # Phase 2: State Registration - O(1)
    state_manager.register_call(
        call_sid=call_sid,
        initial_state='INITIAL'
    )  # O(1) dict insertion with lock
    
    # Phase 3: Twilio Call Initiation - O(1) API call
    twilio_client.calls.create(
        to=phone_number,
        from_=twilio_from_number,
        url=f"{BASE_URL}/twiml"
    )
    
    # Phase 4: WebSocket Processing - Async loop
    # Runs until call termination
    # Average call: 3-5 conversation turns
    while state_manager.is_call_active(call_sid):
        # Process user speech
        # Query LLM - O(1) vector search + O(1) LLM query
        # Generate response
        # Update state - O(1)
        pass
    
    # Phase 5: Cleanup - O(1)
    state_manager.end_call(call_sid)  # O(1) dict removal
    database.update_call_status(call_sid, 'completed')  # O(1) update
```

### Algorithm 2: Progressive Silence Detection

```python
async def progressive_silence_detection(call_sid):
    """
    Adaptive silence timer with escalating timeouts
    
    Strategy:
    - First silence: 6 seconds (user might be thinking)
    - Second silence: 8 seconds (give more time)
    - Third silence: 10 seconds (final chance)
    - After 3rd: Terminate call
    
    Complexity: O(1) per timer
    """
    
    silence_count = state_manager.get_silence_count(call_sid)  # O(1)
    
    # Progressive timeout calculation - O(1)
    timer_duration = 6 + (silence_count * 2)  # 6s, 8s, 10s
    
    async def handle_complete_silence():
        await asyncio.sleep(timer_duration)
        
        # Check if user spoke during wait - O(1)
        if not current_transcript.strip():
            silence_count += 1
            state_manager.update_silence_count(call_sid, silence_count)
            
            if silence_count >= 3:
                # Terminate call - O(1)
                await speak_async(
                    call_sid,
                    "Thank you for calling. Goodbye!",
                    hangup=True
                )
            else:
                # Ask follow-up - O(1)
                await speak_async(
                    call_sid,
                    "Are you still there?",
                    is_followup=True
                )
    
    # Create async task - O(1)
    silence_timer = asyncio.create_task(handle_complete_silence())
    return silence_timer
```

### Algorithm 3: RAG Retrieval & Reranking

```python
def rag_retrieval_pipeline(query_text, conversation_context):
    """
    Multi-stage retrieval with reranking
    
    Stage 1: Embedding - O(d) where d=384 (embedding dimension)
    Stage 2: Vector Search - O(log n) where n=document chunks
    Stage 3: Reranking - O(k*m) where k=candidates, m=model complexity
    Stage 4: LLM Generation - O(1) API call
    
    Total Complexity: O(log n + k*m)
    """
    
    # Stage 1: Create query embedding - O(d)
    query_embedding = embed_model.get_text_embedding(query_text)
    # Result: 384-dimensional vector
    
    # Stage 2: Vector similarity search - O(log n) with FAISS
    # Cosine similarity: dot(query_vec, doc_vec) / (||query|| * ||doc||)
    retriever = index.as_retriever(similarity_top_k=3)
    retrieved_nodes = retriever.retrieve(query_text)
    # Returns: Top 3 most similar document chunks
    
    # Stage 3: Rerank retrieved nodes - O(k*m) where k=3
    reranker = SentenceTransformerRerank(
        model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=3
    )
    reranked_nodes = reranker.postprocess_nodes(
        retrieved_nodes,
        query_bundle=query_text
    )
    # Cross-encoder scores: query-document pairs
    # Returns: Re-scored top 3 with higher precision
    
    # Stage 4: Build prompt with context - O(c) where c=context length
    context_str = "\n\n".join([node.text for node in reranked_nodes])
    
    prompt = f"""
    Context: {context_str}
    
    Previous conversation: {conversation_context}
    
    Question: {query_text}
    
    Answer:
    """
    
    # Stage 5: LLM generation - O(1) API call
    response = llm.complete(prompt)
    
    return response.text
```

### Algorithm 4: Exponential Backoff Retry

```python
def exponential_backoff_retry(
    func,
    max_retries=3,
    base_delay=2.0,
    max_delay=60.0,
    exceptions=(Exception,)
):
    """
    Retry with exponential backoff
    
    Formula: wait_time = min(base_delay * (2 ^ attempt) + jitter, max_delay)
    
    Example:
    - Attempt 1: 2^0 * 2 + random(0,1) = 2-3s
    - Attempt 2: 2^1 * 2 + random(0,1) = 4-5s
    - Attempt 3: 2^2 * 2 + random(0,1) = 8-9s
    
    Complexity: O(r) where r=retries (typically r=3)
    """
    
    for attempt in range(max_retries):
        try:
            result = func()
            return result  # Success
        
        except exceptions as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                raise e
            
            # Calculate exponential backoff
            exponential = base_delay * (2 ** attempt)
            jitter = random.uniform(0, 1)
            wait_time = min(exponential + jitter, max_delay)
            
            print(f"Retry {attempt + 1}/{max_retries} after {wait_time:.2f}s")
            time.sleep(wait_time)
    
    # Should never reach here
    raise RuntimeError("Max retries exhausted")
```

---

## 💻 Code Examples

### Example 1: WebSocket Handler Implementation

```python
@app.websocket("/twilio-stream")
async def twilio_websocket(websocket: WebSocket):
    """
    Main WebSocket handler for Twilio audio streaming
    Complexity: O(1) per message, runs continuously
    """
    await websocket.accept()
    
    # Initialize local state
    call_sid = None
    deepgram_ws = None
    cleanup_done = False
    current_transcript = ""
    silence_count = 0
    
    # Connect to Deepgram STT
    deepgram_ws = await connect_to_deepgram()
    if not deepgram_ws:
        await websocket.close()
        return
    
    async def forward_audio_to_deepgram():
        """Forward audio from Twilio to Deepgram"""
        nonlocal call_sid
        
        while True:
            try:
                # Receive message from Twilio - O(1)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message["event"] == "start":
                    # Call initialization
                    call_sid = message["start"]["callSid"]
                    state_manager.register_call(call_sid, "SPEAKING")
                    state_manager.register_websocket(call_sid, websocket)
                    print(f"📞 Call started: {call_sid}")
                
                elif message["event"] == "media":
                    # Audio chunk received
                    payload = base64.b64decode(message["media"]["payload"])
                    
                    # Forward to Deepgram - O(1)
                    if deepgram_ws:
                        await deepgram_ws.send(payload)
                
                elif message["event"] == "stop":
                    # Call ended
                    print(f"🛑 Call ended: {call_sid}")
                    cleanup()
                    return
            
            except Exception as e:
                print(f"Error in audio forwarding: {e}")
                break
    
    async def process_deepgram_transcripts():
        """Process transcriptions from Deepgram"""
        nonlocal current_transcript
        
        while not cleanup_done:
            try:
                # Receive from Deepgram - O(1)
                msg = await deepgram_ws.recv()
                message = json.loads(msg)
                
                # Extract transcript
                if "channel" in message:
                    transcript = message["channel"]["alternatives"][0]\
                        .get("transcript", "").strip()
                    
                    is_final = message.get("is_final", False)
                    
                    if transcript:
                        # Accumulate transcript
                        current_transcript = f"{current_transcript} {transcript}".strip()
                        
                        if is_final:
                            print(f"📝 Final: {transcript}")
                            # Start 3-second silence timer
                            await start_silence_timer()
            
            except Exception as e:
                print(f"Error in transcript processing: {e}")
                break
    
    async def keep_deepgram_alive():
        """Send silence packets during AI processing"""
        silence_packet = b'\xff' * 160  # μ-law silence
        
        while not cleanup_done:
            await asyncio.sleep(1)
            
            current_status = state_manager.get_call_state(call_sid)\
                .get("status")
            
            # Send silence during SPEAKING/PROCESSING
            if current_status in ["SPEAKING", "PROCESSING"]:
                if deepgram_ws:
                    try:
                        await deepgram_ws.send(silence_packet)
                    except:
                        pass
    
    def cleanup():
        """Resource cleanup"""
        nonlocal cleanup_done
        if cleanup_done:
            return
        
        cleanup_done = True
        
        if deepgram_ws:
            asyncio.create_task(deepgram_ws.close())
        
        if call_sid:
            state_manager.end_call(call_sid)
            database.update_call_status(call_sid, "completed")
    
    # Run all tasks concurrently
    try:
        await asyncio.gather(
            forward_audio_to_deepgram(),
            process_deepgram_transcripts(),
            keep_deepgram_alive()
        )
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        cleanup()
```

### Example 2: RAG Query with Caching

```python
# Global cache
_rag_cache = {}

def query_llm_with_data(
    translated_input: str,
    conversation_context: str,
    call_sid: str = None
) -> str:
    """
    Query LLM with RAG and optional caching
    
    Cache Strategy:
    - Hash query text
    - Check cache (TTL: 1 hour)
    - If hit: return cached response (save API cost)
    - If miss: query LLM, cache result
    
    Complexity:
    - Cache hit: O(1)
    - Cache miss: O(log n + k*m + g)
      where n=docs, k=retrieval, m=rerank, g=generation
    """
    
    # Generate cache key
    cache_key = hashlib.md5(
        translated_input.lower().encode()
    ).hexdigest()
    
    # Check cache
    if cache_key in _rag_cache:
        cached_entry = _rag_cache[cache_key]
        
        # Check TTL (1 hour)
        if time.time() - cached_entry['timestamp'] < 3600:
            print(f"✅ Cache hit for: {translated_input[:50]}")
            return cached_entry['response']
        else:
            # Expired, remove from cache
            del _rag_cache[cache_key]
    
    # Cache miss - query RAG system
    print(f"❌ Cache miss, querying LLM...")
    
    # Create RAG components (cached globally)
    rag_components = create_rag_system()
    query_engine = rag_components["query_engine"]
    
    # Build enhanced prompt
    enhanced_prompt = translated_input
    if conversation_context:
        enhanced_prompt = f"""
        Previous conversation:
        {conversation_context}
        
        Current question: {translated_input}
        """
    
    # Query with retry logic
    response = safe_query_with_retry(query_engine, enhanced_prompt)
    
    # Cache the response
    _rag_cache[cache_key] = {
        'response': response,
        'timestamp': time.time()
    }
    
    # Limit cache size (LRU eviction)
    if len(_rag_cache) > 1000:
        # Remove oldest 100 entries
        sorted_entries = sorted(
            _rag_cache.items(),
            key=lambda x: x[1]['timestamp']
        )
        for key, _ in sorted_entries[:100]:
            del _rag_cache[key]
    
    return response
```

### Example 3: Database Transaction Pattern

```python
def save_conversation_with_transaction(
    call_sid: str,
    question: str,
    answer: str
):
    """
    Save conversation with atomic transaction
    
    ACID Properties:
    - Atomicity: All or nothing
    - Consistency: Valid state transitions
    - Isolation: No interference from concurrent ops
    - Durability: Persisted to disk
    
    Complexity: O(1) with proper indexing
    """
    
    session = mongo_client.start_session()
    
    try:
        with session.start_transaction():
            # Update 1: Add conversation entry
            result1 = calls_collection.update_one(
                {"call_sid": call_sid},
                {
                    "$push": {
                        "conversation": {
                            "question": question,
                            "answer": answer,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                },
                session=session
            )
            
            # Update 2: Update last_updated timestamp
            result2 = calls_collection.update_one(
                {"call_sid": call_sid},
                {
                    "$set": {
                        "updated_at": datetime.now().isoformat()
                    }
                },
                session=session
            )
            
            # Commit transaction
            session.commit_transaction()
            
            print(f"✅ Conversation saved: {call_sid}")
            return True
    
    except Exception as e:
        # Rollback on error
        session.abort_transaction()
        print(f"❌ Transaction failed: {e}")
        return False
    
    finally:
        session.end_session()
```

---

## 🔄 Sequence Diagrams

### Sequence 1: Call Initialization to First Response

```
User          WebForm      FastAPI      Twilio       Database     StateManager
 │               │            │            │             │              │
 │  Fill form    │            │            │             │              │
 ├──────────────>│            │            │             │              │
 │               │            │            │             │              │
 │               │ POST       │            │             │              │
 │               │ /start-call│            │             │              │
 │               ├───────────>│            │             │              │
 │               │            │            │             │              │
 │               │            │ save_call_to_db()        │              │
 │               │            ├────────────────────────>│              │
 │               │            │            │             │              │
 │               │            │ create()   │             │              │
 │               │            ├───────────>│             │              │
 │               │            │            │             │              │
 │               │            │ request TwiML            │              │
 │               │            │<───────────┤             │              │
 │               │            │            │             │              │
 │               │            │ register_call()          │              │
 │               │            ├─────────────────────────────────────────>│
 │               │            │            │             │              │
 │               │ TwiML +    │            │             │              │
 │               │ WebSocket  │            │             │              │
 │               │<───────────┤            │             │              │
 │               │            │            │             │              │
```

### Sequence 2: User Speech to AI Response

```
User    Twilio    WebSocket    Deepgram    StateManager    LLM    Database
│         │          │             │            │           │         │
│ Speaks  │          │             │            │           │         │
├────────>│          │             │            │           │         │
│         │          │             │            │           │         │
│         │ Audio    │             │            │           │         │
│         │ chunks   │             │            │           │         │
│         ├─────────>│             │            │           │         │
│         │          │             │            │           │         │
│         │          │ Forward     │            │           │         │
│         │          │ audio       │            │           │         │
│         │          ├────────────>│            │           │         │
│         │          │             │            │           │         │
│         │          │ Transcribed │            │           │         │
│         │          │ text        │            │           │         │
│         │          │<────────────┤            │           │         │
│         │          │             │            │           │         │
│         │          │ update_state(PROCESSING) │           │         │
│         │          ├─────────────────────────>│           │         │
│         │          │             │            │           │         │
│         │          │ query_rag()              │           │         │
│         │          ├────────────────────────────────────>│         │
│         │          │             │            │           │         │
│         │          │             │            │       Response      │
│         │          │<────────────────────────────────────┤         │
│         │          │             │            │           │         │
│         │          │ save_conversation()      │           │         │
│         │          ├─────────────────────────────────────────────>│
│         │          │             │            │           │         │
│         │ Speak    │             │            │           │         │
│<────────┴──────────┤             │            │           │         │
│         │          │             │            │           │         │
```

---

## 📊 Data Structures

### 1. Call State Dictionary

```python
call_state = {
    "call_sid": "CA1234567890abcdef",
    "status": "WAITING_INPUT",  # Enum: INITIAL, SPEAKING, WAITING_INPUT, PROCESSING
    "start_time": 1707390000.123,  # Unix timestamp (float)
    "last_update": 1707390015.456,
    "input_start_time": 1707390010.789,
    "should_hangup": False,  # Boolean flag
    "is_followup": False,
    "restart_silence_timer": False,
    "detected_lang": "hi"  # Language code
}

# Access Pattern: O(1)
# Memory: ~200 bytes per call
# Concurrent calls: 50 → ~10 KB total
```

### 2. Conversation History List

```python
conversation_history = [
    "What is the fee?",              # Question 1
    "The annual fee is...",          # Answer 1
    "Tell me about placements",      # Question 2
    "Our placement rate is...",      # Answer 2
    "Any scholarships?",             # Question 3
    "We offer merit-based..."        # Answer 3
]

# Structure: Alternating Q&A
# Max size: 6 entries (last 3 exchanges)
# Access: O(1) for append, O(n) for iteration (n≤6)
# Memory: ~500 bytes per call (avg 100 chars per entry)

def get_conversation_context(history):
    """Format for LLM prompt"""
    context = []
    for i in range(0, len(history), 2):
        if i + 1 < len(history):
            context.append(f"User: {history[i]}\nAssistant: {history[i+1]}")
    return "\n\n".join(context)
```

### 3. Vector Store Structure

```python
# Embedding Vector (384 dimensions)
embedding = np.array([
    0.123, -0.456, 0.789, ...,  # 384 float values
])

# Document Node
document_node = {
    "node_id": "node_abc123",
    "text": "Chitkara University offers B.Tech in Computer Science...",
    "metadata": {
        "file_name": "courses.pdf",
        "page": 5,
        "chunk_index": 12
    },
    "embedding": embedding,  # 384-dim numpy array
    "score": 0.87  # Similarity score
}

# Index Structure (simplified)
vector_store = {
    "embeddings": np.ndarray(shape=(N, 384)),  # N documents
    "doc_ids": ["node_1", "node_2", ...],
    "metadata": [{...}, {...}, ...]
}

# Search Complexity: O(N) naive, O(log N) with FAISS
# Space: O(N * d) where d=384
```

### 4. WebSocket Message Queue

```python
from collections import deque

# Audio buffer (circular queue)
audio_buffer = deque(maxlen=100)  # Keep last 100 chunks

# Add audio chunk - O(1)
audio_buffer.append({
    "timestamp": time.time(),
    "payload": audio_bytes,
    "size": len(audio_bytes)
})

# Get average buffer size for monitoring
avg_size = sum(chunk["size"] for chunk in audio_buffer) / len(audio_buffer)
```

---

## 🧵 Concurrency & Threading

### Threading Model

```python
# Main Thread: FastAPI/Uvicorn (ASGI)
#  └─> Handles HTTP requests
#  └─> Spawns async tasks for WebSocket

# Async Event Loop (Single-threaded)
#  ├─> WebSocket Task 1 (Call SID: CA001)
#  │    ├─> forward_audio_to_deepgram()
#  │    ├─> process_deepgram_transcripts()
#  │    └─> keep_deepgram_alive()
#  │
#  ├─> WebSocket Task 2 (Call SID: CA002)
#  │    ├─> forward_audio_to_deepgram()
#  │    ├─> process_deepgram_transcripts()
#  │    └─> keep_deepgram_alive()
#  │
#  └─> ... (50+ concurrent calls)

# Background Threads
#  ├─> RAG Preload Thread (daemon=True)
#  └─> Document Processing Thread (daemon=True)
```

### Lock Hierarchy (Deadlock Prevention)

```python
# Rule: Always acquire locks in this order
# 1. StateManager._write_lock
# 2. StateManager._webhook_lock

# CORRECT: No deadlock
def safe_update():
    with state_manager._write_lock:
        # Update call state
        with state_manager._webhook_lock:
            # Update webhook processing
            pass

# INCORRECT: Potential deadlock
def unsafe_update():
    with state_manager._webhook_lock:  # Wrong order!
        with state_manager._write_lock:
            pass
```

### Async Task Management

```python
async def manage_concurrent_tasks():
    """
    Pattern 1: Fire and forget
    """
    task = asyncio.create_task(background_work())
    # Don't await - runs in background
    
    """
    Pattern 2: Wait for completion
    """
    result = await asyncio.wait_for(
        llm_query(),
        timeout=45.0
    )
    
    """
    Pattern 3: Parallel execution
    """
    results = await asyncio.gather(
        task1(),
        task2(),
        task3(),
        return_exceptions=True
    )
    
    """
    Pattern 4: Cancellation
    """
    task = asyncio.create_task(long_running())
    try:
        await asyncio.wait_for(task, timeout=10)
    except asyncio.TimeoutError:
        task.cancel()
        await task  # Wait for cancellation to complete
```

---

## ⚡ Performance Optimization

### 1. Database Query Optimization

```python
# BAD: Multiple queries -  O(n) round trips
for call_sid in call_sids:
    call = calls_collection.find_one({"call_sid": call_sid})
    process(call)

# GOOD: Single query with $in - O(1) round trip
calls = calls_collection.find({"call_sid": {"$in": call_sids}})
for call in calls:
    process(call)

# BEST: Aggregation pipeline with projection
pipeline = [
    {"$match": {"status": "completed"}},
    {"$project": {"call_sid": 1, "created_at": 1}},  # Only needed fields
    {"$limit": 100}
]
calls = calls_collection.aggregate(pipeline)
```

### 2. Memory Optimization

```python
# Conversation history size limit
MAX_HISTORY_SIZE = 6  # 3 Q&A pairs

def add_to_history(history, question, answer):
    """Bounded memory: O(1) space per call"""
    history.extend([question, answer])
    
    # Keep only last 6 entries
    if len(history) > MAX_HISTORY_SIZE:
        history = history[-MAX_HISTORY_SIZE:]
    
    return history

# Cache size limit
MAX_CACHE_SIZE = 1000

def add_to_cache(cache, key, value):
    """LRU eviction"""
    if len(cache) >= MAX_CACHE_SIZE:
        # Remove oldest 10%
        sorted_items = sorted(cache.items(), key=lambda x: x[1]['timestamp'])
        for k, _ in sorted_items[:100]:
            del cache[k]
    
    cache[key] = {'value': value, 'timestamp': time.time()}
```

### 3. Network Optimization

```python
# Connection pooling for MongoDB
mongo_client = MongoClient(
    MONGODB_URL,
    maxPoolSize=50,  # Reuse connections
    minPoolSize=10,
    maxIdleTimeMS=30000
)

# HTTP session reuse
import httpx

# BAD: New connection every time
async def make_request():
    async with httpx.AsyncClient() as client:
        return await client.get(url)

# GOOD: Reuse connection pool
http_client = httpx.AsyncClient(timeout=10.0)

async def make_request():
    return await http_client.get(url)
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# test_state_manager.py
import unittest
from state_manager import StateManager

class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.state_manager = StateManager()
    
    def test_register_call(self):
        """Test call registration"""
        call_sid = "CA_test_123"
        result = self.state_manager.register_call(call_sid, "INITIAL")
        
        self.assertTrue(result)
        self.assertTrue(self.state_manager.is_call_active(call_sid))
        
        state = self.state_manager.get_call_state(call_sid)
        self.assertEqual(state['status'], "INITIAL")
    
    def test_duplicate_registration(self):
        """Test duplicate call prevention"""
        call_sid = "CA_test_123"
        self.state_manager.register_call(call_sid)
        
        # Second registration should fail
        result = self.state_manager.register_call(call_sid)
        self.assertFalse(result)
    
    def test_conversation_history(self):
        """Test conversation management"""
        call_sid = "CA_test_123"
        self.state_manager.register_call(call_sid)
        
        self.state_manager.add_to_conversation_history(
            call_sid,
            "What is the fee?",
            "The fee is 150000"
        )
        
        context = self.state_manager.get_conversation_context(call_sid)
        self.assertIn("What is the fee?", context)
        self.assertIn("The fee is 150000", context)
```

### Integration Tests

```python
# test_call_flow.py
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_complete_call_flow():
    """Test end-to-end call"""
    
    # Mock external services
    with patch('twilio.rest.Client') as mock_twilio, \
         patch('database.save_call_to_db') as mock_db:
        
        # Setup mocks
        mock_twilio.calls.create.return_value.sid = "CA_test_123"
        
        # Make call
        response = await client.post("/start-call", data={
            "name": "Test User",
            "phone": "+919999999999"
        })
        
        # Assertions
        assert response.status_code == 200
        mock_twilio.calls.create.assert_called_once()
        mock_db.assert_called_once()
```

### Load Tests

```python
# locustfile.py
from locust import HttpUser, task, between

class CallLoadTest(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def start_call(self):
        self.client.post("/start-call", data={
            "name": "Load Test User",
            "phone": "+919999999999"
        })

# Run: locust -f locustfile.py --users 100 --spawn-rate 10
```

---

## 📏 Code Quality Standards

### Type Hints

```python
from typing import Dict, List, Optional, Tuple

def process_query(
    query: str,
    context: Optional[str] = None,
    max_retries: int = 3
) -> Tuple[str, float]:
    """
    Process user query with RAG
    
    Args:
        query: User's question
        context: Optional conversation history
        max_retries: Maximum retry attempts
    
    Returns:
        Tuple of (response_text, processing_time)
    """
    start_time = time.time()
    response = query_rag(query, context)
    processing_time = time.time() - start_time
    
    return response, processing_time
```

### Error Handling

```python
class CallProcessingError(Exception):
    """Base exception for call processing"""
    pass

class DeepgramConnectionError(CallProcessingError):
    """Deepgram connection failed"""
    pass

class LLMQueryError(CallProcessingError):
    """LLM query failed"""
    pass

# Usage
try:
    transcript = await get_transcript()
except DeepgramConnectionError as e:
    logger.error(f"STT failed: {e}")
    await speak_fallback_message()
except LLMQueryError as e:
    logger.error(f"LLM failed: {e}")
    await speak_error_message()
```

### Logging Standards

```python
import logging

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Structured logging
logger.info(
    "call_started",
    extra={
        "call_sid": call_sid,
        "phone_number": phone,
        "timestamp": datetime.now().isoformat()
    }
)
```

---

## 📝 Summary

The Low-Level Design provides:

✅ **Detailed Module Structure** with clear dependencies  
✅ **Class Diagrams** showing object relationships  
✅ **Algorithm Complexity Analysis** for optimization  
✅ **Code Examples** demonstrating best practices  
✅ **Sequence Diagrams** for interaction flows  
✅ **Data Structure Specifications** with memory analysis  
✅ **Concurrency Patterns** for thread safety  
✅ **Performance Optimizations** for scalability  
✅ **Testing Strategy** ensuring quality  
✅ **Code Standards** for maintainability  

This LLD serves as implementation guide for developers.

---

**Document Version**: 1.0  
**Last Updated**: February 8, 2026  
**Related**: See MAIN_SYSTEM_DESIGN.md and HIGH_LEVEL_DESIGN.md

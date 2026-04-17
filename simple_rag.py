




# Import core LlamaIndex components
from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage
)
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler

# Import embedding and LLM components
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.gemini import Gemini

# Import other utility libraries
import os
import time
from datetime import datetime
import config


# 
# Safe query function with retry logic for the gemini to pass to avoid the 503 error of gemini overloading 
#and connected tto the query_rag_system function with line 315
def safe_query_with_retry(query_engine, prompt, retries=3):
    """Query with retry logic for handling API overload gracefully"""
    for attempt in range(retries):
        try:
            response = query_engine.query(prompt)
            if response and str(response).strip():
                return str(response)
        except Exception as e:
            if "503" in str(e) or "overloaded" in str(e).lower():
                wait = (attempt + 1) * 3
                print(f"⚠️ Gemini overloaded, retrying in {wait}s... (attempt {attempt + 1}/{retries})")
                time.sleep(wait)
                continue
            if attempt == retries - 1:  # Last attempt, re-raise
                raise e
            time.sleep(1)
    
    return "I'm having trouble processing your request right now. Please try again shortly."

# Configure debug handler for visibility into retrieval process

#                   CORE RAG CONFIGURATION
llama_debug = LlamaDebugHandler(print_trace_on_end=True)
callback_manager = CallbackManager([llama_debug])

# Configure global settings with embeddings and LLM


# llm = Gemini(
#     api_key=config.GOOGLE_API_KEY, 
#     model_name="gemini-2.5-flash",
#     temperature=0.0,  # Reduced for faster, more deterministic responses
#     streaming=True  # Enable streaming
# )

from llama_index.llms.groq import Groq

llm = Groq(
    model="llama-3.3-70b-versatile",
    api_key=config.GROQ_API_KEY,
    temperature=0.1
)

Settings.llm = llm




embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Configure settings
from llama_index.core.settings import Settings
Settings.llm = llm
Settings.embed_model = embed_model
Settings.callback_manager = callback_manager

# Global variables to store RAG components for reuse
_INDEX_STORAGE_PATH = "./index_storage"
_RAG_COMPONENTS = None
_FORCE_RELOAD = False  # Flag to force reload after index update





# ================================================================================================
# RAG SYSTEM INITIALIZATION
# ================================================================================================
# This function loads the pre-built vector index and configures the query engine.
# The index contains document chunks (nodes) with their embeddings for similarity search.
# 
# To rebuild the index with new documents, run: python update_llamaindex.py
# ================================================================================================

def create_rag_system():
    """
    Load and configure the RAG system from pre-built index.
    
    Note: Index must be pre-built using update_llamaindex.py
    
    Returns:
        Dictionary with RAG components (index, retriever, reranker, query_engine)
    """
    global _RAG_COMPONENTS
    
    # Return cached components if available
    if _RAG_COMPONENTS is not None:
        print("📚 Using cached RAG components")
        return _RAG_COMPONENTS
    
    print("🔧 Creating RAG system...")
    
    # Load existing index (must exist - built by update_llamaindex.py)
    if not os.path.exists(_INDEX_STORAGE_PATH):
        raise FileNotFoundError(
            f"❌ Index not found at {_INDEX_STORAGE_PATH}\n"
            "Please run 'python update_llamaindex.py' first to build the index."
        )
    
    try:
        print("🔄 Loading existing index...")
        storage_context = StorageContext.from_defaults(persist_dir=_INDEX_STORAGE_PATH)
        index = load_index_from_storage(storage_context)
        print("✓ Successfully loaded existing index")
    except Exception as e:
        raise RuntimeError(
            f"❌ Error loading index: {e}\n"
            "Please run 'python update_llamaindex.py' to rebuild the index."
        )
    
    # Create retriever with good configuration
    # Retrieve more chunks initially so reranker has more to work with
    retriever = index.as_retriever(
        similarity_top_k=5  # Get top 5 chunks (cast wide net)
    )
    
    # Create reranker for improved retrieval precision
    # Reranker will re-score those 10 chunks and return top 3 best ones
    reranker = SentenceTransformerRerank(
        model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=3  # Return only top 3 after reranking (high quality)
    )
    
    # Configure response synthesizer with streaming support and custom prompt
    from llama_index.core.prompts import PromptTemplate
    
    # Create a custom prompt template that forces the LLM to use provided context
    # INCLUDES goodbye detection AND follow-up question generation in same call
    custom_prompt_template = PromptTemplate(
        """You are a helpful assistant for Chitkara University admissions. You have access to comprehensive university information.

CRITICAL FIRST STEP - Detect if user wants to end the call:
- If user says goodbye/bye/thanks and leaving, no more questions, "no"/"nope" to more questions, etc.
- Start response with "GOODBYE:" if user wants to end call
- Otherwise start with "CONTINUE:" for normal responses

RESPONSE STRUCTURE (if CONTINUE):
CONTINUE: [Your short answer to their question]

FOLLOWUP: [A contextual follow-up question based on your answer]

IMPORTANT INSTRUCTIONS:
 If the user mispronounces or slightly changes the name (e.g., Chikara, Chitakra, Chitkra, etc.), always understand that they are referring to Chitkara University.
- If the user mistakenly mentions another university name but context suggests Chitkara, treat it as Chitkara University.or hte ame is fully different thn tell user that u can only provide the info regarding the chitakra univsersity
- If the user mentions an incorrect or similar course name (e.g., BVA instead of BCA or BBA), politely clarify OR provide information about the closest relevant course offered at Chitkara University.
- Always keep the conversation focused strictly on Chitkara University.
1. The context below contains REAL university information that you MUST use to answer questions
2. NEVER say "information not available" or "context does not contain" if relevant information is present..this  is important just provide the info regarding the query
3. Look carefully through ALL context sections for relevant details
4. Your main answer MUST be SHORT - maximum 2-3 lines only
5. Answer in a helpful, conversational tone as if you're an admissions counselor and 
Convert only currency amounts to Indian words (e.g., 150000 → one lakh fifty thousand); keep phone numbers, IDs, and years as digits
if user has asked about a certain course jsut tell him about the speciailization avaivalble and course fees.
6. Follow-up question should be relevant to what you just explained:
   - If explained fees: ask about scholarships or payment plans
   - If explained course: ask about placements or specializations
   - If explained admissions: ask about dates or documents
   - Generic fallback: "Is there anything else you would like to know about Chitkara University?"
7. Keep follow-up natural and conversational
8. If user wants to end call (GOODBYE:), just provide brief farewell (no FOLLOWUP needed)

Context Information:
{context_str}

Question: {query_str}

Response (CONTINUE: [answer] FOLLOWUP: [question] OR GOODBYE: [farewell]):"""
    )
    
    response_synthesizer = get_response_synthesizer(
        streaming=True,
        response_mode="compact",  # Using compact mode instead of tree_summarize for shorter responses
        text_qa_template=custom_prompt_template
    )
    
    # Build query engine using the RetrieverQueryEngine class directly
    from llama_index.core.query_engine import RetrieverQueryEngine
    
    query_engine = RetrieverQueryEngine.from_args(
        retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[reranker]
    )
    
    # Store all components for reuse
    _RAG_COMPONENTS = {
        "index": index,
        "retriever": retriever,
        "reranker": reranker,
        "query_engine": query_engine
    }
    
    print("✓ RAG system created successfully")
    return _RAG_COMPONENTS

def warmup_rag_cache():
    """Eagerly initialize and cache RAG components during app startup."""
    start_time = time.time()
    try:
        create_rag_system()
        print(f"🔥 RAG warm-up completed in {time.time() - start_time:.2f} seconds")
        return True
    except Exception as e:
        # Keep app startup resilient; first query can still lazily initialize.
        print(f"⚠️ RAG warm-up failed, will lazy-load on first query: {e}")
        return False
    
# Query the RAG system
def query_rag_system(query_text, conversation_context=""):
    """
    Query the RAG system with a user question and conversation history.
    """
    # Ensure RAG system is initialized
    rag_components = create_rag_system()
    query_engine = rag_components["query_engine"]
    
    # Check for empty query
    if not query_text or not query_text.strip():
        return "Could you please provide a question?"
    
    print(f"🔍 Querying RAG system: {query_text}")
    
    # Use the original query - our custom system prompt will handle the instructions
    enhanced_prompt = query_text
    
    # Add conversation context if available
    if conversation_context:
        enhanced_prompt = f"Previous conversation:\n{conversation_context}\n\nCurrent question: {query_text}"
    
    # Print debug information
    print(f"🔍 Enhanced query with conversation context: {len(conversation_context) > 0}")
    
    # Execute query with timeout protection
    try:
        start_time = datetime.now()
        
        # Use safe retry logic for Gemini API calls
        response_text = safe_query_with_retry(query_engine, enhanced_prompt)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✓ Query completed in {duration:.2f} seconds")
        
        # Simple response validation
        if response_text and response_text.strip():
            return response_text
        
        return "I'm having trouble processing your request right now. Could you please try again?"
        
    except Exception as e:
        print(f"❌ Error during RAG query: {str(e)}")
        return "I'm having trouble processing your request right now. Could you please try again?"
    

# Main function for compatibility with existing code
def query_llm_with_data(translated_input, conversation_context, call_sid=None):
    """
    Function to query the LLM with translated input and conversation context.
    
    Args:
        translated_input (str): The user's translated query
        conversation_context (str): Context from previous conversation
        call_sid (str): The call ID to check if the call is still active
        
    Returns:
        str: The LLM response
    """
    # Check if the call has been ended (if call_sid is provided)
    if call_sid:
        try:
            from config import state_manager
            if hasattr(state_manager, 'is_call_active'):
                if not state_manager.is_call_active(call_sid):
                    print(f"⚠️ Call {call_sid} no longer active, cancelling LLM request")
                    return "Call ended."
        except (ImportError, AttributeError):
            pass  # If state manager unavailable, assume call is active
    
    try:
        # Query the system directly
        response = query_rag_system(translated_input, conversation_context)
        
        if hasattr(response, 'get_response'):  # Handle streaming response
            response_text = str(response)
            print(f"🤖 RAG Response (streaming): {response_text[:100]}...")
            return response_text
        else:
            print(f"🤖 RAG Response: {response[:100]}...")
            return response
            
    except Exception as e:
        import traceback
        print(f"❌ Error in RAG query: {e}")
        traceback.print_exc()
        return "I'm having trouble processing your request right now. Could you please repeat your question?"
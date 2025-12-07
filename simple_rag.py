


# """
# RAG Query System for Chitkara University Admissions
# ===================================================

# This module handles querying the pre-built RAG index.
# To update the index with new documents, run: python update_llamaindex.py

# The index must exist before using this module.
# """

# # Import core LlamaIndex components
# from llama_index.core import (
#     Settings,
#     StorageContext,
#     load_index_from_storage
# )
# from llama_index.core.postprocessor import SentenceTransformerRerank
# from llama_index.core.response_synthesizers import get_response_synthesizer
# from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler

# # Import embedding and LLM components
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# from llama_index.llms.gemini import Gemini

# # Import other utility libraries
# import os
# import time
# from datetime import datetime
# import config


# # 
# # Safe query function with retry logic for the gemini to pass to avoid the 503 error of gemini overloading 
# #and connected tto the query_rag_system function with line 315
# def safe_query_with_retry(query_engine, prompt, retries=3):
#     """Query with retry logic for handling API overload gracefully"""
#     for attempt in range(retries):
#         try:
#             response = query_engine.query(prompt)
#             if response and str(response).strip():
#                 return str(response)
#         except Exception as e:
#             if "503" in str(e) or "overloaded" in str(e).lower():
#                 wait = (attempt + 1) * 3
#                 print(f"⚠️ Gemini overloaded, retrying in {wait}s... (attempt {attempt + 1}/{retries})")
#                 time.sleep(wait)
#                 continue
#             if attempt == retries - 1:  # Last attempt, re-raise
#                 raise e
#             time.sleep(1)
    
#     return "I'm having trouble processing your request right now. Please try again shortly."

# # Configure debug handler for visibility into retrieval process

# #                   CORE RAG CONFIGURATION
# llama_debug = LlamaDebugHandler(print_trace_on_end=True)
# callback_manager = CallbackManager([llama_debug])

# # Configure global settings with embeddings and LLM
# llm = Gemini(
#     api_key=config.GOOGLE_API_KEY, 
#     model_name="gemini-2.5-flash",
#     temperature=0.0,  # Reduced for faster, more deterministic responses
#     streaming=True  # Enable streaming
# )
# embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# # Configure settings
# from llama_index.core.settings import Settings
# Settings.llm = llm
# Settings.embed_model = embed_model
# Settings.callback_manager = callback_manager

# # Global variables to store RAG components for reuse
# _INDEX_STORAGE_PATH = "./index_storage"
# _RAG_COMPONENTS = None
# _FORCE_RELOAD = False  # Flag to force reload after index update





# # ================================================================================================
# # RAG SYSTEM INITIALIZATION
# # ================================================================================================
# # This function loads the pre-built vector index and configures the query engine.
# # The index contains document chunks (nodes) with their embeddings for similarity search.
# # 
# # To rebuild the index with new documents, run: python update_llamaindex.py
# # ================================================================================================

# def create_rag_system(nodes=None, rebuild=False):
#     """
#     Load and configure the RAG system from pre-built index.
    
#     Note: Index must be pre-built using update_llamaindex.py
#     The rebuild parameter is kept for backwards compatibility but is no longer used.
    
#     Returns:
#         Dictionary with RAG components (index, retriever, reranker, query_engine)
#     """
#     global _RAG_COMPONENTS, _FORCE_RELOAD
    
#     # Force reload if flag is set
#     if _FORCE_RELOAD:
#         print("🔄 Force reload flag detected - reloading index...")
#         _RAG_COMPONENTS = None
#         _FORCE_RELOAD = False
#         rebuild = False  # Don't rebuild, just reload from disk
    
#     # Return cached components if available and not rebuilding
#     if _RAG_COMPONENTS is not None and not rebuild:
#         print("📚 Using cached RAG components")
#         return _RAG_COMPONENTS
    
#     print("🔧 Creating RAG system...")
    
#     # Load existing index (must exist - built by update_llamaindex.py)
#     if not os.path.exists(_INDEX_STORAGE_PATH):
#         raise FileNotFoundError(
#             f"❌ Index not found at {_INDEX_STORAGE_PATH}\n"
#             "Please run 'python update_llamaindex.py' first to build the index."
#         )
    
#     try:
#         print("🔄 Loading existing index...")
#         storage_context = StorageContext.from_defaults(persist_dir=_INDEX_STORAGE_PATH)
#         index = load_index_from_storage(storage_context)
#         print("✓ Successfully loaded existing index")
#     except Exception as e:
#         raise RuntimeError(
#             f"❌ Error loading index: {e}\n"
#             "Please run 'python update_llamaindex.py' to rebuild the index."
#         )
    
#     # Create retriever with good configuration
#     # Retrieve more chunks initially so reranker has more to work with
#     retriever = index.as_retriever(
#         similarity_top_k=3  # Get top 3 chunks (cast wide net)
#     )
    
#     # Create reranker for improved retrieval precision
#     # Reranker will re-score those 10 chunks and return top 3 best ones
#     reranker = SentenceTransformerRerank(
#         model="cross-encoder/ms-marco-MiniLM-L-6-v2",
#         top_n=3  # Return only top 3 after reranking (high quality)
#     )
    
#     # Configure response synthesizer with streaming support and custom prompt
#     from llama_index.core.prompts import PromptTemplate
    
#     # Create a custom prompt template that forces the LLM to use provided context
#     # INCLUDES goodbye detection AND follow-up question generation in same call
#     custom_prompt_template = PromptTemplate(
#         """You are a helpful assistant for Chitkara University admissions. You have access to comprehensive university information.

# CRITICAL FIRST STEP - Detect if user wants to end the call:
# - If user says goodbye/bye/thanks and leaving, no more questions, "no"/"nope" to more questions, etc.
# - Start response with "GOODBYE:" if user wants to end call
# - Otherwise start with "CONTINUE:" for normal responses

# RESPONSE STRUCTURE (if CONTINUE):
# CONTINUE: [Your short answer to their question]

# FOLLOWUP: [A contextual follow-up question based on your answer]

# IMPORTANT INSTRUCTIONS:
# 1. The context below contains REAL university information that you MUST use to answer questions
# 2. NEVER say "information not available" or "context does not contain" if relevant information is present
# 3. Look carefully through ALL context sections for relevant details
# 4. Your main answer MUST be EXTREMELY SHORT - maximum 2-3 lines only, no more than 70 words

# 5. Answer in a helpful, conversational tone as if you're an admissions counselor and 
# Convert only currency amounts to Indian words (e.g., 150000 → one lakh fifty thousand); keep phone numbers, IDs, and years as digits
# 6. Follow-up question should be relevant to what you just explained:
#    - If explained fees: ask about scholarships or payment plans
#    - If explained course: ask about placements or specializations
#    - If explained admissions: ask about dates or documents
#    - Generic fallback: "Is there anything else you would like to know about Chitkara University?"
# 7. Keep follow-up natural and conversational
# 8. If user wants to end call (GOODBYE:), just provide brief farewell (no FOLLOWUP needed)

# Context Information:
# {context_str}

# Question: {query_str}

# Response (CONTINUE: [answer] FOLLOWUP: [question] OR GOODBYE: [farewell]):"""
#     )
    
#     response_synthesizer = get_response_synthesizer(
#         streaming=True,
#         response_mode="compact",  # Using compact mode instead of tree_summarize for shorter responses
#         text_qa_template=custom_prompt_template
#     )
    
#     # Build query engine using the RetrieverQueryEngine class directly
#     from llama_index.core.query_engine import RetrieverQueryEngine
    
#     query_engine = RetrieverQueryEngine.from_args(
#         retriever,
#         response_synthesizer=response_synthesizer,
#         node_postprocessors=[reranker]
#     )
    
#     # Store all components for reuse
#     _RAG_COMPONENTS = {
#         "index": index,
#         "retriever": retriever,
#         "reranker": reranker,
#         "query_engine": query_engine
#     }
    
#     print("✓ RAG system created successfully")
#     return _RAG_COMPONENTS

# # Query the RAG system
# def query_rag_system(query_text, conversation_context="", streaming=True):
#     """
#     Query the RAG system with a user question and conversation history.
#     """
#     # Ensure RAG system is initialized
#     rag_components = create_rag_system()
#     query_engine = rag_components["query_engine"]
    
#     # Check for empty query
#     if not query_text or not query_text.strip():
#         return "Could you please provide a question?"
    
#     print(f"🔍 Querying RAG system: {query_text}")
    
#     # Use the original query - our custom system prompt will handle the instructions
#     enhanced_prompt = query_text
    
#     # Add conversation context if available
#     if conversation_context:
#         enhanced_prompt = f"Previous conversation:\n{conversation_context}\n\nCurrent question: {query_text}"
    
#     # Print debug information
#     print(f"🔍 Enhanced query with conversation context: {len(conversation_context) > 0}")
    
#     # Execute query with timeout protection
#     try:
#         # Get the retrieved nodes to print data being sent to LLM
#         retrieved_nodes = rag_components["retriever"].retrieve(enhanced_prompt)
        
#         # Print ONLY the full content that's being passed to the LLM
#         print("\n=== DATA BEING PASSED TO THE LLM ===")
#         if retrieved_nodes:
#             for node in retrieved_nodes:
#                 try:
#                     content = node.get_content() if hasattr(node, 'get_content') else str(node)
#                     if content:
#                         print(f"\n{content}")
#                         print("=" * 80)
#                 except:
#                     continue  # Skip problematic nodes
        
#         start_time = datetime.now()
        
#         # Use safe retry logic for Gemini API calls
#         response_text = safe_query_with_retry(query_engine, enhanced_prompt)
        
#         end_time = datetime.now()
#         duration = (end_time - start_time).total_seconds()
#         print(f"✓ Query completed in {duration:.2f} seconds")
        
#         # Simple response validation
#         if response_text and response_text.strip():
#             return response_text
        
#         return "I'm having trouble processing your request right now. Could you please try again?"
        
#     except Exception as e:
#         print(f"❌ Error during RAG query: {str(e)}")
#         return "I'm having trouble processing your request right now. Could you please try again?"
    
    
# # Function to setup and query the system
# def setup_and_query(query_text, conversation_context=""):
#     """
#     Set up the RAG system and query it in one step.
    
#     Args:
#         query_text: User's question
#         conversation_context: Previous conversation history
        
#     Returns:
#         Response string
#     """
#     # Create RAG system (loads from disk)
#     rag_components = create_rag_system(rebuild=False)
    
#     # Query the system
#     return query_rag_system(query_text, conversation_context)

# # Main function for compatibility with existing code
# def query_llm_with_data(translated_input, conversation_context, original_query=None, call_sid=None):
#     """
#     Function to query the LLM with translated input and conversation context.
#     Uses the improved RAG system with streaming support.
    
#     Args:
#         translated_input (str): The user's translated query
#         conversation_context (str): Context from previous conversation
#         original_query (str): The original query before enhancement (for prompt)
#         call_sid (str): The call ID to check if the call is still active
        
#     Returns:
#         str: The LLM response
#     """
#     print(f"🔍 Starting query_llm_with_data with input: '{translated_input}'")
    
#     # Check if the call has been ended (if call_sid is provided)
#     if call_sid:
#         try:
#             from config import call_states, state_manager
#             # Try the state manager first (new code)
#             if hasattr(state_manager, 'is_call_active'):
#                 if not state_manager.is_call_active(call_sid):
#                     print(f"⚠️ Call {call_sid} no longer active, cancelling LLM request")
#                     return "Call ended."
#             # Fall back to checking call_states directly (old code)
#             elif call_sid not in call_states:
#                 print(f"⚠️ Call {call_sid} no longer active, cancelling LLM request")
#                 return "Call ended."
#         except ImportError:
#             # If we can't import call_states, assume call is active
#             pass
    
#     # Use enhanced prompt if original_query is provided
#     prompt_query = original_query if original_query else translated_input
    
#     try:
#         # Use setup_and_query directly to avoid duplication
#         print(f"🔍 Querying RAG system: {translated_input}")
#         if conversation_context:
#             print(f"🔍 Enhanced query with conversation context: True")
#         else:
#             print(f"🔍 Enhanced query with conversation context: False")
            
#         # Query the system directly without double retrieval
#         response = setup_and_query(translated_input, conversation_context)
        
#         if hasattr(response, 'get_response'):  # Handle streaming response
#             response_text = str(response)
#             print(f"🤖 RAG Response (streaming): {response_text[:100]}...")
#             return response_text
#         else:
#             print(f"🤖 RAG Response: {response[:100]}...")
#             return response
            
#     except Exception as e:
#         import traceback
#         print(f"❌ Error in RAG query: {e}")
#         traceback.print_exc()
#         return "I'm having trouble processing your request right now. Could you please repeat your question?"

# # Print information if script is run directly
# if __name__ == "__main__":
#     print("🔧 LlamaIndex-powered RAG System for Information Retrieval")
#     print("This module provides enhanced RAG capabilities with hybrid retrieval")
    
#     # Interactive testing mode
#     print("\n📝 Interactive mode activated")
#     print("Initializing the RAG system...")
#     rag_components = create_rag_system()
#     print("RAG system initialized successfully!")
    
#     conversation_history = ""
    
#     print("\nType 'exit' to quit, 'stream' to toggle streaming, 'history' to view conversation history, or ask your question.")
#     streaming_mode = True
#     print(f"Streaming mode: {'ON' if streaming_mode else 'OFF'}")
    
#     while True:
#         user_input = input("\nYour question: ")
        
#         if user_input.lower() == 'exit':
#             print("Exiting the RAG system. Goodbye!")
#             break
        
#         if user_input.lower() == 'stream':
#             streaming_mode = not streaming_mode
#             print(f"Streaming mode: {'ON' if streaming_mode else 'OFF'}")
#             continue
            
#         if user_input.lower() == 'history':
#             print("\nConversation History:")
#             print(conversation_history)
#             continue
        
#         print("\nProcessing your question...")
        
#         # Get response using the RAG system
#         response = query_rag_system(user_input, conversation_history, streaming=streaming_mode)
        
#         # For streaming responses, we need to get the text
#         if hasattr(response, 'get_response'):
#             response_text = str(response)
#         else:
#             response_text = response
        
#         # Update conversation history
#         if conversation_history:
#             conversation_history += f"\nUser: {user_input}\nAssistant: {response_text}"
#         else:
#             conversation_history = f"User: {user_input}\nAssistant: {response_text}"
        
#         if not streaming_mode:
#             print(f"\nResponse: {response_text}")
#         question_count = 1
        
#         conversation_context = ""  # Initialize conversation_context
#         conversation_history_list = []  # Use a list to store history items

#         while True:
#             try:
#                 user_query = input(f"\n[{question_count}] Ask a question (or press Enter to exit): ")
#                 if not user_query.strip():
#                     print("Exiting.")
#                     break
                
#                 print("🔍 Processing query...")
#                 response = query_llm_with_data(user_query, conversation_context)
#                 print("\n🤖 Answer:\n", response)
                
#                 # Store conversation for context
#                 if response and response.strip():
#                     conversation_history_list.append(user_query)
#                     conversation_history_list.append(response)
                
#                 # Keep only the last 3 exchanges for context
#                 if len(conversation_history_list) > 6:
#                     conversation_history_list = conversation_history_list[-6:]
                
#                 # Format conversation context
#                 conversation_context = "\n\nPrevious exchanges:\n"
#                 for i in range(0, len(conversation_history_list), 2):
#                     if i + 1 < len(conversation_history_list):
#                         question = conversation_history_list[i]
#                         answer = conversation_history_list[i+1]
#                         if question and answer:  # Additional validation
#                             conversation_context += f"User asked: {question}\n"
#                             conversation_context += f"Assistant responded: {answer}\n\n"
                
#                 question_count += 1
                
#             except KeyboardInterrupt:
#                 print("\nExiting.")
#                 break
#             except Exception as e:
#                 print(f"\n❌ Error: {e}")
#     else:
#         print("To use standalone, import and call query_llm_with_data() directly")
#         print("Or run with --interactive flag for testing mode")
#         print("Example: python simple_rag.py --interactive")












"""
RAG Query System for Chitkara University Admissions
===================================================

This module handles querying the pre-built RAG index.
To update the index with new documents, run: python update_llamaindex.py

The index must exist before using this module.
"""

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
llm = Gemini(
    api_key=config.GOOGLE_API_KEY, 
    model_name="gemini-2.5-flash",
    temperature=0.0,  # Reduced for faster, more deterministic responses
    streaming=True  # Enable streaming
)
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
        similarity_top_k=3  # Get top 3 chunks (cast wide net)
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
1. The context below contains REAL university information that you MUST use to answer questions
2. NEVER say "information not available" or "context does not contain" if relevant information is present
3. Look carefully through ALL context sections for relevant details
4. Your main answer MUST be EXTREMELY SHORT - maximum 2-3 lines only, no more than 70 words
5. Answer in a helpful, conversational tone as if you're an admissions counselor and 
Convert only currency amounts to Indian words (e.g., 150000 → one lakh fifty thousand); keep phone numbers, IDs, and years as digits
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
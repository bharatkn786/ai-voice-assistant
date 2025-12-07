import asyncio
import threading
from typing import Dict, Any
import logging
from collections import defaultdict

class StateManager:
    """
    High-performance centralized state management for the calling bot application.
    Optimized for speed with minimal locking and efficient data structures.
    """
    def __init__(self, twilio_client=None):
        # Minimal locking - only for write operations that need atomicity
        self._write_lock = threading.Lock()  # Faster than RLock
        
        # Core state dictionaries - using defaultdict for faster access
        self._call_states = {}
        self._conversation_states = defaultdict(lambda: {'conversation_count': 0})
        self._conversation_history = defaultdict(list)
        self._active_websockets = {}
        
        # Webhook duplicate prevention - race condition protection
        self._webhook_processing = set()  # Track which calls are processing webhooks
        self._webhook_lock = threading.Lock()  # Separate lock for webhook operations
        
        # Reference to Twilio client for call verification
        self._twilio_client = twilio_client
        
        # Minimal logging for performance
        self.logger = logging.getLogger("state_manager")
        self.logger.setLevel(logging.ERROR)  # Only log errors to reduce overhead
        
        print("🔄 StateManager initialized")  # Use print for startup message
    
    # Call registration and status - optimized for performance
    
    def register_call(self, call_sid: str, initial_state: str = 'INITIAL') -> bool:
        """Register a new call in the system - fast path for new calls"""
        # Quick check without lock first
        if call_sid in self._call_states:
            print(f"⚠️ Call {call_sid} already registered")
            return False
        
        # Only lock for the write operation
        with self._write_lock:
            # Double-check pattern to avoid race conditions
            if call_sid in self._call_states:
                return False
                
            current_time = asyncio.get_event_loop().time()
            self._call_states[call_sid] = {
                'status': initial_state,
                'start_time': current_time,
                'last_update': current_time
            }
            # conversation_states and conversation_history use defaultdict, so no need to initialize
            
        print(f"✅ Call {call_sid} registered with state {initial_state}")
        return True
    
    def update_call_state(self, call_sid: str, new_state: str, **additional_data) -> bool:
        """Update a call's state with additional optional data - optimized version"""
        # Fast fail for non-existent calls
        if call_sid not in self._call_states:
            return False
        
        # Quick update without heavy locking
        with self._write_lock:
            if call_sid not in self._call_states:
                return False
            
            # Direct dictionary update - faster than .update()
            state = self._call_states[call_sid]
            state['status'] = new_state
            state['last_update'] = asyncio.get_event_loop().time()
            
            # Only add additional_data if provided (avoid unnecessary operations)
            if additional_data:
                state.update(additional_data)
                
        return True
            
    def set_input_start_time(self, call_sid: str, timestamp=None) -> bool:
        """Set the input start time for a call - optimized version"""
        if call_sid not in self._call_states:
            return False
        
        if timestamp is None:
            timestamp = asyncio.get_event_loop().time()
        
        # Fast path - direct assignment
        with self._write_lock:
            if call_sid not in self._call_states:
                return False
            self._call_states[call_sid]['input_start_time'] = timestamp
            
        return True
        
    def get_input_start_time(self, call_sid: str) -> float:
        """Get the input start time for a call - optimized for fast reads"""
        # No lock needed for read operations - direct access
        if call_sid not in self._call_states:
            # If call doesn't exist, return current time as fallback
            return asyncio.get_event_loop().time()
            
        return self._call_states.get(call_sid, {}).get('input_start_time', asyncio.get_event_loop().time())
    
    def is_call_active(self, call_sid: str) -> bool:
        """Check if a call is registered and active - NO LOCK for maximum speed"""
        # This is called very frequently, so avoid any locking overhead
        return call_sid in self._call_states
    
    def get_call_state(self, call_sid: str) -> Dict[str, Any]:
        """Get current state of a call - NO LOCK for read operations"""
        # Fast path - direct dictionary access without locking
        state = self._call_states.get(call_sid)
        if not state:
            return {}
        
        # Return minimal state info for performance
        return {
            'status': state.get('status'), 
            'last_update': state.get('last_update')
        }
    
    def end_call(self, call_sid: str) -> bool:
        """End a call and clean up its state - optimized cleanup"""
        # Quick check without lock
        if call_sid not in self._call_states:
            return False
        
        websocket = None
        with self._write_lock:
            if call_sid not in self._call_states:
                return False
                
            # Fast cleanup - direct pop operations
            self._call_states.pop(call_sid, None)
            self._conversation_states.pop(call_sid, None)
            self._conversation_history.pop(call_sid, None)
            websocket = self._active_websockets.pop(call_sid, None)
        
        # Clean up webhook processing flag (outside main lock to avoid deadlock)
        with self._webhook_lock:
            self._webhook_processing.discard(call_sid)
        
        # Close websocket outside of lock to avoid blocking
        if websocket:
            try:
                asyncio.create_task(websocket.close())
            except Exception:
                pass  # Ignore websocket close errors
        
        print(f"🧹 Call {call_sid} ended and cleaned up")
        return True
    
    # Conversation history management - optimized for speed
    
    def add_to_conversation_history(self, call_sid: str, user_input: str, response: str) -> bool:
        """Add a new exchange to the conversation history - fast path"""
        # Fast fail for non-existent calls
        if call_sid not in self._call_states:
            return False
        
        with self._write_lock:
            if call_sid not in self._call_states:
                return False
            
            # Use defaultdict's automatic list creation
            history = self._conversation_history[call_sid]
            history.extend([user_input, response])
            
            # Keep only the last 3 exchanges (6 items) - faster than slicing
            if len(history) > 6:
                # More efficient than slicing for small lists
                self._conversation_history[call_sid] = history[-6:]
                
            # Update conversation counter efficiently
            self._conversation_states[call_sid]['conversation_count'] += 1
                    
        return True
    
    def get_conversation_context(self, call_sid: str) -> str:
        """Get formatted conversation context for LLM prompting - optimized"""
        history = self._conversation_history.get(call_sid, [])
        if not history:
            return ""
        
        # Fast string building with list comprehension
        context_parts = ["\n\nPrevious exchanges:\n"]
        for i in range(0, len(history), 2):
            if i + 1 < len(history):
                context_parts.extend([
                    f"User asked: {history[i]}\n",
                    f"Assistant responded: {history[i+1]}\n\n"
                ])
        
        return "".join(context_parts)
    
    def get_conversation_count(self, call_sid: str) -> int:
        """Get the conversation count for a call - fast lookup"""
        return self._conversation_states[call_sid]['conversation_count']
            
    def increment_conversation_count(self, call_sid: str) -> int:
        """Increment the conversation count and return the new value - optimized"""
        # Use defaultdict's automatic initialization
        count = self._conversation_states[call_sid]['conversation_count'] + 1
        self._conversation_states[call_sid]['conversation_count'] = count
        return count
    
    def update_language(self, call_sid: str, language_code: str) -> bool:
        """Update the detected language for a call - fast path"""
        if call_sid not in self._call_states:
            return False
            
        # Direct assignment - no locking needed for simple updates
        self._conversation_states[call_sid]['detected_lang'] = language_code
        return True
    
    def get_language(self, call_sid: str) -> str:
        """Get the detected language for a call - no lock needed"""
        return self._conversation_states[call_sid].get('detected_lang', 'en')
    
    # Webhook duplicate prevention - race condition protection
    
    def start_webhook_processing(self, call_sid: str) -> bool:
        """
        Mark that webhook is being processed for this call.
        Returns True if we can proceed, False if already processing.
        Thread-safe for multiple concurrent calls.
        """
        with self._webhook_lock:
            if call_sid in self._webhook_processing:
                print(f"🚫 Webhook already processing for {call_sid}")
                return False  # Already processing, reject duplicate
            
            self._webhook_processing.add(call_sid)
            print(f"✅ Started webhook processing for {call_sid}")
            return True
    
    def end_webhook_processing(self, call_sid: str):
        """Mark that webhook processing is complete"""
        with self._webhook_lock:
            self._webhook_processing.discard(call_sid)
            print(f"🏁 Ended webhook processing for {call_sid}")
    
    # WebSocket management - optimized
    
    def register_websocket(self, call_sid: str, websocket) -> bool:
        """Register websocket for a call - minimal locking"""
        if call_sid not in self._call_states:
            return False
            
        with self._write_lock:
            self._active_websockets[call_sid] = websocket
        return True
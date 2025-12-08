import asyncio
import traceback
from config import state_manager
from tts import speak_async
from langdetect import detect
from translator_utils import translate_to_english, translate_from_english, has_hindi_characters
from simple_rag import query_llm_with_data
from database import save_conversation
async def process_university_query(call_sid: str, user_input: str):
    """Process user query with Gemini for Chitkara University information"""
    print(f"🤖 Processing query for call {call_sid}: {user_input}")
    
    # Check if the call still exists using state manager
    if not state_manager.is_call_active(call_sid):
        print(f"⚠️ Call {call_sid} no longer active, skipping LLM processing")
        return
        
    # Update call state to PROCESSING
    state_manager.update_call_state(call_sid, 'PROCESSING')
    
    # Detect language (Hindi or English only)
    try:
        detected_lang = detect(user_input)
        if detected_lang != 'hi':
            detected_lang = 'en'
        print(f"🌍 Detected language: {detected_lang}")
    except Exception:
        detected_lang = 'en'
        print("⚠️ Language detection failed, defaulting to English")

    # Store the detected language using state manager
    state_manager.update_language(call_sid, detected_lang)
    print(f"🔤 Stored language '{detected_lang}' in conversation state")
    
    # Translate to English if not English - this is required for LLM processing
    translated_input = user_input
    if detected_lang != 'en':
        try:
            # Use robust translation with timeout and retry
            translated_input = await translate_to_english(user_input, detected_lang)    # the input has been converted into english
            print(f"🔄 Translated to English: {translated_input}")
        except Exception as e:
            print(f"⚠️ Translation error: {e}")
            print(f"🔄 Continuing with original input: {user_input}")
            translated_input = user_input

    # Get conversation context from state manager
    conversation_context = state_manager.get_conversation_context(call_sid)

    # Query the RAG system
    print(f"🔄 Using improved RAG-enhanced query system with SentenceSplitter...")
    
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(lambda: query_llm_with_data(
                translated_input, 
                conversation_context, 
                call_sid=call_sid
            )),
            timeout=45.0  # Increased from 30s to handle Gemini overload retries
        )
        
        # Validate response
        if not response or response.strip() == "":
            response = "I'm sorry, I couldn't generate a proper response. Could you please repeat your question?"
        
        print(f"🤖 Improved RAG-enhanced response: {response}")
        
    except asyncio.TimeoutError:
        print(f"⏰ RAG query timeout after 45 seconds")
        response = "I'm having trouble processing your request right now. Could you please repeat your question?"
    except Exception as e:
        print(f"❌ RAG Error: {e}")
        traceback.print_exc()
        response = "I'm having a little trouble right now. Could you please repeat your question?"
    
    # ✅ NEW: Check if Gemini detected goodbye intent (response starts with "GOODBYE:")
    if response.startswith("GOODBYE:"):
        print(f"👋 Gemini detected goodbye intent for call {call_sid}")
        
        # Remove the "GOODBYE:" prefix to get the actual farewell message
        goodbye_msg = response.replace("GOODBYE:", "").strip()
        
        # If Gemini didn't provide a good message, use default

        # // this will be trigger whne the user will not give any answer compelte silence
        if not goodbye_msg or len(goodbye_msg) < 10:
            if detected_lang == 'hi':
                goodbye_msg = "चितकारा विश्वविद्यालय को कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!"
            else:
                goodbye_msg = "Thank you for calling Chitkara University. Have a great day!"
        
        # Translate goodbye message if needed
        if detected_lang != 'en' and detected_lang == 'hi':
            try:
                translated_goodbye = await translate_from_english(goodbye_msg, detected_lang)
                goodbye_msg = translated_goodbye
                print(f"🔄 Translated goodbye to {detected_lang}")
            except Exception as e:
                print(f"⚠️ Goodbye translation error, using default: {e}")
                goodbye_msg = "चितकारा विश्वविद्यालय को कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!"

        # 💾 Save goodbye conversation to database
        try:
            save_conversation(call_sid, user_input, goodbye_msg)
            print(f"💾 Goodbye conversation saved to database: Q: {user_input}... A: {goodbye_msg}...")
        except Exception as e:
            print(f"⚠️ Failed to save goodbye conversation to database: {e}")
        
        # Speak goodbye and end call
        await speak_async(call_sid, goodbye_msg, hangup=True)
        print(f"👋 Goodbye message sent, call will end after speech")
        return
    
    # ✅ NEW: Parse main response and follow-up from single Gemini response
    main_response = response
    followup_question = None
    
    # Remove "CONTINUE:" prefix if present
    if main_response.startswith("CONTINUE:"):
        main_response = main_response.replace("CONTINUE:", "").strip()
        print(f"✅ Continuing conversation, removed prefix")
    
    # Check if response contains "FOLLOWUP:" separator
    if "FOLLOWUP:" in main_response:
        parts = main_response.split("FOLLOWUP:", 1)
        main_response = parts[0].strip()
        
        # ✅ FIXED: Check if parts array has more than one element before accessing parts[1]
        if len(parts) > 1 and parts[1].strip():
            followup_question = parts[1].strip()
            print(f"✅ Gemini generated follow-up: {followup_question}")
        else:
            # Edge case: FOLLOWUP: exists but empty - use generic fallback
            followup_question = "Is there anything else you would like to know about Chitkara University?" if detected_lang == 'en' else "क्या आप चितकारा विश्वविद्यालय के बारे में कुछ और जानना चाहेंगे?"
            print(f"⚠️ FOLLOWUP: found but empty, using default")
    else:
        # No FOLLOWUP: found - this shouldn't happen with the prompt, log warning
        followup_question = "Is there anything else you would like to know about Chitkara University?" if detected_lang == 'en' else "क्या आप चितकारा विश्वविद्यालय के बारे में कुछ और जानना चाहेंगे?"
        print(f"⚠️ WARNING: Gemini didn't generate follow-up (check prompt)")

    # Store BOTH main answer AND follow-up question in conversation history
    # This way, when user says "yes", Gemini knows what they're responding to
    full_response_with_followup = f"{main_response} {followup_question}"
    state_manager.add_to_conversation_history(call_sid, user_input, full_response_with_followup)

    # Translate main response if needed
    translated_main = main_response
    if detected_lang != 'en':
        try:
            translated_main = await translate_from_english(main_response, detected_lang)
            print(f"🔄 Translated main response to {detected_lang}")
        except Exception as e:
            print(f"⚠️ Main response translation error, using English: {e}")
    
    # Translate follow-up if needed
    translated_followup = followup_question
    if detected_lang != 'en':
        try:
            # Check if follow-up needs translation (might already be in Hindi from Gemini)
            if not has_hindi_characters(followup_question):
                translated_followup = await translate_from_english(followup_question, detected_lang)
                print(f"🔄 Translated follow-up to {detected_lang}")
        except Exception as e:
            print(f"⚠️ Follow-up translation error, using original: {e}")
    
    # Check call status before speaking
    if not state_manager.is_call_active(call_sid):
        print(f"⚠️ Call {call_sid} not active before response TTS, skipping")
        return
    
    # ✅ NEW: Combine main response + follow-up in SINGLE TTS call
    combined_message = f"{translated_main}. {translated_followup}"

    # 💾 Save conversation to database - save complete response that user heard
    try:
        # Save the complete response (both answer and follow-up) in English for database consistency
        full_response_for_db = f"{main_response}. {followup_question}"
        save_conversation(call_sid, user_input, full_response_for_db)
        print(f"💾 Conversation saved to database: Q: {user_input}... A: {full_response_for_db}...")
    except Exception as e:
        print(f"⚠️ Failed to save conversation to database: {e}")
    
    print(f"🔊 Speaking combined message: answer + follow-up")
    await speak_async(call_sid, combined_message, hangup=False, is_followup=False)
    
    # Increment conversation count
    state_manager.increment_conversation_count(call_sid)
    print(f"🔢 User has asked {state_manager.get_conversation_count(call_sid)} questions")
    
    print(f"✅ Query processing completed with TTS")


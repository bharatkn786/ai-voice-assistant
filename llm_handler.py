# import asyncio
# from config import llm, GOOGLE_API_KEY, state_manager
# from tts import speak_and_wait
# from deep_translator import GoogleTranslator
# from langdetect import detect
# from translator_utils import robust_translate, translate_to_english, translate_from_english, has_hindi_characters

# import asyncio
# from config import llm, GOOGLE_API_KEY, state_manager
# from tts import speak_and_wait
# from langdetect import detect
# from translator_utils import robust_translate, translate_to_english, translate_from_english, has_hindi_characters

# async def process_university_query(call_sid: str, user_input: str):
#     """Process user query with Gemini for Chitkara University information"""
#     print(f"🤖 Processing query for call {call_sid}: {user_input}")
    
#     # Check if the call still exists using state manager
#     if not state_manager.is_call_active(call_sid):
#         print(f"⚠️ Call {call_sid} no longer active, skipping LLM processing")
#         return
        
#     # Update call state to PROCESSING
#     state_manager.update_call_state(call_sid, 'PROCESSING')
    
#     # Simple approach: Let the user choose language with keywords
    
#     # Check for common English phrases first to avoid misdetection
#     # try:
#     #     detected_lang = detect(user_input)
#     #     # Force English for anything other than Hindi
#     #     if detected_lang != 'hi':
#     #         detected_lang = 'en'
#     #         print(f"🌍 Detected language: {detected_lang}")
#     #     else: detected_lang='hi'
#     # except:
#     #     detected_lang = 'en'
#     #     print(f"⚠️ Language detection failed, defaulting to English")
#     try:
#         detected_lang = detect(user_input)
#         # Only consider Hindi or English for simplicity
#         if detected_lang != 'hi':
#             detected_lang = 'en'
#         print(f"🌍 Detected language using langdetect: {detected_lang}")
#     except Exception:
#         detected_lang = 'en'
#         print("⚠️ Language detection failed, defaulting to English")

#     # Store the detected language using state manager
#     state_manager.update_language(call_sid, detected_lang)
#     print(f"🔤 Stored language '{detected_lang}' in conversation state")
    
#     # Translate to English if not English

#     # // translated to english and passed further to gemini
#     translated_input = user_input
#     if detected_lang != 'en':
#         try:
#             # Use robust translation with timeout and retry
#             translated_input = await translate_to_english(user_input, detected_lang)    # the input has been converted into english

#             print(f"🔄 Translated to English: {translated_input}")
#         except Exception as e:
#             print(f"⚠️ Translation error: {e}")
#             print(f"🔄 Continuing with original input: {user_input}")
    
    
#     user_lower = translated_input.lower().strip()
#     user_clean = user_lower.rstrip('.,!?')

#     end_phrases = ["No","no", "no thank you", "nothing", "that's it", "nah", "bye", "goodbye", "no more questions", "no thanks", "nothing else", "that's all", "i'm done", "finished", "end call"]

#     is_goodbye = (user_clean in end_phrases or 
#                   user_lower.startswith("no,") or 
#                   user_lower.startswith("no thank you") or
#                   user_lower.startswith("bye") or
#                   user_lower.startswith("goodbye") or
#                   user_lower.startswith("that's") or
#                   user_lower.startswith("nothing") or
#                   user_lower.startswith("i don't") or
#                   user_lower.startswith("i'm good") or
#                   "no more" in user_lower or
#                   "don't need" in user_lower)

#     if is_goodbye:
#         goodbye_msg = "Thank you for calling Chitkara University. Have a great day!"
#         if detected_lang != 'en':
#             try:
#                 # Use robust translation with timeout and retry
#                 translated_goodbye = await translate_from_english(goodbye_msg, detected_lang)
#                 print(f"🔄 Translated goodbye to {detected_lang}: {translated_goodbye}")
                
#                 # Add Hindi characters for Hindi responses
#                 if detected_lang == 'hi' and not has_hindi_characters(translated_goodbye):
#                     hindi_phrases = {
#                         'hi': "चितकारा विश्वविद्यालय को कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!"
#                     }
#                     if detected_lang in hindi_phrases:
#                         translated_goodbye = hindi_phrases[detected_lang]
#                         print(f"🔄 Using hardcoded Hindi goodbye phrase")
#                 goodbye_msg = translated_goodbye
#             except Exception as e:
#                 print(f"⚠️ Goodbye translation error: {e}")
#                 # Fallback to hardcoded Hindi goodbye if translation fails
#                 if detected_lang == 'hi':
#                     goodbye_msg = "चितकारा विश्वविद्यालय को कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!"
#                     print(f"🔄 Using fallback Hindi goodbye phrase")
#     # Check call status before goodbye
#         try:
#             from config import twilio_client
#             call_info = twilio_client.calls(call_sid).fetch()
#             if call_info.status not in ['in-progress', 'ringing']:
#                 print(f"⚠️ Call {call_sid} not active before goodbye TTS (status: {call_info.status}), skipping")
#                 return
#         except Exception as e:
#             print(f"❌ Error checking call status before goodbye: {e}")
#             return
        
#         await speak_and_wait(call_sid, goodbye_msg, hangup=True)
#         return

#     # Get conversation context from state manager
#     conversation_context = state_manager.get_conversation_context(call_sid)
    
#     # Debug the conversation context
#     print(f"🔍 DEBUG - Formatted conversation context being used: {conversation_context}")

#     # Import query_llm_with_data from simple_rag.py here to avoid circular imports
#     try:
#         from simple_rag import query_llm_with_data
#         print(f"🔄 Using improved RAG-enhanced query system with SentenceSplitter...")
        
#         # Use the simple_rag function to get a response based on document search
#         try:            
#             response = await asyncio.wait_for(
#                 asyncio.to_thread(lambda: query_llm_with_data(translated_input, conversation_context, call_sid=call_sid)),
#                 timeout=30.0
#             )
            
#             # Validate response
#             if not response or response.strip() == "":
#                 response = "I'm sorry, I couldn't generate a proper response. Could you please repeat your question?"
            
#             print(f"🤖 Improved RAG-enhanced response: {response}")
            
#         except asyncio.TimeoutError:
#             print(f"⏰ RAG query timeout after 20 seconds")
#             response = "I'm having trouble processing your request right now. Could you please repeat your question?"
#         except Exception as e:
#             print(f"❌ RAG Error: {e}")
#             import traceback
#             traceback.print_exc()
#             response = "I'm having a little trouble right now. Could you please repeat your question?"
            
#     except ImportError:
#         # Fall back to direct LLM query if simple_rag is not available
#         print(f"⚠️ Simple RAG not available, falling back to direct query")
#         university_prompt = f"""
#         You are a helpful AI assistant for Chitkara University. A prospective student or parent has asked: "{translated_input}"
#         {conversation_context}
#         Provide a helpful, accurate, and concise response about Chitkara University. Use the conversation context to understand references like "it", "that course", "those documents", etc.
#         IMPORTANT: Keep your response very short - maximum 2 sentences only. Be direct and to the point.
#         """

#         try:
#             print(f"🔄 Calling Gemini API directly...")
#             response = await asyncio.wait_for(
#                 asyncio.to_thread(lambda: llm.invoke(university_prompt).content),
#                 timeout=15.0
#             )
#             print(f"🤖 Gemini response: {response}")
#         except asyncio.TimeoutError:
#             print(f"⏰ Gemini API timeout after 15 seconds")
#             response = "I'm having trouble processing your request right now. Could you please repeat your question?"
#         except Exception as e:
#             print(f"❌ Gemini Error: {e}")
#             import traceback
#             traceback.print_exc()
#             response = "I'm having a little trouble right now. Could you please repeat your question?"

#     # Store original English response in conversation history using state manager
#     state_manager.add_to_conversation_history(call_sid, user_input, response)
    
#     # Debug the updated conversation history
#     print(f"🔍 DEBUG - Updated conversation history after adding new exchange")

#     # Translate response back if needed (with corruption detection)
#     if detected_lang != 'en':
#         try:
#             # Use robust translation with timeout and retry
#             translated_response = await translate_from_english(response, detected_lang)
#             print(f"🔄 Translated response to {detected_lang}: {translated_response}")
            
#             # Validate translation - if it looks corrupted, use English
#         except Exception as e:
#             print(f"⚠️ Response translation error, using English: {e}")
            
#             # Check call status before speaking
#             try:
#                 from config import twilio_client
#                 call_info = twilio_client.calls(call_sid).fetch()
#                 if call_info.status not in ['in-progress', 'ringing']:
#                     print(f"⚠️ Call {call_sid} not active before response TTS (status: {call_info.status}), skipping")
#                     return
#             except Exception as e:
#                 print(f"❌ Error checking call status before response: {e}")
#                 return
            
#             await speak_and_wait(call_sid, response)

#     # --- RACE CONDITION FIX ---
#     # After speaking, the user may have hung up. Check if the call still exists in our state.
#     if not state_manager.is_call_active(call_sid):
#         print(f"🏃 Call {call_sid} ended during AI response. Aborting follow-up.")
#         return

#     # Translate follow-up question
#     follow_up = "Is there anything else you would like to know about Chitkara University?"
#     if detected_lang != 'en':
#         try:
#             # Use robust translation with timeout and retry
#             translated_follow_up = await translate_from_english(follow_up, detected_lang)
#             print(f"🔄 Translated follow-up to {detected_lang}: {translated_follow_up}")
            
#             # Validate translation - if corrupted, use hardcoded Hindi or English
#             if (len(translated_follow_up) > len(follow_up) * 3 or 
#                 'thaumak' in translated_follow_up or 
#                 'kanak' in translated_follow_up):
#                 print(f"⚠️ Follow-up translation corrupted, using fallback")
#                 if detected_lang == 'hi':
#                     follow_up = "क्या आप चितकारा विश्वविद्यालय के बारे में कुछ और जानना चाहेंगे?"
#                 else:
#                     follow_up = follow_up  # Keep English
#             else:
#                 # Add Hindi characters for Hindi responses if missing
#                 if detected_lang == 'hi' and not has_hindi_characters(translated_follow_up):
#                     follow_up = "क्या आप चितकारा विश्वविद्यालय के बारे में कुछ और जानना चाहेंगे?"
#                     print(f"🔄 Using hardcoded Hindi follow-up phrase")
            
#             follow_up = translated_follow_up
#         except Exception as e:
#             print(f"⚠️ Follow-up translation error: {e}")
    
#     # Check call status before follow-up
#     try:
#         from config import twilio_client
#         call_info = twilio_client.calls(call_sid).fetch()
#         if call_info.status not in ['in-progress', 'ringing']:
#             print(f"⚠️ Call {call_sid} not active before follow-up TTS (status: {call_info.status}), skipping")
#             return
#     except Exception as e:
#         print(f"❌ Error checking call status before follow-up: {e}")
#         return
    
#     await speak_and_wait(call_sid, follow_up)

#     # --- RACE CONDITION FIX ---
#     # Final check before updating state. If the call ended during the follow-up, do not proceed.
#     if state_manager.is_call_active(call_sid):
#         await asyncio.sleep(0.5)
#         state_manager.set_call_state(call_sid, 'WAITING_INPUT')
#         state_manager.set_input_start_time(call_sid, asyncio.get_event_loop().time())
#         print(f"🎤 READY FOR IMMEDIATE INPUT - You can speak now!")

#         state_manager.increment_conversation_count(call_sid)
#         print(f"🔢 User has asked {state_manager.get_conversation_count(call_sid)} questions - unlimited conversation!")
#     else:
#         print(f"🏃 Call {call_sid} ended during follow-up prompt. State not updated.")











# //according to new state managemnet
#working fine with new state and is before new tts stream and lllm
import asyncio
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
    

    #         goodbye_msg = "चितकारा विश्वविद्यालय को कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!"
    #         print(f"🔄 Using hardcoded Hindi goodbye phrase")
    #     else:
    #         goodbye_msg = "Thank you for calling Chitkara University. Have a great day!"
    #     await speak_async(call_sid, goodbye_msg, hangup=True)
    #     print(f"👋 Goodbye message sent, call will end after speech")
    #     return

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
        import traceback
        traceback.print_exc()
        response = "I'm having a little trouble right now. Could you please repeat your question?"
    
    # ✅ NEW: Check if Gemini detected goodbye intent (response starts with "GOODBYE:")
    if response.startswith("GOODBYE:"):
        print(f"👋 Gemini detected goodbye intent for call {call_sid}")
        
        # Remove the "GOODBYE:" prefix to get the actual farewell message
        goodbye_msg = response.replace("GOODBYE:", "").strip()
        
        # If Gemini didn't provide a good message, use default
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
            # Fallback if FOLLOWUP: exists but no content after it
            if detected_lang == 'hi':
                followup_question = "क्या आप चितकारा विश्वविद्यालय के बारे में कुछ और जानना चाहेंगे?"
            else:
                followup_question = "Is there anything else you would like to know about Chitkara University?"
            print(f"⚠️ FOLLOWUP: found but empty, using default")
    else:
        # Fallback if Gemini didn't generate follow-up
        if detected_lang == 'hi':
            followup_question = "क्या आप चितकारा विश्वविद्यालय के बारे में कुछ और जानना चाहेंगे?"
        else:
            followup_question = "Is there anything else you would like to know about Chitkara University?"
        print(f"⚠️ No follow-up found, using default")

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
            from translator_utils import has_hindi_characters
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


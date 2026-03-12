




# working fine before new stream
# 📍 logging Usage in stream_handler_simple.py:
# With this code, you only see warnings and errors from Twilio:

# ❌ ERROR and WARNING messages still show
# ✅ INFO and DEBUG messages are suppressed
import json
import base64
import asyncio
import websockets
import random
import logging
from fastapi import WebSocket
from config import DEEPGRAM_URL, DEEPGRAM_API_KEY, state_manager
from llm_handler import process_university_query
from database import save_conversation

# Reduce noisy Twilio HTTP client logs
logging.getLogger('twilio').setLevel(logging.WARNING)
logging.getLogger("twilio.http_client").setLevel(logging.WARNING)

async def connect_to_deepgram(retries: int = 3, base_delay: float = 2.0):
    """Try to connect to Deepgram with retry/backoff and max attempts limit"""
    for attempt in range(retries):
        try:
            ws = await asyncio.wait_for(
                websockets.connect(
                    DEEPGRAM_URL,
                    additional_headers=[("Authorization", f"Token {DEEPGRAM_API_KEY}")]
                ),
                timeout=15,
            )
            print("✅ Connected to Deepgram successfully")
            return ws
        except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError, Exception) as e:
            wait = base_delay * (2 ** attempt) + random.random()
            print(f"⚠️ Deepgram connect failed (attempt {attempt+1}) → retrying in {wait:.1f}s | {e}")
            if attempt < retries - 1:  # Don't wait after the last attempt
                await asyncio.sleep(wait)
    print("❌ Could not connect to Deepgram after retries")
    return None

async def twilio_stream_websocket(websocket: WebSocket):
    await websocket.accept()
    call_sid, deepgram_ws, cleanup_done = None, None, False
    current_transcript = ""
    input_timer = None
    silence_timer = None  # Timer for complete silence detection
    silence_count = 0  # 👉 Counts how many times user stayed silent
    deepgram_reconnect_count = 0  # 🔧 Track reconnection attempts
    max_deepgram_reconnects = 10  # 🔧 Maximum reconnection attempts

    try:
        deepgram_ws = await connect_to_deepgram()
        if not deepgram_ws:
            return

        async def ask_followup_question():
            """Ask follow-up when user is completely silent"""
            nonlocal silence_count
            from tts import speak_async

            silence_count += 1
            print(f"🤫 Silence detected — count = {silence_count}")

            # 👉 If user silent 3 times, end the call
            if silence_count >= 3:
                print("📵 User silent 3 times — ending call")
                farewell_message = "Since you are not responding, I will end the call now. Have a great day!"
                
                # Save farewell message to database
                try:
                    save_conversation(call_sid, "NO_RESPONSE_3_TIMES", farewell_message)
                    print(f"💾 Farewell message saved to database for call {call_sid}")
                except Exception as e:
                    print(f"⚠️ Failed to save farewell message: {e}")
                
                await speak_async(call_sid, farewell_message, hangup=True)
                
                # Set a backup timer to force cleanup if webhook fails
                async def force_cleanup_after_silence():
                    await asyncio.sleep(10)  # Wait 10 seconds for speech to complete
                    if state_manager.is_call_active(call_sid):
                        print(f"🚨 Force cleaning up call {call_sid} after silence timeout")
                        cleanup()
                
                asyncio.create_task(force_cleanup_after_silence())
                # Webhook will handle the actual call termination
                return

            # Otherwise just ask follow-up (using is_followup=True since it's a prompt)
            followup_message = "Are you still there? Do you have any questions about the university?"
            try:
                # Save follow-up message to database
                try:
                    save_conversation(call_sid, "SILENCE_DETECTED", followup_message)
                    print(f"💾 Silence follow-up message saved to database for call {call_sid}")
                except Exception as e:
                    print(f"⚠️ Failed to save silence follow-up message: {e}")
                
                # Store flag that we're waiting for response after this silence prompt
                state_manager._call_states[call_sid]['pending_followup'] = None  # No followup after this
                state_manager._call_states[call_sid]['after_silence_prompt'] = True
                await speak_async(call_sid, followup_message, is_followup=True)
                print("🎤 Asked 'Are you still there?', waiting for user response")
                # Timer will be restarted after webhook completes
            except Exception as e:
                print(f"❌ Error asking follow-up: {e}")


        async def start_complete_silence_timer():
            """Starts timer for complete silence (no speech at all)"""
            nonlocal silence_timer, silence_count
            
            # Cancel existing silence timer
            if silence_timer and not silence_timer.done():
                silence_timer.cancel()
            
            # Progressive timer: 5s, 8s, 12s based on silence count
            timer_duration = 6 + (silence_count * 2)  # 5s for first, 8s for second, 12s for third
            
            async def handle_complete_silence():
                await asyncio.sleep(timer_duration)
                if not state_manager.is_call_active(call_sid):
                    return
                state = state_manager.get_call_state(call_sid)
                if state.get("status") == "WAITING_INPUT":
                    # Check if there's been no speech activity
                    if not current_transcript.strip():
                        await ask_followup_question()
            
            silence_timer = asyncio.create_task(handle_complete_silence())
            print(f"🔕 Started complete silence timer ({timer_duration}s) [count={silence_count}]")

        async def process_user_input():
            nonlocal current_transcript, silence_timer,silence_count
            silence_count = 0  # ✅ Reset counter when user talks again

            if call_sid and state_manager.get_call_state(call_sid).get("status") == "WAITING_INPUT":
                print(f"💬 Processing: '{current_transcript}'")
                processed_transcript = current_transcript.strip()
                current_transcript = ""

                # Cancel silence timer since we're processing user input
                if silence_timer and not silence_timer.done():
                    silence_timer.cancel()

                state_manager.update_call_state(call_sid, "PROCESSING")     #state is being updated
                
                # 🎵 Play background music during processing
                try:
                    from config import twilio_client
                    import html
                    # GitHub raw URL - direct MP3 access
                    music_url = "https://raw.githubusercontent.com/bharatkn786/music/main/call-172234.mp3"
                    escaped_url = html.escape(music_url)
                    twilio_client.calls(call_sid).update(
                        twiml=f'<?xml version="1.0" encoding="UTF-8"?><Response><Play loop="100">{escaped_url}</Play><Pause length="60"/></Response>'
                    )
                    print("🎵 Background music started")
                except Exception as e:
                    print(f"⚠️ Music error: {e}")
                
                try:
                    await process_university_query(call_sid, processed_transcript)
                    print("✅ Query processing completed with TTS")
                    
                    # After processing, start silence detection for next input
                    if state_manager.is_call_active(call_sid):
                        await start_complete_silence_timer()
                        
                except Exception as e:
                    print(f"❌ Error in process_university_query: {e}")
                    if state_manager.is_call_active(call_sid):
                        state_manager.update_call_state(call_sid, "WAITING_INPUT",
                                                       input_start_time=asyncio.get_event_loop().time())
                        print("🎤 Reset to WAITING_INPUT after error")
                        await start_complete_silence_timer()

        async def start_silence_timer():
            """Starts or resets a 3s silence timeout after user speech"""
            nonlocal input_timer, silence_timer

            # Cancel both timers when user speaks
            if input_timer and not input_timer.done():
                input_timer.cancel()
            if silence_timer and not silence_timer.done():
                silence_timer.cancel()

            async def handle_timeout():
                await asyncio.sleep(3.5)  #chnaged from 4 to 3
                if not state_manager.is_call_active(call_sid):
                    return
                state = state_manager.get_call_state(call_sid)
                if state.get("status") != "WAITING_INPUT":
                    return
                if current_transcript.strip():
                    print(f"⏰ 3s silence — processing transcript: '{current_transcript}'")
                    await process_user_input()
                else:
                    # No transcript but timer expired - start silence detection
                    await start_complete_silence_timer()

            input_timer = asyncio.create_task(handle_timeout())
            print("⏰ Started speech silence timer (3s)")

        async def forward_audio_to_deepgram():
            nonlocal call_sid, deepgram_ws, deepgram_reconnect_count
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message["event"] == "start":
                        call_sid = message["start"]["callSid"]
                        if state_manager.is_call_active(call_sid):
                            print(f"❌ Duplicate call {call_sid} - closing")
                            return
                        state_manager.register_websocket(call_sid, websocket)
                        state_manager.register_call(call_sid, "SPEAKING")
                        print(f"📞 NEW CALL CONNECTED: {call_sid}")

                        state_manager.update_call_state(call_sid, "WAITING_INPUT",
                                                       input_start_time=asyncio.get_event_loop().time())
                        print("🎤 Ready for user input")
                        
                        # Start silence detection for initial input
                        await start_complete_silence_timer()

                    elif message["event"] == "media":
                        payload = base64.b64decode(message["media"]["payload"])
                        try:
                            if deepgram_ws and hasattr(deepgram_ws, 'send'):
                                await deepgram_ws.send(payload)
                        except Exception as e:
                            # Don't increment counter for simple send errors
                            if "no close frame" in str(e).lower() or "close" in str(e).lower():
                                print(f"⚠️ Deepgram send warning: {e}")
                                # Try to reconnect but don't fail the call
                                try:
                                    deepgram_ws = await connect_to_deepgram()
                                except:
                                    pass  # Continue with existing connection
                            else:
                                deepgram_reconnect_count += 1
                                if deepgram_reconnect_count > max_deepgram_reconnects:
                                    print(f"❌ Max Deepgram reconnection attempts reached in audio forward. Ending call.")
                                    cleanup()
                                    break
                                print(f"🚨 Lost Deepgram during send: {e} (Attempt {deepgram_reconnect_count}/{max_deepgram_reconnects})")
                                deepgram_ws = await connect_to_deepgram()
                                if not deepgram_ws:
                                    print("❌ Failed to reconnect to Deepgram in audio forward. Ending call.")
                                    cleanup()
                                    break

                    elif message["event"] == "stop":
                        print(f"🛑 Call stopped: {call_sid}")
                        cleanup()
                        return

                except Exception as e:
                    print(f"🚨 Twilio stream error: {e}")
                    break

        async def process_deepgram_transcripts():
            nonlocal deepgram_ws, current_transcript, deepgram_reconnect_count

            while not cleanup_done and state_manager.is_call_active(call_sid):
                try:
                    msg = await deepgram_ws.recv()
                    message = json.loads(msg)

                    # Handle user speech transcripts only
                    if "channel" in message and "alternatives" in message["channel"]:
                        transcript = message["channel"]["alternatives"][0].get("transcript", "").strip()
                        is_final = message.get("is_final", False)

                        if transcript and state_manager.is_call_active(call_sid):
                            state = state_manager.get_call_state(call_sid)
                            if state.get("status") == "WAITING_INPUT":
                                current_transcript = f"{current_transcript} {transcript}".strip()
                                if not is_final:
                                    print(f"🎙️ Interim user speech: '{transcript}'")
                                else:
                                    print(f"📝 Final user speech: '{transcript}' (Full: '{current_transcript}')")
                                await start_silence_timer()

                except (websockets.exceptions.ConnectionClosedError, Exception) as e:
                    if cleanup_done or not state_manager.is_call_active(call_sid):
                        break
                    
                    deepgram_reconnect_count += 1
                    if deepgram_reconnect_count > max_deepgram_reconnects:
                        print(f"❌ Max Deepgram reconnection attempts ({max_deepgram_reconnects}) reached. Ending call.")
                        cleanup()
                        break
                    
                    print(f"🚨 Deepgram connection error: {e}. Reconnecting... (Attempt {deepgram_reconnect_count}/{max_deepgram_reconnects})")
                    deepgram_ws = await connect_to_deepgram()
                    if not deepgram_ws:
                        print("❌ Failed to reconnect to Deepgram. Ending call.")
                        cleanup()
                        break

        async def keep_deepgram_alive():
            """Keep Deepgram connection alive by sending silence packets during SPEAKING/PROCESSING"""
            
            # µ-law silence packet (20ms of silence at 8kHz = 160 bytes)
            silence_packet = b'\xff' * 160
            
            while not cleanup_done and state_manager.is_call_active(call_sid):
                try:
                    await asyncio.sleep(1)  # Check every 500ms
                    if cleanup_done or not state_manager.is_call_active(call_sid):
                        break
                    
                    # Get current call state
                    current_status = state_manager.get_call_state(call_sid).get("status")
                    
                    # Send silence packets during SPEAKING or PROCESSING to prevent Deepgram timeout
                    if current_status in ["SPEAKING", "PROCESSING"]:
                        if deepgram_ws and hasattr(deepgram_ws, 'send'):
                            try:
                                await deepgram_ws.send(silence_packet)
                                # Uncomment below for debugging
                                # print(f"🔇 [{current_status}] Sent silence packet")
                            except Exception:
                                pass  # Connection closed, ignore
                    
                    # Check if we need to restart silence timer (access state dict directly)
                    if call_sid in state_manager._call_states:
                        needs_timer_restart = state_manager._call_states[call_sid].get('restart_silence_timer', False)
                        
                        if needs_timer_restart:
                            # Clear flag FIRST
                            state_manager._call_states[call_sid]['restart_silence_timer'] = False
                            print("🔕 [KEEPALIVE] Detected restart flag, restarting silence timer now")
                            await start_complete_silence_timer()
                        
                except Exception as e:
                    # Silent failure to avoid log spam
                    pass

        def cleanup():
            nonlocal cleanup_done, input_timer, silence_timer
            if cleanup_done:
                return

            cleanup_done = True
            print("🧹 Cleaning up call resources")
            
            # Cancel timers
            if input_timer and not input_timer.done():
                input_timer.cancel()
            if silence_timer and not silence_timer.done():
                silence_timer.cancel()

            # Close Deepgram connection immediately to prevent timeout loops
            if deepgram_ws:
                asyncio.create_task(close_deepgram())

            # End call in state manager AND update database
            if call_sid:
                state_manager.end_call(call_sid)
                # Update database status to completed
                from database import update_call_status
                update_call_status(call_sid, "completed")
                print("✅ Call cleanup complete - status updated to completed")

        async def close_deepgram():
            if deepgram_ws:
                try:
                    await deepgram_ws.close()
                    print("🔌 Closed Deepgram connection")
                except Exception as e:
                    print(f"⚠️ Error closing Deepgram connection: {e}")

        # Run all tasks concurrently
        await asyncio.gather(
            forward_audio_to_deepgram(),
            process_deepgram_transcripts(),
            keep_deepgram_alive(),
        )

    except Exception as e:
        print(f"❌ Stream handler error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not cleanup_done:
            cleanup()
        if deepgram_ws:
            try:
                await deepgram_ws.close()
                print("🔌 Closed Deepgram connection in finally block")
            except:
                pass





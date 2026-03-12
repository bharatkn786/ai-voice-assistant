
import asyncio
import traceback
from config import twilio_client, state_manager, call_states, conversation_states, active_websockets, BASE_URL
from_number = "+18884990559"  # Must be string with +
to_number = "+919996420826"   # Must be string with +

#for tts
async def speak_async(call_sid: str, text: str, hangup: bool = False, is_followup: bool = False):
    """Non-blocking TTS - returns immediately, webhook handles completion"""
    print(f"🔊 [ASYNC] Speaking to {call_sid}: {text[:50]}...")
    
    if not state_manager.is_call_active(call_sid):
        print(f"⚠️ Call {call_sid} not active")
        return False
    
    state_manager.update_call_state(call_sid, 'SPEAKING')
    
    # Store hangup flag and speech type for webhook to check later
    if hangup:
        state_manager._call_states[call_sid]['should_hangup'] = True
    else:
        state_manager._call_states[call_sid]['should_hangup'] = False
    
    # Track whether this is a follow-up question or main response
    state_manager._call_states[call_sid]['is_followup'] = is_followup
    print(f"📝 [ASYNC] Speech type: {'follow-up' if is_followup else 'main response'}")
    
    # Clean text
    def clean_text_for_twiml(text):
        import re, html
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'#+', '', text)
        text = re.sub(r'`+', '', text)
        text = re.sub(r'_+', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'[<>&"\']', '', text)
        text = html.escape(text, quote=False)
        return text.strip()
    
    cleaned_text = clean_text_for_twiml(text)
    
    # # Detect language
    # has_hindi = any(0x0900 <= ord(c) <= 0x097F for c in text)
    detected_lang = state_manager.get_language(call_sid)
    
    if detected_lang == 'hi':
        language_code = "hi-IN"
        voice = "Polly.Aditi"  # Changed from Google voice to Polly.Aditi
    else:
        language_code = "en-US"
        # voice = "alice"
        voice = "Polly.Aditi"
    
    # Build webhook URL
    from config import BASE_URL
    webhook_url = f"{BASE_URL}/speech-complete/{call_sid}"
    
    # ✅ ALWAYS use <Redirect> to know when speech finishes
    # The webhook will handle state changes properly
    # Using <prosody rate="slow"> for clear but not overly slow speech
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="{voice}" language="{language_code}" >{cleaned_text}</Say>
  <Redirect method="POST">{webhook_url}</Redirect>
</Response>"""
    
    try:
        twilio_client.calls(call_sid).update(twiml=twiml)
        print(f"✅ [ASYNC] TTS initiated with webhook callback")
        print(f"🔗 Webhook URL: {webhook_url}")
        return True
    except Exception as e:
        error_msg = str(e)
        print(f"❌ [ASYNC] TTS failed: {error_msg}")
        
        # Detect specific tunnel-related errors
        if "530" in error_msg or "unregistered" in error_msg.lower():
            print(f"🔴 TUNNEL ERROR DETECTED: Cloudflare tunnel is down!")
            print(f"   Run: python test_tunnel.py to diagnose")
        elif "not in-progress" in error_msg.lower():
            print(f"⚠️ Call already ended (race condition)")
        elif "timeout" in error_msg.lower():
            print(f"⚠️ Network timeout - possible tunnel instability")
        
        state_manager.end_call(call_sid)
        return False

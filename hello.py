#                         it is connected to   https://github.com/bharatkn786/ai-voice-assistant.git (ai-voice assisant)it is just before the checking repo is is working fine
                            # i have just chnaged the gemini to groq ....files cchnged are--- config.py,simple_rag.py
                            #i have changed the simple rag.py with to retrive the top 5 chuks inspite of 3 earlier and reranker return top3 chunks to llm
                                # changes the reset timer from 3 to 3.5 async await(3)
                                #chnaged some points of prompt
import os
import threading
import time
from fastapi import FastAPI, Request, Response, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from stream_handler_simple import twilio_stream_websocket
from twilio.rest import Client
from dotenv import load_dotenv



import asyncio
from twilio.twiml.voice_response import VoiceResponse, Gather
from config import twilio_client, state_manager, BASE_URL, twilio_from_number

# Import security function for Twilio signature verification
from security import verify_twilio_request
from database import update_call_status,save_call_to_db,save_conversation

# Load environment variables
load_dotenv()

# Load Twilio credentials
account_sid = os.getenv("twilio_sid")
auth_token = os.getenv("twilio_token")

# Preload RAG system in a separate thread to avoid blocking server startup
def preload_modules():
    start_time = time.time()
    print("🔥 Preloading RAG system to reduce cold start times...")
    try:
        import simple_rag
        simple_rag.warmup_rag_cache()
        print(f"✅ Simple RAG system preloaded in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        # Do not block app startup if preload fails.
        print(f"⚠️ RAG preload failed: {e}")

# Start preloading in background
threading.Thread(target=preload_modules, daemon=True).start()

app = FastAPI()
templates = Jinja2Templates(directory="templates")



@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    """Serve home page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/start-call")
async def start_call(request: Request):
    """Handle form + trigger Twilio call - SIMPLE VERSION (Frontend validates)"""
    try:
        # Get form data (already validated by frontend)
        form = await request.form()
        name = form.get("name", "").strip()
        
        # Get the full phone number with country code (from hidden field)
        phone = form.get("full_phone", "").strip()
        
        # Fallback: if full_phone is empty, try to construct it
        if not phone:
            country_code = form.get("country_code", "+91")
            phone_number = form.get("phone", "").strip()
            phone = country_code + phone_number
        
        print(f"📞 Calling {name} at {phone}")

        client = Client(account_sid, auth_token)
        try:
            call = client.calls.create(
                to=phone,
                from_=twilio_from_number,
                url=f"{BASE_URL}/twiml",
                status_callback=f"{BASE_URL}/call-status" , # 👈 Add this
                status_callback_event=["queued", "ringing", "answered", "completed", "busy", "failed", "no-answer"]
            )
            call_sid = call.sid
            print("📞 Call initiated. SID:", call.sid)

            # ✅ Save call to database
            save_call_to_db(call_sid, phone, name, "initiated")
            
            # Update call status to 'calling'
            update_call_status(call_sid, "calling")

            return templates.TemplateResponse("index.html", {
                "request": request,
                "called_name": name,
                "called_number": phone,
                "error_message": None
            })

        except Exception as e:
            print(f"❌ Error making call: {e}")
            return templates.TemplateResponse("index.html", {
                "request": request,
                "called_name": None,
                "called_number": None,
                "error_message": "❌ Failed to initiate call. Please check the number and try again."
            })
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "called_name": None,
            "called_number": None,
            "error_message": "⚠️ Internal server error. Please try again later."
        })


@app.post("/twiml", response_class=Response)
async def generate_twiml(request: Request):
    """Generate TwiML for incoming calls - PROTECTED"""
    # ✅ Verify request is from Twilio
    await verify_twilio_request(request)
    
    # Get call_sid from the request
    form = await request.form()
    call_sid = form.get("CallSid")
    
    # Save initial greeting to database
    initial_greeting = "Hi! This is an AI agent from Chitkara University. How may I help you?"
    if call_sid:
        try:
            save_conversation(call_sid, "CALL_INITIATED", initial_greeting)
            print(f"💾 Initial greeting saved to database for call {call_sid}")
        except Exception as e:
            print(f"⚠️ Failed to save initial greeting: {e}")
    
    stream_url = f"wss://{BASE_URL.replace('https://', '')}/twilio-stream"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Aditi">{initial_greeting}</Say>
  <Start>
    <Stream url="{stream_url}" />
  </Start>
  <Pause length="3600"/>
</Response>"""

    return Response(content=twiml, media_type="application/xml")

# @app.get("/debug/states")
# async def debug_states():
#     return {
#         "active_calls": len(state_manager._call_states),
#         "call_sids": list(state_manager._call_states.keys())
#     }



@app.post("/call-status")       #for db to update the status
async def call_status(request: Request):
    """Receive Twilio call status updates"""
    form = await request.form()
    call_sid = form.get("CallSid")
    status = form.get("CallStatus")

    print(f"📡 Received Twilio status update: {call_sid} -> {status}")

    # Update the database
    update_call_status(call_sid, status)

    return "OK"

@app.post("/speech-complete/{call_sid}")
async def speech_complete(call_sid: str, request: Request):
    """Webhook called when Twilio finishes speaking - PROTECTED"""
    # ✅ Verify request is from Twilio
    await verify_twilio_request(request)
    
    print(f"📣 [WEBHOOK] Speech complete for {call_sid}")
    
    # Simple duplicate prevention
    if not state_manager.start_webhook_processing(call_sid):
        print(f"🚫 [WEBHOOK] Duplicate webhook ignored for {call_sid}")
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")
    
    try:
        # Simple check - if call ended, just return
        if not state_manager.is_call_active(call_sid):
            print(f"⚠️ Call {call_sid} already ended")
            return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")
        
        # Check if we should end call
        call_state = state_manager._call_states.get(call_sid, {})
        should_hangup = call_state.get('should_hangup', False)
        
        if should_hangup:
            print(f"👋 [WEBHOOK] Ending call {call_sid}")
            try:
                twilio_client.calls(call_sid).update(status='completed')
            except Exception as e:
                print(f"⚠️ Error ending call: {e}")
            state_manager.end_call(call_sid)
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                media_type="application/xml"
            )
        
        # ✅ LAYER 3: Check current state
        current_state = call_state.get('status')
        
        # Only process if in SPEAKING state
        if current_state != 'SPEAKING':
            print(f"⚠️ [WEBHOOK] Not in SPEAKING state (currently: {current_state}), ignoring")
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Pause length="3600"/></Response>', 
                media_type="application/xml"
            )
        
        # ✅ Safe to transition to WAITING_INPUT
        print(f"✅ [WEBHOOK] Speech finished, transitioning to WAITING_INPUT")
        state_manager.update_call_state(
            call_sid, 
            'WAITING_INPUT',
            input_start_time=asyncio.get_event_loop().time(),
            restart_silence_timer=True
        )
        
        print(f"🎤 [WEBHOOK] Now WAITING_INPUT for {call_sid}")
         
        # Return TwiML to keep call alive
        twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Pause length="3600"/>
</Response>"""
        
        return Response(content=twiml_response, media_type="application/xml")
    
    finally:
        # ✅ CRITICAL: Always clear the processing flag, even if error occurs
        state_manager.end_webhook_processing(call_sid)


def twilio_response(gather=False):
    """Generate a TwiML response for Twilio callbacks"""
    response = VoiceResponse()
    if gather:
        gather_instance = Gather(input='speech', action='/transcribe', method='POST',
                                 speechTimeout='auto', language='en-US', enhanced=True)
        gather_instance.say("", voice="Polly.Aditi")
        response.append(gather_instance)
        # Fallback pause to keep call alive in case of timeout
        response.pause(length=3600)
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/twilio-stream")
async def twilio_websocket(websocket: WebSocket):
    # Ensure FastAPI provides a WebSocket instance by annotating the param.
    return await twilio_stream_websocket(websocket)


# Document processing functionality
import subprocess
from database import mongo_db

UPLOAD_FOLDER = './pdf'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MongoDB collection for uploaded documents
documents_collection = mongo_db["uploaded_documents"]

def process_uploaded_documents():
    """Check MongoDB for unprocessed files and process them"""
    try:
        # Get unprocessed documents from MongoDB
        documents = list(documents_collection.find({"processed": False}))
        
        if not documents:
            print("✅ No pending documents")
            return
        
        print(f"📥 Processing {len(documents)} documents...")
        
        # Delete all existing files in pdf folder before saving new ones
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        print(f"🗑️ Deleted old file: {filename}")
                except Exception as e:
                    print(f"⚠️ Error deleting {filename}: {e}")
        
        for doc in documents:
            try:
                # Save to ./pdf/ folder
                filepath = os.path.join(UPLOAD_FOLDER, doc['filename'])
                with open(filepath, 'wb') as f:
                    f.write(doc['file_data'])
                
                print(f"✅ Saved: {filepath}")
                
                # Mark as processed in MongoDB
                documents_collection.update_one(
                    {"_id": doc['_id']},
                    {"$set": {"processed": True}}
                )
                
            except Exception as e:
                print(f"❌ Error processing {doc['filename']}: {e}")
        
        # Run update script
        if documents:
            print("🔄 Running update_llamaindex.py...")
            subprocess.run(['python', 'update_llamaindex.py'])
            print("✅ Index updated!")
            
            # Clear RAG cache to force reload on next query
            try:
                import simple_rag
                simple_rag._RAG_COMPONENTS = None
                simple_rag.warmup_rag_cache()
                print("✅ RAG cache refreshed with updated index")
            except Exception as e:
                print(f"⚠️ Could not clear cache: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

@app.post("/api/process-documents")
async def trigger_process():
    """Endpoint triggered by Dashboard after file upload"""
    def run():
        process_uploaded_documents()
    
    threading.Thread(target=run, daemon=True).start()
    
    return {"message": "Processing started"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Chitkara University AI Voice Assistant Server")
    print("📞 Server ready to handle new calls!")
    print("⚡ RAG system will preload in the background")
    uvicorn.run(app, host="0.0.0.0", port=8000)

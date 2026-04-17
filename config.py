


# //according to new state managemnet
import os
from dotenv import load_dotenv
from twilio.rest import Client
from langchain_google_genai import ChatGoogleGenerativeAI
from state_manager import StateManager

load_dotenv(override=True)

# Base URL for Twilio webhooks — set this in your .env file.
# Local dev  → your Cloudflare/ngrok tunnel URL
# Docker/AWS → your EC2 public IP or domain, e.g. https://yourdomain.com
BASE_URL = os.getenv("BASE_URL")

# Environment Variables
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("twilio_sid")
TWILIO_AUTH_TOKEN = os.getenv("twilio_token")
twilio_from_number=os.getenv("YOUR_TWILIO_PHONE_NUMBER")
# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # or "mixtral-8x7b-32768"
    api_key=GROQ_API_KEY,
    temperature=0.0
)
# Use a model with higher quota limits or fall back to another model
# Options: gemini-1.0-pro has higher quota limits than gemini-2.5-flash
# try:
#     llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)
#     print("🔄 Using gemini-2.5-flash model")
# except Exception as e:
#     # Fall back to gemini-1.0-pro if flash is rate-limited
#     print(f"⚠️ Error initializing gemini-2.5-flash: {e}")

    # print("🔄 Falling back to gemini-1.0-pro model")
    # llm = ChatGoogleGenerativeAI(model="gemini-1.0-pro", google_api_key=GOOGLE_API_KEY)


DEEPGRAM_URL = (
    "wss://api.deepgram.com/v1/listen?encoding=mulaw&sample_rate=8000&channels=1"
    "&model=nova-2&punctuate=true&interim_results=false&language=hi"
)
# DEEPGRAM_URL = (
#     "wss://api.deepgram.com/v1/listen?encoding=mulaw&sample_rate=8000&channels=1"
#     "&model=nova-2&punctuate=true&interim_results=false&keepalive=true&detect_language=true"
# )

# Initialize the new state manager
state_manager = StateManager(twilio_client)
print("🔄 State manager initialized")

# For backward compatibility with old code that directly imports these variables
# These are now just references to the state manager's protected dictionaries
call_states = state_manager._call_states
conversation_states = state_manager._conversation_states  
active_websockets = state_manager._active_websockets

# IMPORTANT: For new code, use the state_manager's methods instead of these variables
# These are only kept for compatibility and will be removed in the future

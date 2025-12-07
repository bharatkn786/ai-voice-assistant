# ------------------------- 🧠 DEBUG ROUTES -------------------------


# for testing usse this:  http://localhost:8000/debug/conversations/CAd38f209aeb913e537e5f18dce6f30f4f



from fastapi.responses import JSONResponse

# Add these imports at the top
from pymongo import MongoClient


from fastapi import FastAPI, Request, Response, WebSocket, HTTPException
app = FastAPI()

import os
from dotenv import load_dotenv
load_dotenv()
# MongoDB Atlas connection (same as dashboard)
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME =os.getenv("DATABASE_NAME")

try:
    mongo_client = MongoClient(MONGODB_URL)
    mongo_db = mongo_client[DATABASE_NAME]
    calls_collection = mongo_db["calls"]
    
    # Test connection
    mongo_client.admin.command('ping')
    print("✅ Main app connected to MongoDB Atlas!")
    
except Exception as e:
    print(f"❌ Main app MongoDB connection failed: {e}")
    calls_collection = None


@app.get("/debug/calls")
async def get_all_calls():
    """Return all call records from MongoDB (for debugging)"""
    try:
        data = list(calls_collection.find({}, {"_id": 0}))
        return JSONResponse(content={"count": len(data), "calls": data})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/debug/call/{call_sid}")
async def get_call_by_sid(call_sid: str):
    """Return a specific call record by CallSid"""
    try:
        call = calls_collection.find_one({"call_sid": call_sid}, {"_id": 0})
        if not call:
            return JSONResponse(content={"error": "Call not found"}, status_code=404)
        return JSONResponse(content=call)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/debug/status/{call_sid}")
async def get_call_status(call_sid: str):
    """Return only the current status of a specific call"""
    try:
        call = calls_collection.find_one({"call_sid": call_sid}, {"_id": 0, "status": 1})
        if not call:
            return JSONResponse(content={"error": "Call not found"}, status_code=404)
        return JSONResponse(content=call)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/debug/conversations/{call_sid}")
async def get_conversation(call_sid: str):
    """Return the full conversation log for a specific call"""
    try:
        call = calls_collection.find_one({"call_sid": call_sid}, {"_id": 0, "conversation": 1})
        if not call:
            return JSONResponse(content={"error": "Call not found"}, status_code=404)
        return JSONResponse(content=call)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

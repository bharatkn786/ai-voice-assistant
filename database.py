# Add these imports at the top
from pymongo import MongoClient
from datetime import datetime
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


def save_call_to_db(call_sid, phone, name, status="initiated"):
    """Save call data to MongoDB Atlas"""
    if calls_collection is None:
        print("⚠️ Database not connected")
        return
    
    try:
        call_data = {
            "call_sid": call_sid,
            "phone_number": phone,
            "caller_name": name,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "conversation": []
        }
        
        calls_collection.update_one(
            {"call_sid": call_sid},
            {"$set": call_data},
            upsert=True
        )
        print(f"✅ Saved call {call_sid} to MongoDB Atlas")
        
    except Exception as e:
        print(f"❌ Failed to save call to database: {e}")

def update_call_status(call_sid, status):
    """Update call status in database"""
    if calls_collection is None:
        return
        
    try:
        calls_collection.update_one(
            {"call_sid": call_sid},
            {"$set": {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }}
        )
        print(f"✅ Updated call {call_sid} status to {status}")
        
    except Exception as e:
        print(f"❌ Failed to update call status: {e}")

def save_conversation(call_sid, question, answer):
    """Save Q&A to database"""
    if calls_collection is None:
        return
        
    try:
        calls_collection.update_one(
            {"call_sid": call_sid},
            {
                "$push": {
                    "conversation": {
                        "question": question,
                        "answer": answer,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                "$set": {
                    "updated_at": datetime.now().isoformat()
                }
            }
        )
        print(f"✅ Saved conversation for {call_sid}")
        
    except Exception as e:
        print(f"❌ Failed to save conversation: {e}")
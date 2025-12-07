from fastapi import APIRouter, File, UploadFile, HTTPException
import httpx
import os
from datetime import datetime
from db import db

router = APIRouter(prefix="/api/upload", tags=["upload"])

# MongoDB collection for uploaded documents
documents_collection = db["uploaded_documents"]

@router.post("/document")
async def upload_document(file: UploadFile = File(...)):
    """Upload file to MongoDB and trigger Main App processing"""
    
    # Validate file type
    if not file.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files allowed")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Save to MongoDB
        document = {
            "filename": file.filename,
            "file_data": file_content,  # Binary data
            "file_size": len(file_content),
            "uploaded_at": datetime.utcnow(),
            "processed": False
        }
        
        result = documents_collection.insert_one(document)
        
        print(f"✅ File saved to MongoDB: {file.filename} (ID: {result.inserted_id})")
        
        # Trigger Main App to process (adjust URL for production)
        try:
            MAIN_APP_URL = os.getenv("MAIN_APP_URL", "http://localhost:8000")
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(f"{MAIN_APP_URL}/api/process-documents")
            print("✅ Main App notified")
        except Exception as e:
            print(f"⚠️ Could not notify Main App: {e}")
        
        return {
            "success": True,
            "message": f"File '{file.filename}' uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def upload_status():
    """Get upload statistics"""
    try:
        pending = documents_collection.count_documents({"processed": False})
        processed = documents_collection.count_documents({"processed": True})
        
        return {
            "pending": pending,
            "processed": processed,
            "total": pending + processed
        }
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return {"pending": 0, "processed": 0, "total": 0}

from fastapi import APIRouter, HTTPException
from db import calls_collection  # adjust path if required

router = APIRouter(prefix="/api/calls", tags=["Calls"])

# ---------------------------------------------
# 1. GET ALL CALLS
# ---------------------------------------------
@router.get("/")
def get_all_calls():
    try:
        calls = list(calls_collection.find({}, {"_id": 0}))
        return {"success": True, "data": calls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------
# 2. STATUS SUMMARY (for dashboard chart)
# ---------------------------------------------
@router.get("/status-summary")
def get_call_status_summary():
    try:
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        summary = list(calls_collection.aggregate(pipeline))
        return {"success": True, "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------
# 3. ACTIVE CALLS
# ---------------------------------------------
@router.get("/active")
def get_active_calls():
    try:
        # Active = calls that are ongoing (not completed/failed/no-answer/busy)
        active_statuses = ["initiated", "calling", "queued", "ringing", "in-progress"]
        calls = list(
            calls_collection.find(
                {"status": {"$in": active_statuses}}, 
                {"_id": 0}
            ).sort("created_at", -1)
        )
        return {"success": True, "data": calls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------
# 4. GET CALL BY SID
# ---------------------------------------------
@router.get("/{call_sid}")
def get_call_by_sid(call_sid: str):
    try:
        call = calls_collection.find_one({"call_sid": call_sid}, {"_id": 0})
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        return {"success": True, "data": call}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


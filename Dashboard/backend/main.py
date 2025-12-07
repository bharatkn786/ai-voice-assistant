from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import calls, upload

app = FastAPI(title="Twilio Dashboard API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(calls.router)
app.include_router(upload.router)

# Root route
@app.get("/")
def home():
    return {"message": "Backend running successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

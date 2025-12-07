"""
Security Module - Twilio Request Verification and Rate Limiting
Handles all security-related functionality for the application
"""

import os
from collections import defaultdict
import time
from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Twilio signature validator
TWILIO_AUTH_TOKEN = os.getenv("twilio_token")
validator = RequestValidator(TWILIO_AUTH_TOKEN)

# Rate limiting storage (in-memory)
call_attempts = defaultdict(list)



async def verify_twilio_request(request: Request) -> bool:
    """
    Verify that request is actually from Twilio using cryptographic signature validation.
    
    This function:
    1. Extracts the X-Twilio-Signature header
    2. Recreates the signature using HMAC-SHA1 with your auth token
    3. Compares the signatures to verify authenticity
    
    Security: Without your TWILIO_AUTH_TOKEN, it's mathematically impossible 
    for an attacker to generate a valid signature.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        bool: True if signature is valid
        
    Raises:
        HTTPException: 403 if signature is missing or invalid
    """
    
    # Step 1: Get signature from Twilio's HTTP header
    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        print("⚠️ Missing Twilio signature!")
        raise HTTPException(status_code=403, detail="Forbidden - Missing signature")
    
    # Step 2: Get full URL (Twilio signs the complete URL)
    url = str(request.url)
    
    # Step 3: Get all form data that Twilio sent
    form_data = await request.form()
    params = dict(form_data)
    
    # Step 4: Validate signature using Twilio's official validator
    # This recreates the signature using YOUR secret auth token and compares
    is_valid = validator.validate(url, params, signature)
    
    if not is_valid:
        print(f"⚠️ Invalid Twilio signature! URL: {url}")
        raise HTTPException(status_code=403, detail="Forbidden - Invalid signature")
    
    print(f"✅ Twilio signature verified for {url}")
    return True


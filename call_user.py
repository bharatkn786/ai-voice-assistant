# from twilio.rest import Client
# import os
# from dotenv import load_dotenv

# load_dotenv()

# account_sid = os.getenv("twilio_sid")
# auth_token = os.getenv("twilio_token")
# from_number = "+19804487778"  # Must be string with +
# to_number = "+919996420826"   # Must be string with +

# client = Client(account_sid, auth_token)

# try:
#     call = client.calls.create(
#         to=to_number,
#         from_=from_number,
#         url="https://collections-shopzilla-induction-therapeutic.trycloudflare.com/twiml"  # Updated to use webhook
#     )
#     print("📞 Call initiated. SID:", call.sid)
#     print(f"📞 Calling {to_number} from {from_number}")
    
# except Exception as e:
#     print(f"❌ Error making call: {e}")
#     print("🔍 Possible solutions:")
#     print("1. Check your internet connection")
#     print("2. Verify Twilio credentials in .env file")
#     print("3. Ensure your Twilio account has sufficient balance")
#     print("4. Try again in a few minutes (might be temporary network issue)")

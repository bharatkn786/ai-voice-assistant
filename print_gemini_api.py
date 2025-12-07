# import os
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI

# # Load .env file
# load_dotenv()

# print("Env key:", os.getenv("GOOGLE_API_KEY"))

# def test_gemini_api():
#     try:
#         llm = ChatGoogleGenerativeAI(
#             model="gemini-2.5-flash",
#             google_api_key=os.getenv("GOOGLE_API_KEY")  # explicitly pass key
#         )
       
#         query = "give me a pragrpah on frinedship"
#         response = llm.invoke(query)
#         print("✅ API Key is working!")
#         print("Response:", response.content)
#     except Exception as e:
#         print("❌ API Key test failed:", e)

# if __name__ == "__main__":
#     test_gemini_api()

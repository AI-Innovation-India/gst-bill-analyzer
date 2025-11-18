"""
Check available Gemini models for your API key
"""
import os
import google.generativeai as genai

api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyBK43ALMA_VriahnZ0hJdnl2-J6zXxBqhE')

print("Testing Gemini API with key:", api_key[:20] + "...")
print()

try:
    genai.configure(api_key=api_key)
    print("Available Gemini models:")
    print("="*60)

    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")

    print("="*60)
    print("\nAPI key is valid!")

except Exception as e:
    print(f"Error: {e}")
    print("\nPossible issues:")
    print("1. API key is invalid")
    print("2. Gemini API is not enabled for this key")
    print("3. Check https://aistudio.google.com to verify your API key")

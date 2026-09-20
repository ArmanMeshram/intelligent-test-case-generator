"""Quick script to check which Gemini models are available with your API key."""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found. Add it to your .env file.")
client = genai.Client(api_key=GEMINI_API_KEY)

print("=" * 60)
print("Checking available Gemini models...")
print("=" * 60)

try:
    for model in client.models.list():
        name = model.name
        if "gemini" in name.lower():
            print(f"  OK: {name}")
except Exception as e:
    print(f"  ERROR listing models: {e}")

print("\n" + "=" * 60)
print("Testing generation with each candidate model...")
print("=" * 60)

test_models = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
]

for model in test_models:
    try:
        response = client.models.generate_content(
            model=model,
            contents="Say hello in one word.",
            config=genai.types.GenerateContentConfig(max_output_tokens=10),
        )
        print(f"  OK     {model}: {response.text.strip()}")
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            print(f"  QUOTA  {model}: Free tier limit exhausted")
        elif "404" in err or "NOT_FOUND" in err:
            print(f"  GONE   {model}: Model not found / unavailable")
        else:
            print(f"  FAIL   {model}: {err[:150]}")

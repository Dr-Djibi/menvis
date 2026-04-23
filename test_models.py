import json, os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("/home/menma/menvis/.env")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "NO_KEY"),
)

models_to_test = [
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-3-12b-it:free",
    "qwen/qwen3-coder:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
]

for model in models_to_test:
    try:
        print(f"Testing {model}...")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Quelle heure est-il ?"}],
            tools=[{"type": "function", "function": {"name": "get_current_time", "description": "Donne l'heure", "parameters": {"type": "object", "properties": {}}}}]
        )
        if response.choices[0].message.tool_calls:
            print(f"✅ {model} supports tools!")
        else:
            print(f"❌ {model} responded without tools.")
    except Exception as e:
        print(f"❌ {model} failed: {e}")

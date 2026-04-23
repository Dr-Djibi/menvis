import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ASSISTANT_NAME = "Menvis"
    DEBUG = False

    # ── 1. Groq ───────────────────────────────────────────────
    GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL  = "https://api.groq.com/openai/v1"
    GROQ_MODEL     = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # ── 2. Gemini (endpoint compatible OpenAI) ────────────────
    GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # ── 3. OpenRouter ─────────────────────────────────────────
    OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL    = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

    # ── 4. Ollama (local / fallback final) ────────────────────
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

    # Ordre de la cascade (modifiable ici)
    PROVIDER_CASCADE = ["groq", "gemini", "openrouter", "ollama"]

import os
import sys
from google import genai
from dotenv import load_dotenv

# Charge la clé API
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("[!] Erreur : GEMINI_API_KEY non trouvée dans le .env")
    sys.exit(1)

print(f"[*] Test du Nexus avec la clé : {api_key[:5]}...{api_key[-5:]}")

try:
    client = genai.Client(api_key=api_key)
    # On teste le modèle le plus léger
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Réponds juste 'Nexus Opérationnel' si tu m'entends."
    )
    print(f"[✅] RÉPONSE : {response.text}")
except Exception as e:
    print(f"[❌] ERREUR QUOTA/API : {e}")

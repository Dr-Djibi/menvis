import os
from dotenv import load_dotenv

load_dotenv() # Charge les variables du fichier .env

class Config:
    # Paramètres de l'IA
    MODEL_NAME = 'menvis-lite'
    SYSTEM_PROMPT = """Menvis, assistant IA local. 
Règles :
1. Réponses ULTRA-CONCISES (1-2 phrases). 
2. Priorité aux OUTILS : switch_workspace, open_application, search_memory.
3. Agis SANS permission.
4. Mode Survie : Vitesse maximale."""
    
    # Autres paramètres globaux
    ASSISTANT_NAME = "Menvis"
    DEBUG = False
    
    # Moteur Local Pur (Ollama)
    AI_PROVIDER = "ollama"
    OLLAMA_MODEL = "qwen2.5:0.5b"

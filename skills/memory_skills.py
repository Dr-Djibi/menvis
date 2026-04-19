import json
import os

MEMORY_FILE = "/home/menma/menvis/brain/memory.json"

def _load_memory() -> list:
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def _save_memory(data: list):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def remember_fact(fact: str) -> str:
    """Enregistre une information (préférence de l'utilisateur, prénom, etc.) de manière permanente."""
    mem = _load_memory()
    if fact not in mem:
        mem.append(fact)
        _save_memory(mem)
        return f"J'ai mémorisé le fait suivant de manière persistante : '{fact}'"
    return f"Je savais déjà cela : '{fact}'"

def search_memory(query: str) -> str:
    """Recherche un souvenir dans la mémoire permanente de Menvis."""
    mem = _load_memory()
    results = [m for m in mem if query.lower() in m.lower()]
    if results:
        return "J'ai retrouvé ces souvenirs : " + " | ".join(results)
    return "Je n'ai aucun souvenir à ce sujet dans ma base de données."

def get_all_memory_context() -> str:
    """Fonction interne pour injecter la mémoire au démarrage de Menvis."""
    mem = _load_memory()
    if mem:
        return "\n--- NOTES PERSISTANTES SUR L'UTILISATEUR ---\n" + "\n".join(mem)
    return ""

MEMORY_TOOLS = {
    'remember_fact': remember_fact,
    'search_memory': search_memory
}

MEMORY_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'remember_fact',
            'description': 'Stocke une information importante envoyée par l\'utilisateur pour t\'en souvenir indéfiniment même après un redémarrage (ex: son nom, ce qu\'il aime).',
            'parameters': {
                'type': 'object',
                'properties': {
                    'fact': {'type': 'string', 'description': 'L\'information précise à mémoriser (ex: "L\'utilisateur s\'appelle Menma")'}
                },
                'required': ['fact']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'search_memory',
            'description': 'Cherche dans ta base de données persistante pour voir si tu as déjà noté une information sur l\'utilisateur ou ses préférences.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'Un ou plusieurs mots clés (ex: "nom", "aime")'}
                },
                'required': ['query']
            }
        }
    }
]

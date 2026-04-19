import subprocess

def search_web(query: str) -> str:
    """Effectue une recherche rapide sur le Web à l'aide de DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
            if not results:
                return f"Aucun résultat trouvé sur le web pour '{query}'"
                
            formatted_results = ""
            for i, res in enumerate(results):
                formatted_results += f"[{i+1}] {res['title']} : {res['body']}\n"
                
            return f"Résultats de recherche pour '{query}' :\n{formatted_results}"
    except ImportError:
        return "L'outil de recherche Web n'est pas complètement installé (pip install duckduckgo-search)."
    except Exception as e:
        return f"Erreur lors de la recherche internet : {e}"

def open_in_firefox(url_or_search: str) -> str:
    """Ouvre spécifiquement le navigateur Firefox vers une URL ou lance une recherche."""
    try:
        # Si ça ne ressemble pas à une URL, c'est une recherche
        if not url_or_search.startswith("http"):
             url_or_search = f"https://duckduckgo.com/?q={url_or_search}"
             
        # Lancement de Firefox détaché
        subprocess.Popen(["firefox", url_or_search], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "J'ai affiché cela devant vous dans le navigateur Firefox."
    except Exception as e:
        return f"Firefox semble introuvable : {e}"

WEB_TOOLS = {
    'search_web': search_web,
    'open_in_firefox': open_in_firefox
}

WEB_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'search_web',
            'description': 'Effectue une recherche sur internet pour trouver des informations récentes ou générales',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'Les mots clés de recherche'}
                },
                'required': ['query']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'open_in_firefox',
            'description': 'Ouvre directement Firefox (navigateur par défaut de l\'utilisateur) pour afficher un site précis ou lancer une recherche visuelle sur l\'écran de l\'utilisateur.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'url_or_search': {'type': 'string', 'description': 'L\'URL du site ou les mots à rechercher (ex: "youtube.com" ou "vidéos de chats")'}
                },
                'required': ['url_or_search']
            }
        }
    }
]

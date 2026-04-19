from .system_skills import get_current_time, get_system_status, get_weather

def daily_briefing(city: str = "Paris") -> str:
    """Agrége les informations pour un récapitulatif global matinal."""
    date = get_current_time()
    sys = get_system_status()
    meteo = get_weather(city)
    
    briefing = (
        f"Voici le statut complet, Chef.\n"
        f"- TEMPS: {date}\n"
        f"- SYSTÈME: {sys}\n"
        f"- EXTÉRIEUR: {meteo}"
    )
    return briefing

ROUTINE_TOOLS = {
    'daily_briefing': daily_briefing
}

ROUTINE_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'daily_briefing',
            'description': 'Exécute une routine de diagnostic globale qui rassemble date, heure, météo et état CPU/RAM en un seul appel.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'city': {'type': 'string', 'description': 'Ville pour la météo (ex: Paris)'}
                },
                'required': ['city']
            }
        }
    }
]

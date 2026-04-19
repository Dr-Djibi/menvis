import ollama
import sys
import datetime
import subprocess

# --- Définition de nos Outils (Fonctions Système) ---

def get_current_time():
    """Récupère l'heure et la date actuelle."""
    now = datetime.datetime.now()
    return now.strftime("Il est %H:%M et nous sommes le %d/%m/%Y.")

def open_application(app_name):
    """Ouvre une application en utilisant hyprctl."""
    # Nettoie le nom de l'app si besoin
    app_name = app_name.lower().strip()
    print(f"[Menvis] Lancement de l'application : {app_name}...")
    try:
        # Envoie la commande à Hyprland pour l'ouvrir
        subprocess.run(["hyprctl", "dispatch", "exec", app_name], check=True, capture_output=True)
        return f"J'ai bien ouvert l'application {app_name}."
    except Exception as e:
        return f"Je n'ai pas pu ouvrir {app_name}. Erreur: {str(e)}"

# Dictionnaire pour lier le nom de l'outil à la fonction
available_tools = {
    'get_current_time': get_current_time,
    'open_application': open_application
}

# --- Cerveau Principal ---

def chat_with_menvis(prompt):
    model_name = 'qwen2.5:1.5b' 

    print(f"[*] Analyse de la requête par {model_name}...")
    
    # 1. On donne les définitions des outils à l'IA
    messages = [
        {
            'role': 'system',
            'content': 'Tu es Menvis, un assistant IA personnel sur EndeavourOS (Hyprland). Tu parles français. Tu peux ouvrir des applications (navigateur, terminal, etc) et donner l\'heure de manière concise.'
        },
        {'role': 'user', 'content': prompt}
    ]

    try:
        response = ollama.chat(
            model=model_name,
            messages=messages,
            tools=[
                {
                    'type': 'function',
                    'function': {
                        'name': 'get_current_time',
                        'description': 'Donne la date et l\'heure actuelle',
                        'parameters': {'type': 'object', 'properties': {}}
                    }
                },
                {
                    'type': 'function',
                    'function': {
                        'name': 'open_application',
                        'description': 'Ouvre une application sur l\'ordinateur de l\'utilisateur (ex: firefox, kitty, alacritty)',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'app_name': {
                                    'type': 'string',
                                    'description': 'Le nom de l\'application à ouvrir en un seul mot, par exemple "firefox", "kitty", "thunar", "discord"'
                                }
                            },
                            'required': ['app_name']
                        }
                    }
                }
            ]
        )

        message = response['message']

        # 2. Vérifier si l'IA a décidé d'utiliser un outil
        if message.get('tool_calls'):
            for tool_call in message['tool_calls']:
                function_name = tool_call['function']['name']
                arguments = tool_call['function']['arguments']
                
                # Exécuter l'outil !
                print(f"[!] Menvis actionne l'outil : {function_name} ({arguments})")
                func_to_run = available_tools.get(function_name)
                
                if func_to_run:
                    if arguments and 'app_name' in arguments:
                        tool_result = func_to_run(arguments['app_name'])
                    else:
                        tool_result = func_to_run()
                    
                    # 3. On renvoie le résultat de l'outil à l'IA pour qu'elle formule sa réponse
                    messages.append(message)
                    messages.append({'role': 'tool', 'name': function_name, 'content': tool_result})
                    
                    final_response = ollama.chat(model=model_name, messages=messages)
                    print('\nMenvis: ' + final_response['message']['content'])
        else:
            # Pas d'outil, juste du texte
            print('\nMenvis: ' + message['content'])

    except Exception as e:
        print(f"[!] Erreur: {e}")
        print("[!] Assurez-vous que le serveur Ollama est démarré et que le modèle gère bien le json.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        user_input = input("Vous: ")
    
    chat_with_menvis(user_input)

import subprocess
import json
import os
import threading
import time

CACHE_FILE = "/home/menma/menvis/brain/notifications_cache.json"

def save_notification(app_name, title, body):
    """Enregistre la notification dans le cache JSON (limité aux 15 dernières)."""
    # Exclure les notifications envoyées par Menvis lui-même !
    if "Menvis" in app_name or "mako" in app_name or "notify-send" in app_name:
        return
        
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            notifs = json.load(f)
    except Exception:
        notifs = []
        
    # Formatage de l'entrée
    entry = {
        'time': time.strftime("%H:%M"),
        'source': "Téléphone (KDE Connect)" if "kdeconnect" in app_name.lower() else f"PC ({app_name})",
        'title': title,
        'message': body
    }
    
    notifs.append(entry)
    notifs = notifs[-15:] # Garde uniquement les 15 plus récentes
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(notifs, f, indent=4, ensure_ascii=False)

def start_listening():
    """Démarre le moniteur D-Bus silencieux."""
    print("[Menvis] Le sixième sens (Écoute des Notifications) est activé en arrière-plan.")
    
    process = subprocess.Popen(
        ["dbus-monitor", "interface='org.freedesktop.Notifications',member='Notify'"],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    
    app_name, title, body = "", "", ""
    strings_found = 0
    
    # Parseur astucieux pour extraire les strings du log brut de dbus-monitor sans bibliothèques lourdes !
    for line in iter(process.stdout.readline, ""):
        line = line.strip()
        
        if line.startswith("method call"): 
            app_name, title, body = "", "", ""
            strings_found = 0
            
        elif line.startswith("string"):
            try:
                # Extraire le texte entre guillemets
                val = line.split("\"", 1)[1].rsplit("\"", 1)[0]
                strings_found += 1
                
                # Selon l'interface D-Bus de FreeDesktop: str1=app_name, str2=replaces_id, str3=icon, str4=summary, str5=body
                if strings_found == 1:
                    app_name = val
                elif strings_found == 3: # Titre / Summary
                    title = val
                elif strings_found == 4: # Corps
                    body = val
                    if title or body:
                        save_notification(app_name, title, body)
            except Exception:
                pass

if __name__ == "__main__":
    start_listening()

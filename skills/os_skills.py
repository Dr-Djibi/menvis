import os
import shutil

def list_directory(path: str) -> str:
    """Liste les fichiers et dossiers."""
    try:
        real_path = os.path.expanduser(path)
        items = os.listdir(real_path)
        if not items:
            return f"Le dossier {path} est vide."
        files = [i for i in items if os.path.isfile(os.path.join(real_path, i))]
        dirs = [i for i in items if os.path.isdir(os.path.join(real_path, i))]
        return f"Dossiers : {len(dirs)} ({', '.join(dirs[:5])}...) | Fichiers : {len(files)} ({', '.join(files[:5])}...)"
    except Exception as e:
        return f"Erreur de lecture du dossier : {e}"

def move_file(source: str, destination: str) -> str:
    """Déplace ou renomme un fichier/dossier."""
    try:
        src = os.path.expanduser(source)
        dst = os.path.expanduser(destination)
        shutil.move(src, dst)
        return f"Item déplacé avec succès de {source} vers {destination}."
    except Exception as e:
        return f"Impossible de déplacer le fichier : {e}"

def organize_directory(path: str) -> str:
    """Organise automatiquement un dossier en triant les fichiers par extension."""
    try:
        real_path = os.path.expanduser(path)
        if not os.path.exists(real_path):
            return f"Le dossier {path} n'existe pas."

        mappings = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
            'Vidéos': ['.mp4', '.mkv', '.avi', '.mov', '.webm'],
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.md', '.xls', '.csv'],
            'Archives': ['.zip', '.tar', '.gz', '.rar', '.7z'],
            'Musiques': ['.mp3', '.wav', '.flac', '.ogg'],
            'Exécutables': ['.AppImage', '.deb', '.exe', '.sh']
        }

        moved_count = 0
        for item in os.listdir(real_path):
            item_path = os.path.join(real_path, item)
            
            # Ne trier que les fichiers, pas les dossiers
            if os.path.isfile(item_path):
                _, ext = os.path.splitext(item)
                ext = ext.lower()
                
                # Trouver la catégorie
                assigned_category = 'Divers'
                for cat, extensions in mappings.items():
                    if ext in extensions:
                        assigned_category = cat
                        break
                
                # Créer le sous-dossier si besoin
                cat_path = os.path.join(real_path, assigned_category)
                os.makedirs(cat_path, exist_ok=True)
                
                # Déplacer le fichier
                shutil.move(item_path, os.path.join(cat_path, item))
                moved_count += 1

        return f"J'ai terminé le grand nettoyage de '{path}' ! J'ai trié et rangé {moved_count} fichiers dans leurs dossiers respectifs."
    except Exception as e:
        return f"J'ai rencontré un problème en voulant organiser ce dossier : {e}"


OS_TOOLS = {
    'list_directory': list_directory,
    'move_file': move_file,
    'organize_directory': organize_directory
}

OS_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'list_directory',
            'description': 'Liste le contenu d\'un dossier (ex: ~/Téléchargements ou /home/menma).',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Le chemin du dossier'}
                },
                'required': ['path']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'move_file',
            'description': 'Déplace ou renomme un fichier d\'un emplacement à un autre.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'source': {'type': 'string', 'description': 'Chemin d\'origine'},
                    'destination': {'type': 'string', 'description': 'Chemin de destination'}
                },
                'required': ['source', 'destination']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'organize_directory',
            'description': 'Trie intelligemment tous les fichiers d\'un dossier en créant des sous-dossiers automatisés (Documents, Images, Vidéos, Archives...). Parfait pour ranger un dossier Téléchargements en vrac.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Le chemin du dossier à organiser proprement'}
                },
                'required': ['path']
            }
        }
    }
]

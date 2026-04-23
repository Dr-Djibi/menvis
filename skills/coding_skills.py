import os
import re
import subprocess
from pathlib import Path

# ════════════════════════════════════════════════
#  🔍  RECHERCHE GLOBALE (GREP)
# ════════════════════════════════════════════════

def grep_code(pattern: str, search_path: str = ".", case_insensitive: bool = True) -> str:
    """Recherche un motif (regex) dans le contenu des fichiers du projet."""
    path = os.path.expanduser(search_path)
    if not os.path.exists(path):
        return f"Erreur : Le chemin {path} n'existe pas."

    flags = re.IGNORECASE if case_insensitive else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Erreur : Pattern regex invalide : {e}"

    results = []
    files_searched = 0
    matches_found = 0

    for root, dirs, files in os.walk(path):
        # Exclure les dossiers inutiles
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".venv", "venv"}]
        
        for file in files:
            file_path = Path(root) / file
            if file.startswith(".") or file_path.suffix in {'.pyc', '.exe', '.bin', '.png', '.jpg', '.pdf'}:
                continue
            
            files_searched += 1
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    file_matches = []
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            file_matches.append(f"{i}: {line.strip()}")
                            matches_found += 1
                    
                    if file_matches:
                        rel_path = os.path.relpath(file_path, path)
                        results.append(f"--- {rel_path} ---")
                        results.extend(file_matches[:10]) # Limite à 10 par fichier
                        if len(file_matches) > 10:
                            results.append("... (plus de résultats dans ce fichier)")
                        results.append("")
            except Exception:
                continue
            
            if len(results) > 100: # Limite globale
                results.append("⚠️ Trop de résultats, recherche tronquée.")
                break
        if len(results) > 100: break

    if not results:
        return f"Aucun résultat trouvé pour '{pattern}'."
    
    header = f"🔍 Grep : {matches_found} occurrences dans {files_searched} fichiers.\n\n"
    return header + "\n".join(results)


# ════════════════════════════════════════════════
#  📝  ÉDITION CHIRURGICALE (PATCH)
# ════════════════════════════════════════════════

def edit_file_patch(file_path: str, old_string: str, new_string: str) -> str:
    """Remplace précisément un bloc de texte par un autre dans un fichier."""
    path = os.path.expanduser(file_path)
    if not os.path.exists(path):
        return f"Erreur : Le fichier {path} n'existe pas."

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if old_string not in content:
            # Tentative de matching sans espaces si exact échoue ? (Optionnel)
            return f"Erreur : Le texte à remplacer n'a pas été trouvé exactement dans {file_path}."
        
        count = content.count(old_string)
        if count > 1:
            return f"Erreur : Le texte à remplacer apparaît {count} fois. Soyez plus spécifique."

        new_content = content.replace(old_string, new_string)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        return f"✅ Fichier {os.path.basename(file_path)} modifié avec succès."
    except Exception as e:
        return f"Erreur lors de l'édition : {e}"


# ════════════════════════════════════════════════
#  📂  LISTE RÉCURSIVE DU PROJET
# ════════════════════════════════════════════════

def list_project_tree(path: str = ".", max_depth: int = 3) -> str:
    """Affiche une arborescence propre du projet pour comprendre sa structure."""
    base_path = os.path.expanduser(path)
    if not os.path.exists(base_path):
        return f"Erreur : Chemin {base_path} non trouvé."

    output = []
    
    def _walk(current_path, depth):
        if depth > max_depth: return
        
        try:
            items = sorted(os.listdir(current_path))
        except PermissionError:
            return

        for item in items:
            if item in {".git", "__pycache__", "node_modules", ".venv", "venv"}:
                continue
            if item.startswith("."): continue
            
            full_path = os.path.join(current_path, item)
            indent = "  " * depth
            if os.path.isdir(full_path):
                output.append(f"{indent}📁 {item}/")
                _walk(full_path, depth + 1)
            else:
                output.append(f"{indent}📄 {item}")

    output.append(f"📂 Structure de {os.path.basename(os.path.abspath(base_path))}")
    _walk(base_path, 0)
    
    return "\n".join(output)


# ════════════════════════════════════════════════
#  🗺️  REGISTRES D'EXPORT
# ════════════════════════════════════════════════

CODING_TOOLS = {
    'grep_code':         grep_code,
    'edit_file_patch':   edit_file_patch,
    'list_project_tree': list_project_tree,
}

CODING_SCHEMAS = [
    {
        'type': 'function', 'function': {
            'name': 'grep_code',
            'description': "Recherche un motif texte ou regex dans tous les fichiers du projet.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'pattern': {'type': 'string', 'description': "Texte ou regex à chercher (ex: 'TODO', 'def main')"},
                    'search_path': {'type': 'string', 'description': "Dossier de recherche (défaut: courant)"},
                    'case_insensitive': {'type': 'boolean', 'description': "Ignorer la casse (défaut: true)"}
                },
                'required': ['pattern']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'edit_file_patch',
            'description': "Édition chirurgicale : remplace un bloc de texte EXACT par un autre. Utile pour modifier du code sans tout réécrire.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'file_path':  {'type': 'string', 'description': "Chemin du fichier à modifier"},
                    'old_string': {'type': 'string', 'description': "La portion EXACTE de texte à remplacer (incluant espaces/indentation)"},
                    'new_string': {'type': 'string', 'description': "Le nouveau texte à insérer"}
                },
                'required': ['file_path', 'old_string', 'new_string']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'list_project_tree',
            'description': "Affiche l'arborescence des fichiers du projet pour s'orienter.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': "Dossier à lister"},
                    'max_depth': {'type': 'integer', 'description': "Profondeur max (défaut: 3)"}
                },
                'required': []
            }
        }
    }
]

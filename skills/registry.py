# Registre pour aggréger toutes les compétences de Menvis

from .system_skills import TOOLS_REGISTRY as sys_tools, TOOLS_SCHEMAS as sys_schemas
from .adb_skills import TOOLS_REGISTRY as adb_tools, TOOLS_SCHEMAS as adb_schemas
from .phone_skills import PHONE_TOOLS, PHONE_SCHEMAS
from .utilities_skills import UTILITIES_TOOLS, UTILITIES_SCHEMAS
from .web_skills import WEB_TOOLS, WEB_SCHEMAS
from .memory_skills import MEMORY_TOOLS, MEMORY_SCHEMAS
from .os_skills import OS_TOOLS, OS_SCHEMAS
from .keyboard_skills import KEYBOARD_TOOLS, KEYBOARD_SCHEMAS
from .media_skills import MEDIA_TOOLS, MEDIA_SCHEMAS
from .routine_skills import ROUTINE_TOOLS, ROUTINE_SCHEMAS
from .notification_skills import NOTIF_TOOLS, NOTIF_SCHEMAS
from .cool_skills import COOL_TOOLS, COOL_SCHEMAS
from .extra_skills import EXTRA_TOOLS, EXTRA_SCHEMAS
from .smart_skills import SMART_TOOLS, SMART_SCHEMAS

# Combinaison dynamique de tous les dictionnaires d'outils
MENVIS_TOOLS = {
    **sys_tools,
    **adb_tools,
    **PHONE_TOOLS,
    **UTILITIES_TOOLS,
    **WEB_TOOLS,
    **MEMORY_TOOLS,
    **OS_TOOLS,
    **KEYBOARD_TOOLS,
    **MEDIA_TOOLS,
    **ROUTINE_TOOLS,
    **NOTIF_TOOLS,
    **COOL_TOOLS,
    **EXTRA_TOOLS,
    **SMART_TOOLS
}

# Combinaison dynamique de tous les schémas
MENVIS_SCHEMAS = sys_schemas + adb_schemas + PHONE_SCHEMAS + UTILITIES_SCHEMAS + WEB_SCHEMAS + MEMORY_SCHEMAS + OS_SCHEMAS + KEYBOARD_SCHEMAS + MEDIA_SCHEMAS + ROUTINE_SCHEMAS + NOTIF_SCHEMAS + COOL_SCHEMAS + EXTRA_SCHEMAS + SMART_SCHEMAS

# ── Mode Survie (Survival Mode) – Pour modèles < 1B paramètres ───────────
# On ne garde que l'essentiel pour éviter la surcharge cognitive du modèle
SURVIVAL_TOOLS = {
    **sys_tools,
    **MEMORY_TOOLS,
    **OS_TOOLS
}

SURVIVAL_SCHEMAS = sys_schemas + MEMORY_SCHEMAS + OS_SCHEMAS

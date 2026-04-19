# Registre pour aggréger toutes les compétences de Menvis

from .system_skills import TOOLS_REGISTRY as sys_tools, TOOLS_SCHEMAS as sys_schemas
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

# Combinaison dynamique de tous les dictionnaires d'outils
MENVIS_TOOLS = {
    **sys_tools,
    **PHONE_TOOLS,
    **UTILITIES_TOOLS,
    **WEB_TOOLS,
    **MEMORY_TOOLS,
    **OS_TOOLS,
    **KEYBOARD_TOOLS,
    **MEDIA_TOOLS,
    **ROUTINE_TOOLS,
    **NOTIF_TOOLS,
    **COOL_TOOLS
}

# Combinaison dynamique de tous les schémas
MENVIS_SCHEMAS = sys_schemas + PHONE_SCHEMAS + UTILITIES_SCHEMAS + WEB_SCHEMAS + MEMORY_SCHEMAS + OS_SCHEMAS + KEYBOARD_SCHEMAS + MEDIA_SCHEMAS + ROUTINE_SCHEMAS + NOTIF_SCHEMAS + COOL_SCHEMAS

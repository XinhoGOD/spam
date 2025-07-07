# Configuración del Bot Híbrido de Reenvío para Railway
# ====================================================

import os

# 1. CONFIGURACIÓN DE LA API DE TELEGRAM
# Obtener desde variables de entorno de Railway
API_ID = int(os.environ.get('API_ID', 12345678))
API_HASH = os.environ.get('API_HASH', "tu_api_hash_aquí")
BOT_TOKEN = os.environ.get('BOT_TOKEN', "tu_bot_token_aquí")

# 2. CONFIGURACIÓN DE GRUPOS DE DESTINO
AUTO_GET_GROUPS = True  # Obtener automáticamente

# LISTA MANUAL (solo si AUTO_GET_GROUPS = False)
MANUAL_GROUP_IDS = [
    # Agregar IDs de grupos aquí si es necesario
]

# FILTROS PARA GRUPOS AUTOMÁTICOS
GROUP_FILTERS = {
    "admin_only": False,
    "exclude_keywords": [],
    "include_keywords": [],
    "min_members": 1,
    "max_members": 0,
    "exclude_channels": False,
    "exclude_group_ids": []
}

# 3. CONFIGURACIÓN OPCIONAL
FORWARD_DELAY = 30.0  # Tiempo entre reenvíos (30 segundos para evitar límites)
DEBUG_MODE = False

# 4. CONFIGURACIÓN DE ACCESO
PUBLIC_ACCESS = True
AUTHORIZED_USERS = []

# 5. CONFIGURACIÓN DE SEGURIDAD
SECURITY_SETTINGS = {
    "require_introduction": False,
    "max_messages_per_hour": 0,
    "blocked_users": [],
    "log_all_messages": True,
    "notify_owner": True,
    "auto_detect_bot_groups": False,
    "exclude_bot_groups": False,
} 
# Configuración del Bot Híbrido de Reenvío para Railway
# ====================================================

import os

# 1. CONFIGURACIÓN DE LA API DE TELEGRAM
# Obtener desde variables de entorno de Railway
API_ID = int(os.environ.get('API_ID', '22252541'))
API_HASH = os.environ.get('API_HASH', '91c195d7deb3fb56ee7a95eaeb13e2fb')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8157414882:AAHYfRdqn8IG770rDlROnBvFwi78k_KmGwA')

# 1.1. CONFIGURACIÓN DE SESIÓN PARA RAILWAY
# Variables de entorno para la sesión del userbot
PHONE_NUMBER = os.environ.get('PHONE_NUMBER', '')
SESSION_STRING = os.environ.get('SESSION_STRING', '')

# 1.1. CONFIGURACIÓN DEL USERBOT (sesión)
# El userbot usará el archivo userbot_session.session para autenticarse

# 2. CONFIGURACIÓN DE GRUPOS DE DESTINO
AUTO_GET_GROUPS = True  # Obtener automáticamente del userbot

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

# 6. CONFIGURACIÓN ESPECÍFICA PARA RAILWAY
# Para evitar problemas con autenticación en Railway
RAILWAY_MODE = True
USE_SESSION_STRING = bool(os.environ.get('SESSION_STRING', ''))
FALLBACK_TO_BOT_ONLY = True  # Si no hay userbot, funcionar solo como bot normal
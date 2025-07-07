#!/usr/bin/env python3
"""
Bot Híbrido de Reenvío de Mensajes para Telegram - Versión Railway
=================================================================

Esta versión está optimizada para funcionar en Railway con las siguientes mejoras:
- Manejo de sesiones sin archivos persistentes
- Fallback a modo bot-only si no hay userbot disponible
- Configuración mejorada para entornos de producción
- Manejo robusto de errores y reconexiones

Autor: Experto en Python/Telethon
Fecha: 7 de julio de 2025
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional
from telethon import TelegramClient, events, Button
from telethon.tl.types import Message, User
from telethon.sessions import StringSession

# ==================== CONFIGURACIÓN ====================

# Importar configuración
try:
    # Usar config_railway.py para Railway
    from config_railway import (
        API_ID, API_HASH, BOT_TOKEN, 
        AUTO_GET_GROUPS, MANUAL_GROUP_IDS, GROUP_FILTERS,
        FORWARD_DELAY, DEBUG_MODE, PUBLIC_ACCESS, AUTHORIZED_USERS, 
        SECURITY_SETTINGS, RAILWAY_MODE, USE_SESSION_STRING, FALLBACK_TO_BOT_ONLY,
        PHONE_NUMBER, SESSION_STRING
    )
    logger = logging.getLogger(__name__)
    logger.info("✅ Configuración de Railway cargada correctamente")
    logger.info(f"🔍 DEBUG - RAILWAY_MODE: {RAILWAY_MODE}")
    logger.info(f"🔍 DEBUG - USE_SESSION_STRING: {USE_SESSION_STRING}")
    import os
    logger.info(f"🔍 DEBUG - SESSION_STRING en env: {bool(os.environ.get('SESSION_STRING', ''))}")
except ImportError:
    # Fallback a configuración local
    try:
        from config import (
            API_ID, API_HASH, BOT_TOKEN,
            AUTO_GET_GROUPS, MANUAL_GROUP_IDS, GROUP_FILTERS,
            FORWARD_DELAY, DEBUG_MODE, PUBLIC_ACCESS, AUTHORIZED_USERS,
            SECURITY_SETTINGS
        )
        RAILWAY_MODE = False
        USE_SESSION_STRING = False
        FALLBACK_TO_BOT_ONLY = False
        PHONE_NUMBER = ""
        SESSION_STRING = ""
        logger = logging.getLogger(__name__)
        logger.info("✅ Configuración local cargada")
    except ImportError:
        # Configuración por defecto
        logger = logging.getLogger(__name__)
        logger.error("❌ No se pudo cargar configuración - usando valores por defecto")
        
        API_ID = int(os.environ.get('API_ID', '22252541'))
        API_HASH = os.environ.get('API_HASH', '91c195d7deb3fb56ee7a95eaeb13e2fb')
        BOT_TOKEN = os.environ.get('BOT_TOKEN', '8157414882:AAHYfRdqn8IG770rDlROnBvFwi78k_KmGwA')
        
        AUTO_GET_GROUPS = True
        MANUAL_GROUP_IDS = []
        GROUP_FILTERS = {}
        FORWARD_DELAY = 30.0
        DEBUG_MODE = False
        PUBLIC_ACCESS = True
        AUTHORIZED_USERS = []
        SECURITY_SETTINGS = {
            "require_introduction": False,
            "max_messages_per_hour": 0,
            "blocked_users": [],
            "log_all_messages": True,
            "notify_owner": True,
        }
        
        RAILWAY_MODE = True
        USE_SESSION_STRING = bool(os.environ.get('SESSION_STRING', ''))
        FALLBACK_TO_BOT_ONLY = True
        PHONE_NUMBER = os.environ.get('PHONE_NUMBER', '')
        SESSION_STRING = os.environ.get('SESSION_STRING', '')

# Variables globales
TARGET_GROUP_IDS = []
PROBLEMATIC_GROUPS = set()
PROCESSED_MESSAGES = set()
ADMIN_ID = None
BOT_ID = None
user_message_count = {}
user_introductions = {}

# Bandera para indicar si el userbot está disponible
USERBOT_AVAILABLE = False

# ==================== CONFIGURACIÓN DE LOGGING ====================

log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== ESTADOS DEL BOT ====================

class BotState:
    """Maneja los estados del bot para cada usuario"""
    def __init__(self):
        self.waiting_for_message: Dict[int, bool] = {}
        self.processing_message: Dict[int, int] = {}
    
    def set_waiting(self, user_id: int) -> None:
        """Establece que el bot está esperando un mensaje del usuario"""
        self.waiting_for_message[user_id] = True
    
    def is_waiting(self, user_id: int) -> bool:
        """Verifica si el bot está esperando un mensaje del usuario"""
        return self.waiting_for_message.get(user_id, False)
    
    def clear_waiting(self, user_id: int) -> None:
        """Limpia el estado de espera del usuario"""
        self.waiting_for_message[user_id] = False
    
    def set_processing(self, user_id: int, message_id: int) -> None:
        """Establece que se está procesando un mensaje"""
        self.processing_message[user_id] = message_id
    
    def get_processing(self, user_id: int) -> Optional[int]:
        """Obtiene el ID del mensaje que se está procesando"""
        return self.processing_message.get(user_id)
    
    def clear_processing(self, user_id: int) -> None:
        """Limpia el estado de procesamiento"""
        if user_id in self.processing_message:
            del self.processing_message[user_id]

# ==================== INICIALIZACIÓN DE CLIENTES ====================

# Cliente para el bot (siempre funcional)
bot = TelegramClient('bot_session', API_ID, API_HASH)

# Cliente para el userbot (puede no estar disponible en Railway)
userbot = None

# Estado del bot
bot_state = BotState()

# ==================== FUNCIONES AUXILIARES ====================

async def get_bot_id() -> int:
    """Obtiene el ID del bot"""
    global BOT_ID
    if BOT_ID is None:
        me = await bot.get_me()
        BOT_ID = me.id
    return BOT_ID

async def get_admin_id() -> int:
    """Obtiene el ID del administrador"""
    global ADMIN_ID
    if ADMIN_ID is None:
        if USERBOT_AVAILABLE and userbot:
            try:
                me = await userbot.get_me()
                ADMIN_ID = me.id
            except:
                # Si no hay userbot, usar el primer usuario autorizado o 0
                ADMIN_ID = AUTHORIZED_USERS[0] if AUTHORIZED_USERS else 0
        else:
            ADMIN_ID = AUTHORIZED_USERS[0] if AUTHORIZED_USERS else 0
    return ADMIN_ID

async def is_admin(user_id: int) -> bool:
    """Verifica si el usuario es el administrador"""
    admin_id = await get_admin_id()
    return user_id == admin_id

async def can_use_bot(user_id: int) -> bool:
    """Verifica si el usuario puede usar el bot"""
    if PUBLIC_ACCESS:
        if user_id in SECURITY_SETTINGS.get("blocked_users", []):
            return False
        return True
    
    admin_id = await get_admin_id()
    if user_id == admin_id:
        return True
    
    if user_id in AUTHORIZED_USERS:
        return True
    
    return False

async def check_rate_limit(user_id: int) -> bool:
    """Verifica si el usuario ha excedido el límite de mensajes por hora"""
    max_messages = SECURITY_SETTINGS.get("max_messages_per_hour", 0)
    if max_messages == 0:
        return True
    
    import time
    current_hour = int(time.time() / 3600)
    
    if user_id not in user_message_count:
        user_message_count[user_id] = {}
    
    user_message_count[user_id] = {
        hour: count for hour, count in user_message_count[user_id].items() 
        if hour >= current_hour - 1
    }
    
    current_count = user_message_count[user_id].get(current_hour, 0)
    
    if current_count >= max_messages:
        return False
    
    user_message_count[user_id][current_hour] = current_count + 1
    return True

async def log_user_activity(user_id: int, username: str, message_text: str):
    """Registra la actividad del usuario"""
    if SECURITY_SETTINGS.get("log_all_messages", True):
        logger.info(f"📝 Usuario {user_id} (@{username or 'sin_username'}): {message_text[:50]}...")
    
    if SECURITY_SETTINGS.get("notify_owner", True):
        admin_id = await get_admin_id()
        if user_id != admin_id and admin_id != 0:
            try:
                notification = (
                    f"🔔 **Actividad en el bot**\n\n"
                    f"👤 Usuario: @{username or 'sin_username'}\n"
                    f"🆔 ID: `{user_id}`\n"
                    f"💬 Mensaje: {message_text[:100]}..."
                )
                await bot.send_message(admin_id, notification)
            except Exception as e:
                logger.debug(f"Error notificando al dueño: {e}")

async def send_notification_to_admin(message: str) -> None:
    """Envía una notificación al administrador a través del bot"""
    try:
        admin_id = await get_admin_id()
        if admin_id != 0:
            await bot.send_message(admin_id, message)
    except Exception as e:
        logger.error(f"Error enviando notificación al admin: {e}")

# ==================== INICIALIZACIÓN DE CLIENTES ====================

async def init_userbot():
    """Inicializa el userbot con diferentes métodos según la configuración"""
    global userbot, USERBOT_AVAILABLE
    
    # DEBUG: Verificar variables de entorno
    import os
    session_string_env = os.environ.get('SESSION_STRING', '')
    logger.info(f"🔍 DEBUG - RAILWAY_MODE: {RAILWAY_MODE}")
    logger.info(f"🔍 DEBUG - USE_SESSION_STRING: {USE_SESSION_STRING}")
    logger.info(f"🔍 DEBUG - SESSION_STRING disponible: {bool(session_string_env)}")
    logger.info(f"🔍 DEBUG - Longitud SESSION_STRING: {len(session_string_env)}")
    
    # DEBUG: Mostrar todas las variables que contienen "SESSION"
    logger.info("🔍 DEBUG - Variables de entorno con 'SESSION':")
    for key, value in os.environ.items():
        if 'SESSION' in key.upper():
            logger.info(f"  {key}: {len(value)} caracteres")
    
    # DEBUG: Mostrar primeras variables para confirmar
    logger.info("🔍 DEBUG - Primeras 5 variables de entorno:")
    for i, (key, value) in enumerate(os.environ.items()):
        if i < 5:
            logger.info(f"  {key}: {len(value)} caracteres")
        else:
            break
    
    try:
        if USE_SESSION_STRING and SESSION_STRING:
            logger.info("🔄 Intentando conectar userbot con session string...")
            userbot = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
            await userbot.start()
            
            userbot_info = await userbot.get_me()
            logger.info(f"✅ Userbot conectado con session string: @{userbot_info.username}")
            USERBOT_AVAILABLE = True
            
        elif not RAILWAY_MODE:
            logger.info("🔄 Intentando conectar userbot con sesión local...")
            userbot = TelegramClient('userbot_session', API_ID, API_HASH)
            await userbot.start()
            
            userbot_info = await userbot.get_me()
            logger.info(f"✅ Userbot conectado localmente: @{userbot_info.username}")
            USERBOT_AVAILABLE = True
            
        else:
            logger.warning("⚠️ Userbot no disponible en Railway - funcionando solo como bot")
            USERBOT_AVAILABLE = False
            
    except Exception as e:
        logger.error(f"❌ Error inicializando userbot: {e}")
        if FALLBACK_TO_BOT_ONLY:
            logger.info("🔄 Continuando en modo solo-bot...")
            USERBOT_AVAILABLE = False
        else:
            raise

async def initialize_target_groups():
    """Inicializa la lista de grupos de destino"""
    global TARGET_GROUP_IDS
    
    if not USERBOT_AVAILABLE:
        logger.warning("⚠️ Sin userbot disponible - no se pueden obtener grupos automáticamente")
        TARGET_GROUP_IDS = MANUAL_GROUP_IDS.copy()
        return
    
    try:
        if AUTO_GET_GROUPS:
            logger.info("🔄 Obteniendo grupos automáticamente...")
            TARGET_GROUP_IDS = await get_groups_from_userbot()
        else:
            logger.info("🔄 Usando lista manual de grupos")
            TARGET_GROUP_IDS = MANUAL_GROUP_IDS.copy()
            
    except Exception as e:
        logger.error(f"Error inicializando grupos: {e}")
        TARGET_GROUP_IDS = MANUAL_GROUP_IDS.copy()

async def get_groups_from_userbot() -> List[int]:
    """Obtiene automáticamente los grupos del userbot aplicando filtros"""
    if not USERBOT_AVAILABLE or not userbot:
        return []
    
    try:
        logger.info("🔍 Obteniendo grupos del userbot...")
        dialogs = await userbot.get_dialogs()
        logger.info(f"📋 Total de diálogos encontrados: {len(dialogs)}")
        
        groups = [d for d in dialogs if d.is_group]
        channels = [d for d in dialogs if d.is_channel and not d.is_group]
        
        all_targets = []
        if not GROUP_FILTERS.get("exclude_channels", False):
            all_targets.extend(channels)
        all_targets.extend(groups)
        
        eligible_groups = []
        for dialog in all_targets:
            try:
                if await should_include_group(dialog):
                    eligible_groups.append(dialog.id)
                    logger.info(f"✅ Grupo incluido: {dialog.title} (ID: {dialog.id})")
            except Exception as e:
                logger.error(f"Error procesando grupo {dialog.title}: {e}")
        
        return eligible_groups
        
    except Exception as e:
        logger.error(f"Error obteniendo grupos del userbot: {e}")
        return []

async def should_include_group(dialog) -> bool:
    """Determina si un grupo debe ser incluido según los filtros"""
    try:
        # Aplicar filtros básicos
        if dialog.id in GROUP_FILTERS.get("exclude_group_ids", []):
            return False
        
        # Filtros de palabras clave
        exclude_keywords = GROUP_FILTERS.get("exclude_keywords", [])
        if exclude_keywords:
            title_lower = dialog.title.lower() if dialog.title else ""
            for keyword in exclude_keywords:
                if keyword.lower() in title_lower:
                    return False
        
        include_keywords = GROUP_FILTERS.get("include_keywords", [])
        if include_keywords:
            title_lower = dialog.title.lower() if dialog.title else ""
            found_keyword = any(keyword.lower() in title_lower for keyword in include_keywords)
            if not found_keyword:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error aplicando filtros: {e}")
        return False

# ==================== HANDLERS DEL BOT ====================

@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Maneja el comando /start"""
    try:
        user_id = event.sender_id
        user = await event.get_sender()
        username = user.username
        
        if not await can_use_bot(user_id):
            await event.respond("❌ Lo siento, no tienes permiso para usar este bot.")
            return
        
        await log_user_activity(user_id, username, "/start")
        
        is_owner = await is_admin(user_id)
        
        if USERBOT_AVAILABLE:
            status_msg = "🤖 **Bot Híbrido Activo** (Bot + Userbot)"
            functionality = "Puedo reenviar mensajes a todos los grupos donde participa el userbot."
        else:
            status_msg = "🤖 **Bot en Modo Básico** (Solo Bot)"
            functionality = "Modo limitado - El userbot no está disponible."
        
        if is_owner:
            welcome_message = (
                f"{status_msg}\n\n"
                f"¡Hola! {functionality}\n\n"
                "👇 Selecciona una opción:"
            )
            
            buttons = [
                [Button.inline("🚀 Reenviar Mensaje", b"forward_message")],
                [Button.inline("📊 Ver Estado", b"show_status")],
            ]
            
            if USERBOT_AVAILABLE:
                buttons.append([Button.inline("🔄 Actualizar Grupos", b"refresh_groups")])
        else:
            welcome_message = (
                f"{status_msg}\n\n"
                f"¡Hola! {functionality}\n\n"
                "👇 Presiona el botón para comenzar:"
            )
            
            buttons = [
                [Button.inline("🚀 Reenviar Mensaje", b"forward_message")]
            ]
        
        await event.respond(welcome_message, buttons=buttons)
        logger.info(f"Usuario {user_id} (@{username}) inició el bot")
        
    except Exception as e:
        logger.error(f"Error en start_command: {e}")
        await event.respond("❌ Ocurrió un error inesperado.")

@bot.on(events.CallbackQuery(data=b"forward_message"))
async def forward_message_callback(event):
    """Maneja el callback del botón 'Reenviar Mensaje'"""
    try:
        user_id = event.sender_id
        
        if not await can_use_bot(user_id):
            await event.answer("❌ No tienes permiso para usar este bot.")
            return
        
        if not await check_rate_limit(user_id):
            await event.answer("⏳ Has excedido el límite de mensajes por hora.")
            return
        
        if not USERBOT_AVAILABLE:
            await event.edit(
                "❌ **Función no disponible**\n\n"
                "El userbot no está conectado. Esta función requiere "
                "un userbot activo para reenviar mensajes a grupos.\n\n"
                "💡 **Configura SESSION_STRING** en las variables de entorno."
            )
            await event.answer("❌ Userbot no disponible")
            return
        
        await event.edit(
            "✅ **Entendido**\n\n"
            "Por favor, envíame ahora el mensaje que deseas "
            "reenviar a los grupos.\n\n"
            "📝 Puedes enviar texto, fotos, videos, documentos, etc."
        )
        
        bot_state.set_waiting(user_id)
        await event.answer("✅ Listo para recibir tu mensaje")
        
    except Exception as e:
        logger.error(f"Error en forward_message_callback: {e}")
        await event.answer("❌ Error inesperado.")

@bot.on(events.CallbackQuery(data=b"show_status"))
async def show_status_callback(event):
    """Muestra el estado del sistema"""
    try:
        user_id = event.sender_id
        
        if not await is_admin(user_id):
            await event.answer("❌ Solo para administradores.")
            return
        
        status_message = "📊 **Estado del Sistema**\n\n"
        
        # Estado del userbot
        if USERBOT_AVAILABLE:
            status_message += "✅ **Userbot**: Conectado\n"
            status_message += f"📋 **Grupos configurados**: {len(TARGET_GROUP_IDS)}\n"
        else:
            status_message += "❌ **Userbot**: No disponible\n"
            status_message += "💡 Configura SESSION_STRING para activarlo\n"
        
        # Estado del bot
        status_message += "✅ **Bot**: Conectado\n"
        
        # Configuración
        mode = "Automático" if AUTO_GET_GROUPS else "Manual"
        status_message += f"⚙️ **Modo grupos**: {mode}\n"
        
        access = "Público" if PUBLIC_ACCESS else "Privado"
        status_message += f"🔐 **Acceso**: {access}\n"
        
        # Usuarios autorizados
        if not PUBLIC_ACCESS and AUTHORIZED_USERS:
            status_message += f"👥 **Usuarios autorizados**: {len(AUTHORIZED_USERS)}\n"
        
        back_button = Button.inline("🔙 Volver", b"back_to_main")
        await event.edit(status_message, buttons=back_button)
        await event.answer("📊 Estado del sistema")
        
    except Exception as e:
        logger.error(f"Error en show_status_callback: {e}")
        await event.answer("❌ Error obteniendo estado")

@bot.on(events.CallbackQuery(data=b"refresh_groups"))
async def refresh_groups_callback(event):
    """Actualiza la lista de grupos"""
    try:
        user_id = event.sender_id
        
        if not await is_admin(user_id):
            await event.answer("❌ Solo para administradores.")
            return
        
        if not USERBOT_AVAILABLE:
            await event.edit(
                "❌ **No se pueden actualizar grupos**\n\n"
                "El userbot no está disponible.",
                buttons=Button.inline("🔙 Volver", b"back_to_main")
            )
            await event.answer("❌ Userbot no disponible")
            return
        
        await event.edit("⏳ **Actualizando lista de grupos...**")
        
        await initialize_target_groups()
        
        if TARGET_GROUP_IDS:
            result_message = (
                f"✅ **¡Lista actualizada!**\n\n"
                f"📊 **Total de grupos**: {len(TARGET_GROUP_IDS)}"
            )
        else:
            result_message = (
                "⚠️ **No se encontraron grupos**\n\n"
                "Ajusta los filtros en la configuración."
            )
        
        back_button = Button.inline("🔙 Volver", b"back_to_main")
        await event.edit(result_message, buttons=back_button)
        await event.answer("🔄 Grupos actualizados")
        
    except Exception as e:
        logger.error(f"Error en refresh_groups_callback: {e}")
        await event.answer("❌ Error actualizando grupos")

@bot.on(events.CallbackQuery(data=b"back_to_main"))
async def back_to_main_callback(event):
    """Vuelve al menú principal"""
    try:
        # Simular comando /start
        await start_command(event)
        await event.answer("🏠 Menú principal")
        
    except Exception as e:
        logger.error(f"Error en back_to_main_callback: {e}")
        await event.answer("❌ Error volviendo al menú")

@bot.on(events.NewMessage())
async def handle_message(event):
    """Maneja todos los mensajes enviados al bot"""
    try:
        user_id = event.sender_id
        user = await event.get_sender()
        username = user.username
        
        if not await can_use_bot(user_id):
            await event.respond("❌ No tienes permiso para usar este bot.")
            return
        
        if event.text and event.text.startswith('/'):
            return
        
        if not await check_rate_limit(user_id):
            await event.respond("⏳ Has excedido el límite de mensajes por hora.")
            return
        
        message_text = event.text or "[Contenido multimedia]"
        await log_user_activity(user_id, username, message_text)
        
        if not bot_state.is_waiting(user_id):
            await event.respond(
                "ℹ️ Para reenviar un mensaje, usa /start y presiona '🚀 Reenviar Mensaje'"
            )
            return
        
        if not USERBOT_AVAILABLE:
            bot_state.clear_waiting(user_id)
            await event.respond(
                "❌ **Reenvío no disponible**\n\n"
                "El userbot no está conectado."
            )
            return
        
        # Procesar mensaje para reenvío
        bot_state.set_processing(user_id, event.message.id)
        
        confirm_message = (
            "📋 **Mensaje capturado**\n\n"
            f"**Contenido:**\n{message_text[:200]}{'...' if len(message_text) > 200 else ''}\n\n"
            "¿Reenviar a todos los grupos configurados?"
        )
        
        buttons = [
            [Button.inline("✅ Sí, reenviar", b"confirm_forward")],
            [Button.inline("❌ Cancelar", b"cancel_forward")]
        ]
        
        await event.respond(confirm_message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error en handle_message: {e}")
        await event.respond("❌ Error al procesar el mensaje.")

@bot.on(events.CallbackQuery(data=b"confirm_forward"))
async def confirm_forward_callback(event):
    """Confirma y ejecuta el reenvío"""
    try:
        user_id = event.sender_id
        
        if not await can_use_bot(user_id):
            await event.answer("❌ Sin permisos.")
            return
        
        message_id = bot_state.get_processing(user_id)
        if not message_id:
            await event.answer("❌ No hay mensaje para reenviar.")
            return
        
        if not USERBOT_AVAILABLE:
            await event.edit("❌ Userbot no disponible")
            return
        
        await event.edit("⏳ **Procesando reenvío...**")
        
        # Obtener y reenviar mensaje
        try:
            original_message = await bot.get_messages(user_id, ids=message_id)
            if not original_message:
                await event.edit("❌ No se pudo obtener el mensaje original.")
                return
            
            logger.info(f"🔄 Iniciando reenvío del mensaje a {len(TARGET_GROUP_IDS)} grupos")
            
            # Reenviar a grupos usando el userbot para enviar el contenido
            successful_forwards = 0
            failed_forwards = 0
            
            for group_id in TARGET_GROUP_IDS:
                try:
                    # En lugar de forward_messages, enviar el contenido del mensaje
                    if original_message.text:
                        # Mensaje de texto
                        await userbot.send_message(group_id, original_message.text)
                    elif original_message.media:
                        # Mensaje con media (foto, video, documento, etc.)
                        if original_message.photo:
                            await userbot.send_file(group_id, original_message.photo, caption=original_message.text or "")
                        elif original_message.video:
                            await userbot.send_file(group_id, original_message.video, caption=original_message.text or "")
                        elif original_message.document:
                            await userbot.send_file(group_id, original_message.document, caption=original_message.text or "")
                        elif original_message.voice:
                            await userbot.send_file(group_id, original_message.voice, caption=original_message.text or "")
                        elif original_message.video_note:
                            await userbot.send_file(group_id, original_message.video_note)
                        elif original_message.sticker:
                            await userbot.send_file(group_id, original_message.sticker)
                        else:
                            # Otros tipos de media
                            await userbot.send_file(group_id, original_message.media, caption=original_message.text or "")
                    else:
                        # Mensaje vacío o sin contenido reconocible
                        await userbot.send_message(group_id, "[Mensaje sin contenido de texto]")
                    
                    successful_forwards += 1
                    logger.info(f"✅ Mensaje enviado exitosamente al grupo {group_id}")
                    await asyncio.sleep(FORWARD_DELAY)
                    
                except Exception as e:
                    failed_forwards += 1
                    logger.error(f"❌ Error enviando a {group_id}: {e}")
                    # Log más detallado del error
                    logger.error(f"   Tipo de error: {type(e).__name__}")
                    logger.error(f"   Detalles del mensaje: texto={bool(original_message.text)}, media={bool(original_message.media)}")
            
            # Mostrar resultado
            if successful_forwards > 0:
                result_message = (
                    f"✅ **¡Reenvío completado!**\n\n"
                    f"• ✅ Exitosos: {successful_forwards}\n"
                    f"• ❌ Fallidos: {failed_forwards}\n"
                    f"• 📋 Total: {len(TARGET_GROUP_IDS)}"
                )
            else:
                result_message = "❌ **Error en el reenvío**\n\nNo se pudo reenviar a ningún grupo."
            
            await event.edit(result_message)
            
        except Exception as e:
            logger.error(f"Error en reenvío: {e}")
            await event.edit("❌ Error durante el reenvío.")
        
        # Limpiar estado
        bot_state.clear_processing(user_id)
        bot_state.clear_waiting(user_id)
        
    except Exception as e:
        logger.error(f"Error en confirm_forward_callback: {e}")
        await event.answer("❌ Error confirmando reenvío")

@bot.on(events.CallbackQuery(data=b"cancel_forward"))
async def cancel_forward_callback(event):
    """Cancela el reenvío"""
    try:
        user_id = event.sender_id
        
        bot_state.clear_processing(user_id)
        bot_state.clear_waiting(user_id)
        
        await event.edit("❌ **Reenvío cancelado**")
        await event.answer("Reenvío cancelado")
        
    except Exception as e:
        logger.error(f"Error en cancel_forward_callback: {e}")
        await event.answer("❌ Error cancelando")

# ==================== FUNCIONES PRINCIPALES ====================

async def start_bot():
    """Inicia el bot"""
    try:
        await bot.start(bot_token=BOT_TOKEN)
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot iniciado: @{bot_info.username}")
        
    except Exception as e:
        logger.error(f"Error iniciando bot: {e}")
        raise

async def main():
    """Función principal"""
    try:
        logger.info("=== INICIANDO BOT PARA RAILWAY ===")
        
        # Validar configuración básica
        if not all([API_ID, API_HASH, BOT_TOKEN]):
            logger.error("❌ Configuración incompleta - verifica las variables de entorno")
            return
        
        # Inicializar userbot si es posible
        await init_userbot()
        
        # Inicializar grupos si hay userbot
        if USERBOT_AVAILABLE:
            await initialize_target_groups()
        
        # Iniciar bot
        await start_bot()
        
        logger.info("✅ Sistema iniciado correctamente")
        
        if USERBOT_AVAILABLE:
            logger.info(f"📊 Grupos configurados: {len(TARGET_GROUP_IDS)}")
        else:
            logger.warning("⚠️ Funcionando en modo solo-bot (sin userbot)")
        
        # Ejecutar bot
        await bot.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Sistema cerrado por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)
    finally:
        logger.info("Sistema cerrado")

# ==================== PUNTO DE ENTRADA ====================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔴 Programa interrumpido")
    except Exception as e:
        print(f"🔴 Error fatal: {e}")
        sys.exit(1)

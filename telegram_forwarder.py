#!/usr/bin/env python3
"""
Bot Híbrido de Reenvío de Mensajes para Telegram
===============================================

Este script implementa un sistema híbrido que combina:
- Un bot de BotFather para la interfaz de usuario
- Un userbot para la ejecución de acciones de reenvío

Autor: Experto en Python/Telethon
Fecha: 6 de julio de 2025
"""

import asyncio
import logging
from typing import Dict, List, Optional
from telethon import TelegramClient, events, Button
from telethon.tl.types import Message, User

# ==================== CONFIGURACIÓN ====================

# Importar configuración desde archivo externo
try:
    # Intentar primero config_railway.py (para Railway)
    from config_railway import API_ID, API_HASH, BOT_TOKEN
    from config_railway import AUTO_GET_GROUPS, MANUAL_GROUP_IDS, GROUP_FILTERS
    from config_railway import FORWARD_DELAY, DEBUG_MODE
    from config_railway import PUBLIC_ACCESS, AUTHORIZED_USERS, SECURITY_SETTINGS
except ImportError:
    # Si no existe, usar config.py local
    try:
        from config import API_ID, API_HASH, BOT_TOKEN
        from config import AUTO_GET_GROUPS, MANUAL_GROUP_IDS, GROUP_FILTERS
        from config import FORWARD_DELAY, DEBUG_MODE
        from config import PUBLIC_ACCESS, AUTHORIZED_USERS, SECURITY_SETTINGS
    except ImportError:
        # Configuración por defecto si no existe config.py
        API_ID = 12345678  # Reemplaza con tu API_ID
        API_HASH = "tu_api_hash_aquí"  # Reemplaza con tu API_HASH
        BOT_TOKEN = "tu_bot_token_aquí"  # Reemplaza con tu BOT_TOKEN
        AUTO_GET_GROUPS = True
        MANUAL_GROUP_IDS = []
        GROUP_FILTERS = {
            "admin_only": False,
            "exclude_keywords": [],  # Sin palabras clave de exclusión por defecto
            "include_keywords": [],
            "min_members": 1,  # Permitir grupos con al menos 1 miembro
            "max_members": 0,
            "exclude_channels": False,  # Incluir canales por defecto
            "exclude_group_ids": []
        }
        FORWARD_DELAY = 0.5
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

# Variable global para almacenar los grupos de destino
TARGET_GROUP_IDS = []

# Variable global para almacenar grupos problemáticos (con bots)
PROBLEMATIC_GROUPS = set()

# Variable global para almacenar mensajes ya procesados (evitar duplicados)
PROCESSED_MESSAGES = set()

# ID del administrador (se obtiene automáticamente)
ADMIN_ID = None
BOT_ID = None

# Manejo de usuarios y seguridad
user_message_count = {}  # user_id -> {hour: count}
user_introductions = {}  # user_id -> bool

# ==================== CONFIGURACIÓN DE LOGGING ====================

# Configurar nivel de logging basado en DEBUG_MODE
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
        self.processing_message: Dict[int, int] = {}  # user_id -> message_id
    
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

# Cliente para el userbot
userbot = TelegramClient('userbot_session', API_ID, API_HASH)

# Cliente para el bot
bot = TelegramClient('bot_session', API_ID, API_HASH)

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
    """Obtiene el ID del administrador (dueño del userbot)"""
    global ADMIN_ID
    if ADMIN_ID is None:
        me = await userbot.get_me()
        ADMIN_ID = me.id
    return ADMIN_ID

async def is_admin(user_id: int) -> bool:
    """Verifica si el usuario es el administrador"""
    admin_id = await get_admin_id()
    return user_id == admin_id

async def can_use_bot(user_id: int) -> bool:
    """Verifica si el usuario puede usar el bot"""
    # Si es acceso público, permitir a todos (con excepciones)
    if PUBLIC_ACCESS:
        # Verificar si el usuario está bloqueado
        if user_id in SECURITY_SETTINGS.get("blocked_users", []):
            return False
        return True
    
    # Si es acceso restringido, verificar permisos
    admin_id = await get_admin_id()
    if user_id == admin_id:
        return True
    
    # Verificar si está en la lista de usuarios autorizados
    if user_id in AUTHORIZED_USERS:
        return True
    
    return False

async def check_rate_limit(user_id: int) -> bool:
    """Verifica si el usuario ha excedido el límite de mensajes por hora"""
    max_messages = SECURITY_SETTINGS.get("max_messages_per_hour", 0)
    if max_messages == 0:
        return True  # Sin límite
    
    import time
    current_hour = int(time.time() / 3600)
    
    if user_id not in user_message_count:
        user_message_count[user_id] = {}
    
    # Limpiar horas antiguas
    user_message_count[user_id] = {
        hour: count for hour, count in user_message_count[user_id].items() 
        if hour >= current_hour - 1
    }
    
    # Contar mensajes en la hora actual
    current_count = user_message_count[user_id].get(current_hour, 0)
    
    if current_count >= max_messages:
        return False
    
    # Incrementar contador
    user_message_count[user_id][current_hour] = current_count + 1
    return True

async def log_user_activity(user_id: int, username: str, message_text: str):
    """Registra la actividad del usuario"""
    if SECURITY_SETTINGS.get("log_all_messages", True):
        logger.info(f"📝 Usuario {user_id} (@{username or 'sin_username'}): {message_text[:50]}...")
    
    # Notificar al dueño si está configurado
    if SECURITY_SETTINGS.get("notify_owner", True):
        admin_id = await get_admin_id()
        if user_id != admin_id:  # No notificar cuando el dueño usa el bot
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

async def detect_problematic_groups():
    """Detecta grupos que contienen bots y los marca como problemáticos"""
    global PROBLEMATIC_GROUPS
    
    logger.info("🔍 Detectando grupos problemáticos (con bots)...")
    
    for group_id in TARGET_GROUP_IDS:
        try:
            # Intentar obtener participantes del grupo (solo los primeros 50 para eficiencia)
            participants = await userbot.get_participants(group_id, limit=50)
            
            # Verificar si hay bots en el grupo
            bot_count = sum(1 for participant in participants if participant.bot)
            
            if bot_count > 0:
                PROBLEMATIC_GROUPS.add(group_id)
                entity = await userbot.get_entity(group_id)
                group_title = getattr(entity, 'title', f'Grupo {group_id}')
                logger.warning(f"⚠️ Grupo problemático detectado: {group_title} ({group_id}) - Contiene {bot_count} bot(s)")
            else:
                # Remover de grupos problemáticos si ya no tiene bots
                PROBLEMATIC_GROUPS.discard(group_id)
                
        except Exception as e:
            error_msg = str(e)
            if "CHAT_WRITE_FORBIDDEN" in error_msg or "USER_NOT_PARTICIPANT" in error_msg:
                # No podemos acceder al grupo, marcarlo como problemático
                PROBLEMATIC_GROUPS.add(group_id)
                logger.warning(f"⚠️ Grupo inaccesible marcado como problemático: {group_id} - {error_msg}")
            else:
                logger.warning(f"No se pudo verificar grupo {group_id} para bots: {e}")
                # Por precaución, marcar como problemático
                PROBLEMATIC_GROUPS.add(group_id)
    
    logger.info(f"📊 Grupos problemáticos detectados: {len(PROBLEMATIC_GROUPS)}")

async def clear_problematic_groups():
    """Limpia la lista de grupos problemáticos (útil para reintentar)"""
    global PROBLEMATIC_GROUPS
    old_count = len(PROBLEMATIC_GROUPS)
    PROBLEMATIC_GROUPS.clear()
    logger.info(f"🧹 Grupos problemáticos limpiados: {old_count} → 0")

async def clear_processed_messages():
    """Limpia la lista de mensajes procesados (útil para reintentar)"""
    global PROCESSED_MESSAGES
    old_count = len(PROCESSED_MESSAGES)
    PROCESSED_MESSAGES.clear()
    logger.info(f"🧹 Mensajes procesados limpiados: {old_count} → 0")

async def send_notification_to_admin(message: str) -> None:
    """Envía una notificación al administrador a través del bot"""
    try:
        admin_id = await get_admin_id()
        await bot.send_message(admin_id, message)
    except Exception as e:
        logger.error(f"Error enviando notificación al admin: {e}")

# ==================== HANDLERS DEL BOT ====================

@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Maneja el comando /start"""
    try:
        user_id = event.sender_id
        user = await event.get_sender()
        username = user.username
        
        # Verificar si el usuario puede usar el bot
        if not await can_use_bot(user_id):
            await event.respond("❌ Lo siento, no tienes permiso para usar este bot.")
            logger.warning(f"Usuario {user_id} (@{username}) intentó usar el bot sin permisos")
            return
        
        # Registrar actividad
        await log_user_activity(user_id, username, "/start")
        
        # Determinar tipo de mensaje según el usuario
        is_owner = await is_admin(user_id)
        
        if is_owner:
            # Mensaje para el dueño
            welcome_message = (
                "🤖 **Bot de Reenvío de Mensajes** (Modo Administrador)\n\n"
                "¡Hola! Soy tu bot híbrido para reenviar mensajes.\n"
                "Puedo enviar mensajes a todos los grupos donde participa tu userbot.\n\n"
                "👇 Selecciona una opción:"
            )
            
            # Botones completos para el administrador
            buttons = [
                [Button.inline("🚀 Reenviar Mensaje", b"forward_message")],
                [Button.inline("📊 Ver Grupos", b"show_groups"), Button.inline("🔄 Actualizar Grupos", b"refresh_groups")],
                [Button.inline("🧹 Limpiar Grupos Problemáticos", b"clear_problematic")],
                [Button.inline("🗑️ Limpiar Mensajes Procesados", b"clear_processed")]
            ]
        else:
            # Mensaje para usuarios públicos
            welcome_message = (
                "🤖 **Bot de Reenvío de Mensajes**\n\n"
                "¡Hola! Puedo reenviar tus mensajes a múltiples grupos.\n"
                "Envíame cualquier mensaje y lo distribuiré automáticamente.\n\n"
                "👇 Presiona el botón para comenzar:"
            )
            
            # Botón simple para usuarios públicos
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
        user = await event.get_sender()
        username = user.username
        
        # Verificar permisos
        if not await can_use_bot(user_id):
            await event.answer("❌ No tienes permiso para usar este bot.")
            return
        
        # Verificar límite de velocidad
        if not await check_rate_limit(user_id):
            await event.answer("⏳ Has excedido el límite de mensajes por hora. Intenta más tarde.")
            return
        
        # Editar el mensaje
        await event.edit(
            "✅ **Entendido**\n\n"
            "Por favor, envíame ahora el mensaje que deseas "
            "reenviar a los grupos.\n\n"
            "📝 Puedes enviar texto, fotos, videos, documentos, etc."
        )
        
        # Establecer estado de espera
        bot_state.set_waiting(user_id)
        
        await event.answer("✅ Listo para recibir tu mensaje")
        
        logger.info(f"Usuario {user_id} (@{username}) solicitó reenvío de mensaje")
        
    except Exception as e:
        logger.error(f"Error en forward_message_callback: {e}")
        await event.answer("❌ Ocurrió un error inesperado.")

@bot.on(events.CallbackQuery(data=b"show_groups"))
async def show_groups_callback(event):
    """Maneja el callback del botón 'Ver Grupos'"""
    try:
        user_id = event.sender_id
        
        # Solo el administrador puede ver grupos
        if not await is_admin(user_id):
            await event.answer("❌ Esta función es solo para administradores.")
            return
        
        # Obtener resumen de grupos
        summary = await get_groups_summary()
        
        # Botón para volver
        back_button = Button.inline("🔙 Volver", b"back_to_main")
        
        await event.edit(summary, buttons=back_button)
        await event.answer("📊 Mostrando grupos configurados")
        
    except Exception as e:
        logger.error(f"Error en show_groups_callback: {e}")
        await event.answer("❌ Error obteniendo información de grupos")

@bot.on(events.CallbackQuery(data=b"refresh_groups"))
async def refresh_groups_callback(event):
    """Maneja el callback del botón 'Actualizar Grupos'"""
    try:
        user_id = event.sender_id
        
        # Solo el administrador puede actualizar grupos
        if not await is_admin(user_id):
            await event.answer("❌ Esta función es solo para administradores.")
            return
        
        # Mostrar mensaje de procesamiento
        await event.edit("⏳ **Actualizando lista de grupos...**\n\nEsto puede tomar unos segundos...")
        
        # Actualizar grupos
        group_count = await refresh_target_groups()
        
        # Mostrar resultado
        if group_count > 0:
            result_message = (
                f"✅ **¡Lista actualizada!**\n\n"
                f"📊 **Total de grupos configurados**: {group_count}\n\n"
                f"Los grupos han sido actualizados según los filtros configurados."
            )
        else:
            result_message = (
                "⚠️ **No se encontraron grupos**\n\n"
                "No se encontraron grupos que cumplan con los filtros configurados.\n"
                "Puedes ajustar los filtros en el archivo config.py"
            )
        
        # Botón para volver
        back_button = Button.inline("🔙 Volver", b"back_to_main")
        
        await event.edit(result_message, buttons=back_button)
        await event.answer("🔄 Grupos actualizados")
        
    except Exception as e:
        logger.error(f"Error en refresh_groups_callback: {e}")
        await event.answer("❌ Error actualizando grupos")

@bot.on(events.CallbackQuery(data=b"back_to_main"))
async def back_to_main_callback(event):
    """Maneja el callback del botón 'Volver'"""
    try:
        user_id = event.sender_id
        
        # Verificar permisos
        if not await can_use_bot(user_id):
            await event.answer("❌ No tienes permiso para usar este bot.")
            return
        
        # Determinar tipo de usuario
        is_owner = await is_admin(user_id)
        
        if is_owner:
            # Mensaje para el dueño
            welcome_message = (
                "🤖 **Bot de Reenvío de Mensajes** (Modo Administrador)\n\n"
                "¡Hola! Soy tu bot híbrido para reenviar mensajes.\n"
                "Puedo enviar mensajes a todos los grupos donde participa tu userbot.\n\n"
                "👇 Selecciona una opción:"
            )
            
            # Botones completos para el administrador
            buttons = [
                [Button.inline("🚀 Reenviar Mensaje", b"forward_message")],
                [Button.inline("📊 Ver Grupos", b"show_groups"), Button.inline("🔄 Actualizar Grupos", b"refresh_groups")],
                [Button.inline("🧹 Limpiar Grupos Problemáticos", b"clear_problematic")],
                [Button.inline("🗑️ Limpiar Mensajes Procesados", b"clear_processed")]
            ]
        else:
            # Mensaje para usuarios públicos
            welcome_message = (
                "🤖 **Bot de Reenvío de Mensajes**\n\n"
                "¡Hola! Puedo reenviar tus mensajes a múltiples grupos.\n"
                "Envíame cualquier mensaje y lo distribuiré automáticamente.\n\n"
                "👇 Presiona el botón para comenzar:"
            )
            
            # Botón simple para usuarios públicos
            buttons = [
                [Button.inline("🚀 Reenviar Mensaje", b"forward_message")]
            ]
        
        await event.edit(welcome_message, buttons=buttons)
        await event.answer("🏠 Volviendo al menú principal")
        
    except Exception as e:
        logger.error(f"Error en back_to_main_callback: {e}")
        await event.answer("❌ Error volviendo al menú principal")

@bot.on(events.CallbackQuery(data=b"clear_problematic"))
async def clear_problematic_callback(event):
    """Maneja el callback del botón 'Limpiar Grupos Problemáticos'"""
    try:
        user_id = event.sender_id
        if not await is_admin(user_id):
            await event.answer("❌ Solo el administrador puede usar esta función.")
            return
        await clear_problematic_groups()
        await event.edit("🧹 **Grupos problemáticos limpiados.**\n\nPuedes volver a intentar el reenvío o actualizar la lista de grupos.", buttons=Button.inline("🔙 Volver", b"back_to_main"))
        await event.answer("Grupos problemáticos limpiados")
    except Exception as e:
        logger.error(f"Error en clear_problematic_callback: {e}")
        await event.answer("❌ Error limpiando grupos problemáticos")

@bot.on(events.CallbackQuery(data=b"confirm_forward"))
async def confirm_forward_callback(event):
    """Maneja el callback del botón 'Sí, reenviar'"""
    try:
        user_id = event.sender_id
        if not await can_use_bot(user_id):
            await event.answer("❌ No tienes permiso para usar este bot.")
            return
        
        # Obtener el mensaje guardado
        message_id = bot_state.get_processing(user_id)
        if not message_id:
            await event.answer("❌ No hay mensaje para reenviar.")
            return
        
        # Mostrar mensaje de procesamiento
        await event.edit("⏳ **Procesando reenvío...**")
        
        # Reenviar el mensaje al userbot
        admin_id = await get_admin_id()
        try:
            # Obtener el mensaje original
            original_message = await bot.get_messages(user_id, ids=message_id)
            if not original_message:
                await event.answer("❌ No se pudo obtener el mensaje original.")
                return
            
            # Reenviar al userbot
            forwarded_msg = await bot.forward_messages(admin_id, original_message)
            logger.info(f"✅ Mensaje reenviado exitosamente al userbot: {forwarded_msg.id}")
            
            await event.answer("✅ Mensaje enviado para reenvío")
            
        except Exception as e:
            logger.error(f"❌ Error reenviando al userbot: {e}")
            await event.answer("❌ Error al procesar el mensaje.")
        
        # Limpiar estado
        bot_state.clear_processing(user_id)
        bot_state.clear_waiting(user_id)
        
    except Exception as e:
        logger.error(f"Error en confirm_forward_callback: {e}")
        await event.answer("❌ Error confirmando reenvío")

@bot.on(events.CallbackQuery(data=b"cancel_forward"))
async def cancel_forward_callback(event):
    """Maneja el callback del botón 'No, cancelar'"""
    try:
        user_id = event.sender_id
        if not await can_use_bot(user_id):
            await event.answer("❌ No tienes permiso para usar este bot.")
            return
        
        # Limpiar estado
        bot_state.clear_processing(user_id)
        bot_state.clear_waiting(user_id)
        
        await event.edit("❌ **Reenvío cancelado**\n\nEl mensaje no será reenviado.")
        await event.answer("Reenvío cancelado")
        
    except Exception as e:
        logger.error(f"Error en cancel_forward_callback: {e}")
        await event.answer("❌ Error cancelando reenvío")

@bot.on(events.CallbackQuery(data=b"clear_processed"))
async def clear_processed_callback(event):
    """Maneja el callback del botón 'Limpiar Mensajes Procesados'"""
    try:
        user_id = event.sender_id
        if not await is_admin(user_id):
            await event.answer("❌ Solo el administrador puede usar esta función.")
            return
        await clear_processed_messages()
        await event.edit("🗑️ **Mensajes procesados limpiados.**\n\nPuedes volver a reenviar mensajes sin riesgo de duplicados.", buttons=Button.inline("🔙 Volver", b"back_to_main"))
        await event.answer("Mensajes procesados limpiados")
    except Exception as e:
        logger.error(f"Error en clear_processed_callback: {e}")
        await event.answer("❌ Error limpiando mensajes procesados")

@bot.on(events.NewMessage())
async def handle_message(event):
    """Maneja todos los mensajes enviados al bot"""
    try:
        user_id = event.sender_id
        user = await event.get_sender()
        username = user.username
        
        logger.info(f"📨 Bot recibió mensaje de {username} ({user_id}): {event.text or '[Multimedia]'}")
        
        # Verificar permisos básicos
        if not await can_use_bot(user_id):
            logger.warning(f"❌ Usuario {user_id} sin permisos")
            await event.respond("❌ No tienes permiso para usar este bot.")
            return
        
        # Ignorar comandos
        if event.text and event.text.startswith('/'):
            logger.debug(f"📝 Ignorando comando: {event.text}")
            return
        
        # Verificar límite de velocidad
        if not await check_rate_limit(user_id):
            logger.warning(f"⏳ Usuario {user_id} excedió límite de velocidad")
            await event.respond("⏳ Has excedido el límite de mensajes por hora. Intenta más tarde.")
            return
        
        # Registrar actividad
        message_text = event.text or "[Contenido multimedia]"
        await log_user_activity(user_id, username, message_text)
        
        # Verificar si estamos esperando un mensaje
        if not bot_state.is_waiting(user_id):
            logger.info(f"ℹ️ Usuario {user_id} no está en modo espera")
            await event.respond(
                "ℹ️ Para reenviar un mensaje, primero usa el comando /start "
                "y presiona el botón '🚀 Reenviar Mensaje'"
            )
            return
        
        logger.info(f"✅ Usuario {user_id} está en modo espera, procesando mensaje...")
        
        # Guardar el mensaje para confirmación
        bot_state.set_processing(user_id, event.message.id)
        
        # Mostrar mensaje de confirmación con botones
        confirm_message = (
            "📋 **Mensaje capturado**\n\n"
            f"**Contenido:**\n{message_text[:200]}{'...' if len(message_text) > 200 else ''}\n\n"
            "¿Deseas reenviar este mensaje a todos los grupos configurados?"
        )
        
        # Botones de confirmación
        buttons = [
            [Button.inline("✅ Sí, reenviar", b"confirm_forward")],
            [Button.inline("❌ No, cancelar", b"cancel_forward")]
        ]
        
        await event.respond(confirm_message, buttons=buttons)
        
        logger.info(f"📋 Mensaje de {username} ({user_id}) capturado para confirmación")
        
    except Exception as e:
        logger.error(f"Error en handle_message: {e}")
        await event.respond("❌ Error al procesar el mensaje.")

# ==================== HANDLERS DEL USERBOT ====================

@userbot.on(events.NewMessage())
async def handle_saved_messages(event):
    """Maneja SOLO los mensajes reenviados por el bot y apaga el sistema tras procesar uno válido"""
    try:
        message_id = event.message.id
        logger.info(f"🔍 Userbot recibió mensaje: {message_id}")

        # FILTRO: Solo procesar si es un reenvío válido del bot y no ha sido procesado
        if message_id in PROCESSED_MESSAGES:
            logger.info(f"⏭️ Mensaje {message_id} ya fue procesado, saltando...")
            return
        if not event.message.fwd_from:
            logger.debug("❌ Mensaje no es un reenvío, ignorando...")
            return
        # Verifica que el mensaje reenviado venga del bot
        bot_id = await get_bot_id()
        fwd_from_id = getattr(event.message.fwd_from.from_id, 'user_id', None)
        if fwd_from_id != bot_id:
            logger.debug(f"❌ Mensaje reenviado no proviene del bot (fwd_from_id={fwd_from_id}), ignorando...")
            return

        # Si pasa los filtros, ejecutar la lógica de reenvío y apagado
        logger.info("✅ Mensaje válido detectado - procediendo con reenvío y apagado")
        # ... (resto del código de reenvío y apagado igual que antes) ...
        # (COPIAR aquí el bloque desde 'Contador de grupos exitosos' hasta sys.exit(0))

        # Contador de grupos exitosos
        successful_forwards = 0
        failed_forwards = 0
        valid_groups = [gid for gid in TARGET_GROUP_IDS if gid not in PROBLEMATIC_GROUPS]
        logger.info(f"📊 Grupos configurados: {len(TARGET_GROUP_IDS)}")
        logger.info(f"📊 Grupos problemáticos: {len(PROBLEMATIC_GROUPS)}")
        logger.info(f"📊 Grupos válidos para reenvío: {len(valid_groups)}")
        logger.info("📋 Grupos a procesar:")
        for i, group_id in enumerate(valid_groups, 1):
            try:
                entity = await userbot.get_entity(group_id)
                group_title = getattr(entity, 'title', f'Grupo {group_id}')
                logger.info(f"   {i}. {group_title} (ID: {group_id})")
            except:
                logger.info(f"   {i}. Grupo {group_id} (no accesible)")
        if not valid_groups and TARGET_GROUP_IDS:
            logger.warning("⚠️ No hay grupos válidos, intentando reenvío forzado...")
            valid_groups = TARGET_GROUP_IDS.copy()
        if not valid_groups:
            logger.warning("⚠️ No hay grupos configurados para reenviar")
            result_message = (
                "❌ **No se pudo reenviar el mensaje**\n\n"
                "No hay grupos configurados para el reenvío.\n\n"
                "💡 **Solución:**\n"
                "• Usa el botón '🔄 Actualizar Grupos' para detectar grupos\n"
                "• O configura grupos manualmente en config.py"
            )
            for user_id, message_id in bot_state.processing_message.items():
                try:
                    await bot.edit_message(user_id, message_id, result_message)
                    bot_state.clear_processing(user_id)
                except:
                    pass
            return
        for group_id in valid_groups:
            try:
                try:
                    entity = await userbot.get_entity(group_id)
                    group_title = getattr(entity, 'title', f'Grupo {group_id}')
                except Exception as e:
                    logger.warning(f"No se pudo obtener información del grupo {group_id}: {e}")
                    group_title = f'Grupo {group_id}'
                await userbot.forward_messages(group_id, event.message)
                successful_forwards += 1
                logger.info(f"Mensaje reenviado exitosamente a {group_title} ({group_id})")
                await asyncio.sleep(FORWARD_DELAY)
            except Exception as e:
                failed_forwards += 1
                error_msg = str(e)
                if "Bots can't send messages to other bots" in error_msg:
                    logger.warning(f"Error reenviando a {group_title} ({group_id}): El grupo contiene bots y no se puede reenviar")
                    PROBLEMATIC_GROUPS.add(group_id)
                elif "A wait of" in error_msg and "seconds is required" in error_msg:
                    logger.warning(f"Error reenviando a {group_title} ({group_id}): Límite de velocidad alcanzado")
                    await asyncio.sleep(10)
                elif "CHAT_WRITE_FORBIDDEN" in error_msg:
                    logger.warning(f"Error reenviando a {group_title} ({group_id}): Sin permisos de escritura")
                elif "USER_NOT_PARTICIPANT" in error_msg:
                    logger.warning(f"Error reenviando a {group_title} ({group_id}): Userbot no es participante del grupo")
                elif "CHANNEL_PRIVATE" in error_msg:
                    logger.warning(f"Error reenviando a {group_title} ({group_id}): Canal privado sin acceso")
                else:
                    logger.error(f"Error reenviando a {group_title} ({group_id}): {e}")
        if successful_forwards > 0:
            result_message = (
                f"✅ **¡Reenvío completado!**\n\n"
                f"📊 **Estadísticas:**\n"
                f"• ✅ Exitosos: {successful_forwards}\n"
                f"• ❌ Fallidos: {failed_forwards}\n"
                f"• 📋 Total: {len(TARGET_GROUP_IDS)}"
            )
            if failed_forwards > 0:
                result_message += "\n\n⚠️ **Nota:** Algunos grupos pueden contener bots, lo cual impide el reenvío automático."
        else:
            result_message = (
                "❌ **Error en el reenvío**\n\n"
                "No se pudo reenviar el mensaje a ningún grupo.\n\n"
                "💡 **Posibles causas:**\n"
                "• Los grupos contienen bots\n"
                "• Problemas de permisos\n"
                "• Grupos privados sin acceso"
            )
        try:
            admin_id = await get_admin_id()
            await send_notification_to_admin(result_message)
            for user_id, message_id in bot_state.processing_message.items():
                try:
                    await bot.edit_message(user_id, message_id, result_message)
                    bot_state.clear_processing(user_id)
                except:
                    pass
        except Exception as e:
            logger.error(f"Error notificando resultado: {e}")
        PROCESSED_MESSAGES.add(message_id)
        logger.info(f"✅ Mensaje {message_id} marcado como procesado")
        if len(PROCESSED_MESSAGES) > 1000:
            processed_list = list(PROCESSED_MESSAGES)
            PROCESSED_MESSAGES = set(processed_list[-1000:])
            logger.info("🧹 Lista de mensajes procesados limpiada")
        logger.info(f"Reenvío completado: {successful_forwards} exitosos, {failed_forwards} fallidos")
        logger.info("🛑 Apagando el bot tras finalizar el reenvío de mensajes...")
        await userbot.disconnect()
        await bot.disconnect()
        import sys
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error en handle_saved_messages: {e}")
        await send_notification_to_admin("❌ Error inesperado durante el reenvío.")

# ==================== FUNCIONES DE GESTIÓN DE GRUPOS ====================

async def get_groups_from_userbot() -> List[int]:
    """
    Obtiene automáticamente los grupos del userbot aplicando filtros
    """
    try:
        logger.info("🔍 Obteniendo grupos del userbot...")
        
        # Obtener todos los diálogos (chats) del userbot
        dialogs = await userbot.get_dialogs()
        logger.info(f"📋 Total de diálogos encontrados: {len(dialogs)}")
        
        # Filtrar grupos y canales
        groups = [d for d in dialogs if d.is_group]
        channels = [d for d in dialogs if d.is_channel and not d.is_group]
        
        logger.info(f"🏘️ Grupos encontrados: {len(groups)}")
        logger.info(f"📺 Canales encontrados: {len(channels)}")
        
        # Combinar grupos y canales según configuración
        all_targets = []
        if not GROUP_FILTERS.get("exclude_channels", False):
            all_targets.extend(channels)
            logger.info("📺 Canales incluidos en la búsqueda")
        
        all_targets.extend(groups)
        
        if not all_targets:
            logger.warning("⚠️ El userbot no está en ningún grupo o canal")
            logger.info("💡 Asegúrate de que el userbot esté agregado a al menos un grupo o canal")
            return []
        
        # Mostrar todos los grupos y canales encontrados
        logger.info("📝 Grupos y canales donde está el userbot:")
        for i, target in enumerate(all_targets, 1):
            try:
                entity = await userbot.get_entity(target.id)
                participants_count = getattr(entity, 'participants_count', 'N/A')
                target_type = "Canal" if target.is_channel else "Grupo"
                logger.info(f"   {i}. {target.title} (ID: {target.id}, Tipo: {target_type}, Miembros: {participants_count})")
            except:
                target_type = "Canal" if target.is_channel else "Grupo"
                logger.info(f"   {i}. {target.title} (ID: {target.id}, Tipo: {target_type})")
        
        eligible_groups = []
        
        logger.info("🔍 Aplicando filtros...")
        for dialog in all_targets:
            try:
                # Aplicar filtros
                if await should_include_group(dialog):
                    eligible_groups.append(dialog.id)
                    logger.info(f"✅ Grupo incluido: {dialog.title} (ID: {dialog.id})")
                else:
                    logger.info(f"⏭️ Grupo excluido: {dialog.title} (ID: {dialog.id})")
                    
            except Exception as e:
                logger.error(f"Error procesando grupo {dialog.title}: {e}")
                continue
        
        if not eligible_groups:
            logger.warning("⚠️ Ningún grupo pasó los filtros configurados")
            logger.info("💡 Considera ajustar GROUP_FILTERS en config.py")
            logger.info("💡 Para incluir todos los grupos, usa: GROUP_FILTERS = {}")
        else:
            logger.info(f"📊 Total de grupos elegibles: {len(eligible_groups)}")
        
        return eligible_groups
        
    except Exception as e:
        logger.error(f"Error obteniendo grupos del userbot: {e}")
        return []

async def should_include_group(dialog) -> bool:
    """
    Determina si un grupo o canal debe ser incluido según los filtros configurados
    """
    try:
        target_type = "Canal" if dialog.is_channel else "Grupo"
        
        # Verificar si es canal y está excluido
        if GROUP_FILTERS.get("exclude_channels", False) and dialog.is_channel:
            logger.debug(f"Excluido {dialog.title}: Es un canal y exclude_channels=True")
            return False
        
        # Verificar si está en la lista de exclusión
        if dialog.id in GROUP_FILTERS.get("exclude_group_ids", []):
            logger.debug(f"Excluido {dialog.title}: Está en lista de exclusión")
            return False
        
        # Verificar palabras clave de exclusión
        exclude_keywords = GROUP_FILTERS.get("exclude_keywords", [])
        if exclude_keywords:
            title_lower = dialog.title.lower() if dialog.title else ""
            for keyword in exclude_keywords:
                if keyword.lower() in title_lower:
                    logger.debug(f"Excluido {dialog.title}: Contiene palabra '{keyword}'")
                    return False
        
        # Verificar palabras clave de inclusión
        include_keywords = GROUP_FILTERS.get("include_keywords", [])
        if include_keywords:
            title_lower = dialog.title.lower() if dialog.title else ""
            found_keyword = False
            for keyword in include_keywords:
                if keyword.lower() in title_lower:
                    found_keyword = True
                    break
            if not found_keyword:
                logger.debug(f"Excluido {dialog.title}: No contiene palabras clave requeridas")
                return False
        
        # Verificar permisos de administrador si es requerido
        if GROUP_FILTERS.get("admin_only", False):
            try:
                # Obtener información del usuario en el grupo/canal
                participant = await userbot.get_permissions(dialog.id, 'me')
                if not participant.is_admin:
                    logger.debug(f"Excluido {dialog.title}: No es administrador")
                    return False
            except Exception as e:
                logger.debug(f"Excluido {dialog.title}: No se pudieron verificar permisos de admin: {e}")
                return False
        
        # Verificar tamaño del grupo/canal
        min_members = GROUP_FILTERS.get("min_members", 0)
        max_members = GROUP_FILTERS.get("max_members", 0)
        
        if min_members > 0 or max_members > 0:
            try:
                # Obtener información completa del chat
                chat_info = await userbot.get_entity(dialog.id)
                participants_count = getattr(chat_info, 'participants_count', 0)
                
                if min_members > 0 and participants_count < min_members:
                    logger.debug(f"Excluido {dialog.title}: Menos de {min_members} miembros ({participants_count})")
                    return False
                
                if max_members > 0 and participants_count > max_members:
                    logger.debug(f"Excluido {dialog.title}: Más de {max_members} miembros ({participants_count})")
                    return False
                    
            except Exception as e:
                logger.debug(f"No se pudo obtener información de miembros de {dialog.title}: {e}")
                # Si no se puede obtener la info, incluir el grupo/canal por defecto
        
        # Verificar permisos de escritura
        try:
            permissions = await userbot.get_permissions(dialog.id, 'me')
            
            # Para canales, verificar si puede enviar mensajes
            if dialog.is_channel:
                # En canales, solo los admins pueden escribir generalmente
                if not (permissions.is_admin or permissions.post_messages or permissions.send_messages):
                    logger.debug(f"Excluido {dialog.title}: Sin permisos de escritura en canal")
                    return False
            else:
                # Para grupos, verificar permisos normales de envío
                if not permissions.send_messages:
                    logger.debug(f"Excluido {dialog.title}: Sin permisos de escritura en grupo")
                    return False
                    
        except Exception as e:
            logger.debug(f"No se pudieron verificar permisos de escritura en {dialog.title}: {e}")
            # Si no se pueden verificar permisos, incluir por defecto
        
        logger.debug(f"Incluido {dialog.title} ({target_type}): Pasó todos los filtros")
        return True
        
    except Exception as e:
        logger.error(f"Error aplicando filtros al {target_type.lower()} {dialog.title}: {e}")
        return False

async def initialize_target_groups():
    """
    Inicializa la lista de grupos de destino según la configuración
    """
    global TARGET_GROUP_IDS
    
    try:
        if AUTO_GET_GROUPS:
            logger.info("🔄 Configuración: Obtener grupos automáticamente")
            TARGET_GROUP_IDS = await get_groups_from_userbot()
            
            if not TARGET_GROUP_IDS:
                logger.warning("⚠️ No se encontraron grupos elegibles")
                logger.info("💡 Puedes ajustar los filtros en config.py")
            else:
                logger.info(f"✅ {len(TARGET_GROUP_IDS)} grupos configurados para reenvío")
                
        else:
            logger.info("🔄 Configuración: Usar lista manual de grupos")
            TARGET_GROUP_IDS = MANUAL_GROUP_IDS.copy()
            
            if not TARGET_GROUP_IDS:
                logger.warning("⚠️ Lista manual de grupos está vacía")
            else:
                logger.info(f"✅ {len(TARGET_GROUP_IDS)} grupos configurados manualmente")
        
        # Detectar grupos problemáticos si está habilitado
        if SECURITY_SETTINGS.get("auto_detect_bot_groups", True) and TARGET_GROUP_IDS:
            await detect_problematic_groups()
            
            if PROBLEMATIC_GROUPS:
                valid_count = len([gid for gid in TARGET_GROUP_IDS if gid not in PROBLEMATIC_GROUPS])
                logger.info(f"📊 Grupos válidos: {valid_count}, Problemáticos: {len(PROBLEMATIC_GROUPS)}")
            else:
                logger.info("✅ Todos los grupos son válidos (sin bots)")
                
    except Exception as e:
        logger.error(f"Error inicializando grupos de destino: {e}")
        TARGET_GROUP_IDS = []

async def refresh_target_groups():
    """
    Actualiza la lista de grupos de destino (útil para refrescar sin reiniciar)
    """
    logger.info("🔄 Actualizando lista de grupos de destino...")
    await initialize_target_groups()
    return len(TARGET_GROUP_IDS)

async def get_groups_summary() -> str:
    """
    Genera un resumen de los grupos de destino configurados
    """
    try:
        if not TARGET_GROUP_IDS:
            return "❌ No hay grupos configurados"
        
        summary = f"📊 **Grupos de Destino Configurados**: {len(TARGET_GROUP_IDS)}\n\n"
        
        # Obtener información de cada grupo
        for i, group_id in enumerate(TARGET_GROUP_IDS[:10], 1):  # Limitar a 10 para no saturar
            try:
                entity = await userbot.get_entity(group_id)
                title = getattr(entity, 'title', 'Grupo sin título')
                participants_count = getattr(entity, 'participants_count', 'N/A')
                
                summary += f"{i}. **{title}**\n"
                summary += f"   ID: `{group_id}`\n"
                summary += f"   Miembros: {participants_count}\n\n"
                
            except Exception as e:
                summary += f"{i}. **Grupo No Accesible**\n"
                summary += f"   ID: `{group_id}`\n"
                summary += f"   Error: {str(e)[:50]}...\n\n"
        
        if len(TARGET_GROUP_IDS) > 10:
            summary += f"... y {len(TARGET_GROUP_IDS) - 10} grupos más\n\n"
        
        # Configuración actual
        mode = "Automático" if AUTO_GET_GROUPS else "Manual"
        summary += f"🔧 **Modo**: {mode}\n"
        
        if AUTO_GET_GROUPS:
            summary += "⚙️ **Filtros activos**:\n"
            if GROUP_FILTERS.get("admin_only"):
                summary += "• Solo grupos donde soy admin\n"
            if GROUP_FILTERS.get("exclude_keywords"):
                summary += f"• Excluir: {', '.join(GROUP_FILTERS['exclude_keywords'])}\n"
            if GROUP_FILTERS.get("include_keywords"):
                summary += f"• Incluir: {', '.join(GROUP_FILTERS['include_keywords'])}\n"
            if GROUP_FILTERS.get("min_members", 0) > 0:
                summary += f"• Mínimo {GROUP_FILTERS['min_members']} miembros\n"
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generando resumen de grupos: {e}")
        return f"❌ Error obteniendo información de grupos: {e}"

# ==================== FUNCIONES PRINCIPALES ====================

async def start_bot():
    """Inicia el bot"""
    try:
        await bot.start(bot_token=BOT_TOKEN)
        logger.info("Bot iniciado correctamente")
        
        # Obtener información del bot
        bot_info = await bot.get_me()
        logger.info(f"Bot conectado como: @{bot_info.username}")
        
    except Exception as e:
        logger.error(f"Error iniciando bot: {e}")
        raise

async def start_userbot():
    """Inicia el userbot"""
    try:
        await userbot.start()
        logger.info("Userbot iniciado correctamente")
        
        # Obtener información del userbot
        userbot_info = await userbot.get_me()
        logger.info(f"Userbot conectado como: @{userbot_info.username}")
        
        # Inicializar grupos de destino
        await initialize_target_groups()
        
    except Exception as e:
        logger.error(f"Error iniciando userbot: {e}")
        raise

async def main():
    """Función principal que ejecuta ambos clientes"""
    try:
        logger.info("=== INICIANDO SISTEMA HÍBRIDO DE REENVÍO ===")
        
        # Verificar configuración
        if API_ID == 12345678 or API_HASH == "tu_api_hash_aquí" or BOT_TOKEN == "tu_bot_token_aquí":
            logger.error("⚠️ CONFIGURACIÓN INCOMPLETA")
            logger.error("Por favor, configura API_ID, API_HASH y BOT_TOKEN")
            return
        
        # Mostrar configuración de grupos
        if AUTO_GET_GROUPS:
            logger.info("🔧 Configuración: Obtener grupos automáticamente del userbot")
        else:
            logger.info("🔧 Configuración: Usar lista manual de grupos")
            if not MANUAL_GROUP_IDS:
                logger.warning("⚠️ Lista manual de grupos vacía")
        
        # Mostrar configuración de acceso
        if PUBLIC_ACCESS:
            logger.info("🌐 Configuración: Acceso público activado - Cualquier usuario puede usar el bot")
            if SECURITY_SETTINGS.get("max_messages_per_hour", 0) > 0:
                logger.info(f"⏱️ Límite de velocidad: {SECURITY_SETTINGS['max_messages_per_hour']} mensajes/hora")
        else:
            logger.info("🔒 Configuración: Acceso privado - Solo usuarios autorizados")
            logger.info(f"✅ Usuarios autorizados: {len(AUTHORIZED_USERS)}")
        
        # Iniciar ambos clientes de forma concurrente
        await asyncio.gather(
            start_bot(),
            start_userbot()
        )
        
        logger.info("✅ Sistema híbrido iniciado correctamente")
        logger.info("🤖 Bot y userbot ejecutándose simultáneamente")
        
        # Eliminar la ejecución indefinida para que el bot se apague tras el reenvío
        # await asyncio.gather(
        #     bot.run_until_disconnected(),
        #     userbot.run_until_disconnected()
        # )
        logger.info("⏹️ Esperando reenvío, el sistema se apagará tras reenviar el mensaje.")
        while True:
            await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        logger.info("Cerrando sistema...")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
    finally:
        logger.info("Sistema cerrado")

# ==================== PUNTO DE ENTRADA ====================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔴 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"🔴 Error fatal: {e}")

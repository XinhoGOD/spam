#!/usr/bin/env python3
"""
Script de Testing para Bot Híbrido de Reenvío
==============================================

Este script realiza pruebas básicas para verificar que el bot esté funcionando correctamente.
Útil para validar configuración antes del deployment en Railway.

Autor: Experto en Python/Telethon
Fecha: 7 de julio de 2025
"""

import asyncio
import logging
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_bot_connection():
    """Prueba la conexión del bot oficial"""
    try:
        from config_railway import API_ID, API_HASH, BOT_TOKEN
        
        logger.info("🔍 Probando conexión del bot oficial...")
        bot = TelegramClient('test_bot_session', API_ID, API_HASH)
        
        await bot.start(bot_token=BOT_TOKEN)
        me = await bot.get_me()
        logger.info(f"✅ Bot conectado: @{me.username} (ID: {me.id})")
        
        await bot.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error conectando bot: {e}")
        return False

async def test_userbot_connection():
    """Prueba la conexión del userbot con SESSION_STRING"""
    try:
        from config_railway import API_ID, API_HASH, SESSION_STRING
        
        if not SESSION_STRING:
            logger.warning("⚠️ SESSION_STRING no configurado - saltando prueba de userbot")
            return False
            
        logger.info("🔍 Probando conexión del userbot...")
        userbot = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        
        await userbot.start()
        me = await userbot.get_me()
        logger.info(f"✅ Userbot conectado: @{me.username} (ID: {me.id})")
        
        # Contar grupos disponibles
        dialogs = await userbot.get_dialogs()
        groups = [d for d in dialogs if d.is_group]
        channels = [d for d in dialogs if d.is_channel and not d.is_group]
        
        logger.info(f"📊 Grupos disponibles: {len(groups)}")
        logger.info(f"📊 Canales disponibles: {len(channels)}")
        
        # Mostrar algunos grupos (primeros 5)
        if groups:
            logger.info("📋 Primeros grupos encontrados:")
            for i, group in enumerate(groups[:5]):
                logger.info(f"  {i+1}. {group.name} (ID: {group.id})")
        
        await userbot.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error conectando userbot: {e}")
        return False

async def test_environment_variables():
    """Verifica que todas las variables de entorno estén configuradas"""
    logger.info("🔍 Verificando variables de entorno...")
    
    required_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN']
    optional_vars = ['SESSION_STRING', 'FORWARD_DELAY', 'DEBUG_MODE', 'PUBLIC_ACCESS']
    
    all_good = True
    
    # Variables requeridas
    for var in required_vars:
        value = os.environ.get(var, '')
        if value:
            logger.info(f"✅ {var}: {'*' * min(len(value), 20)}")
        else:
            logger.error(f"❌ {var}: NO CONFIGURADA")
            all_good = False
    
    # Variables opcionales
    for var in optional_vars:
        value = os.environ.get(var, '')
        if value:
            logger.info(f"✅ {var}: {'*' * min(len(value), 20)}")
        else:
            logger.info(f"ℹ️ {var}: No configurada (opcional)")
    
    return all_good

async def test_config_import():
    """Prueba que se pueda importar la configuración correctamente"""
    try:
        logger.info("🔍 Probando importación de configuración...")
        
        # Intentar importar config_railway
        try:
            from config_railway import (
                API_ID, API_HASH, BOT_TOKEN, SESSION_STRING,
                AUTO_GET_GROUPS, FORWARD_DELAY, DEBUG_MODE
            )
            logger.info("✅ config_railway.py importado correctamente")
            logger.info(f"  - API_ID: {API_ID}")
            logger.info(f"  - AUTO_GET_GROUPS: {AUTO_GET_GROUPS}")
            logger.info(f"  - FORWARD_DELAY: {FORWARD_DELAY}")
            logger.info(f"  - DEBUG_MODE: {DEBUG_MODE}")
            return True
        except ImportError as e:
            logger.error(f"❌ Error importando config_railway.py: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error general en importación: {e}")
        return False

async def run_all_tests():
    """Ejecuta todas las pruebas"""
    logger.info("🚀 Iniciando pruebas del bot híbrido...")
    logger.info("=" * 50)
    
    results = {
        'environment': await test_environment_variables(),
        'config_import': await test_config_import(),
        'bot_connection': await test_bot_connection(),
        'userbot_connection': await test_userbot_connection()
    }
    
    logger.info("=" * 50)
    logger.info("📊 RESUMEN DE PRUEBAS:")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    logger.info(f"\n🎯 Resultado: {passed_tests}/{total_tests} pruebas pasaron")
    
    if passed_tests == total_tests:
        logger.info("🎉 ¡Todas las pruebas pasaron! El bot está listo para deployment.")
    elif results['bot_connection'] and results['config_import']:
        logger.info("⚠️ El bot básico funciona, pero hay problemas con el userbot.")
        logger.info("   El sistema funcionará en modo 'solo-bot' si es necesario.")
    else:
        logger.error("❌ Hay problemas críticos que deben resolverse antes del deployment.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        # Limpiar archivos de sesión de prueba
        import os
        test_session_files = ['test_bot_session.session']
        for file in test_session_files:
            if os.path.exists(file):
                os.remove(file)
                
        # Ejecutar pruebas
        result = asyncio.run(run_all_tests())
        
        # Limpiar archivos de sesión de prueba nuevamente
        for file in test_session_files:
            if os.path.exists(file):
                os.remove(file)
        
        exit(0 if result else 1)
        
    except KeyboardInterrupt:
        logger.info("❌ Pruebas interrumpidas por el usuario")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Error ejecutando pruebas: {e}")
        exit(1)

#!/usr/bin/env python3
"""
Regenerador de SESSION_STRING para Railway - Versión Mejorada
============================================================

Script mejorado para generar un SESSION_STRING válido y funcional para Railway.
Esta versión incluye validaciones adicionales y mejor manejo de errores.

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

# Configuración (usar las mismas credenciales que en Railway)
API_ID = 22252541
API_HASH = "91c195d7deb3fb56ee7a95eaeb13e2fb"

async def generar_session_string():
    """Genera un SESSION_STRING válido para Railway"""
    
    print("🚀 GENERADOR DE SESSION_STRING PARA RAILWAY")
    print("=" * 50)
    print("⚠️  IMPORTANTE: Usa el mismo número de teléfono que quieres")
    print("    usar para el reenvío de mensajes en Railway.")
    print("=" * 50)
    
    # Crear cliente temporal para obtener la sesión
    session_name = 'temp_session_for_railway'
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        logger.info("🔄 Conectando a Telegram...")
        await client.start()
        
        # Obtener información del usuario
        me = await client.get_me()
        logger.info(f"✅ Conectado como: @{me.username} ({me.first_name})")
        logger.info(f"📱 Número: {me.phone}")
        logger.info(f"🆔 ID: {me.id}")
        
        # Verificar que la conexión sea estable
        logger.info("🔍 Verificando estabilidad de la conexión...")
        
        # Obtener algunos diálogos para verificar que funciona
        dialogs = await client.get_dialogs(limit=5)
        logger.info(f"📋 Diálogos obtenidos: {len(dialogs)}")
        
        # Contar grupos disponibles
        all_dialogs = await client.get_dialogs()
        groups = [d for d in all_dialogs if d.is_group]
        channels = [d for d in all_dialogs if d.is_channel and not d.is_group]
        
        logger.info(f"📊 Estadísticas de tu cuenta:")
        logger.info(f"   • Grupos: {len(groups)}")
        logger.info(f"   • Canales: {len(channels)}")
        logger.info(f"   • Total diálogos: {len(all_dialogs)}")
        
        if len(groups) > 0:
            logger.info("📋 Primeros grupos encontrados:")
            for i, group in enumerate(groups[:5]):
                logger.info(f"   {i+1}. {group.name}")
        
        # Obtener el string de sesión
        session_string = client.session.save()
        
        if not session_string:
            raise Exception("No se pudo generar el session string")
        
        logger.info(f"✅ SESSION_STRING generado exitosamente!")
        logger.info(f"📏 Longitud: {len(session_string)} caracteres")
        
        print("\n" + "=" * 60)
        print("🎉 ¡SESSION_STRING GENERADO EXITOSAMENTE!")
        print("=" * 60)
        print(f"SESSION_STRING={session_string}")
        print("=" * 60)
        print("\n📋 INSTRUCCIONES PARA RAILWAY:")
        print("1. Copia el SESSION_STRING completo (toda la línea)")
        print("2. Ve a tu proyecto en Railway")
        print("3. Ve a Variables → Add New Variable")
        print("4. Nombre: SESSION_STRING")
        print("5. Valor: [pega aquí el string completo]")
        print("6. Guarda y haz redeploy")
        print("\n⚠️  IMPORTANTE:")
        print("• No compartas este SESSION_STRING con nadie")
        print("• Es equivalente a tu contraseña de Telegram")
        print("• Si se compromete, revócalo en: Telegram → Configuración → Sesiones")
        
        # Verificar que el session string funciona
        logger.info("\n🔍 Verificando que el SESSION_STRING funciona...")
        test_client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        
        try:
            await test_client.connect()
            
            if await test_client.is_user_authorized():
                test_me = await test_client.get_me()
                logger.info(f"✅ Verificación exitosa: @{test_me.username}")
                logger.info("🎯 El SESSION_STRING está listo para Railway!")
            else:
                logger.warning("⚠️ Advertencia: is_user_authorized() devolvió False")
                logger.info("🔍 Intentando get_me() de todas formas...")
                
                try:
                    test_me = await test_client.get_me()
                    logger.info(f"✅ ¡Funciona! Usuario: @{test_me.username}")
                    logger.info("📝 Nota: Algunos casos devuelven False en is_user_authorized pero funcionan")
                except Exception as e:
                    logger.error(f"❌ Error en verificación: {e}")
                    raise Exception("El SESSION_STRING generado no funciona correctamente")
            
            await test_client.disconnect()
            
        except Exception as e:
            logger.error(f"❌ Error verificando SESSION_STRING: {e}")
            raise
        
        await client.disconnect()
        
        # Limpiar archivos de sesión temporales
        session_files = [f'{session_name}.session']
        for file in session_files:
            if os.path.exists(file):
                os.remove(file)
                logger.info(f"🧹 Limpiado: {file}")
        
        return session_string
        
    except Exception as e:
        logger.error(f"❌ Error generando SESSION_STRING: {e}")
        
        # Limpiar archivos en caso de error
        session_files = [f'{session_name}.session']
        for file in session_files:
            if os.path.exists(file):
                os.remove(file)
        
        raise
    
    finally:
        if client.is_connected():
            await client.disconnect()

async def main():
    """Función principal"""
    try:
        session_string = await generar_session_string()
        
        # Guardar en archivo local también (backup)
        with open('session_string_backup.txt', 'w', encoding='utf-8') as f:
            f.write(f"SESSION_STRING={session_string}\n")
            f.write(f"# Generado el: {__import__('datetime').datetime.now()}\n")
            f.write(f"# Para: API_ID={API_ID}\n")
        
        logger.info("💾 SESSION_STRING guardado en 'session_string_backup.txt'")
        
        print("\n🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        print("📁 El SESSION_STRING también se guardó en 'session_string_backup.txt'")
        
    except KeyboardInterrupt:
        logger.info("❌ Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en el proceso: {e}")
        print("\n❌ Hubo un error. Posibles soluciones:")
        print("1. Verificar conexión a internet")
        print("2. Verificar que API_ID y API_HASH sean correctos")
        print("3. Intentar en unos minutos (posible límite de rate)")
        print("4. Verificar que el número de teléfono sea válido")

if __name__ == "__main__":
    print("🔐 GENERADOR DE SESSION_STRING PARA RAILWAY")
    print("Este script te ayudará a generar un SESSION_STRING válido.")
    print("Necesitarás tu número de teléfono y acceso a los códigos SMS.")
    
    confirm = input("\n¿Estás listo para continuar? (s/n): ").lower().strip()
    if confirm in ['s', 'si', 'sí', 'y', 'yes']:
        asyncio.run(main())
    else:
        print("❌ Proceso cancelado.")

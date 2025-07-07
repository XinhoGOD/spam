#!/usr/bin/env python3
"""
SOLUCIÓN: Generador de Session String para Railway
================================================

PROBLEMA IDENTIFICADO:
- El userbot es tu cuenta personal de Telegram
- Railway no puede autenticar tu cuenta interactivamente
- Sin userbot, el bot no puede reenviar mensajes

SOLUCIÓN:
- Genera un SESSION_STRING una vez en tu computadora
- Úsalo como variable de entorno en Railway
- Tu cuenta estará "preautenticada" en Railway

PASOS:
1. Ejecuta este script EN TU COMPUTADORA
2. Se autenticará con tu cuenta personal
3. Generará un SESSION_STRING
4. Úsalo en Railway como variable de entorno

IMPORTANTE: Tu cuenta personal funcionará en Railway sin necesidad de autenticación manual
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Tu configuración actual
API_ID = 22252541
API_HASH = "91c195d7deb3fb56ee7a95eaeb13e2fb"

async def generate_session_for_railway():
    """
    Genera un session string para tu cuenta personal de Telegram
    que funcionará en Railway
    """
    try:
        print("🔐 GENERADOR DE SESSION STRING PARA RAILWAY")
        print("=" * 60)
        print()
        print("🎯 OBJETIVO: Preautenticar tu cuenta personal para Railway")
        print("📱 TU CUENTA: Usarás tu número y código de verificación")
        print("🚀 RESULTADO: Un STRING que funcionará en Railway")
        print()
        print("⚠️  IMPORTANTE: Este proceso usa tu cuenta personal de Telegram")
        print("   - Es seguro y solo se hace una vez")
        print("   - El SESSION_STRING es como una 'contraseña' de sesión")
        print("   - Manténlo privado y seguro")
        print()
        
        # Crear cliente con StringSession vacío
        print("🔄 Iniciando cliente de Telegram...")
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        
        print("📱 Iniciando proceso de autenticación con tu cuenta...")
        print("   (Se te pedirá tu número de teléfono y código de verificación)")
        print()
        
        # Iniciar sesión (pedirá teléfono y código)
        await client.start()
        
        # Verificar que la autenticación fue exitosa
        me = await client.get_me()
        
        print("✅ ¡AUTENTICACIÓN EXITOSA!")
        print(f"👤 Cuenta: {me.first_name} {me.last_name or ''}")
        print(f"📞 Teléfono: {me.phone}")
        print(f"🆔 Username: @{me.username or 'sin_username'}")
        print(f"🔢 ID: {me.id}")
        print()
        
        # Generar session string
        session_string = client.session.save()
        
        print("🎉 ¡SESSION_STRING GENERADO EXITOSAMENTE!")
        print("=" * 60)
        print()
        print("📋 COPIA ESTA LÍNEA COMPLETA PARA RAILWAY:")
        print()
        print(f"SESSION_STRING={session_string}")
        print()
        print("=" * 60)
        print()
        print("📝 INSTRUCCIONES PARA RAILWAY:")
        print()
        print("1. Ve a tu proyecto en Railway")
        print("2. Selecciona 'Variables' en el panel izquierdo")
        print("3. Haz clic en '+ New Variable'")
        print("4. Agrega:")
        print("   • Variable name: SESSION_STRING")
        print("   • Variable value: (el string de arriba)")
        print("5. Haz clic en 'Add'")
        print("6. Redeploy tu aplicación")
        print()
        print("🔒 SEGURIDAD:")
        print("• Guarda el SESSION_STRING en un lugar seguro")
        print("• No lo compartas con nadie")
        print("• Si se compromete, puedes cerrar sesiones en Telegram")
        print()
        print("✅ RESULTADO:")
        print("• Tu cuenta personal funcionará en Railway")
        print("• El bot podrá reenviar mensajes a tus grupos")
        print("• No necesitarás autenticación manual en Railway")
        
        await client.disconnect()
        
        print()
        print("🎯 ¿QUÉ SIGUE?")
        print("1. Configurar SESSION_STRING en Railway")
        print("2. Deploar tu bot")
        print("3. ¡Tu cuenta personal funcionará automáticamente!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("💡 POSIBLES SOLUCIONES:")
        print("• Verifica que API_ID y API_HASH sean correctos")
        print("• Asegúrate de tener conexión a internet")
        print("• Usa un número de teléfono válido registrado en Telegram")
        print("• Si tienes 2FA, tendrás que ingresarlo también")

if __name__ == "__main__":
    try:
        print("⚠️  AVISO: Este script autenticará tu cuenta PERSONAL de Telegram")
        print("🔐 Se generará un SESSION_STRING para usar en Railway")
        print()
        
        confirm = input("¿Continuar? (y/N): ").strip().lower()
        if confirm in ['y', 'yes', 'sí', 'si']:
            asyncio.run(generate_session_for_railway())
        else:
            print("❌ Proceso cancelado por el usuario")
            
    except KeyboardInterrupt:
        print("\n🔴 Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"🔴 Error fatal: {e}")

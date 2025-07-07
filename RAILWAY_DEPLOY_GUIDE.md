# Guía de Deployment en Railway 🚀

## 📋 Resumen de Cambios Realizados

Tu bot ha sido optimizado para funcionar en Railway con las siguientes mejoras:

### ✅ Problemas Solucionados

1. **Autenticación del Userbot**: Ahora usa SESSION_STRING en lugar de archivos de sesión
2. **Configuración de Variables**: Sistema robusto de variables de entorno
3. **Fallback Mode**: Si no hay userbot, funciona como bot básico
4. **Manejo de Errores**: Mejor gestión de errores en entornos de producción

### 📁 Archivos Modificados/Creados

- `telegram_forwarder_railway.py` - Versión optimizada para Railway
- `config_railway.py` - Configuración mejorada con variables de entorno
- `generate_session.py` - Script para generar SESSION_STRING
- `Procfile` - Actualizado para usar la nueva versión
- `requirements.txt` - Dependencias optimizadas
- `.env.example` - Ejemplo de variables de entorno

## 🚀 Pasos para Deploy en Railway

### 1. Preparación del Userbot (Recomendado)

Para que tu bot pueda reenviar mensajes, necesitas un SESSION_STRING:

```bash
# Ejecuta localmente (solo una vez)
python generate_session.py
```

Este script te pedirá:
- Tu número de teléfono
- Código de verificación (SMS/Telegram)
- Te generará un SESSION_STRING

### 2. Configurar Variables de Entorno en Railway

Ve a tu proyecto en Railway → Variables → Environment Variables y agrega:

**Variables Obligatorias:**
```
API_ID=22252541
API_HASH=91c195d7deb3fb56ee7a95eaeb13e2fb
BOT_TOKEN=8157414882:AAHYfRdqn8IG770rDlROnBvFwi78k_KmGwA
```

**Variables del Userbot (para reenvío):**
```
SESSION_STRING=(el string generado con generate_session.py)
PHONE_NUMBER=+1234567890
```

**Variables Opcionales:**
```
FORWARD_DELAY=30.0
DEBUG_MODE=false
PUBLIC_ACCESS=true
```

### 3. Deploy en Railway

1. Conecta tu repositorio a Railway
2. Railway detectará automáticamente el `Procfile`
3. Se instalarán las dependencias de `requirements.txt`
4. El bot se ejecutará automáticamente

## 🤖 Modos de Funcionamiento

### Modo Completo (Con Userbot)
- ✅ Reenvío a grupos automático
- ✅ Detección automática de grupos
- ✅ Todas las funciones disponibles

### Modo Básico (Solo Bot)
- ✅ Interfaz de usuario funcional
- ❌ Sin reenvío a grupos
- ℹ️ Mensaje informativo al usuario

## 📊 Funcionalidades Disponibles

### Para Usuarios Normales:
- Interfaz con botones interactivos
- Captura de mensajes para reenvío
- Notificaciones de estado

### Para Administradores:
- Panel de estado del sistema
- Actualización de grupos
- Estadísticas de reenvío
- Control de acceso

## 🔧 Configuración Avanzada

### Filtros de Grupos
Edita `GROUP_FILTERS` en `config_railway.py`:

```python
GROUP_FILTERS = {
    "admin_only": False,           # Solo grupos donde soy admin
    "exclude_keywords": ["bot"],   # Excluir grupos con estas palabras
    "include_keywords": [],        # Solo grupos con estas palabras
    "min_members": 10,            # Mínimo de miembros
    "max_members": 0,             # Máximo de miembros (0 = sin límite)
    "exclude_channels": False,     # Excluir canales
    "exclude_group_ids": []       # IDs específicos a excluir
}
```

### Control de Acceso
```python
PUBLIC_ACCESS = True              # Acceso público
AUTHORIZED_USERS = [123456789]    # IDs de usuarios autorizados

SECURITY_SETTINGS = {
    "max_messages_per_hour": 10,  # Límite de mensajes por hora
    "blocked_users": [],          # Usuarios bloqueados
    "log_all_messages": True,     # Registrar actividad
    "notify_owner": True          # Notificar al dueño
}
```

## 🐛 Solución de Problemas

### Error: "Userbot no disponible"
- Verifica que SESSION_STRING esté configurado
- Regenera SESSION_STRING con `generate_session.py`
- El userbot puede funcionar sin esto en modo básico

### Error: "No se encontraron grupos"
- Ajusta GROUP_FILTERS para ser menos restrictivo
- Usa MANUAL_GROUP_IDS para especificar grupos manualmente
- Verifica que el userbot esté en grupos/canales

### Bot no responde
- Verifica BOT_TOKEN en variables de entorno
- Checa los logs en Railway
- Asegúrate de que el bot esté iniciado en BotFather

## 📈 Monitoreo

### Logs en Railway
```bash
# Ver logs en tiempo real
railway logs --follow
```

### Comandos del Bot
- `/start` - Iniciar bot
- Botones interactivos para todas las funciones

## 🔒 Seguridad

### Variables Sensibles
- Nunca hagas commit de SESSION_STRING
- Usa variables de entorno en Railway
- Cambia tokens si se comprometen

### Best Practices
- SESSION_STRING solo en variables de entorno
- Backup de SESSION_STRING en lugar seguro
- Monitoreo regular de logs

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs en Railway
2. Verifica variables de entorno
3. Prueba localmente primero
4. Contacta soporte si es necesario

---

¡Tu bot está listo para Railway! 🎉

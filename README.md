# 🤖 Bot Híbrido de Reenvío - Guía Completa

## 📋 Descripción

Bot híbrido que combina:
- **Bot oficial** (interfaz con botones) 
- **Userbot** (tu cuenta personal para reenvío)

## 🚀 Deployment en Railway

### 1. **Variables de Entorno Requeridas:**

```bash
# OBLIGATORIAS:
API_ID=22252541
API_HASH=91c195d7deb3fb56ee7a95eaeb13e2fb
BOT_TOKEN=8157414882:AAHYfRdqn8IG770rDlROnBvFwi78k_KmGwA

# CRÍTICA - Tu cuenta personal:
SESSION_STRING=(generado con generar_session_para_railway.py)

# OPCIONALES:
FORWARD_DELAY=30.0
DEBUG_MODE=false
PUBLIC_ACCESS=true
```

### 2. **Generar SESSION_STRING:**

```bash
# En tu computadora (solo una vez):
python generar_session_para_railway.py

# Te autenticas con tu número y código SMS
# Obtienes el SESSION_STRING para Railway
```

### 3. **Archivos principales:**

- `telegram_forwarder_railway.py` - Bot optimizado para Railway
- `config_railway.py` - Configuración con variables de entorno
- `Procfile` - Configuración de deployment
- `requirements.txt` - Dependencias Python

## 🔧 Funcionalidades

### Para usuarios:
- ✅ Interfaz con botones interactivos
- ✅ Captura y confirmación de mensajes
- ✅ Reenvío automático a grupos

### Para administradores:
- ✅ Panel de estado del sistema
- ✅ Gestión de grupos
- ✅ Estadísticas de reenvío
- ✅ Configuración de acceso

## ⚙️ Configuración

### Filtros de grupos (config_railway.py):
```python
GROUP_FILTERS = {
    "admin_only": False,           # Solo grupos donde eres admin
    "exclude_keywords": [],        # Excluir grupos con estas palabras
    "include_keywords": [],        # Solo grupos con estas palabras
    "min_members": 1,             # Mínimo de miembros
    "exclude_channels": False      # Incluir/excluir canales
}
```

### Control de acceso:
```python
PUBLIC_ACCESS = True              # Acceso público vs privado
AUTHORIZED_USERS = []            # IDs de usuarios autorizados
SECURITY_SETTINGS = {
    "max_messages_per_hour": 0,  # Límite de mensajes
    "blocked_users": []          # Usuarios bloqueados
}
```

## 🔒 Seguridad

### SESSION_STRING:
- 🔐 **Qué es:** Credencial de tu cuenta personal
- ⚠️ **Importante:** Mantener privado y seguro
- 🔄 **Revocable:** En Telegram → Configuración → Sesiones activas

### Mejores prácticas:
- Solo configurar SESSION_STRING como variable de entorno
- Nunca incluir en código fuente
- Regenerar si se compromete
- Monitorear logs regularmente

## 🐛 Solución de Problemas

### "Userbot no disponible":
- Verificar SESSION_STRING en variables de entorno
- Regenerar SESSION_STRING si es necesario
- Verificar que no esté cortado/incompleto

### "No se encontraron grupos":
- Ajustar GROUP_FILTERS (menos restrictivos)
- Verificar que tu cuenta esté en grupos
- Usar MANUAL_GROUP_IDS si es necesario

### Bot no responde:
- Verificar BOT_TOKEN
- Chequear logs en Railway
- Confirmar que el bot esté activo en BotFather

## 📈 Monitoreo

### Logs exitosos:
```
✅ Userbot conectado con session string: @tu_username
📊 Grupos configurados: X
🔄 Sistema ejecutándose - esperando mensajes...
```

### Comandos del bot:
- `/start` - Iniciar interacción
- Botones interactivos para todas las funciones

## 📁 Estructura final del proyecto:

```
├── telegram_forwarder_railway.py  # Bot principal
├── config_railway.py              # Configuración  
├── generar_session_para_railway.py # Generador de SESSION_STRING
├── Procfile                        # Configuración Railway
├── requirements.txt                # Dependencias
├── runtime.txt                     # Versión de Python
├── .gitignore                      # Archivos a ignorar
├── .env.example                    # Ejemplo de variables
└── README.md                       # Esta documentación
```

## 🚀 Deployment Checklist:

- [x] Código subido a GitHub
- [x] Proyecto conectado en Railway  
- [x] Variables de entorno configuradas
- [x] SESSION_STRING generado y configurado
- [x] Deployment exitoso
- [x] Bot respondiendo en Telegram

---

🎉 **¡Tu bot está listo para funcionar en Railway!**

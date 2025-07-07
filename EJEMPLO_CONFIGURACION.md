# 📋 Ejemplo de Configuración para Railway

## 🔧 Configuración de Grupos

### **Modo Automático (Recomendado)**

El bot obtiene automáticamente los grupos del userbot. Solo necesitas:

1. **Agregar el userbot a los grupos** donde quieres reenviar
2. **Dar permisos de administrador** al userbot (recomendado)
3. **Asegurarte de que los grupos no contengan bots**

### **Modo Manual (Opcional)**

Si prefieres configurar grupos manualmente:

#### **Método 1: Usando @userinfobot**
1. Agrega tu bot al grupo donde quieres reenviar
2. Envía cualquier mensaje al grupo
3. Ve a [@userinfobot](https://t.me/userinfobot)
4. Reenvía el mensaje que enviaste al grupo
5. El bot te mostrará información incluyendo el ID del chat
6. El ID será algo como `-1001234567890`

#### **Método 2: Usando @RawDataBot**
1. Agrega [@RawDataBot](https://t.me/RawDataBot) al grupo
2. Envía un mensaje al grupo
3. El bot te mostrará el `chat_id` que necesitas

### **Paso 2: Configurar en config_railway.py**

Edita el archivo `config_railway.py` y agrega los IDs de tus grupos:

```python
# LISTA MANUAL (obligatorio para Railway)
MANUAL_GROUP_IDS = [
    -1001234567890,  # Grupo de ejemplo 1
    -1001987654321,  # Grupo de ejemplo 2
    -1001122334455,  # Grupo de ejemplo 3
]
```

### **Paso 3: Verificar Permisos**

Asegúrate de que tu bot tenga permisos en todos los grupos:
- ✅ **Enviar mensajes**
- ✅ **Reenviar mensajes** (si aplica)
- ✅ **Leer mensajes**

## 🚀 Ejemplo Completo

```python
# config_railway.py
import os

# Credenciales de Telegram
API_ID = int(os.environ.get('API_ID', 12345678))
API_HASH = os.environ.get('API_HASH', "tu_api_hash_aquí")
BOT_TOKEN = os.environ.get('BOT_TOKEN', "tu_bot_token_aquí")

# Configuración de grupos
AUTO_GET_GROUPS = False  # Deshabilitado para Railway
MANUAL_GROUP_IDS = [
    -1001234567890,  # Tu grupo principal
    -1001987654321,  # Tu grupo secundario
]

# Configuración de velocidad
FORWARD_DELAY = 30.0  # 30 segundos entre reenvíos

# Configuración de acceso
PUBLIC_ACCESS = True
DEBUG_MODE = False
```

## ⚠️ Notas Importantes

1. **Los IDs de grupos siempre empiezan con `-100`**
2. **No uses IDs de usuarios individuales**
3. **El bot debe estar agregado a todos los grupos**
4. **Los grupos deben ser públicos o el bot debe ser admin**

## 🔍 Verificar Configuración

Una vez configurado, puedes verificar que todo esté correcto:

1. Ejecuta el bot
2. Envía `/start`
3. Presiona "📊 Ver Grupos Configurados"
4. Deberías ver la lista de grupos configurados

## 🆘 Solución de Problemas

### **Error: "No hay grupos configurados"**
- Verifica que `MANUAL_GROUP_IDS` no esté vacío
- Asegúrate de que los IDs sean correctos

### **Error: "Bot no puede enviar mensajes"**
- Verifica que el bot esté agregado al grupo
- Asegúrate de que tenga permisos de administrador

### **Error: "Grupo no encontrado"**
- Verifica que el ID del grupo sea correcto
- Asegúrate de que el bot esté en el grupo 
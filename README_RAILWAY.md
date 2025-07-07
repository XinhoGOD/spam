# Bot Híbrido de Reenvío - Deploy en Railway

## 📋 Archivos a subir a Railway

### **Archivos principales:**
- `telegram_forwarder.py` - Bot principal
- `config_railway.py` - Configuración para Railway
- `requirements.txt` - Dependencias
- `Procfile` - Instrucciones para Railway
- `runtime.txt` - Versión de Python

### **Archivos que NO subir:**
- `config.py` - Contiene datos sensibles
- `*.session` - Archivos de sesión
- `*.session-journal` - Archivos de sesión

## 🔧 Configuración en Railway

### **1. Variables de Entorno**
Configurar estas variables en Railway:

```
API_ID=22252541
API_HASH=91c195d7deb3fb56ee7a95eaeb13e2fb
BOT_TOKEN=8157414882:AAHYfRdqn8IG770rDlROnBvFwi78k_KmGwA
```

### **2. Configuración de Grupos**
El bot obtiene automáticamente los grupos del userbot. Asegúrate de que:

- ✅ El userbot esté agregado a los grupos donde quieres reenviar
- ✅ El userbot tenga permisos de administrador (recomendado)
- ✅ Los grupos no contengan bots (pueden causar problemas)

**Para configurar grupos manualmente** (opcional):
```python
AUTO_GET_GROUPS = False
MANUAL_GROUP_IDS = [
    -1001234567890,  # Reemplaza con IDs reales
    -1001987654321,
]
```

### **3. Configuración de Velocidad**
- **Delay entre reenvíos:** 30 segundos (configurado para evitar límites de Telegram)
- **Manejo automático de límites:** Si se detecta un límite, pausa 10 segundos adicionales
- **Tiempo estimado:** ~2-3 minutos para reenviar a 10 grupos

### **3. Pasos para deploy:**

1. **Crear repositorio en GitHub** con estos archivos
2. **Conectar GitHub a Railway**
3. **Configurar variables de entorno**
4. **Deploy automático**

## ⚠️ Importante

- **NO subir archivos de sesión** a GitHub
- **Usar variables de entorno** para datos sensibles
- **El bot se reiniciará** automáticamente si se cae
- **Delay conservador** para evitar límites de velocidad
- **AUTENTICACIÓN AUTOMÁTICA:** El userbot usa el token del bot para autenticarse automáticamente
- **GRUPOS AUTOMÁTICOS:** El bot obtiene grupos automáticamente del userbot

## 🚀 Comandos de Railway

```bash
# Ver logs
railway logs

# Reiniciar servicio
railway restart

# Ver estado
railway status
```

## 📊 Monitoreo

- Railway proporciona logs en tiempo real
- Notificaciones por email si el servicio se cae
- Métricas de uso y rendimiento

## 🔐 Seguridad

- Las credenciales se almacenan en variables de entorno
- No se exponen en el código
- Railway encripta las variables automáticamente

## 📝 Notas importantes

- El bot creará automáticamente los archivos de sesión en Railway
- Los archivos de sesión se mantienen entre reinicios
- Si el bot se cae, Railway lo reiniciará automáticamente
- **Delay de 30 segundos** entre cada reenvío para evitar límites 
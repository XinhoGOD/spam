#!/usr/bin/env python3
"""
Validador de Deployment en Railway
==================================

Script para verificar que el bot esté funcionando correctamente en Railway.
Ejecuta una serie de validaciones básicas que se pueden usar desde logs o terminal.

Autor: Experto en Python/Telethon
Fecha: 7 de julio de 2025
"""

import os
import logging
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_environment():
    """Valida que todas las variables de entorno críticas estén presentes"""
    logger.info("🔍 Validando variables de entorno en Railway...")
    
    # Variables críticas
    critical_vars = {
        'API_ID': 'ID de la aplicación de Telegram',
        'API_HASH': 'Hash de la aplicación de Telegram', 
        'BOT_TOKEN': 'Token del bot oficial',
        'SESSION_STRING': 'Sesión del userbot (crítica para reenvío)'
    }
    
    # Variables opcionales
    optional_vars = {
        'FORWARD_DELAY': 'Retardo entre reenvíos',
        'DEBUG_MODE': 'Modo de depuración',
        'PUBLIC_ACCESS': 'Acceso público al bot',
        'PHONE_NUMBER': 'Número de teléfono (backup)'
    }
    
    missing_critical = []
    present_vars = []
    
    # Verificar variables críticas
    for var, description in critical_vars.items():
        value = os.environ.get(var, '')
        if value:
            present_vars.append(var)
            # Mostrar longitud para SESSION_STRING, primeros caracteres para otros
            if var == 'SESSION_STRING':
                logger.info(f"✅ {var}: {len(value)} caracteres")
            else:
                logger.info(f"✅ {var}: {value[:10]}...")
        else:
            missing_critical.append(var)
            logger.error(f"❌ {var}: FALTANTE - {description}")
    
    # Verificar variables opcionales
    for var, description in optional_vars.items():
        value = os.environ.get(var, '')
        if value:
            present_vars.append(var)
            logger.info(f"✅ {var}: {value}")
        else:
            logger.info(f"ℹ️ {var}: No configurada - {description}")
    
    # Resultado
    if missing_critical:
        logger.error(f"❌ Variables críticas faltantes: {', '.join(missing_critical)}")
        return False
    else:
        logger.info(f"✅ Todas las variables críticas están presentes")
        logger.info(f"📊 Total configuradas: {len(present_vars)} variables")
        return True

def validate_file_structure():
    """Valida que todos los archivos necesarios estén presentes"""
    logger.info("🔍 Validando estructura de archivos...")
    
    required_files = {
        'telegram_forwarder_railway.py': 'Script principal del bot',
        'config_railway.py': 'Configuración para Railway',
        'requirements.txt': 'Dependencias de Python',
        'Procfile': 'Configuración de proceso para Railway',
        'runtime.txt': 'Versión de Python'
    }
    
    optional_files = {
        'README.md': 'Documentación',
        '.gitignore': 'Archivos a ignorar en git',
        '.env.example': 'Ejemplo de variables de entorno'
    }
    
    missing_required = []
    present_files = []
    
    # Verificar archivos requeridos
    for file, description in required_files.items():
        if os.path.exists(file):
            present_files.append(file)
            logger.info(f"✅ {file}: Presente - {description}")
        else:
            missing_required.append(file)
            logger.error(f"❌ {file}: FALTANTE - {description}")
    
    # Verificar archivos opcionales
    for file, description in optional_files.items():
        if os.path.exists(file):
            present_files.append(file)
            logger.info(f"✅ {file}: Presente - {description}")
        else:
            logger.info(f"ℹ️ {file}: No presente - {description}")
    
    # Resultado
    if missing_required:
        logger.error(f"❌ Archivos requeridos faltantes: {', '.join(missing_required)}")
        return False
    else:
        logger.info(f"✅ Todos los archivos requeridos están presentes")
        logger.info(f"📊 Total archivos: {len(present_files)}")
        return True

def validate_procfile():
    """Valida que el Procfile esté configurado correctamente"""
    logger.info("🔍 Validando Procfile...")
    
    try:
        if not os.path.exists('Procfile'):
            logger.error("❌ Procfile no encontrado")
            return False
        
        with open('Procfile', 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        expected_content = "worker: python telegram_forwarder_railway.py"
        
        if content == expected_content:
            logger.info(f"✅ Procfile correcto: {content}")
            return True
        else:
            logger.error(f"❌ Procfile incorrecto:")
            logger.error(f"   Encontrado: {content}")
            logger.error(f"   Esperado: {expected_content}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error leyendo Procfile: {e}")
        return False

def validate_requirements():
    """Valida que requirements.txt contenga las dependencias necesarias"""
    logger.info("🔍 Validando requirements.txt...")
    
    try:
        if not os.path.exists('requirements.txt'):
            logger.error("❌ requirements.txt no encontrado")
            return False
        
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            requirements = f.read().strip().lower()
        
        required_packages = ['telethon', 'asyncio']
        optional_packages = ['python-dotenv']
        
        missing_packages = []
        present_packages = []
        
        for package in required_packages:
            if package in requirements:
                present_packages.append(package)
                logger.info(f"✅ {package}: Presente")
            else:
                missing_packages.append(package)
                logger.error(f"❌ {package}: FALTANTE")
        
        for package in optional_packages:
            if package in requirements:
                present_packages.append(package)
                logger.info(f"✅ {package}: Presente (opcional)")
            else:
                logger.info(f"ℹ️ {package}: No presente (opcional)")
        
        if missing_packages:
            logger.error(f"❌ Paquetes requeridos faltantes: {', '.join(missing_packages)}")
            return False
        else:
            logger.info(f"✅ Todas las dependencias requeridas están presentes")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error leyendo requirements.txt: {e}")
        return False

def main():
    """Función principal de validación"""
    logger.info("🚀 Iniciando validación de deployment en Railway...")
    logger.info("=" * 60)
    
    validations = {
        'Variables de entorno': validate_environment(),
        'Estructura de archivos': validate_file_structure(),
        'Configuración Procfile': validate_procfile(),
        'Dependencias requirements': validate_requirements()
    }
    
    logger.info("=" * 60)
    logger.info("📊 RESUMEN DE VALIDACIÓN:")
    
    total_validations = len(validations)
    passed_validations = sum(validations.values())
    
    for validation_name, result in validations.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"  {validation_name}: {status}")
    
    logger.info(f"\n🎯 Resultado: {passed_validations}/{total_validations} validaciones pasaron")
    
    if passed_validations == total_validations:
        logger.info("🎉 ¡Validación completa exitosa! El proyecto está listo para Railway.")
        logger.info("📋 Próximos pasos:")
        logger.info("   1. Hacer push de cualquier cambio pendiente")
        logger.info("   2. Conectar repositorio en Railway")
        logger.info("   3. Configurar variables de entorno en Railway")
        logger.info("   4. Hacer deploy")
        logger.info("   5. Verificar logs de deployment")
        return True
    else:
        logger.error("❌ Hay problemas que deben resolverse antes del deployment.")
        logger.error("📋 Acciones requeridas:")
        
        if not validations['Variables de entorno']:
            logger.error("   - Configurar variables de entorno faltantes")
        if not validations['Estructura de archivos']:
            logger.error("   - Agregar archivos requeridos faltantes")
        if not validations['Configuración Procfile']:
            logger.error("   - Corregir Procfile")
        if not validations['Dependencias requirements']:
            logger.error("   - Actualizar requirements.txt")
        
        return False

if __name__ == "__main__":
    try:
        result = main()
        exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("❌ Validación interrumpida por el usuario")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Error durante la validación: {e}")
        exit(1)

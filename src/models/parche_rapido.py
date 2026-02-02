"""
PARCHE RÁPIDO - Correcciones para Errores Comunes
==================================================

Ejecuta este script para aplicar las correcciones necesarias
"""

import os
import sys

def aplicar_parche_chromadb():
    """Corrige el error de filtros múltiples en ChromaDB"""
    
    archivo = "vector_db.py"  # O el nombre de tu archivo
    
    if not os.path.exists(archivo):
        print(f"❌ No se encuentra {archivo}")
        return False
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Parche 1: Corregir filtro en indexar_documento
    contenido_viejo = 'where={"pliego_id": pliego_id, "tipo_documento": tipo_documento}'
    contenido_nuevo = '''where={
                "$and": [
                    {"pliego_id": pliego_id},
                    {"tipo_documento": tipo_documento}
                ]
            }'''
    
    if contenido_viejo in contenido:
        contenido = contenido.replace(contenido_viejo, contenido_nuevo)
        print("✓ Corregido: filtro en indexar_documento")
    
    # Parche 2: Corregir filtro en buscar_contexto
    # Buscar el bloque completo
    buscar_viejo = '''filtros = {}
        
        if pliego_id:
            filtros["pliego_id"] = pliego_id
        
        if tipo_documento:
            filtros["tipo_documento"] = tipo_documento'''
    
    buscar_nuevo = '''# Construir filtros con operador $and si hay múltiples condiciones
        filtros = None
        condiciones = []
        
        if pliego_id:
            condiciones.append({"pliego_id": pliego_id})
        
        if tipo_documento:
            condiciones.append({"tipo_documento": tipo_documento})
        
        if len(condiciones) > 1:
            filtros = {"$and": condiciones}
        elif len(condiciones) == 1:
            filtros = condiciones[0]'''
    
    if buscar_viejo in contenido:
        contenido = contenido.replace(buscar_viejo, buscar_nuevo)
        print("✓ Corregido: filtro en buscar_contexto")
    
    # Guardar archivo corregido
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print(f"✅ Parche aplicado a {archivo}")
    return True


def aplicar_parche_windows():
    """Corrige problemas de archivos temporales en Windows"""
    
    # Puedes aplicar esto manualmente o crear un script similar
    print("\n📝 CORRECCIÓN MANUAL NECESARIA:")
    print("-" * 60)
    print("\nEn tu archivo de extracción de PDFs, busca el bloque:")
    print("""
    finally:
        if es_temporal and os.path.exists(ruta_pdf):
            try:
                os.remove(ruta_pdf)
            except:
                pass
    """)
    
    print("\nY reemplázalo por:")
    print("""
    finally:
        if es_temporal and os.path.exists(ruta_pdf):
            import time
            for intento in range(3):
                try:
                    time.sleep(0.5)
                    os.remove(ruta_pdf)
                    print("🧹 Archivo temporal eliminado")
                    break
                except PermissionError:
                    if intento < 2:
                        print(f"⏳ Esperando... (intento {intento+1}/3)")
                        time.sleep(1)
                    else:
                        print("⚠️ No se pudo eliminar archivo temporal")
                except Exception as e:
                    break
    """)


def verificar_chromadb_version():
    """Verifica la versión de ChromaDB"""
    try:
        import chromadb
        version = chromadb.__version__
        print(f"\n📦 ChromaDB versión: {version}")
        
        # Las versiones >= 0.4.x requieren operadores lógicos
        major, minor = map(int, version.split('.')[:2])
        if major == 0 and minor >= 4:
            print("✓ Versión correcta (requiere operadores $and)")
        else:
            print("⚠️ Versión antigua detectada")
            print("   Actualiza con: pip install --upgrade chromadb")
    except ImportError:
        print("❌ ChromaDB no instalado")


if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════╗")
    print("║       PARCHE RÁPIDO - Sistema de Licitaciones         ║")
    print("╚════════════════════════════════════════════════════════╝\n")
    
    # Verificar versión de ChromaDB
    verificar_chromadb_version()
    
    # Aplicar parches
    print("\n" + "="*60)
    print("APLICANDO CORRECCIONES")
    print("="*60 + "\n")
    
    # Parche 1: ChromaDB
    print("1️⃣ Corrigiendo filtros de ChromaDB...")
    if aplicar_parche_chromadb():
        print("   ✅ Completado\n")
    else:
        print("   ⚠️ Archivo no encontrado - aplicar manualmente\n")
    
    # Parche 2: Windows
    print("2️⃣ Corrección para archivos temporales (Windows)...")
    aplicar_parche_windows()
    
    print("\n" + "="*60)
    print("✅ PROCESO COMPLETADO")
    print("="*60)
    print("\nReinicia tu script y el error debería estar resuelto.")
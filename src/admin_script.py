"""
Utilidad para gestionar el usuario Admin y migrar búsquedas antiguas
Ejecuta este script para verificar o forzar la migración de búsquedas
"""

import json
import os
import hashlib
from datetime import datetime

def hash_password(password):
    """Crea hash de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def cargar_busquedas_antiguas(archivo="busquedas_guardadas.json"):
    """Carga búsquedas del sistema antiguo"""
    if os.path.exists(archivo):
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def cargar_usuarios(archivo="usuarios.json"):
    """Carga usuarios existentes"""
    if os.path.exists(archivo):
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_usuarios(usuarios, archivo="usuarios.json"):
    """Guarda usuarios"""
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def crear_usuario_admin():
    """Crea o actualiza el usuario Admin con búsquedas migradas"""
    usuarios = cargar_usuarios()
    busquedas_antiguas = cargar_busquedas_antiguas()
    
    # Crear estructura del usuario Admin
    admin_data = {
        "password": hash_password("123456"),
        "email": "admin@licitaciones.com",
        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "busquedas_guardadas": [],
        "cpvs_descartados": [],
        "grupos_cpv": {},
        "favoritos": [],
        "configuracion": {
            "alertas_activas": True,
            "limite_licitaciones": None
        }
    }
    
    # Si Admin ya existe, preservar sus datos actuales
    if "Admin" in usuarios:
        print("⚠️  Usuario Admin ya existe")
        respuesta = input("¿Deseas migrar búsquedas antiguas a Admin? (s/n): ")
        if respuesta.lower() != 's':
            print("❌ Operación cancelada")
            return
        
        # Preservar datos existentes
        admin_data = usuarios["Admin"]
        busquedas_existentes = [b["nombre"] for b in admin_data.get("busquedas_guardadas", [])]
    else:
        print("✅ Creando nuevo usuario Admin")
        busquedas_existentes = []
    
    # Migrar búsquedas antiguas
    migradas = 0
    for busqueda in busquedas_antiguas:
        if busqueda["nombre"] not in busquedas_existentes:
            admin_data["busquedas_guardadas"].append({
                "nombre": busqueda["nombre"],
                "filtros": busqueda["filtros"],
                "fecha": busqueda.get("fecha", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            })
            migradas += 1
    
    # Guardar usuario Admin
    usuarios["Admin"] = admin_data
    guardar_usuarios(usuarios)
    
    print(f"\n✅ Usuario Admin configurado correctamente")
    print(f"   - Usuario: Admin")
    print(f"   - Contraseña: 123456")
    print(f"   - Email: {admin_data['email']}")
    print(f"   - Búsquedas guardadas: {len(admin_data['busquedas_guardadas'])}")
    print(f"   - Búsquedas migradas: {migradas}")

def listar_usuarios():
    """Lista todos los usuarios registrados"""
    usuarios = cargar_usuarios()
    
    if not usuarios:
        print("❌ No hay usuarios registrados")
        return
    
    print("\n" + "="*60)
    print("USUARIOS REGISTRADOS")
    print("="*60)
    
    for username, data in usuarios.items():
        print(f"\n👤 Usuario: {username}")
        print(f"   Email: {data.get('email', 'N/A')}")
        print(f"   Fecha registro: {data.get('fecha_registro', 'N/A')}")
        print(f"   Búsquedas guardadas: {len(data.get('busquedas_guardadas', []))}")
        print(f"   CPVs descartados: {len(data.get('cpvs_descartados', []))}")
        print(f"   Favoritos: {len(data.get('favoritos', []))}")

def mostrar_busquedas_admin():
    """Muestra las búsquedas guardadas del usuario Admin"""
    usuarios = cargar_usuarios()
    
    if "Admin" not in usuarios:
        print("❌ Usuario Admin no encontrado")
        return
    
    busquedas = usuarios["Admin"].get("busquedas_guardadas", [])
    
    if not busquedas:
        print("❌ Admin no tiene búsquedas guardadas")
        return
    
    print("\n" + "="*60)
    print("BÚSQUEDAS GUARDADAS DE ADMIN")
    print("="*60)
    
    for i, busqueda in enumerate(busquedas, 1):
        print(f"\n{i}. {busqueda['nombre']}")
        print(f"   Fecha: {busqueda.get('fecha', 'N/A')}")
        print(f"   Filtros aplicados:")
        
        filtros = busqueda.get('filtros', {})
        if filtros.get('cpv'):
            print(f"      - CPVs: {len(filtros['cpv'])} seleccionados")
        if filtros.get('lugar'):
            print(f"      - Lugar: {filtros['lugar']}")
        if filtros.get('entidades'):
            print(f"      - Entidades: {', '.join(filtros['entidades'])}")
        if filtros.get('palabras_clave'):
            print(f"      - Palabras clave: {', '.join(filtros['palabras_clave'])}")

def menu_principal():
    """Menú principal de la utilidad"""
    while True:
        print("\n" + "="*60)
        print("GESTIÓN DE USUARIO ADMIN")
        print("="*60)
        print("1. Crear/Actualizar usuario Admin")
        print("2. Listar todos los usuarios")
        print("3. Mostrar búsquedas de Admin")
        print("4. Salir")
        print("="*60)
        
        opcion = input("\nSelecciona una opción: ")
        
        if opcion == "1":
            crear_usuario_admin()
        elif opcion == "2":
            listar_usuarios()
        elif opcion == "3":
            mostrar_busquedas_admin()
        elif opcion == "4":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    menu_principal()
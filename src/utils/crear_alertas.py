#!/usr/bin/env python3
"""
Script para generar alertas basadas en búsquedas guardadas de usuarios.
Compara las licitaciones en Pliegos_general.parquet con las búsquedas guardadas
y genera/actualiza alertas en alertas.json
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Set
import os

# Nota: Para leer parquet necesitamos pyarrow o fastparquet
# Si no están disponibles, se debe convertir el parquet a CSV/JSON primero
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("ADVERTENCIA: pandas no disponible. El script requiere pandas para funcionar.")


# Estados que NO generan alertas
ESTADOS_EXCLUIDOS = ['RES', 'ADJ', 'EV', 'ANUL']

# Estados que SÍ generan alertas
ESTADOS_VALIDOS = ['PUB', 'PRE']


def generar_hash_busqueda(nombre_busqueda: str) -> str:
    """Genera un hash único para una búsqueda basado en su nombre"""
    hash_obj = hashlib.md5(nombre_busqueda.encode('utf-8'))
    return f"bq_{hash_obj.hexdigest()[:8]}"


def generar_id_alerta(contador: int) -> str:
    """Genera un ID único para una alerta"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"ALT_{timestamp}_{contador:06d}"


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparación (minúsculas, sin tildes básicas)"""
    if not texto:
        return ""
    texto = texto.lower()
    # Reemplazos básicos de tildes
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
        'ñ': 'n'
    }
    for orig, repl in reemplazos.items():
        texto = texto.replace(orig, repl)
    return texto


def mapear_estado(estado_full: str) -> str:
    """Mapea el estado completo al código corto"""
    mapeo = {
        'publicado': 'PUB',
        'anuncio previo': 'PRE',
        'resuelta': 'RES',
        'adjudicada': 'ADJ',
        'evaluacion': 'EV',
        'evaluación': 'EV'
    }
    return mapeo.get(normalizar_texto(estado_full), estado_full)


# def licitacion_coincide_con_busqueda(licitacion: Dict, filtros: Dict, df_criterios, df_requisitos) -> tuple:
#     """
#     Verifica si una licitación coincide con los filtros de una búsqueda.
#     Retorna (coincide: bool, motivos: List[str])
#     """
#     motivos = []
    
#     # 1. Verificar palabras clave (si hay)
    
#     # --- Extensión del filtro por palabras clave ---
#     if filtros.get("palabras_clave"):
#         palabras = [p.lower() for p in filtros["palabras_clave"]]

#         def contiene_palabras(texto):
#             if not isinstance(texto, str):
#                 return False
#             t = texto.lower()
#             return any(p in t for p in palabras)

#         ids_encontrados = set(licitacion["ID_INTERNO"])
#         # print(ids_encontrados)
        
#         ## BUSCAMOS COINCIDENCIAS DIRECTAS DE ID
#         ids_coincidencia_directa = set(
#             licitacion.loc[licitacion["ID"].apply(contiene_palabras),
#                            "ID_INTERNO"]
#         )
#         ids_encontrados |= ids_coincidencia_directa
#         print(ids_encontrados)

#         # Buscar coincidencias en criterios
#         if df_criterios is not None and not df_criterios.empty:
#             ids_en_criterios = set(
#                 df_criterios.loc[
#                     df_criterios["DESCRIPCION"].apply(contiene_palabras), 
#                     "ID_INTERNO"
#                 ]
#             )
#             ids_encontrados |= ids_en_criterios

#         # Buscar coincidencias en requisitos
#         if df_requisitos is not None and not df_requisitos.empty:
#             ids_en_requisitos = set(
#                 df_requisitos.loc[
#                     df_requisitos["DESCRIPCION"].apply(contiene_palabras), 
#                     "ID_INTERNO"
#                 ]
#             )
#             ids_encontrados |= ids_en_requisitos
    
#     palabras_clave = filtros.get('palabras_clave', [])
#     if palabras_clave:
#         # Buscar en nombre, descripción, etc.
#         texto_licitacion = normalizar_texto(
#             f"{licitacion.get('NOMBRE_PROYECTO', '')} {licitacion.get('descripcion', '')} "
#             f"{licitacion.get('ENTIDAD', '')}"
#         )
        
#         palabras_encontradas = []
#         for palabra in palabras_clave:
#             if normalizar_texto(palabra) in texto_licitacion:
#                 palabras_encontradas.append(palabra)
        
#         if palabras_encontradas:
#             motivos.append('palabras_clave')
    
#     # 2. Verificar CPVs (si hay)
#     cpvs_busqueda = filtros.get('cpv', [])
#     # print('EN CPVS',cpvs_busqueda)
#     if cpvs_busqueda:
#         cpvs_licitacion = licitacion.get('CPV', [])
#         if isinstance(cpvs_licitacion, str):
#             cpvs_licitacion = [cpvs_licitacion]
        
#         for cpv_busqueda in cpvs_busqueda:
#             # Extraer código CPV (parte antes del guión)
#             codigo_busqueda = cpv_busqueda.split(' - ')[0].strip() if ' - ' in cpv_busqueda else cpv_busqueda.strip()
            
#             for cpv_lic in cpvs_licitacion:
#                 codigo_lic = cpv_lic.split(' - ')[0].strip() if ' - ' in cpv_lic else cpv_lic.strip()
#                 if codigo_busqueda == codigo_lic:
#                     if 'cpv' not in motivos:
#                         motivos.append('cpv')
#                     break
    
#     # 3. Verificar importe (si hay límites)
#     importe_min = filtros.get('importe_min', 0)
#     importe_max = filtros.get('importe_max', float('inf'))
    
#     importe_str = licitacion.get('IMPORTE', '0')
#     # print(importe_str)
#     try:
#         # Extraer número del importe (puede venir como "152542.43 EUR")
#         importe = float(importe_str.split()[0].replace(',', '.'))
#         if not (importe_min <= importe <= importe_max):
#             return False, []  # No coincide si está fuera de rango
#     except (ValueError, IndexError, AttributeError):
#         pass
    
#     # 4. Verificar lugar (si hay)
#     lugar_filtro = filtros.get('lugar')
#     if lugar_filtro and lugar_filtro != 'Todos' and lugar_filtro:
#         lugar_licitacion = licitacion.get('UBICACION', '')
#         # print(lugar_filtro==lugar_licitacion)
#         if normalizar_texto(lugar_filtro) not in normalizar_texto(lugar_licitacion):
#             # Si el lugar no coincide, no es match (a menos que sea flexible)
#             # Por ahora lo consideramos flexible
#             pass
    
#     # # 5. Verificar entidades (si hay)
#     # entidades_filtro = filtros.get('entidades', [])
#     # # print(entidades_filtro)
#     # if entidades_filtro:
#     #     tipo_entidad_licitacion = licitacion.get('SECTOR_PUBLICO', '')
#     #     coincide_entidad = False
#     #     for entidad in entidades_filtro:
#     #         if normalizar_texto(entidad) in normalizar_texto(tipo_entidad_licitacion):
#     #             coincide_entidad = True
#     #             break
        
#     #     if not coincide_entidad and entidades_filtro:
#     #         # Si no coincide ninguna entidad, no es match
#     #         # Por ahora lo hacemos flexible
#     #         pass
    
#     # 6. Verificar estados (si hay)
#     estados_filtro = filtros.get('estados', [])
#     if estados_filtro:
#         estado_licitacion = licitacion.get('ESTADO', '')
#         estado_codigo = mapear_estado(estado_licitacion)
        
#         estados_codigos_filtro = [mapear_estado(e) for e in estados_filtro]
#         if estado_codigo not in estados_codigos_filtro:
#             return False, []  # No coincide si el estado no está en el filtro
    
#     # Si hay al menos un motivo (palabras clave o CPV), es una coincidencia
#     # Si no hay palabras clave ni CPVs en el filtro, consideramos que coincide
#     if motivos or (not palabras_clave and not cpvs_busqueda):
#         if not motivos:
#             motivos.append('filtros_generales')
#         print(motivos)
#         return True, motivos
    
#     return False, []

def licitacion_coincide_con_busqueda(licitacion: Dict, filtros: Dict, df_criterios, df_requisitos) -> tuple:
    motivos = []
    id_interno_actual = licitacion.get("ID_INTERNO")
    
    # 1. Verificar palabras clave
    palabras_clave = filtros.get("palabras_clave", [])
    if palabras_clave:
        palabras = [p.lower() for p in palabras_clave]

        def contiene_palabras(texto):
            if not isinstance(texto, str): return False
            t = texto.lower()
            return any(p in t for p in palabras)

        # A. Buscar en la licitación actual (que es un DICT)
        campos_a_revisar = [
            licitacion.get('NOMBRE_PROYECTO', ''),
            licitacion.get('descripcion', ''),
            licitacion.get('ENTIDAD', ''),
            licitacion.get('ID', '')
        ]
        
        texto_unido = " ".join([str(c) for c in campos_a_revisar])
        if contiene_palabras(texto_unido):
            motivos.append('palabras_clave')

        # B. Buscar coincidencias en criterios (solo para este ID_INTERNO)
        if 'palabras_clave' not in motivos and df_criterios is not None and not df_criterios.empty:
            # Filtramos el dataframe de criterios por el ID actual
            criterios_lic = df_criterios[df_criterios["ID_INTERNO"] == id_interno_actual]
            if any(criterios_lic["DESCRIPCION"].apply(contiene_palabras)):
                motivos.append('palabras_clave')

        # C. Buscar coincidencias en requisitos (solo para este ID_INTERNO)
        if 'palabras_clave' not in motivos and df_requisitos is not None and not df_requisitos.empty:
            # Filtramos el dataframe de requisitos por el ID actual
            req_lic = df_requisitos[df_requisitos["ID_INTERNO"] == id_interno_actual]
            if any(req_lic["DESCRIPCION"].apply(contiene_palabras)):
                motivos.append('palabras_clave')
    
    # --- 2. Verificar CPVs ---
    cpvs_busqueda = filtros.get('cpv', [])
    if cpvs_busqueda:
        # ... (tu lógica de CPV está bien, solo asegúrate de manejar si licitacion['CPV'] es lista o string)
        cpvs_licitacion = licitacion.get('CPV', [])
        if isinstance(cpvs_licitacion, str):
            cpvs_licitacion = [cpvs_licitacion]
        elif cpvs_licitacion is None:
            cpvs_licitacion = []
            
        for cpv_busqueda in cpvs_busqueda:
            codigo_busqueda = cpv_busqueda.split(' - ')[0].strip()
            for cpv_lic in cpvs_licitacion:
                codigo_lic = str(cpv_lic).split(' - ')[0].strip()
                if codigo_busqueda == codigo_lic:
                    if 'cpv' not in motivos:
                        motivos.append('cpv')
                    break
    
    # --- 3. Verificar importe ---
    importe_min = filtros.get('importe_min', 0)
    importe_max = filtros.get('importe_max', float('inf'))
    try:
        val_importe = licitacion.get('IMPORTE', 0)
        if isinstance(val_importe, str):
            # Limpieza básica para "100.000,00 EUR" -> 100000.00
            importe = float(val_importe.split()[0].replace('.', '').replace(',', '.'))
        else:
            importe = float(val_importe)
            
        if not (importe_min <= importe <= importe_max):
            return False, []
    except:
        pass

    # --- 6. Verificar estados ---
    estados_filtro = filtros.get('estados', [])
    if estados_filtro:
        estado_licitacion = licitacion.get('ESTADO', '')
        estado_codigo = mapear_estado(estado_licitacion)
        estados_codigos_filtro = [mapear_estado(e) for e in estados_filtro]
        if estado_codigo not in estados_codigos_filtro:
            return False, []

    # Decisión final
    if motivos or (not palabras_clave and not cpvs_busqueda):
        if not motivos:
            motivos.append('filtros_generales')
        return True, motivos
    
    return False, []


def cargar_alertas_existentes(ruta_alertas: str) -> Dict:
    """Carga el archivo de alertas existente o retorna un dict vacío"""
    if os.path.exists(ruta_alertas):
        try:
            with open(ruta_alertas, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Advertencia: No se pudo leer {ruta_alertas}, se creará uno nuevo")
    return {}


def obtener_licitaciones_alertadas(alertas: Dict) -> Dict[str, Set[str]]:
    """
    Retorna un diccionario con las licitaciones que ya tienen alertas.
    Formato: {licitacion_id: {set de id_alertas}}
    """
    licitaciones_alertadas = {}
    for id_alerta, alerta in alertas.items():
        lic_id = alerta.get('licitacion_id')
        if lic_id:
            if lic_id not in licitaciones_alertadas:
                licitaciones_alertadas[lic_id] = set()
            licitaciones_alertadas[lic_id].add(id_alerta)
    return licitaciones_alertadas


def actualizar_estados_alertas(alertas: Dict, df_licitaciones: 'pd.DataFrame') -> Dict:
    """
    Actualiza los estados de las alertas existentes según el estado actual
    de las licitaciones en el DataFrame.
    """
    # Crear un índice de licitaciones por ID para búsqueda rápida
    licitaciones_dict = {}
    for _, row in df_licitaciones.iterrows():
        lic_id = row.get('licitacion_id', row.get('id'))
        if lic_id:
            licitaciones_dict[lic_id] = row.to_dict()
    
    alertas_actualizadas = 0
    for id_alerta, alerta in alertas.items():
        lic_id = alerta.get('licitacion_id')
        if lic_id in licitaciones_dict:
            licitacion_actual = licitaciones_dict[lic_id]
            estado_actual = licitacion_actual.get('estado', '')
            estado_codigo = mapear_estado(estado_actual)
            
            # Actualizar metadatos de la licitación
            if 'metadatos' in alerta and 'licitacion_info' in alerta['metadatos']:
                alerta['metadatos']['licitacion_info']['estado'] = estado_codigo
                alertas_actualizadas += 1
    
    if alertas_actualizadas > 0:
        print(f"✓ Actualizados estados de {alertas_actualizadas} alertas existentes")
    
    return alertas


def generar_alertas(ruta_usuarios: str, ruta_pliegos: str, ruta_alertas: str):
    """
    Función principal que genera las alertas basadas en búsquedas guardadas
    """
    if not PANDAS_AVAILABLE:
        print("ERROR: pandas no está disponible. Por favor instala pandas y pyarrow/fastparquet.")
        return
    
    print("=" * 60)
    print("GENERADOR DE ALERTAS - LICITACIONES")
    print("=" * 60)
    print()
    
    # 1. Cargar usuarios
    print("1. Cargando usuarios...")
    try:
        with open(ruta_usuarios, 'r', encoding='utf-8') as f:
            usuarios = json.load(f)
        print(f"   ✓ {len(usuarios)} usuarios cargados")
    except Exception as e:
        print(f"   ✗ Error al cargar usuarios: {e}")
        return
    
    try:
        df_criterios = pd.read_parquet("src/data/Criterios_general.parquet")
        print(f"   ✓ {len(df_criterios)} licitaciones cargadas")
        print(f"   Columnas disponibles: {', '.join(df_criterios.columns.tolist())}")
    except Exception as e:
        print(f"   ✗ Error al cargar criterios: {e}")
        return
    
    try:
        df_requisitos = pd.read_parquet("src/data/Requisitos_general.parquet")
        print(f"   ✓ {len(df_requisitos)} licitaciones cargadas")
        print(f"   Columnas disponibles: {', '.join(df_requisitos.columns.tolist())}")
    except Exception as e:
        print(f"   ✗ Error al cargar criterios: {e}")
        return
    
    # 2. Cargar licitaciones
    print("2. Cargando licitaciones...")
    try:
        df_licitaciones = pd.read_parquet(ruta_pliegos)
        print(f"   ✓ {len(df_licitaciones)} licitaciones cargadas")
        print(f"   Columnas disponibles: {', '.join(df_licitaciones.columns.tolist())}")
    except Exception as e:
        print(f"   ✗ Error al cargar licitaciones: {e}")
        return
    
    # 3. Cargar alertas existentes
    print("3. Cargando alertas existentes...")
    alertas = cargar_alertas_existentes(ruta_alertas)
    print(f"   ✓ {len(alertas)} alertas existentes")
    
    # 4. Actualizar estados de alertas existentes
    print("4. Actualizando estados de alertas existentes...")
    alertas = actualizar_estados_alertas(alertas, df_licitaciones)
    
    # 5. Obtener licitaciones que ya tienen alertas
    licitaciones_con_alertas = obtener_licitaciones_alertadas(alertas)
    
    # 6. Procesar cada usuario y sus búsquedas
    print("5. Generando nuevas alertas...")
    contador_global = len(alertas) + 1
    alertas_nuevas = 0
    
    for nombre_usuario, datos_usuario in usuarios.items():
        busquedas = datos_usuario.get('busquedas_guardadas', [])
        
        if not busquedas:
            continue
        
        print(f"\n   Procesando usuario: {nombre_usuario}")
        print(f"   Búsquedas guardadas: {len(busquedas)}")
        
        for busqueda in busquedas:
            nombre_busqueda = busqueda.get('nombre', 'Sin nombre')
            filtros = busqueda.get('filtros', {})
            hash_busqueda = generar_hash_busqueda(nombre_busqueda)
            
            print(f"     - Búsqueda: '{nombre_busqueda}' (hash: {hash_busqueda})")
            
            coincidencias_busqueda = 0
            
            # Verificar cada licitación
            for idx, row in df_licitaciones.iterrows():
                # print(row)
                licitacion = row.to_dict()
                
                # Obtener ID de licitación
                lic_id = licitacion.get('licitacion_id', licitacion.get('ID', ''))
                # print(lic_id)
                
                if not lic_id:
                    continue
                
                # Verificar estado de la licitación
                estado = licitacion.get('ESTADO', '')
                estado_codigo = mapear_estado(estado)
                # print(estado, estado_codigo)
                
                # Saltar si el estado está excluido
                # print(estado in ESTADOS_EXCLUIDOS, estado.strip() == "RES", estado)
                if estado.strip() in ESTADOS_EXCLUIDOS:
                    # print("EXCLUIDA!")
                    continue
                
                # Verificar si ya existe alerta para esta combinación usuario-búsqueda-licitación
                # (Para evitar duplicados)
                alerta_existe = False
                if lic_id in licitaciones_con_alertas:
                    for id_alerta in licitaciones_con_alertas[lic_id]:
                        if (alertas[id_alerta].get('usuario') == nombre_usuario and
                            alertas[id_alerta].get('busqueda', {}).get('hash') == hash_busqueda):
                            alerta_existe = True
                            break
                
                if alerta_existe:
                    continue
                
                # Verificar si coincide con los filtros
                coincide, motivos = licitacion_coincide_con_busqueda(licitacion, filtros, df_criterios ,df_requisitos)
                
                if coincide:
                    # Crear nueva alerta
                    id_alerta = generar_id_alerta(contador_global)
                    contador_global += 1
                    coincidencias_busqueda += 1
                    
                    alerta = {
                        "id_alerta": id_alerta,
                        "usuario": nombre_usuario,
                        "licitacion_id": lic_id,
                        "id_interno": licitacion.get('ID_INTERNO', ''),
                        "busqueda": {
                            "nombre": nombre_busqueda,
                            "hash": hash_busqueda
                        },
                        "estado": "nueva",
                        "leida": False,
                        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "metadatos": {
                            "origen": "ingestion",
                            "coincidencias": motivos,
                            "licitacion_info": {
                                "nombre": licitacion.get('NOMBRE_PROYECTO', ''),
                                "entidad": licitacion.get('ENTIDAD', ''),
                                "importe": licitacion.get('IMPORTE', ''),
                                "estado": estado_codigo,
                                "fecha_limite": licitacion.get('FECHA_LIMITE', ''),
                                "url": licitacion.get('URL', '')
                            }
                        }
                    }
                    
                    alertas[id_alerta] = alerta
                    alertas_nuevas += 1
            
            if coincidencias_busqueda > 0:
                print(f"       ✓ {coincidencias_busqueda} nuevas coincidencias encontradas")
    
    # 7. Guardar alertas actualizadas
    print(f"\n6. Guardando alertas...")
    try:
        with open(ruta_alertas, 'w', encoding='utf-8') as f:
            json.dump(alertas, f, ensure_ascii=False, indent=2)
        print(f"   ✓ Archivo guardado: {ruta_alertas}")
    except Exception as e:
        print(f"   ✗ Error al guardar alertas: {e}")
        return
    
    # 8. Resumen
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total de alertas en sistema: {len(alertas)}")
    print(f"Alertas nuevas generadas: {alertas_nuevas}")
    print(f"Alertas actualizadas: {len(alertas) - alertas_nuevas}")
    print()


if __name__ == "__main__":
    import sys
    
    # Rutas por defecto
    # ruta_usuarios = "/mnt/user-data/uploads/usuarios.json"
    ruta_usuarios = r"usuarios.json"
    ruta_pliegos = "src/data/Pliegos_general.parquet"
    ruta_alertas = "alertas.json"
    
    # Permitir rutas personalizadas como argumentos
    if len(sys.argv) > 1:
        ruta_usuarios = sys.argv[1]
    if len(sys.argv) > 2:
        ruta_pliegos = sys.argv[2]
    if len(sys.argv) > 3:
        ruta_alertas = sys.argv[3]
    
    generar_alertas(ruta_usuarios, ruta_pliegos, ruta_alertas)
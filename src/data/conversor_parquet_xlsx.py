# import pandas as pd

# def convertir_parquet_a_excel(archivo_parquet, archivo_excel):
#     try:
#         # 1. Leer el archivo Parquet
#         print(f"Leyendo {archivo_parquet}...")
#         df = pd.read_parquet(archivo_parquet)

#         # 2. Guardar a Excel
#         print(f"Exportando a {archivo_excel}...")
#         # Usamos el motor 'openpyxl' para crear el .xlsx
#         df.to_excel(archivo_excel, index=False, engine='openpyxl')

#         print("¡Conversión exitosa!")
        
#     except Exception as e:
#         print(f"Ocurrió un error: {e}")

# # --- Configuración ---
# input_file = 'src/data/Pliegos_general.parquet'  # Cambia esto por tu archivo
# output_file = 'src/data/Pliegos_general.xlsx'      # Nombre del archivo de salida

# convertir_parquet_a_excel(input_file, output_file)

# import pandas as pd
# import pathlib

# def convertir_multiples_parquet_a_excel(carpeta_input, archivo_salida):
#     # Crear una ruta para la carpeta
#     ruta = pathlib.Path(carpeta_input)
#     archivos_parquet = list(ruta.glob("*.parquet"))

#     if not archivos_parquet:
#         print("No se encontraron archivos .parquet en la carpeta.")
#         return

#     try:
#         # Usar ExcelWriter para gestionar múltiples hojas
#         with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
#             for archivo in archivos_parquet:
#                 nombre_hoja = archivo.stem[:31]  # Excel limita el nombre de la hoja a 31 caracteres
                
#                 print(f"Procesando: {archivo.name} -> Hoja: {nombre_hoja}")
                
#                 # Leer parquet y escribir en su respectiva hoja
#                 df = pd.read_parquet(archivo)
#                 df.to_excel(writer, sheet_name=nombre_hoja, index=False)
        
#         print(f"\n✅ ¡Listo! Archivo generado: {archivo_salida}")

#     except Exception as e:
#         print(f"❌ Error durante la conversión: {e}")

# # --- Configuración ---
# CARPETA_DATOS = 'src/data'  # Carpeta donde están tus archivos
# ARCHIVO_FINAL = 'data_base_licitacions.xlsx'

# convertir_multiples_parquet_a_excel(CARPETA_DATOS, ARCHIVO_FINAL)

import pandas as pd
import pathlib
import sys
import os

# Añade la raíz del proyecto al PATH de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.filtrador import filtrando_df_general, criterios_filtrado

def convertir_multiples_parquet_a_excel(carpeta_input, archivo_salida):
    # --- Configuración del Filtro ---
    cpvs_interes = [
        "30000000-9 - Máquinas, equipo y artículos de oficina y de informática, excepto mobiliario y paquetes de software",
        "30100000-0 - Máquinas, equipo y artículos de oficina, excepto ordenadores, impresoras y mobiliario",
        "30200000-1 - Equipo y material informático",
        "30210000-4 - Máquinas procesadoras de datos (hardware)",
        "30230000-0 - Equipo relacionado con la informática",
        "32000000-3 - Equipos de radio, televisión, comunicaciones y telecomunicaciones y equipos conexos",
        "32400000-7 - Redes",
        "32500000-8 - Equipo y material para telecomunicaciones",
        "48510000-6 - Paquetes de software de comunicación",
        "48600000-4 - Paquetes de software de bases de datos y de funcionamiento",
        "48620000-0 - Sistemas operativos",
        "48710000-8 - Paquetes de software de copia de seguridad o recuperación",
        "48730000-4 - Paquetes de software de seguridad",
        "48760000-3 - Paquetes de software de protección antivirus",
        "48780000-9 - Paquetes de software de gestión de sistemas, almacenamiento y contenido",
        "48800000-6 - Sistemas y servidores de información",
        "50300000-8 - Servicios de reparación, mantenimiento y servicios asociados relacionados con ordenadores personales, equipo de oficina, telecomunicaciones y equipo audiovisual",
        "51300000-5 - Servicios de instalación de equipos de comunicaciones",
        "51600000-8 - Servicios de instalación de ordenadores y equipo de oficina",
        "48820000-2 - Servidores"
    ]
    filtros = {'cpv':cpvs_interes}
    print(filtros.get('cpv'))

    ruta = pathlib.Path(carpeta_input)
    archivos_parquet = list(ruta.glob("*.parquet"))
    # print(ruta.glob("Pliegos_general.parquet"))
    archivos_parquet = ruta.glob("Pliegos_general.parquet")
    archivos_parquet_adju = ruta.glob("Adjudicatarios_general.parquet")
    # print(archivos_parquet_adju)
    

    if not archivos_parquet:
        print("No se encontraron archivos .parquet.")
        return

    try:
        with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
            for archivo in archivos_parquet:
                nombre_hoja = archivo.stem[:31]
                
                # 1. Leer el archivo
                df = pd.read_parquet(archivo)

                # 2. Aplicar Filtro
                # Suponiendo que la columna se llama 'cpv' o 'CPV'
                # Usamos .isin() para filtrar los que coincidan con tu lista
                # print(df.columns)
                columna_cpv = 'CPV' # ⚠️ Ajusta esto al nombre real de tu columna
                
                if columna_cpv in df.columns:
                    # print(columna_cpv)
                    # df_filtrado = df[df[columna_cpv].isin(cpvs_interes)].copy()
                    df_filtrado = filtrando_df_general(df,filtros)
                    
                    # print(df_filtrado.head())
                    
                    if not df_filtrado.empty:
                        print(f"Procesando: {archivo.name} -> {len(df_filtrado)} registros filtrados.")
                        df_filtrado.to_excel(writer, sheet_name=nombre_hoja, index=False)
                    else:
                        print(f"Omitiendo {archivo.name}: Ningún registro coincide con los CPV.")
                        
                    
                else:
                    print(f"⚠️ Alerta: La columna '{columna_cpv}' no existe en {archivo.name}")
                    
            for archivo in archivos_parquet_adju:
                print("IN")
                print('IN',archivo)
                nombre_hoja_adj = archivo.stem[:31]
                
                # 1. Leer el archivo
                df_adjudicatarios = pd.read_parquet(archivo)

                # 2. Aplicar Filtro
                # Suponiendo que la columna se llama 'cpv' o 'CPV'
                # Usamos .isin() para filtrar los que coincidan con tu lista
                # print(df.columns)
                # columna_cpv = 'CPV' # ⚠️ Ajusta esto al nombre real de tu columna
                
                # print(columna_cpv)
                # df_filtrado = df[df[columna_cpv].isin(cpvs_interes)].copy()
                
                print(df_adjudicatarios.head())
                df_adjudicatarios_filtrado = criterios_filtrado(df_adjudicatarios,df_filtrado=df_filtrado)
                # print(df_filtrado.head())
                    
                if not df_adjudicatarios_filtrado.empty:
                    print(f"Procesando: {archivo.name} -> {len(df_adjudicatarios_filtrado)} registros filtrados.")
                    df_adjudicatarios_filtrado.to_excel(writer, sheet_name=nombre_hoja_adj, index=False)
                else:
                    print(f"Omitiendo {archivo.name}: Ningún registro coincide con los CPV.")
                
        
        print(f"\n✅ ¡Listo! Archivo generado: {archivo_salida}")

    except Exception as e:
        print(f"❌ Error: {e}")

# --- Ejecución ---
CARPETA_DATOS = 'src/data'
ARCHIVO_FINAL = 'data_base_licitacions.xlsx'
convertir_multiples_parquet_a_excel(CARPETA_DATOS, ARCHIVO_FINAL)
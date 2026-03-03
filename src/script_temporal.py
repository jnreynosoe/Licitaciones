# import pandas as pd
# import requests
# from bs4 import BeautifulSoup
# import time
# import os
# from urllib.parse import urljoin

# def descargar_xml_adjudicacion(uri, output_folder='xmls_adjudicacion'):
#     """
#     Descarga el XML de adjudicación desde la URI proporcionada
#     """
#     try:
#         # Crear carpeta si no existe
#         os.makedirs(output_folder, exist_ok=True)
        
#         # Hacer petición a la página
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#         }
#         response = requests.get(uri, headers=headers, timeout=30)
#         response.raise_for_status()
        
#         # Parsear HTML
#         soup = BeautifulSoup(response.content, 'html.parser')
#         print(soup)
        
#         # Buscar la tabla con id="myTablaDetalleVISUOE"
#         tabla = soup.find('table', {'id': 'myTablaDetalleVISUOE'})
        
#         if not tabla:
#             print(f"No se encontró tabla en {uri}")
#             return None
        
#         # Buscar todas las filas
#         filas = tabla.find('tbody').find_all('tr')
        
#         for fila in filas:
#             # Buscar celda con tipo de documento
#             tipo_doc = fila.find('td', class_='tipoDocumento')
            
#             if tipo_doc:
#                 texto = tipo_doc.get_text(strip=True)
#                 # Verificar si es Adjudicación (con o sin entidades HTML)
#                 if 'Adjudicaci' in texto:
#                     # Buscar enlaces en la misma fila
#                     enlaces = fila.find_all('a', href=True)
                    
#                     for enlace in enlaces:
#                         # Buscar el enlace del XML
#                         img = enlace.find('img', alt='Documento xml')
#                         if img:
#                             url_xml = enlace['href']
                            
#                             # Si es URL relativa, hacerla absoluta
#                             if not url_xml.startswith('http'):
#                                 base_url = 'https://contrataciondelestado.es'
#                                 url_xml = urljoin(base_url, url_xml)
                            
#                             # Descargar XML
#                             print(f"Descargando XML de: {uri}")
#                             xml_response = requests.get(url_xml, headers=headers, timeout=30)
#                             xml_response.raise_for_status()
                            
#                             # Generar nombre de archivo
#                             # Extraer ID del expediente si es posible
#                             nombre_archivo = f"adjudicacion_{hash(uri)}.xml"
#                             ruta_completa = os.path.join(output_folder, nombre_archivo)
                            
#                             # Guardar XML
#                             with open(ruta_completa, 'wb') as f:
#                                 f.write(xml_response.content)
                            
#                             print(f"✓ XML guardado: {ruta_completa}")
#                             return ruta_completa
        
#         print(f"No se encontró documento de Adjudicación en {uri}")
#         return None
        
#     except Exception as e:
#         print(f"Error procesando {uri}: {str(e)}")
#         return None

# def procesar_pliegos(archivo_parquet, delay=2):
#     """
#     Procesa el archivo parquet y descarga los XMLs de adjudicación
#     """
#     print("Cargando archivo parquet...")
#     df = pd.read_parquet(archivo_parquet)
    
#     print(f"Total de registros: {len(df)}")
    
#     # Filtrar por ESTADO = ADJ
#     print(df['ESTADO'].unique())


#     df_adj = df[df['ESTADO'] == ' ADJ'].copy()
#     print(f"Registros con estado ADJ: {len(df_adj)}")
    
#     # Verificar que existe columna URI
#     if 'URL' not in df_adj.columns:
#         print("Error: No se encontró la columna 'URI' en el archivo")
#         return
    
#     resultados = []
#     total = len(df_adj)
    
#     print(f"\nIniciando descarga de {total} XMLs...\n")
    
#     for idx, row in df_adj.iterrows():
#         uri = row['URL']
#         print(f"\n[{idx+1}/{total}] Procesando: {uri}")
        
#         resultado = descargar_xml_adjudicacion(uri)
#         resultados.append({
#             'URL': uri,
#             'XML_descargado': resultado is not None,
#             'Ruta_XML': resultado
#         })
        
#         # Delay entre peticiones para no saturar el servidor
#         if idx < total - 1:
#             time.sleep(delay)
    
#     # Crear DataFrame con resultados
#     df_resultados = pd.DataFrame(resultados)
#     df_resultados.to_csv('resultados_descarga.csv', index=False)
    
#     print("\n" + "="*60)
#     print(f"Proceso completado!")
#     print(f"XMLs descargados exitosamente: {df_resultados['XML_descargado'].sum()}")
#     print(f"Fallidos: {(~df_resultados['XML_descargado']).sum()}")
#     print(f"Resultados guardados en: resultados_descarga.csv")
#     print("="*60)

# if __name__ == "__main__":
#     # Configuración
#     ARCHIVO_PARQUET = r"src\data\Pliegos_general.parquet"
#     DELAY_SEGUNDOS = 2  # Tiempo de espera entre peticiones
    
#     # Ejecutar
#     procesar_pliegos(ARCHIVO_PARQUET, delay=DELAY_SEGUNDOS)

## ----------------------------------------------

# import pandas as pd
# import requests
# from bs4 import BeautifulSoup
# import time
# import os
# from urllib.parse import urljoin
# import xml.etree.ElementTree as ET

# def extraer_datos_xml(ruta_xml):
#     """
#     Extrae NIF y nombre de la empresa adjudicataria del XML
#     """
#     try:
#         tree = ET.parse(ruta_xml)
#         root = tree.getroot()
        
#         # Definir namespaces comunes en XMLs de contratación
#         namespaces = {
#             'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
#             'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
#         }
        
#         datos = []
        
#         # Buscar todos los WinningParty
#         winning_parties = root.findall('.//cac:WinningParty', namespaces)
        
#         for party in winning_parties:
#             # Extraer NIF
#             nif_elem = party.find('.//cac:PartyIdentification/cbc:ID[@schemeName="NIF"]', namespaces)
#             if nif_elem is None:
#                 nif_elem = party.find('.//cac:PartyIdentification/cbc:ID', namespaces)
            
#             # Extraer nombre
#             nombre_elem = party.find('.//cac:PartyName/cbc:Name', namespaces)
            
#             # Extraer información adicional opcional
#             ciudad_elem = party.find('.//cac:PhysicalLocation/cac:Address/cbc:CityName', namespaces)
#             provincia_elem = party.find('.//cac:PhysicalLocation/cbc:CountrySubentity', namespaces)
#             telefono_elem = party.find('.//cac:AgentParty/cac:Contact/cbc:Telephone', namespaces)
#             email_elem = party.find('.//cac:AgentParty/cac:Contact/cbc:ElectronicMail', namespaces)
            
#             datos.append({
#                 'NIF': nif_elem.text if nif_elem is not None else None,
#                 'Nombre_Empresa': nombre_elem.text if nombre_elem is not None else None,
#                 'Ciudad': ciudad_elem.text if ciudad_elem is not None else None,
#                 'Provincia': provincia_elem.text if provincia_elem is not None else None,
#                 'Telefono': telefono_elem.text if telefono_elem is not None else None,
#                 'Email': email_elem.text if email_elem is not None else None
#             })
        
#         return datos if datos else [{'NIF': None, 'Nombre_Empresa': None, 'Ciudad': None, 
#                                       'Provincia': None, 'Telefono': None, 'Email': None}]
        
#     except Exception as e:
#         print(f"Error extrayendo datos del XML {ruta_xml}: {str(e)}")
#         return [{'NIF': None, 'Nombre_Empresa': None, 'Ciudad': None, 
#                  'Provincia': None, 'Telefono': None, 'Email': None}]

# def descargar_xml_adjudicacion(uri, output_folder='xmls_adjudicacion'):
#     """
#     Descarga el XML de adjudicación desde la URI proporcionada
#     """
#     try:
#         os.makedirs(output_folder, exist_ok=True)
        
#         # 1. Generar el nombre de archivo ANTES de descargar
#         nombre_archivo = f"adjudicacion_{hash(uri)}.xml"
#         ruta_completa = os.path.join(output_folder, nombre_archivo)
        
#         # 2. VERIFICACIÓN: Si el archivo ya existe, saltar la descarga
#         if os.path.exists(ruta_completa):
#             print(f"skipping: El archivo ya existe en {ruta_completa}")
#             datos_empresas = extraer_datos_xml(ruta_completa)
#             return ruta_completa, datos_empresas
        
#         # Hacer petición a la página
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#         }
#         response = requests.get(uri, headers=headers, timeout=30)
#         response.raise_for_status()
        
#         # Parsear HTML
#         soup = BeautifulSoup(response.content, 'html.parser')
        
#         # Buscar la tabla con id="myTablaDetalleVISUOE"
#         tabla = soup.find('table', {'id': 'myTablaDetalleVISUOE'})
        
#         if not tabla:
#             print(f"No se encontró tabla en {uri}")
#             return None, None
        
#         # Buscar todas las filas
#         filas = tabla.find('tbody').find_all('tr')
        
#         for fila in filas:
#             # Buscar celda con tipo de documento
#             tipo_doc = fila.find('td', class_='tipoDocumento')
            
#             if tipo_doc:
#                 texto = tipo_doc.get_text(strip=True)
#                 # Verificar si es Adjudicación (con o sin entidades HTML)
#                 if 'Adjudicaci' in texto:
#                     # Buscar enlaces en la misma fila
#                     enlaces = fila.find_all('a', href=True)
                    
#                     for enlace in enlaces:
#                         # Buscar el enlace del XML
#                         img = enlace.find('img', alt='Documento xml')
#                         if img:
#                             url_xml = enlace['href']
                            
#                             # Si es URL relativa, hacerla absoluta
#                             if not url_xml.startswith('http'):
#                                 base_url = 'https://contrataciondelestado.es'
#                                 url_xml = urljoin(base_url, url_xml)
                            
#                             # Descargar XML
#                             print(f"Descargando XML de: {uri}")
#                             xml_response = requests.get(url_xml, headers=headers, timeout=30)
#                             xml_response.raise_for_status()
                            
#                             # Generar nombre de archivo
#                             nombre_archivo = f"adjudicacion_{hash(uri)}.xml"
#                             ruta_completa = os.path.join(output_folder, nombre_archivo)
                            
#                             # Guardar XML
#                             with open(ruta_completa, 'wb') as f:
#                                 f.write(xml_response.content)
                            
#                             print(f"✓ XML guardado: {ruta_completa}")
                            
#                             # Extraer datos del XML
#                             datos_empresas = extraer_datos_xml(ruta_completa)
                            
#                             return ruta_completa, datos_empresas
        
#         print(f"No se encontró documento de Adjudicación en {uri}")
#         return None, None
        
#     except Exception as e:
#         print(f"Error procesando {uri}: {str(e)}")
#         return None, None

# def procesar_pliegos(archivo_parquet, delay=2):
#     """
#     Procesa el archivo parquet y descarga los XMLs de adjudicación
#     """
#     print("Cargando archivo parquet...")
#     df = pd.read_parquet(archivo_parquet)
    
#     print(f"Total de registros: {len(df)}")
    
#     # Filtrar por ESTADO = ADJ
#     df_adj = df[df['ESTADO'] == ' ADJ'].copy()
#     print(f"Registros con estado ADJ: {len(df_adj)}")
    
#     # Verificar que existe columna URI
#     if 'URL' not in df_adj.columns:
#         print("Error: No se encontró la columna 'URI' en el archivo")
#         return
    
#     resultados = []
#     total = len(df_adj)
    
#     print(f"\nIniciando descarga de {total} XMLs...\n")
    
#     for idx, row in df_adj.iterrows():
#         uri = row['URL']
#         print(f"\n[{idx+1}/{total}] Procesando: {uri}")
        
#         ruta_xml, datos_empresas = descargar_xml_adjudicacion(uri)
        
#         # Si hay múltiples empresas adjudicatarias, crear una fila por cada una
#         if datos_empresas:
#             for datos_empresa in datos_empresas:
#                 resultados.append({
#                     'URL': uri,
#                     'XML_descargado': ruta_xml is not None,
#                     'Ruta_XML': ruta_xml,
#                     'NIF': datos_empresa['NIF'],
#                     'Nombre_Empresa': datos_empresa['Nombre_Empresa'],
#                     'Ciudad': datos_empresa['Ciudad'],
#                     'Provincia': datos_empresa['Provincia'],
#                     'Telefono': datos_empresa['Telefono'],
#                     'Email': datos_empresa['Email']
#                 })
#         else:
#             resultados.append({
#                 'URL': uri,
#                 'XML_descargado': False,
#                 'Ruta_XML': None,
#                 'NIF': None,
#                 'Nombre_Empresa': None,
#                 'Ciudad': None,
#                 'Provincia': None,
#                 'Telefono': None,
#                 'Email': None
#             })
        
#         # Delay entre peticiones para no saturar el servidor
#         if idx < total - 1:
#             time.sleep(delay)
    
#     # Crear DataFrame con resultados
#     df_resultados = pd.DataFrame(resultados)
#     df_resultados.to_csv('resultados_descarga.csv', index=False)
#     df_resultados.to_excel('resultados_descarga.xlsx', index=False, engine='openpyxl')
    
#     print("\n" + "="*60)
#     print(f"Proceso completado!")
#     print(f"XMLs descargados exitosamente: {df_resultados['XML_descargado'].sum()}")
#     print(f"Fallidos: {(~df_resultados['XML_descargado']).sum()}")
#     print(f"Empresas adjudicatarias únicas: {df_resultados['NIF'].nunique()}")
#     print(f"\nResultados guardados en:")
#     print(f"  - resultados_descarga.csv")
#     print(f"  - resultados_descarga.xlsx")
#     print("="*60)
    
#     # Mostrar muestra de datos
#     print("\nMuestra de empresas adjudicatarias:")
#     print(df_resultados[['NIF', 'Nombre_Empresa', 'Provincia']].dropna().head(10))

# if __name__ == "__main__":
#     # Configuración
#     ARCHIVO_PARQUET = r"src\data\Pliegos_general.parquet"
#     DELAY_SEGUNDOS = 2  # Tiempo de espera entre peticiones
    
#     # Ejecutar
#     procesar_pliegos(ARCHIVO_PARQUET, delay=DELAY_SEGUNDOS)


## SCRIPT DE PROCESAMIENTO DE RENTABILIDAD

# import pandas as pd
# from fpdf import FPDF

# from utils.filtrador import filtrando_df_general

# class PDFInforme(FPDF):
#     def header(self):
#         self.set_font('Arial', 'B', 15)
#         self.cell(0, 10, 'Informe de Rentabilidad: Licitación vs Adjudicación', 0, 1, 'C')
#         self.ln(10)

#     def footer(self):
#         self.set_y(-15)
#         self.set_font('Arial', 'I', 8)
#         self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# def generar_pdf(df_resultados, nombre_archivo="Informe_Rentabilidad.pdf"):
#     pdf = PDFInforme()
#     pdf.add_page()
    
#     # --- Resumen Ejecutivo ---
#     pdf.set_font('Arial', 'B', 12)
#     pdf.cell(0, 10, '1. Resumen General', 0, 1)
#     pdf.set_font('Arial', '', 11)
    
#     total_licitacion = df_resultados['IMPORTE'].sum()
#     total_adjudicacion = df_resultados['IMPORTE_CON_IVA'].sum()
#     ahorro_medio = df_resultados['BAJA_PORCENTUAL'].mean()

#     pdf.cell(0, 8, f"Total Expedientes Analizados: {len(df_resultados)}", 0, 1)
#     pdf.cell(0, 8, f"Suma Importe Licitación: {total_licitacion:,.2f} EUR", 0, 1)
#     pdf.cell(0, 8, f"Suma Importe Adjudicación: {total_adjudicacion:,.2f} EUR", 0, 1)
#     pdf.cell(0, 8, f"Porcentaje de Baja Medio (Rentabilidad): {ahorro_medio:.2f}%", 0, 1)
#     pdf.ln(10)

#     # --- Tabla de Detalles ---
#     pdf.set_font('Arial', 'B', 12)
#     pdf.cell(0, 10, '2. Detalle por ID Interno (Top 20)', 0, 1)
    
#     # Cabecera de Tabla
#     pdf.set_fill_color(200, 220, 255)
#     pdf.set_font('Arial', 'B', 10)
#     pdf.cell(40, 10, 'ID Interno', 1, 0, 'C', True)
#     pdf.cell(50, 10, 'Imp. Licitación', 1, 0, 'C', True)
#     pdf.cell(50, 10, 'Imp. Adjudicación', 1, 0, 'C', True)
#     pdf.cell(40, 10, '% Rentabilidad', 1, 1, 'C', True)

#     # Filas (Limitamos a los primeros 20 para el PDF)
#     pdf.set_font('Arial', '', 9)
#     for i, row in df_resultados.head(20).iterrows():
#         pdf.cell(40, 8, str(row['ID_INTERNO']), 1)
#         pdf.cell(50, 8, f"{row['IMPORTE']:,.2f}", 1, 0, 'R')
#         pdf.cell(50, 8, f"{row['IMPORTE_CON_IVA']:,.2f}", 1, 0, 'R')
#         pdf.cell(40, 8, f"{row['BAJA_PORCENTUAL']:.2f}%", 1, 1, 'R')

#     pdf.output(nombre_archivo)
#     print(f"PDF generado con éxito: {nombre_archivo}")
    
# def analizar_rentabilidad(path_pliegos, path_adjudicatarios):
#     # 1. Carga de datos
#     df_pliegos = pd.read_parquet(path_pliegos)
#     df_adjudicatarios = pd.read_parquet(path_adjudicatarios)

#     # 2. Definición de filtros (Tus criterios proporcionados)
#     cpvs_interes = [
#         "30000000-9 - Máquinas, equipo y artículos de oficina y de informática, excepto mobiliario y paquetes de software",
#         "30100000-0 - Máquinas, equipo y artículos de oficina, excepto ordenadores, impresoras y mobiliario",
#         "30200000-1 - Equipo y material informático",
#         "30210000-4 - Máquinas procesadoras de datos (hardware)",
#         "30230000-0 - Equipo relacionado con la informática",
#         "32000000-3 - Equipos de radio, televisión, comunicaciones y telecomunicaciones y equipos conexos",
#         "32400000-7 - Redes",
#         "32500000-8 - Equipo y material para telecomunicaciones",
#         "48510000-6 - Paquetes de software de comunicación",
#         "48600000-4 - Paquetes de software de bases de datos y de funcionamiento",
#         "48620000-0 - Sistemas operativos",
#         "48710000-8 - Paquetes de software de copia de seguridad o recuperación",
#         "48730000-4 - Paquetes de software de seguridad",
#         "48760000-3 - Paquetes de software de protección antivirus",
#         "48780000-9 - Paquetes de software de gestión de sistemas, almacenamiento y contenido",
#         "48800000-6 - Sistemas y servidores de información",
#         "50300000-8 - Servicios de reparación, mantenimiento y servicios asociados relacionados con ordenadores personales, equipo de oficina, telecomunicaciones y equipo audiovisual",
#         "51300000-5 - Servicios de instalación de equipos de comunicaciones",
#         "51600000-8 - Servicios de instalación de ordenadores y equipo de oficina",
#         "48820000-2 - Servidores"
#     ]
    
#     filtros = {
#         'cpv': cpvs_interes,
#         'estado': ['ADJ', 'RES', 'Adjudicada', 'Resuelta']
#     }

#     # 3. Aplicar filtros a Pliegos
#     print("Filtrando datos...")
#     df_pliegos_filt = filtrando_df_general(df_pliegos, filtros)

#     # 4. Cruce de Dataframes (PK-FK: ID_INTERNO)
#     # Seleccionamos solo las columnas necesarias para optimizar memoria
#     df_merged = pd.merge(
#         df_pliegos_filt[['ID_INTERNO', 'IMPORTE']], 
#         df_adjudicatarios[['ID_INTERNO', 'IMPORTE_CON_IVA']], 
#         on='ID_INTERNO', 
#         how='inner'
#     )

#     # 5. Cálculo de Rentabilidad / Ahorro
#     # Rentabilidad % = ((Importe Licitación - Importe Adjudicación) / Importe Licitación) * 100
#     # Nota: Un valor positivo indica una baja respecto al presupuesto base.
#     df_merged['BAJA_PORCENTUAL'] = (
#         (df_merged['IMPORTE'] - df_merged['IMPORTE_CON_IVA']) / 
#         df_merged['IMPORTE']
#     ) * 100

#     return df_merged

# # --- Ejecución ---
# df_final = analizar_rentabilidad('src/data/Pliegos_general.parquet', 'src/data/Adjudicatarios_general.parquet')
# print(df_final[['ID_INTERNO', 'IMPORTE', 'IMPORTE_CON_IVA', 'BAJA_PORCENTUAL']].head())

# # --- Integración con tu flujo ---

# # 1. Cargar y Filtrar (Usando la lógica del mensaje anterior)
# # df_pliegos = pd.read_parquet('src/data/Pliegos_general.parquet')
# # df_adj = pd.read_parquet('src/data/Adjudicatarios_general.parquet')

# # Supongamos que df_final es el resultado del merge y cálculo:
# df_final['BAJA_PORCENTUAL'] = ((df_final['IMPORTE'] - df_final['IMPORTE_CON_IVA']) / df_final['IMPORTE']) * 100

# # 2. Exportar
# generar_pdf(df_final)


## ---------------
import pandas as pd
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos # Importamos para eliminar los DeprecationWarnings
from utils.filtrador import filtrando_df_general

def limpiar_texto_pdf(texto):
    """
    Elimina o reemplaza caracteres que fallan en fuentes estándar (latin-1).
    """
    if not texto: return ""
    # Reemplaza el guion largo por uno normal y elimina caracteres no compatibles
    texto = str(texto).replace('\u2013', '-').replace('\u2014', '-')
    # Mantenemos solo caracteres básicos para evitar el error de codificación
    return texto.encode('latin-1', 'ignore').decode('latin-1')

def limpiar_importe(serie):
    return (
        serie.astype(str)
        .str.replace(r'[^\d,.-]', '', regex=True)
        # .str.replace('.', '', regex=False)        
        # .str.replace(',', '.', regex=False)       
        .astype(float)
    )

def analizar_rentabilidad(path_pliegos, path_adjudicatarios):
    df_pliegos = pd.read_parquet(path_pliegos)
    df_adj = pd.read_parquet(path_adjudicatarios)

    df_pliegos['IMPORTE_CLEAN'] = limpiar_importe(df_pliegos['IMPORTE'])
    df_adj['IMPORTE_ADJ_CLEAN'] = limpiar_importe(df_adj['IMPORTE_SIN_IVA'])

    palabras_clave = ['cuadros de mando', 'power bi', 'business intelligence', 'etl']
    filtros = {'cpv': [], 'palabras_clave': palabras_clave, 'estado': ['ADJ', 'RES', 'Adjudicada', 'Resuelta']}
    
    df_pliegos_filt = filtrando_df_general(df_pliegos, filtros)

    # Merge corregido con nombres de columnas exactos
    df_merged = pd.merge(
        df_pliegos_filt[['ID_INTERNO', 'ID','NOMBRE_PROYECTO', 'IMPORTE_CLEAN', 'URL']], 
        df_adj[['ID_INTERNO','NOMBRE_ADJUDICATARIO', 'NIF_ADJUDICATARIO',  'IMPORTE_ADJ_CLEAN']], 
        on='ID_INTERNO', 
        how='inner'
    )

    # df_merged['BAJA_PORCENTUAL'] = ((df_merged['IMPORTE_CLEAN'] - df_merged['IMPORTE_ADJ_CLEAN']) / df_merged['IMPORTE_CLEAN']) * 100
    df_merged['BAJA_PORCENTUAL'] = ((df_merged['IMPORTE_ADJ_CLEAN']-df_merged['IMPORTE_CLEAN']) / df_merged['IMPORTE_CLEAN']) * 100
    return df_merged

def exportar_a_pdf(df, filename="Informe_Rentabilidad.pdf"):
    # Cambiamos Arial por Helvetica para evitar avisos (son equivalentes en PDF)
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 15, "INFORME DETALLADO DE RENTABILIDAD", align='C', 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT) # Nueva sintaxis para ln=True
    pdf.ln(5)
    
    # Cabeceras
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", "B", 9)
    
    w = {'id': 50, 'adj': 70, 'nif': 30, 'imp': 35, 'baja': 25, 'url': 32}
    
    headers = [("ID Expediente", w['id']), ("Adjudicatario", w['adj']), ("NIF", w['nif']), 
               ("Licitación", w['imp']), ("Adjudicación", w['imp']), ("% Baja", w['baja']), ("Enlace", w['url'])]
    
    for text, width in headers:
        pdf.cell(width, 10, text, border=1, align='C', fill=True, 
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 8)
    
    palabras_interes = ['power bi']
    
    for _, row in df.head(60).iterrows():
        # --- Lógica de Resaltado ---
        # Comprobamos si alguna palabra clave está en el nombre de la licitación
        nombre_licitacion = str(row.get('NOMBRE_PROYECTO', '')).lower()
        es_interes_especial = any(pc.lower() in nombre_licitacion for pc in palabras_interes)
        
        # Si es de interés, ponemos un fondo amarillo suave, si no, blanco
        if es_interes_especial:
            pdf.set_fill_color(255, 255, 200) # Amarillo claro
        else:
            pdf.set_fill_color(255, 255, 255) # Blanco
        
        # Limpiamos los textos antes de enviarlos al PDF
        id_txt = limpiar_texto_pdf(row['ID'])
        nombre_txt = limpiar_texto_pdf(row['NOMBRE_ADJUDICATARIO'])
        
        y_start = pdf.get_y()
        x_start = pdf.get_x()
        
        # Columna ID
        pdf.multi_cell(w['id'], 6, id_txt, border=1, fill=True)
        h_fila = pdf.get_y() - y_start
        
        # Columna Adjudicatario
        pdf.set_xy(x_start + w['id'], y_start)
        pdf.multi_cell(w['adj'], 6, nombre_txt, border=1, fill=True)
        h_fila = max(h_fila, pdf.get_y() - y_start)
        
        # Celdas simples con la altura calculada
        pdf.set_xy(x_start + w['id'] + w['adj'], y_start)
        pdf.cell(w['nif'], h_fila, str(row['NIF_ADJUDICATARIO']), border=1, fill=True)
        pdf.cell(w['imp'], h_fila, f"{row['IMPORTE_CLEAN']:,.2f}", border=1, align='R', fill=True)
        pdf.cell(w['imp'], h_fila, f"{row['IMPORTE_ADJ_CLEAN']:,.2f}", border=1, align='R', fill=True)
        
        # Color %
        if row['BAJA_PORCENTUAL'] <= 0: pdf.set_text_color(200, 0, 0)
        else: pdf.set_text_color(0, 120, 0)
        pdf.cell(w['baja'], h_fila, f"{row['BAJA_PORCENTUAL']:.2f}%", border=1, align='R', fill=True)
        
        # URL
        pdf.set_text_color(0, 0, 255)
        pdf.set_font("Helvetica", "U", 8)
        pdf.cell(w['url'], h_fila, "Ver Licitación", border=1, align='C', 
                 link=str(row['URL']), fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Reset para la siguiente fila
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 8)

    pdf.output(filename)

if __name__ == "__main__":
    df_final = analizar_rentabilidad('src/data/Pliegos_general.parquet', 'src/data/Adjudicatarios_general.parquet')
    exportar_a_pdf(df_final)
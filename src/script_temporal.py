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

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

def extraer_datos_xml(ruta_xml):
    """
    Extrae NIF y nombre de la empresa adjudicataria del XML
    """
    try:
        tree = ET.parse(ruta_xml)
        root = tree.getroot()
        
        # Definir namespaces comunes en XMLs de contratación
        namespaces = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }
        
        datos = []
        
        # Buscar todos los WinningParty
        winning_parties = root.findall('.//cac:WinningParty', namespaces)
        
        for party in winning_parties:
            # Extraer NIF
            nif_elem = party.find('.//cac:PartyIdentification/cbc:ID[@schemeName="NIF"]', namespaces)
            if nif_elem is None:
                nif_elem = party.find('.//cac:PartyIdentification/cbc:ID', namespaces)
            
            # Extraer nombre
            nombre_elem = party.find('.//cac:PartyName/cbc:Name', namespaces)
            
            # Extraer información adicional opcional
            ciudad_elem = party.find('.//cac:PhysicalLocation/cac:Address/cbc:CityName', namespaces)
            provincia_elem = party.find('.//cac:PhysicalLocation/cbc:CountrySubentity', namespaces)
            telefono_elem = party.find('.//cac:AgentParty/cac:Contact/cbc:Telephone', namespaces)
            email_elem = party.find('.//cac:AgentParty/cac:Contact/cbc:ElectronicMail', namespaces)
            
            datos.append({
                'NIF': nif_elem.text if nif_elem is not None else None,
                'Nombre_Empresa': nombre_elem.text if nombre_elem is not None else None,
                'Ciudad': ciudad_elem.text if ciudad_elem is not None else None,
                'Provincia': provincia_elem.text if provincia_elem is not None else None,
                'Telefono': telefono_elem.text if telefono_elem is not None else None,
                'Email': email_elem.text if email_elem is not None else None
            })
        
        return datos if datos else [{'NIF': None, 'Nombre_Empresa': None, 'Ciudad': None, 
                                      'Provincia': None, 'Telefono': None, 'Email': None}]
        
    except Exception as e:
        print(f"Error extrayendo datos del XML {ruta_xml}: {str(e)}")
        return [{'NIF': None, 'Nombre_Empresa': None, 'Ciudad': None, 
                 'Provincia': None, 'Telefono': None, 'Email': None}]

def descargar_xml_adjudicacion(uri, output_folder='xmls_adjudicacion'):
    """
    Descarga el XML de adjudicación desde la URI proporcionada
    """
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        # 1. Generar el nombre de archivo ANTES de descargar
        nombre_archivo = f"adjudicacion_{hash(uri)}.xml"
        ruta_completa = os.path.join(output_folder, nombre_archivo)
        
        # 2. VERIFICACIÓN: Si el archivo ya existe, saltar la descarga
        if os.path.exists(ruta_completa):
            print(f"skipping: El archivo ya existe en {ruta_completa}")
            datos_empresas = extraer_datos_xml(ruta_completa)
            return ruta_completa, datos_empresas
        
        # Hacer petición a la página
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(uri, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parsear HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar la tabla con id="myTablaDetalleVISUOE"
        tabla = soup.find('table', {'id': 'myTablaDetalleVISUOE'})
        
        if not tabla:
            print(f"No se encontró tabla en {uri}")
            return None, None
        
        # Buscar todas las filas
        filas = tabla.find('tbody').find_all('tr')
        
        for fila in filas:
            # Buscar celda con tipo de documento
            tipo_doc = fila.find('td', class_='tipoDocumento')
            
            if tipo_doc:
                texto = tipo_doc.get_text(strip=True)
                # Verificar si es Adjudicación (con o sin entidades HTML)
                if 'Adjudicaci' in texto:
                    # Buscar enlaces en la misma fila
                    enlaces = fila.find_all('a', href=True)
                    
                    for enlace in enlaces:
                        # Buscar el enlace del XML
                        img = enlace.find('img', alt='Documento xml')
                        if img:
                            url_xml = enlace['href']
                            
                            # Si es URL relativa, hacerla absoluta
                            if not url_xml.startswith('http'):
                                base_url = 'https://contrataciondelestado.es'
                                url_xml = urljoin(base_url, url_xml)
                            
                            # Descargar XML
                            print(f"Descargando XML de: {uri}")
                            xml_response = requests.get(url_xml, headers=headers, timeout=30)
                            xml_response.raise_for_status()
                            
                            # Generar nombre de archivo
                            nombre_archivo = f"adjudicacion_{hash(uri)}.xml"
                            ruta_completa = os.path.join(output_folder, nombre_archivo)
                            
                            # Guardar XML
                            with open(ruta_completa, 'wb') as f:
                                f.write(xml_response.content)
                            
                            print(f"✓ XML guardado: {ruta_completa}")
                            
                            # Extraer datos del XML
                            datos_empresas = extraer_datos_xml(ruta_completa)
                            
                            return ruta_completa, datos_empresas
        
        print(f"No se encontró documento de Adjudicación en {uri}")
        return None, None
        
    except Exception as e:
        print(f"Error procesando {uri}: {str(e)}")
        return None, None

def procesar_pliegos(archivo_parquet, delay=2):
    """
    Procesa el archivo parquet y descarga los XMLs de adjudicación
    """
    print("Cargando archivo parquet...")
    df = pd.read_parquet(archivo_parquet)
    
    print(f"Total de registros: {len(df)}")
    
    # Filtrar por ESTADO = ADJ
    df_adj = df[df['ESTADO'] == ' ADJ'].copy()
    print(f"Registros con estado ADJ: {len(df_adj)}")
    
    # Verificar que existe columna URI
    if 'URL' not in df_adj.columns:
        print("Error: No se encontró la columna 'URI' en el archivo")
        return
    
    resultados = []
    total = len(df_adj)
    
    print(f"\nIniciando descarga de {total} XMLs...\n")
    
    for idx, row in df_adj.iterrows():
        uri = row['URL']
        print(f"\n[{idx+1}/{total}] Procesando: {uri}")
        
        ruta_xml, datos_empresas = descargar_xml_adjudicacion(uri)
        
        # Si hay múltiples empresas adjudicatarias, crear una fila por cada una
        if datos_empresas:
            for datos_empresa in datos_empresas:
                resultados.append({
                    'URL': uri,
                    'XML_descargado': ruta_xml is not None,
                    'Ruta_XML': ruta_xml,
                    'NIF': datos_empresa['NIF'],
                    'Nombre_Empresa': datos_empresa['Nombre_Empresa'],
                    'Ciudad': datos_empresa['Ciudad'],
                    'Provincia': datos_empresa['Provincia'],
                    'Telefono': datos_empresa['Telefono'],
                    'Email': datos_empresa['Email']
                })
        else:
            resultados.append({
                'URL': uri,
                'XML_descargado': False,
                'Ruta_XML': None,
                'NIF': None,
                'Nombre_Empresa': None,
                'Ciudad': None,
                'Provincia': None,
                'Telefono': None,
                'Email': None
            })
        
        # Delay entre peticiones para no saturar el servidor
        if idx < total - 1:
            time.sleep(delay)
    
    # Crear DataFrame con resultados
    df_resultados = pd.DataFrame(resultados)
    df_resultados.to_csv('resultados_descarga.csv', index=False)
    df_resultados.to_excel('resultados_descarga.xlsx', index=False, engine='openpyxl')
    
    print("\n" + "="*60)
    print(f"Proceso completado!")
    print(f"XMLs descargados exitosamente: {df_resultados['XML_descargado'].sum()}")
    print(f"Fallidos: {(~df_resultados['XML_descargado']).sum()}")
    print(f"Empresas adjudicatarias únicas: {df_resultados['NIF'].nunique()}")
    print(f"\nResultados guardados en:")
    print(f"  - resultados_descarga.csv")
    print(f"  - resultados_descarga.xlsx")
    print("="*60)
    
    # Mostrar muestra de datos
    print("\nMuestra de empresas adjudicatarias:")
    print(df_resultados[['NIF', 'Nombre_Empresa', 'Provincia']].dropna().head(10))

if __name__ == "__main__":
    # Configuración
    ARCHIVO_PARQUET = r"src\data\Pliegos_general.parquet"
    DELAY_SEGUNDOS = 2  # Tiempo de espera entre peticiones
    
    # Ejecutar
    procesar_pliegos(ARCHIVO_PARQUET, delay=DELAY_SEGUNDOS)
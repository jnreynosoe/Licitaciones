# import fitz  # PyMuPDF
# import re
# import json
# from sentence_transformers import SentenceTransformer, util
# import torch
# from rapidfuzz import fuzz
# import io
# import requests
# import hashlib
# import camelot
# import tempfile
# import os
# from pathlib import Path
# from typing import List, Dict, Optional, Tuple

# try:
#     from vector_db import GestorLicitacionesMejorado
#     from cache_bdd import CacheResumenes
# except:
#     try:
#         from .vector_db import GestorLicitacionesMejorado
#         from .cache_bdd import CacheResumenes
#     except:
#         # Si no existen estos módulos, crear versiones dummy
#         class GestorLicitacionesMejorado:
#             def indexar_documento(self, *args, **kwargs): pass
#             def buscar_contexto(self, *args, **kwargs): return []
        
#         class CacheResumenes:
#             def obtener_resumen(self, *args, **kwargs): return None
#             def guardar_resumen(self, *args, **kwargs): return 1
#             def listar_versiones(self, *args, **kwargs): return []


# def extract_text_from_pdf(path_or_url):
#     """
#     Extrae texto de un PDF, desde una ruta local o una URL.
#     """
#     try:
#         # Detectar si es URL
#         if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
#             print(f"📥 Descargando PDF desde URL...")
#             response = requests.get(path_or_url, timeout=30)
#             response.raise_for_status()
#             pdf_bytes = io.BytesIO(response.content)
#             doc = fitz.open(stream=pdf_bytes, filetype="pdf")
#         else:
#             print(f"📂 Abriendo PDF local: {path_or_url}")
#             doc = fitz.open(path_or_url)

#         text = ""
#         for page in doc:
#             text += page.get_text("text") + "\n"

#         text = re.sub(r"\s+", " ", text)
#         doc.close()
#         return text.strip()

#     except Exception as e:
#         print(f"⚠️ Error leyendo PDF ({path_or_url}): {e}")
#         return ""


# # ==========================================
# # EXTRACCIÓN DE EMPRESAS LICITADORAS
# # ==========================================

# def extraer_empresas_licitadoras(texto: str) -> List[Dict[str, str]]:
#     """
#     Extrae información de empresas licitadoras del texto.
#     Busca patrones comunes en documentos de adjudicación.
    
#     Returns:
#         Lista de diccionarios con info de cada empresa: {nombre, nif, oferta, puntuacion}
#     """
#     empresas = []
    
#     # Patrones para detectar empresas
#     patrones_empresa = [
#         # Patrón 1: "Empresa: NOMBRE S.L. NIF: A12345678"
#         r"(?:Empresa|Licitador|Adjudicatario|Contratista)[:\s]+([A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ\s,\.]+(?:S\.?L\.?|S\.?A\.?|S\.?L\.?L\.?|UTE|AIE)?)\s*(?:NIF|CIF|DNI)?[:\s]*([A-Z]\d{7,8}[A-Z0-9])?",
        
#         # Patrón 2: Solo nombre de empresa (debe tener forma societaria)
#         r"([A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ\s,\.]{3,50}(?:S\.?L\.?|S\.?A\.?|S\.?L\.?L\.?|UTE|AIE))",
        
#         # Patrón 3: NIF seguido de nombre
#         r"(?:NIF|CIF)[:\s]*([A-Z]\d{7,8}[A-Z0-9])[:\s]*([A-ZÑÁÉÍÓÚ][A-ZÑÁÉÍÓÚ\s,\.]+)",
#     ]
    
#     # Buscar todas las menciones de empresas
#     empresas_encontradas = set()
    
#     for patron in patrones_empresa:
#         matches = re.finditer(patron, texto, re.IGNORECASE)
#         for match in matches:
#             if len(match.groups()) >= 1:
#                 nombre = match.group(1).strip()
#                 nif = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None
                
#                 # Limpiar el nombre
#                 nombre = limpiar_nombre_empresa(nombre)
                
#                 # Validar que parece un nombre de empresa válido
#                 if validar_nombre_empresa(nombre):
#                     empresas_encontradas.add((nombre, nif))
    
#     # Convertir a lista de diccionarios
#     for nombre, nif in empresas_encontradas:
#         empresa_info = {
#             'nombre': nombre,
#             'nif': nif or "No especificado",
#             'oferta_economica': None,
#             'puntuacion_total': None,
#             'es_adjudicatario': False
#         }
#         empresas.append(empresa_info)
    
#     return empresas


# def limpiar_nombre_empresa(nombre: str) -> str:
#     """Limpia y normaliza el nombre de una empresa"""
#     # Eliminar caracteres extraños al inicio/final
#     nombre = nombre.strip()
    
#     # Eliminar textos comunes que se cuelan en el regex
#     palabras_eliminar = ['Empresa', 'Licitador', 'Adjudicatario', 'Contratista', 
#                          'NIF', 'CIF', 'DNI', ':', ',']
#     for palabra in palabras_eliminar:
#         nombre = re.sub(rf'\b{palabra}\b', '', nombre, flags=re.IGNORECASE)
    
#     # Normalizar espacios
#     nombre = re.sub(r'\s+', ' ', nombre).strip()
    
#     return nombre


# def validar_nombre_empresa(nombre: str) -> bool:
#     """Valida que un string parece ser un nombre de empresa válido"""
#     if not nombre or len(nombre) < 5:
#         return False
    
#     # Debe contener al menos una forma societaria
#     formas_societarias = ['S.L.', 'SL', 'S.A.', 'SA', 'S.L.L.', 'UTE', 'AIE', 'S.COOP']
#     tiene_forma = any(forma in nombre.upper() for forma in formas_societarias)
    
#     # O debe tener al menos 2 palabras capitalizadas
#     palabras_cap = re.findall(r'[A-ZÑÁÉÍÓÚ][a-zñáéíóú]+', nombre)
#     tiene_palabras = len(palabras_cap) >= 2
    
#     return tiene_forma or tiene_palabras


# def extraer_ofertas_economicas(texto: str, empresas: List[Dict]) -> List[Dict]:
#     """
#     Extrae las ofertas económicas y las asocia a las empresas encontradas.
#     Busca en el contexto cercano a cada empresa mencionada.
#     """
#     # Patrones para ofertas económicas
#     patrones_oferta = [
#         r"(?:oferta|importe|precio)[:\s]*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€?",
#         r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€",
#         r"€\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
#     ]
    
#     for empresa in empresas:
#         nombre = empresa['nombre']
        
#         # Buscar menciones de la empresa en el texto
#         # Crear patrón flexible del nombre (primeras 3 palabras)
#         palabras_nombre = nombre.split()[:3]
#         patron_nombre = '.*'.join(re.escape(p) for p in palabras_nombre)
        
#         matches_empresa = list(re.finditer(patron_nombre, texto, re.IGNORECASE))
        
#         for match in matches_empresa:
#             # Extraer contexto (200 caracteres antes y después)
#             inicio = max(0, match.start() - 200)
#             fin = min(len(texto), match.end() + 200)
#             contexto = texto[inicio:fin]
            
#             # Buscar importes en el contexto
#             for patron in patrones_oferta:
#                 oferta_match = re.search(patron, contexto, re.IGNORECASE)
#                 if oferta_match:
#                     importe_str = oferta_match.group(1)
#                     try:
#                         # Convertir a float
#                         importe = float(importe_str.replace('.', '').replace(',', '.'))
                        
#                         # Si no tiene oferta o esta es mayor (probablemente más precisa)
#                         if empresa['oferta_economica'] is None or importe > empresa['oferta_economica']:
#                             empresa['oferta_economica'] = importe
#                             break
#                     except:
#                         continue
    
#     return empresas


# def extraer_puntuaciones(texto: str, empresas: List[Dict]) -> List[Dict]:
#     """
#     Extrae puntuaciones totales de las empresas.
#     """
#     patrones_puntuacion = [
#         r"(?:puntuación|puntos)[:\s]*(\d{1,3}(?:,\d{2})?)",
#         r"(\d{1,3}(?:,\d{2})?)\s*puntos",
#     ]
    
#     for empresa in empresas:
#         nombre = empresa['nombre']
#         palabras_nombre = nombre.split()[:3]
#         patron_nombre = '.*'.join(re.escape(p) for p in palabras_nombre)
        
#         matches_empresa = list(re.finditer(patron_nombre, texto, re.IGNORECASE))
        
#         for match in matches_empresa:
#             inicio = max(0, match.start() - 300)
#             fin = min(len(texto), match.end() + 300)
#             contexto = texto[inicio:fin]
            
#             for patron in patrones_puntuacion:
#                 punt_match = re.search(patron, contexto, re.IGNORECASE)
#                 if punt_match:
#                     try:
#                         puntos = float(punt_match.group(1).replace(',', '.'))
#                         if empresa['puntuacion_total'] is None or puntos > empresa['puntuacion_total']:
#                             empresa['puntuacion_total'] = puntos
#                             break
#                     except:
#                         continue
    
#     return empresas


# def identificar_adjudicatario(texto: str, empresas: List[Dict]) -> List[Dict]:
#     """
#     Identifica qué empresa(s) fue(ron) adjudicataria(s).
#     """
#     palabras_clave_adjudicacion = [
#         'adjudicatario', 'adjudicataria', 'adjudicación',
#         'contratista', 'ganador', 'seleccionado',
#         'formalización', 'contrato formalizado'
#     ]
    
#     for empresa in empresas:
#         nombre = empresa['nombre']
#         palabras_nombre = nombre.split()[:3]
#         patron_nombre = '.*'.join(re.escape(p) for p in palabras_nombre)
        
#         matches_empresa = list(re.finditer(patron_nombre, texto, re.IGNORECASE))
        
#         for match in matches_empresa:
#             inicio = max(0, match.start() - 100)
#             fin = min(len(texto), match.end() + 100)
#             contexto = texto[inicio:fin].lower()
            
#             # Si hay palabras de adjudicación cerca del nombre
#             if any(palabra in contexto for palabra in palabras_clave_adjudicacion):
#                 empresa['es_adjudicatario'] = True
#                 break
    
#     return empresas


# # ==========================================
# # EXTRACCIÓN DESDE TABLAS (CAMELOT)
# # ==========================================

# def extraer_empresas_desde_tablas(path_or_url: str) -> List[Dict]:
#     """
#     Extrae información de empresas desde tablas usando Camelot.
#     Muchos documentos de adjudicación tienen tablas con licitadores.
#     """
#     temp_file_path = None
#     empresas = []
    
#     try:
#         # Preparar archivo para Camelot
#         if path_or_url.startswith(("http://", "https://")):
#             print(f"📥 Descargando PDF para análisis de tablas...")
#             response = requests.get(path_or_url, timeout=30)
#             response.raise_for_status()
            
#             fd, temp_file_path = tempfile.mkstemp(suffix=".pdf")
#             with os.fdopen(fd, 'wb') as tmp:
#                 tmp.write(response.content)
#             path_a_procesar = temp_file_path
#         else:
#             path_a_procesar = path_or_url

#         # Extraer tablas
#         print(f"📊 Extrayendo tablas con Camelot...")
#         tablas = camelot.read_pdf(path_a_procesar, pages='all', flavor='lattice')
        
#         if len(tablas) == 0:
#             # Intentar con otro método
#             tablas = camelot.read_pdf(path_a_procesar, pages='all', flavor='stream')
        
#         print(f"   ✓ {len(tablas)} tabla(s) encontrada(s)")
        
#         # Analizar cada tabla
#         for i, tabla in enumerate(tablas):
#             df = tabla.df
#             print(f"\n   Analizando tabla {i+1}...")
            
#             # Buscar columnas relevantes
#             empresas_tabla = procesar_tabla_licitadores(df)
#             empresas.extend(empresas_tabla)
        
#         return empresas

#     except Exception as e:
#         print(f"⚠️ Error extrayendo tablas: {e}")
#         return []

#     finally:
#         if temp_file_path and os.path.exists(temp_file_path):
#             try:
#                 os.remove(temp_file_path)
#             except:
#                 pass


# def procesar_tabla_licitadores(df) -> List[Dict]:
#     """
#     Procesa un DataFrame de pandas para extraer información de licitadores.
#     """
#     empresas = []
    
#     # Intentar identificar columnas relevantes por su contenido
#     columnas_empresa = []
#     columnas_nif = []
#     columnas_oferta = []
#     columnas_puntos = []
    
#     for col_idx, col_name in enumerate(df.columns):
#         # Examinar las primeras filas de cada columna
#         col_data = df[col_name].astype(str).str.lower()
#         muestra = ' '.join(col_data.head(5).tolist())
        
#         # Detectar tipo de columna
#         if any(keyword in muestra for keyword in ['empresa', 'licitador', 'razón social', 'contratista']):
#             columnas_empresa.append(col_idx)
#         elif any(keyword in muestra for keyword in ['nif', 'cif', 'dni']):
#             columnas_nif.append(col_idx)
#         elif any(keyword in muestra for keyword in ['importe', 'oferta', 'precio', '€', 'euros']):
#             columnas_oferta.append(col_idx)
#         elif any(keyword in muestra for keyword in ['punt', 'total']):
#             columnas_puntos.append(col_idx)
    
#     # Si no encontramos columnas, intentar con heurísticas
#     if not columnas_empresa:
#         # La columna más a la izquierda con texto largo suele ser la empresa
#         for col_idx in range(len(df.columns)):
#             longitud_media = df[df.columns[col_idx]].astype(str).str.len().mean()
#             if longitud_media > 15:  # Nombres de empresa suelen ser largos
#                 columnas_empresa.append(col_idx)
#                 break
    
#     # Procesar filas
#     for idx, row in df.iterrows():
#         empresa_info = {
#             'nombre': None,
#             'nif': None,
#             'oferta_economica': None,
#             'puntuacion_total': None,
#             'es_adjudicatario': False,
#             'origen': 'tabla'
#         }
        
#         # Extraer nombre
#         if columnas_empresa:
#             nombre = str(row[df.columns[columnas_empresa[0]]])
#             if validar_nombre_empresa(nombre):
#                 empresa_info['nombre'] = limpiar_nombre_empresa(nombre)
        
#         # Extraer NIF
#         if columnas_nif and empresa_info['nombre']:
#             nif = str(row[df.columns[columnas_nif[0]]]).strip()
#             if re.match(r'^[A-Z]\d{7,8}[A-Z0-9]$', nif):
#                 empresa_info['nif'] = nif
        
#         # Extraer oferta
#         if columnas_oferta and empresa_info['nombre']:
#             oferta_str = str(row[df.columns[columnas_oferta[0]]])
#             oferta = extraer_numero_de_celda(oferta_str)
#             if oferta:
#                 empresa_info['oferta_economica'] = oferta
        
#         # Extraer puntuación
#         if columnas_puntos and empresa_info['nombre']:
#             puntos_str = str(row[df.columns[columnas_puntos[0]]])
#             puntos = extraer_numero_de_celda(puntos_str)
#             if puntos:
#                 empresa_info['puntuacion_total'] = puntos
        
#         # Solo añadir si tiene nombre
#         if empresa_info['nombre']:
#             empresas.append(empresa_info)
    
#     return empresas


# def extraer_numero_de_celda(texto: str) -> Optional[float]:
#     """
#     Extrae un número de una celda de tabla.
#     Maneja formatos como: "1.234,56 €", "1234.56", "1.234,56"
#     """
#     # Limpiar
#     texto = texto.strip().replace('€', '').replace('euros', '')
    
#     # Patrón para números con puntos de miles y coma decimal (español)
#     match = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', texto)
#     if match:
#         numero_str = match.group(1)
#         try:
#             # Convertir formato español a float
#             numero = float(numero_str.replace('.', '').replace(',', '.'))
#             return numero
#         except:
#             pass
    
#     # Intentar patrón punto decimal (inglés)
#     match = re.search(r'(\d+\.?\d*)', texto)
#     if match:
#         try:
#             return float(match.group(1))
#         except:
#             pass
    
#     return None


# # ==========================================
# # FUNCIÓN PRINCIPAL MEJORADA
# # ==========================================

# def analizar_licitadores_completo(path_or_url: str) -> Dict:
#     """
#     Análisis completo de empresas licitadoras:
#     1. Extrae texto completo
#     2. Busca empresas en tablas (Camelot)
#     3. Busca empresas en texto natural
#     4. Combina y deduplica resultados
#     5. Identifica adjudicatario
    
#     Returns:
#         Dict con estructura completa del análisis
#     """
#     print(f"\n{'='*60}")
#     print(f"🔍 ANÁLISIS DE LICITADORES")
#     print(f"{'='*60}\n")
    
#     # 1. Extraer texto
#     print("📄 Paso 1: Extrayendo texto del PDF...")
#     texto = extract_text_from_pdf(path_or_url)
#     print(f"   ✓ {len(texto)} caracteres extraídos\n")
    
#     # 2. Extraer desde tablas
#     print("📊 Paso 2: Buscando información en tablas...")
#     empresas_tablas = extraer_empresas_desde_tablas(path_or_url)
#     print(f"   ✓ {len(empresas_tablas)} empresa(s) encontrada(s) en tablas\n")
    
#     # 3. Extraer desde texto
#     print("📝 Paso 3: Buscando información en texto natural...")
#     empresas_texto = extraer_empresas_licitadoras(texto)
#     print(f"   ✓ {len(empresas_texto)} empresa(s) encontrada(s) en texto\n")
    
#     # 4. Combinar y enriquecer
#     print("🔗 Paso 4: Combinando y enriqueciendo información...")
#     empresas_combinadas = combinar_empresas(empresas_tablas, empresas_texto)
    
#     # Enriquecer con ofertas y puntuaciones del texto
#     empresas_combinadas = extraer_ofertas_economicas(texto, empresas_combinadas)
#     empresas_combinadas = extraer_puntuaciones(texto, empresas_combinadas)
#     empresas_combinadas = identificar_adjudicatario(texto, empresas_combinadas)
    
#     print(f"   ✓ {len(empresas_combinadas)} empresa(s) únicas identificadas\n")
    
#     # 5. Ordenar por puntuación o si es adjudicatario
#     empresas_combinadas.sort(
#         key=lambda x: (
#             not x['es_adjudicatario'],  # Adjudicatarios primero
#             -(x['puntuacion_total'] or 0)  # Luego por puntuación descendente
#         )
#     )
    
#     # 6. Preparar resultado
#     resultado = {
#         'total_licitadores': len(empresas_combinadas),
#         'adjudicatarios': [e for e in empresas_combinadas if e['es_adjudicatario']],
#         'otras_empresas': [e for e in empresas_combinadas if not e['es_adjudicatario']],
#         'todas_empresas': empresas_combinadas,
#         'metadatos': {
#             'url_origen': path_or_url if path_or_url.startswith('http') else None,
#             'empresas_desde_tablas': len(empresas_tablas),
#             'empresas_desde_texto': len(empresas_texto),
#         }
#     }
    
#     return resultado


# def combinar_empresas(empresas_tablas: List[Dict], empresas_texto: List[Dict]) -> List[Dict]:
#     """
#     Combina listas de empresas evitando duplicados.
#     Prioriza información de tablas por ser más estructurada.
#     """
#     empresas_unicas = {}
    
#     # Primero añadir las de tablas (más confiables)
#     for empresa in empresas_tablas:
#         nombre_normalizado = normalizar_nombre_empresa(empresa['nombre'])
#         empresas_unicas[nombre_normalizado] = empresa
    
#     # Luego añadir las del texto si no existen
#     for empresa in empresas_texto:
#         nombre_normalizado = normalizar_nombre_empresa(empresa['nombre'])
        
#         if nombre_normalizado not in empresas_unicas:
#             empresas_unicas[nombre_normalizado] = empresa
#         else:
#             # Si ya existe, combinar información (completar campos None)
#             empresa_existente = empresas_unicas[nombre_normalizado]
#             for key, value in empresa.items():
#                 if empresa_existente.get(key) is None and value is not None:
#                     empresa_existente[key] = value
    
#     return list(empresas_unicas.values())


# def normalizar_nombre_empresa(nombre: str) -> str:
#     """
#     Normaliza un nombre de empresa para comparación.
#     """
#     # Convertir a minúsculas
#     nombre = nombre.lower()
    
#     # Eliminar formas societarias para comparar mejor
#     nombre = re.sub(r'\b(s\.?l\.?|s\.?a\.?|s\.?l\.?l\.?|ute|aie)\b', '', nombre)
    
#     # Eliminar puntos y comas
#     nombre = nombre.replace('.', '').replace(',', '')
    
#     # Normalizar espacios
#     nombre = re.sub(r'\s+', ' ', nombre).strip()
    
#     return nombre


# # ==========================================
# # FUNCIÓN PARA MOSTRAR RESULTADOS
# # ==========================================

# def mostrar_resultados(resultado: Dict):
#     """
#     Muestra los resultados de forma legible en consola.
#     """
#     print(f"\n{'='*60}")
#     print(f"📊 RESULTADOS DEL ANÁLISIS")
#     print(f"{'='*60}\n")
    
#     print(f"Total de empresas identificadas: {resultado['total_licitadores']}\n")
    
#     # Adjudicatarios
#     if resultado['adjudicatarios']:
#         print(f"🏆 EMPRESA(S) ADJUDICATARIA(S):")
#         print(f"{'-'*60}")
#         for empresa in resultado['adjudicatarios']:
#             mostrar_empresa(empresa)
    
#     # Otras empresas
#     if resultado['otras_empresas']:
#         print(f"\n📋 OTRAS EMPRESAS LICITADORAS:")
#         print(f"{'-'*60}")
#         for empresa in resultado['otras_empresas']:
#             mostrar_empresa(empresa)
    
#     # Metadatos
#     print(f"\n{'='*60}")
#     print(f"ℹ️  Metadatos:")
#     print(f"   - Empresas desde tablas: {resultado['metadatos']['empresas_desde_tablas']}")
#     print(f"   - Empresas desde texto: {resultado['metadatos']['empresas_desde_texto']}")
#     print(f"{'='*60}\n")


# def mostrar_empresa(empresa: Dict):
#     """
#     Muestra información de una empresa de forma formateada.
#     """
#     print(f"\n  • {empresa['nombre']}")
#     if empresa.get('nif'):
#         print(f"    NIF: {empresa['nif']}")
#     if empresa.get('oferta_economica'):
#         print(f"    💰 Oferta: {empresa['oferta_economica']:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.'))
#     if empresa.get('puntuacion_total'):
#         print(f"    ⭐ Puntuación: {empresa['puntuacion_total']:.2f} puntos")


# # ==========================================
# # EXPORTAR A JSON/EXCEL
# # ==========================================

# def exportar_resultados(resultado: Dict, formato: str = 'json', nombre_archivo: str = None):
#     """
#     Exporta los resultados a JSON o Excel.
    
#     Args:
#         resultado: Dict con los resultados del análisis
#         formato: 'json' o 'excel'
#         nombre_archivo: Nombre del archivo de salida (opcional)
#     """
#     if nombre_archivo is None:
#         timestamp = hashlib.md5(str(resultado).encode()).hexdigest()[:8]
#         nombre_archivo = f"licitadores_{timestamp}"
    
#     if formato == 'json':
#         output_path = f"{nombre_archivo}.json"
#         with open(output_path, 'w', encoding='utf-8') as f:
#             json.dump(resultado, f, ensure_ascii=False, indent=2)
#         print(f"✅ Resultados exportados a: {output_path}")
#         return output_path
    
#     elif formato == 'excel':
#         try:
#             import pandas as pd
            
#             # Crear DataFrame
#             df = pd.DataFrame(resultado['todas_empresas'])
            
#             # Reordenar columnas
#             columnas_orden = ['nombre', 'nif', 'oferta_economica', 'puntuacion_total', 'es_adjudicatario']
#             df = df[[col for col in columnas_orden if col in df.columns]]
            
#             # Exportar
#             output_path = f"{nombre_archivo}.xlsx"
#             df.to_excel(output_path, index=False, engine='openpyxl')
#             print(f"✅ Resultados exportados a: {output_path}")
#             return output_path
            
#         except ImportError:
#             print("⚠️ pandas y openpyxl son necesarios para exportar a Excel")
#             print("   Instalar con: pip install pandas openpyxl")
#             return None


# # ==========================================
# # EJECUCIÓN PRINCIPAL
# # ==========================================

# if __name__ == "__main__":
#     # URLs de ejemplo
#     urls_prueba = [
#         "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=KqdVeoilEmM%2B4vM6li8pUZp8Wy512jN4pHGgHXJWNpo2JfnWQeV0okW8cBCtmQP8LOFnuXZdXlAHRRtrrIO2x8KsckmfnNxJeXaRLl1/JaG1aXEvq3KHa/AEHgtDrQw0",
#         "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=ya6B%2BEL7pV4MpNcyaU0AFhRWd60f4%2BsE22u6VnfmCMf0pCcTdwkSxwFERS3X2b5mUT28MuPDHv7RWamAXO7Uani%2BLnUer%2BrjRwJs5QnfbKn3GVhXrFFqN7yFncy7YfRK",
#         "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=DjQANl8zG%2BZqxiZzAExtKh5e67j0yR8uN0NBKNVHEvONiKme6YUoEgPQnoPHa6P09xwrsWDWsY7wuxfoFvy5G5Qs1ma2HBNgmk9XIIGnnFeCx2e6p7hqtlp2aFupgHMr",
#     ]
    
#     # Probar con el primer PDF
#     url_pdf = urls_prueba[0]
    
#     print(f"Procesando: {url_pdf[:80]}...\n")
    
#     # Ejecutar análisis
#     resultado = analizar_licitadores_completo(url_pdf)
    
#     # Mostrar resultados
#     mostrar_resultados(resultado)
    
#     # Exportar
#     exportar_resultados(resultado, formato='json', nombre_archivo='licitadores_analisis')
    
#     # Si tienes pandas instalado, también exportar a Excel
#     # exportar_resultados(resultado, formato='excel', nombre_archivo='licitadores_analisis')

import time 

import fitz  # PyMuPDF
import re
import json
from typing import List, Dict, Optional, Tuple
import io
import requests
import hashlib
import camelot
import tempfile
import os
from pathlib import Path

# ==========================================
# CONFIGURACIÓN DE MODELOS LLM
# ==========================================

LLM_CONFIG = {
    "default_model": "qwen2.5:32b",
    "alternative_models": [
        "qwen2.5:32b",
        "qwen2.5:14b", 
        "llama3.2:3b",
        "deepseek-r1:14b"
    ],
    "api_url": "http://localhost:11434/api/generate",
    "timeout": 600,  # 10 minutos
}


def extract_text_from_pdf(path_or_url):
    """
    Extrae texto de un PDF, desde una ruta local o una URL.
    """
    try:
        # Detectar si es URL
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            print(f"📥 Descargando PDF desde URL...")
            response = requests.get(path_or_url, timeout=30)
            response.raise_for_status()
            pdf_bytes = io.BytesIO(response.content)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            print(f"📂 Abriendo PDF local: {path_or_url}")
            doc = fitz.open(path_or_url)

        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"

        text = re.sub(r"\s+", " ", text)
        doc.close()
        return text.strip()

    except Exception as e:
        print(f"⚠️ Error leyendo PDF ({path_or_url}): {e}")
        return ""


# ==========================================
# FUNCIONES DE INTERACCIÓN CON LLM
# ==========================================

def llamar_llm(prompt: str, modelo: str = None, temperatura: float = 0.1) -> str:
    """
    Llama a un modelo LLM local vía Ollama API.
    
    Args:
        prompt: El prompt a enviar al modelo
        modelo: Nombre del modelo (usa default_model si es None)
        temperatura: Control de creatividad (0.0 = determinista, 1.0 = creativo)
    
    Returns:
        Respuesta del modelo como string
    """
    if modelo is None:
        modelo = LLM_CONFIG["default_model"]
    
    url = LLM_CONFIG["api_url"]
    
    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 8192,
            "temperature": temperatura,
            "top_p": 0.9,
        }
    }
    
    try:
        print(f"🤖 Consultando a {modelo}...")
        response = requests.post(url, json=payload, timeout=LLM_CONFIG["timeout"])
        response.raise_for_status()
        
        resultado = response.json()
        respuesta = resultado.get('response', '')
        
        return respuesta.strip()
        
    except requests.exceptions.Timeout:
        print(f"⚠️ Timeout esperando respuesta del modelo {modelo}")
        return ""
    except requests.exceptions.ConnectionError:
        print(f"⚠️ No se pudo conectar a Ollama. ¿Está ejecutándose?")
        print(f"   Ejecuta: ollama serve")
        return ""
    except Exception as e:
        print(f"⚠️ Error llamando al LLM: {e}")
        return ""


def extraer_json_de_respuesta(respuesta: str) -> Optional[Dict]:
    """
    Extrae JSON de la respuesta del LLM, incluso si viene con texto adicional.
    """
    # Buscar bloques JSON entre ```json y ```
    patron_markdown = r'```json\s*(.*?)\s*```'
    match = re.search(patron_markdown, respuesta, re.DOTALL)
    
    if match:
        json_str = match.group(1)
    else:
        # Intentar encontrar JSON directamente
        # Buscar desde { hasta }
        inicio = respuesta.find('{')
        if inicio == -1:
            inicio = respuesta.find('[')
        
        if inicio != -1:
            # Encontrar el cierre correspondiente
            json_str = respuesta[inicio:]
            # Intentar parsear progresivamente
            for i in range(len(json_str), 0, -1):
                try:
                    return json.loads(json_str[:i])
                except:
                    continue
        
        json_str = respuesta
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"⚠️ No se pudo parsear JSON: {e}")
        print(f"Respuesta recibida: {respuesta[:200]}...")
        return None


# ==========================================
# EXTRACCIÓN INTELIGENTE CON LLM
# ==========================================

def extraer_empresas_con_llm(texto: str, modelo: str = None) -> List[Dict]:
    """
    Usa un LLM para extraer información de empresas licitadoras del texto.
    Mucho más robusto que regex puro.
    
    Args:
        texto: Texto del PDF
        modelo: Modelo LLM a usar
    
    Returns:
        Lista de empresas con su información
    """
    
    # Limitar el texto si es muy largo (los primeros 6000 caracteres suelen contener lo importante)
    texto_procesable = texto[:8000] if len(texto) > 8000 else texto
    
    prompt = f"""Eres un experto en análisis de documentos de licitaciones públicas españolas.

Tu tarea es extraer TODA la información sobre empresas licitadoras del siguiente texto.

TEXTO DEL DOCUMENTO:
{texto_procesable}

INSTRUCCIONES:
1. Identifica TODAS las empresas mencionadas (licitadoras, adjudicatarias, contratistas)
2. Para cada empresa extrae:
   - Nombre completo (razón social)
   - NIF/CIF si aparece
   - Oferta económica (importe, precio, oferta) en euros
   - Puntuación total si aparece
   - Si es adjudicataria (ganadora del contrato)

FORMATO DE SALIDA:
Responde ÚNICAMENTE con un JSON válido, sin texto adicional, en este formato exacto:

```json
{{
  "empresas": [
    {{
      "nombre": "NOMBRE COMPLETO DE LA EMPRESA S.L.",
      "nif": "B12345678",
      "oferta_economica": 125000.50,
      "puntuacion_total": 95.5,
      "es_adjudicatario": true
    }},
    {{
      "nombre": "OTRA EMPRESA S.A.",
      "nif": "A87654321",
      "oferta_economica": 130000.00,
      "puntuacion_total": 88.3,
      "es_adjudicatario": false
    }}
  ]
}}
```

REGLAS IMPORTANTES:
- Si un campo no aparece, usa null (no inventes datos)
- oferta_economica debe ser un número (sin puntos de miles, usa punto decimal)
- es_adjudicatario debe ser true o false
- El JSON debe ser válido y parseable
- NO incluyas texto antes o después del JSON
- Si no encuentras empresas, devuelve: {{"empresas": []}}

Responde SOLO con el JSON:"""

    respuesta = llamar_llm(prompt, modelo=modelo, temperatura=0.1)
    
    if not respuesta:
        return []
    
    # Extraer JSON de la respuesta
    datos = extraer_json_de_respuesta(respuesta)
    
    if datos and 'empresas' in datos:
        empresas = datos['empresas']
        
        # Validar y limpiar datos
        empresas_validadas = []
        for empresa in empresas:
            if empresa.get('nombre'):
                empresa_limpia = {
                    'nombre': empresa.get('nombre', '').strip(),
                    'nif': empresa.get('nif', None),
                    'oferta_economica': empresa.get('oferta_economica', None),
                    'puntuacion_total': empresa.get('puntuacion_total', None),
                    'es_adjudicatario': empresa.get('es_adjudicatario', False),
                    'origen': 'llm'
                }
                empresas_validadas.append(empresa_limpia)
        
        return empresas_validadas
    
    return []


def extraer_licitadores_por_chunks(texto: str, modelo: str = None, chunk_size: int = 6000) -> List[Dict]:
    """
    Para documentos muy largos, divide el texto en chunks y analiza cada uno.
    Luego combina los resultados eliminando duplicados.
    """
    
    # Si el texto es corto, procesarlo de una vez
    if len(texto) <= chunk_size:
        return extraer_empresas_con_llm(texto, modelo=modelo)
    
    print(f"📄 Documento largo ({len(texto)} caracteres), dividiendo en chunks...")
    
    # Dividir en chunks con overlap
    chunks = []
    overlap = 500  # Caracteres de overlap para no perder contexto
    
    i = 0
    while i < len(texto):
        fin = min(i + chunk_size, len(texto))
        chunk = texto[i:fin]
        chunks.append(chunk)
        i += chunk_size - overlap
    
    print(f"   Procesando {len(chunks)} chunks...")
    
    # Procesar cada chunk
    todas_empresas = []
    for idx, chunk in enumerate(chunks, 1):
        print(f"   Chunk {idx}/{len(chunks)}...")
        empresas_chunk = extraer_empresas_con_llm(chunk, modelo=modelo)
        todas_empresas.extend(empresas_chunk)
    
    # Deduplicar empresas
    empresas_unicas = deduplicar_empresas_llm(todas_empresas)
    
    print(f"   ✓ {len(empresas_unicas)} empresas únicas encontradas")
    
    return empresas_unicas


def deduplicar_empresas_llm(empresas: List[Dict]) -> List[Dict]:
    """
    Deduplica empresas combinando información de múltiples menciones.
    """
    empresas_dict = {}
    
    for empresa in empresas:
        nombre = empresa['nombre']
        nombre_normalizado = normalizar_nombre_empresa(nombre)
        
        if nombre_normalizado not in empresas_dict:
            empresas_dict[nombre_normalizado] = empresa
        else:
            # Combinar información (completar campos None)
            empresa_existente = empresas_dict[nombre_normalizado]
            
            # Mantener el nombre más completo
            if len(empresa['nombre']) > len(empresa_existente['nombre']):
                empresa_existente['nombre'] = empresa['nombre']
            
            # Completar campos que sean None
            for campo in ['nif', 'oferta_economica', 'puntuacion_total']:
                if empresa_existente.get(campo) is None and empresa.get(campo) is not None:
                    empresa_existente[campo] = empresa[campo]
            
            # Si alguna menciona que es adjudicatario, marcar como tal
            if empresa.get('es_adjudicatario', False):
                empresa_existente['es_adjudicatario'] = True
    
    return list(empresas_dict.values())


def normalizar_nombre_empresa(nombre: str) -> str:
    """
    Normaliza un nombre de empresa para comparación.
    """
    # Convertir a minúsculas
    nombre = nombre.lower()
    
    # Eliminar formas societarias para comparar mejor
    nombre = re.sub(r'\b(s\.?l\.?|s\.?a\.?|s\.?l\.?l\.?|ute|aie|s\.?coop)\b', '', nombre)
    
    # Eliminar puntos y comas
    nombre = nombre.replace('.', '').replace(',', '')
    
    # Normalizar espacios
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    
    return nombre


# ==========================================
# EXTRACCIÓN DESDE TABLAS (CAMELOT)
# ==========================================

def extraer_empresas_desde_tablas(path_or_url: str) -> List[Dict]:
    """
    Extrae información de empresas desde tablas usando Camelot.
    """
    temp_file_path = None
    empresas = []
    
    try:
        # Preparar archivo para Camelot
        if path_or_url.startswith(("http://", "https://")):
            print(f"📥 Descargando PDF para análisis de tablas...")
            response = requests.get(path_or_url, timeout=30)
            response.raise_for_status()
            
            fd, temp_file_path = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(response.content)
            path_a_procesar = temp_file_path
        else:
            path_a_procesar = path_or_url

        # Extraer tablas
        print(f"📊 Extrayendo tablas con Camelot...")
        
        try:
            tablas = camelot.read_pdf(path_a_procesar, pages='all', flavor='lattice')
            
            if len(tablas) == 0:
                # Intentar con otro método
                tablas = camelot.read_pdf(path_a_procesar, pages='all', flavor='stream')
        except Exception as e:
            print(f"⚠️ Error con Camelot: {e}")
            return []
        
        print(f"   ✓ {len(tablas)} tabla(s) encontrada(s)")
        
        # Si hay tablas, usar LLM para analizarlas
        if len(tablas) > 0:
            empresas = analizar_tablas_con_llm(tablas)
        
        return empresas

    except Exception as e:
        print(f"⚠️ Error extrayendo tablas: {e}")
        return []

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass


def analizar_tablas_con_llm(tablas, modelo: str = None) -> List[Dict]:
    """
    Usa un LLM para analizar tablas extraídas y obtener información estructurada.
    """
    empresas_todas = []
    
    for i, tabla in enumerate(tablas):
        print(f"   Analizando tabla {i+1} con LLM...")
        
        # Convertir tabla a formato texto legible
        df = tabla.df
        tabla_texto = df.to_string(index=False)
        
        # Si la tabla es muy grande, tomar solo las primeras filas relevantes
        if len(tabla_texto) > 4000:
            # Tomar headers + primeras 20 filas
            lineas = tabla_texto.split('\n')
            tabla_texto = '\n'.join(lineas[:22])
        
        prompt = f"""Analiza la siguiente tabla extraída de un documento de licitación pública.

TABLA {i+1}:
{tabla_texto}

TAREA:
Extrae información de todas las empresas licitadoras que aparecen en esta tabla.

FORMATO DE SALIDA:
Responde SOLO con JSON válido en este formato:

```json
{{
  "empresas": [
    {{
      "nombre": "NOMBRE EMPRESA",
      "nif": "B12345678",
      "oferta_economica": 125000.50,
      "puntuacion_total": 95.5,
      "es_adjudicatario": true
    }}
  ]
}}
```

REGLAS:
- Si un dato no aparece en la tabla, usa null
- oferta_economica debe ser número (sin separadores de miles)
- Si no hay empresas en la tabla, devuelve {{"empresas": []}}
- NO inventes datos que no estén en la tabla

Responde:"""

        respuesta = llamar_llm(prompt, modelo=modelo, temperatura=0.0)
        
        if respuesta:
            datos = extraer_json_de_respuesta(respuesta)
            if datos and 'empresas' in datos:
                for empresa in datos['empresas']:
                    if empresa.get('nombre'):
                        empresa['origen'] = 'tabla_llm'
                        empresas_todas.append(empresa)
    
    return empresas_todas


# ==========================================
# ANÁLISIS ENRIQUECIDO CON LLM
# ==========================================

def enriquecer_datos_con_llm(empresas: List[Dict], texto_completo: str, modelo: str = None) -> List[Dict]:
    """
    Usa el LLM para enriquecer los datos de empresas con información contextual.
    Por ejemplo, si falta la oferta económica, buscarla en el texto.
    """
    
    print(f"🔍 Enriqueciendo datos de {len(empresas)} empresas con LLM...")
    
    # Para cada empresa que tenga campos None, intentar completarlos
    empresas_incompletas = [e for e in empresas if e.get('oferta_economica') is None or e.get('nif') is None]
    
    if not empresas_incompletas:
        return empresas
    
    # Crear contexto con las empresas a enriquecer
    nombres_empresas = [e['nombre'] for e in empresas_incompletas]
    
    # Limitar texto
    texto_limitado = texto_completo[:6000]
    
    prompt = f"""Tienes un documento de licitación y una lista de empresas.
Tu tarea es buscar en el texto información adicional sobre estas empresas.

EMPRESAS A BUSCAR:
{json.dumps(nombres_empresas, ensure_ascii=False, indent=2)}

TEXTO DEL DOCUMENTO:
{texto_limitado}

TAREA:
Para cada empresa, busca en el texto:
- NIF/CIF si no lo tiene
- Oferta económica (precio, importe) si no la tiene
- Puntuación si no la tiene

FORMATO DE SALIDA (JSON válido):
```json
{{
  "datos_adicionales": [
    {{
      "nombre": "EMPRESA X S.L.",
      "nif_encontrado": "B12345678",
      "oferta_encontrada": 125000.00,
      "puntuacion_encontrada": 95.5
    }}
  ]
}}
```

Si no encuentras un dato, usa null.
Responde SOLO con el JSON:"""

    respuesta = llamar_llm(prompt, modelo=modelo, temperatura=0.1)
    
    if respuesta:
        datos = extraer_json_de_respuesta(respuesta)
        if datos and 'datos_adicionales' in datos:
            # Actualizar empresas con los datos encontrados
            for dato in datos['datos_adicionales']:
                nombre = dato.get('nombre', '')
                
                # Buscar la empresa correspondiente
                for empresa in empresas:
                    if normalizar_nombre_empresa(empresa['nombre']) == normalizar_nombre_empresa(nombre):
                        # Actualizar solo si el campo está vacío
                        if empresa.get('nif') is None and dato.get('nif_encontrado'):
                            empresa['nif'] = dato['nif_encontrado']
                        if empresa.get('oferta_economica') is None and dato.get('oferta_encontrada'):
                            empresa['oferta_economica'] = dato['oferta_encontrada']
                        if empresa.get('puntuacion_total') is None and dato.get('puntuacion_encontrada'):
                            empresa['puntuacion_total'] = dato['puntuacion_encontrada']
                        break
    
    return empresas


# ==========================================
# FUNCIÓN PRINCIPAL CON LLM
# ==========================================

def analizar_licitadores_con_llm(path_or_url: str, modelo: str = None, usar_tablas: bool = True) -> Dict:
    """
    Análisis completo de empresas licitadoras usando LLM.
    
    Args:
        path_or_url: Ruta o URL del PDF
        modelo: Modelo LLM a usar (default: qwen2.5:32b)
        usar_tablas: Si usar también extracción de tablas con Camelot
    
    Returns:
        Dict con toda la información estructurada
    """
    
    print(f"\n{'='*60}")
    print(f"🤖 ANÁLISIS DE LICITADORES CON LLM")
    print(f"   Modelo: {modelo or LLM_CONFIG['default_model']}")
    print(f"{'='*60}\n")
    
    # 1. Extraer texto
    print("📄 Paso 1: Extrayendo texto del PDF...")
    texto = extract_text_from_pdf(path_or_url)
    print(f"   ✓ {len(texto)} caracteres extraídos\n")
    
    if not texto:
        print("❌ No se pudo extraer texto del PDF")
        return {
            'total_licitadores': 0,
            'adjudicatarios': [],
            'otras_empresas': [],
            'todas_empresas': [],
            'metadatos': {'error': 'No se pudo extraer texto'}
        }
    
    # 2. Extraer desde tablas (opcional)
    empresas_tablas = []
    if usar_tablas:
        print("📊 Paso 2: Extrayendo desde tablas con Camelot + LLM...")
        empresas_tablas = extraer_empresas_desde_tablas(path_or_url)
        print(f"   ✓ {len(empresas_tablas)} empresa(s) desde tablas\n")
    
    # 3. Extraer desde texto con LLM
    print("🤖 Paso 3: Analizando texto con LLM...")
    empresas_texto = extraer_licitadores_por_chunks(texto, modelo=modelo)
    print(f"   ✓ {len(empresas_texto)} empresa(s) desde texto\n")
    
    # 4. Combinar resultados
    print("🔗 Paso 4: Combinando y deduplicando información...")
    todas_empresas = empresas_tablas + empresas_texto
    empresas_unicas = deduplicar_empresas_llm(todas_empresas)
    print(f"   ✓ {len(empresas_unicas)} empresa(s) únicas\n")
    
    # 5. Enriquecer datos (completar campos faltantes)
    print("✨ Paso 5: Enriqueciendo datos con contexto adicional...")
    empresas_enriquecidas = enriquecer_datos_con_llm(empresas_unicas, texto, modelo=modelo)
    print(f"   ✓ Datos enriquecidos\n")
    
    # 6. Ordenar (adjudicatarios primero, luego por puntuación)
    empresas_enriquecidas.sort(
        key=lambda x: (
            not x.get('es_adjudicatario', False),
            -(x.get('puntuacion_total') or 0)
        )
    )
    
    # 7. Preparar resultado
    adjudicatarios = [e for e in empresas_enriquecidas if e.get('es_adjudicatario', False)]
    otras = [e for e in empresas_enriquecidas if not e.get('es_adjudicatario', False)]
    
    resultado = {
        'total_licitadores': len(empresas_enriquecidas),
        'adjudicatarios': adjudicatarios,
        'otras_empresas': otras,
        'todas_empresas': empresas_enriquecidas,
        'metadatos': {
            'url_origen': path_or_url if path_or_url.startswith('http') else None,
            'empresas_desde_tablas': len(empresas_tablas),
            'empresas_desde_texto': len(empresas_texto),
            'modelo_usado': modelo or LLM_CONFIG['default_model'],
            'metodo': 'LLM + Tablas' if usar_tablas else 'LLM puro'
        }
    }
    
    return resultado


# ==========================================
# FUNCIONES DE UTILIDAD
# ==========================================

def mostrar_resultados(resultado: Dict):
    """
    Muestra los resultados de forma legible en consola.
    """
    print(f"\n{'='*60}")
    print(f"📊 RESULTADOS DEL ANÁLISIS")
    print(f"{'='*60}\n")
    
    print(f"Total de empresas identificadas: {resultado['total_licitadores']}")
    print(f"Método usado: {resultado['metadatos'].get('metodo', 'N/A')}")
    print(f"Modelo LLM: {resultado['metadatos'].get('modelo_usado', 'N/A')}\n")
    
    # Adjudicatarios
    if resultado['adjudicatarios']:
        print(f"🏆 EMPRESA(S) ADJUDICATARIA(S):")
        print(f"{'-'*60}")
        for empresa in resultado['adjudicatarios']:
            mostrar_empresa(empresa)
    
    # Otras empresas
    if resultado['otras_empresas']:
        print(f"\n📋 OTRAS EMPRESAS LICITADORAS:")
        print(f"{'-'*60}")
        for empresa in resultado['otras_empresas']:
            mostrar_empresa(empresa)
    
    # Metadatos
    print(f"\n{'='*60}")
    print(f"ℹ️  Metadatos:")
    print(f"   - Empresas desde tablas: {resultado['metadatos'].get('empresas_desde_tablas', 0)}")
    print(f"   - Empresas desde texto: {resultado['metadatos'].get('empresas_desde_texto', 0)}")
    print(f"{'='*60}\n")


def mostrar_empresa(empresa: Dict):
    """
    Muestra información de una empresa de forma formateada.
    """
    print(f"\n  • {empresa['nombre']}")
    if empresa.get('nif'):
        print(f"    NIF: {empresa['nif']}")
    if empresa.get('oferta_economica') is not None:
        oferta = empresa['oferta_economica']
        print(f"    💰 Oferta: {oferta:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.'))
    if empresa.get('puntuacion_total') is not None:
        print(f"    ⭐ Puntuación: {empresa['puntuacion_total']:.2f} puntos")
    print(f"    📌 Origen: {empresa.get('origen', 'desconocido')}")


def exportar_resultados(resultado: Dict, formato: str = 'json', nombre_archivo: str = None):
    """
    Exporta los resultados a JSON o Excel.
    """
    if nombre_archivo is None:
        timestamp = hashlib.md5(str(resultado).encode()).hexdigest()[:8]
        nombre_archivo = f"licitadores_llm_{timestamp}"
    
    if formato == 'json':
        output_path = f"{nombre_archivo}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        print(f"✅ Resultados exportados a: {output_path}")
        return output_path
    
    elif formato == 'excel':
        try:
            import pandas as pd
            
            df = pd.DataFrame(resultado['todas_empresas'])
            
            # Reordenar columnas
            columnas_orden = ['nombre', 'nif', 'oferta_economica', 'puntuacion_total', 'es_adjudicatario', 'origen']
            df = df[[col for col in columnas_orden if col in df.columns]]
            
            output_path = f"{nombre_archivo}.xlsx"
            df.to_excel(output_path, index=False, engine='openpyxl')
            print(f"✅ Resultados exportados a: {output_path}")
            return output_path
            
        except ImportError:
            print("⚠️ pandas y openpyxl son necesarios para exportar a Excel")
            return None


# ==========================================
# EJECUCIÓN DE PRUEBA
# ==========================================

def ejecutador_principal(url_pdf):
    # Probar con el primer PDF
    # inicio_proceso = time.perf_counter()
    url_pdf = urls_prueba[0]
    
    print(f"Procesando: {url_pdf[:80]}...\n")
    
    # Ejecutar análisis
    resultado = analizar_licitadores_con_llm(
        url_pdf, 
        modelo="qwen2.5:32b",  # Puedes cambiar por "qwen2.5:14b", "llama3.2:3b", etc.
        usar_tablas=True
    )
    
    # # 2. MARCAR EL FINAL
    # fin_proceso = time.perf_counter()
    
    # # 3. CALCULAR DURACIÓN
    # duracion_total = fin_proceso - inicio_proceso
    # minutos = int(duracion_total // 60)
    # segundos = duracion_total % 60
    
    # Mostrar resultados
    # mostrar_resultados(resultado)
    
    # 4. MOSTRAR TIEMPO EN PANTALLA
    # print(f"{'='*60}")
    # print(f"⏱️  TIEMPO DE EJECUCIÓN TOTAL: {minutos}m {segundos:.2f}s")
    # print(f"{'='*60}\n")
    
    # Exportar
    # exportar_resultados(resultado, formato='json', nombre_archivo='licitadores_llm')
    
    # print("\n✅ Análisis completado")
    return resultado
    

if __name__ == "__main__":
    # URLs de prueba
    urls_prueba = [
        # "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=KqdVeoilEmM%2B4vM6li8pUZp8Wy512jN4pHGgHXJWNpo2JfnWQeV0okW8cBCtmQP8LOFnuXZdXlAHRRtrrIO2x8KsckmfnNxJeXaRLl1/JaG1aXEvq3KHa/AEHgtDrQw0",
        # "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=ya6B%2BEL7pV4MpNcyaU0AFhRWd60f4%2BsE22u6VnfmCMf0pCcTdwkSxwFERS3X2b5mUT28MuPDHv7RWamAXO7Uani%2BLnUer%2BrjRwJs5QnfbKn3GVhXrFFqN7yFncy7YfRK",
        # "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=DjQANl8zG%2BZqxiZzAExtKh5e67j0yR8uN0NBKNVHEvONiKme6YUoEgPQnoPHa6P09xwrsWDWsY7wuxfoFvy5G5Qs1ma2HBNgmk9XIIGnnFeCx2e6p7hqtlp2aFupgHMr",
        "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=S%2BxuNQrrvx0cAhvvAsvnqvyjYsS18BUwuu8A9VtlvYKC4ExvlYYkzGD4eDbWjB/VS3Pxrag7FL6NdUzmoYZ%2BIQDR96i17/9S%2B2%2B1/WsT%2BH97QB3HKyQaFUExmUVQCerk",
        "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=v4VLq9HbR/uL8VtceWUSYqnEaKB9mvtNknmnNwidcfhzCi7TuRxdbGHHPrBXWg1%2Blx56pGSlb3cybGlbEAw/diI9KTSkp7mkTJmfK8Z8Y1g//q7NB2iMZvNyf0xrJmjt",
    ]
    
#     print("""
# ╔═══════════════════════════════════════════════════════════╗
# ║   EXTRACTOR DE LICITADORES CON LLM (Qwen 2.5 32B)        ║
# ╚═══════════════════════════════════════════════════════════╝

# IMPORTANTE: Asegúrate de tener Ollama ejecutándose:
#   $ ollama serve
  
# Y el modelo descargado:
#   $ ollama pull qwen2.5:32b

# Presiona Enter para continuar o Ctrl+C para cancelar...
#     """)
    
#     input()
    
    # Probar con el primer PDF
    inicio_proceso = time.perf_counter()
    url_pdf = urls_prueba[0]
    
    print(f"Procesando: {url_pdf[:80]}...\n")
    
    # Ejecutar análisis
    resultado = analizar_licitadores_con_llm(
        url_pdf, 
        modelo="qwen2.5:32b",  # Puedes cambiar por "qwen2.5:14b", "llama3.2:3b", etc.
        usar_tablas=True
    )
    
    # 2. MARCAR EL FINAL
    fin_proceso = time.perf_counter()
    
    # 3. CALCULAR DURACIÓN
    duracion_total = fin_proceso - inicio_proceso
    minutos = int(duracion_total // 60)
    segundos = duracion_total % 60
    
    # Mostrar resultados
    mostrar_resultados(resultado)
    
    # 4. MOSTRAR TIEMPO EN PANTALLA
    print(f"{'='*60}")
    print(f"⏱️  TIEMPO DE EJECUCIÓN TOTAL: {minutos}m {segundos:.2f}s")
    print(f"{'='*60}\n")
    
    # Exportar
    exportar_resultados(resultado, formato='json', nombre_archivo='licitadores_llm')
    
    print("\n✅ Análisis completado")
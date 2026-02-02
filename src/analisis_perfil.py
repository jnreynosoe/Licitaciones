# import pandas as pd
# import os
# import re
# import requests
# import tempfile
# from paddleocr import PaddleOCR
# import fitz  # PyMuPDF

# # ============================================================================
# # CONFIGURACIÓN Y PERFIL DE EMPRESA
# # ============================================================================

# perfil_enetic = {
#     "lugares": [
#         "Comunidad Valenciana",
#         "Albacete", "Murcia", "Valencia"
#     ],
#     "sectores": [
#         "Infraestructura IT",
#         "Ciberseguridad",
#         "Servidores",
#         "Storage",
#         "Redes"
#     ],
#     "empresas_partner": [
#         "DELL", 
#         "Huawei", 
#         "Veeam", 
#         "VMware", 
#         "Broadcom", 
#         "Watchguard", 
#         "Eset", 
#         "Qnap"
#     ],
#     "certificaciones": [
#         "ISO28001", "ISO 28001", 
#         "ISO27017", "ISO 27017",
#         "ISO22301", "ISO 22301",
#         "NIS2", "ENS"
#     ],
#     "certificaciones_descarte": [
#         "ISO9001", "ISO 9001",
#         "ISO14001", "ISO 14001",
#     ],
#     "terminos_excluyentes": [
#         "obra civil", "construcción", "limpieza", "catering",
#         "mobiliario", "papelería", "imprenta", "transporte",
#         "mantenimiento edificios", "jardinería", "fontanería",
#         "electricidad", "climatización", "ascensores"
#     ],
#     "cpv_relevantes": [
#         '48',      # Paquetes de software y sistemas de información
#         '72',      # Servicios de tecnología de la información
#         '30213',   # Ordenadores personales
#         '30231',   # Monitores y consolas
#         '32420',   # Dispositivos de red
#         '48820',   # Servidores
#         '71356',   # Servicios técnicos de seguridad
#         '79342',   # Servicios de marketing y publicidad (a veces IT)
#         "30000000","30100000","30200000","30210000","30230000","32000000","32400000",
#         "32500000","48000000","48510000","48600000","48620000","48710000","48730000",
#         "48760000","48780000","48800000","50300000","51300000","51600000", 
#     ],
#     "presupuesto_min": 10000,
#     "presupuesto_max": 500000
# }

# # ============================================================================
# # CARGA DE DATOS
# # ============================================================================

# def load_datasets():
#     """Carga todos los datasets necesarios"""
#     base_path = r"data"
    
#     try:
#         df_general = pd.read_parquet("src\data\Pliegos_general.parquet", engine="pyarrow")
#         df_requisitos = pd.read_parquet("src\data\Requisitos_general.parquet", engine="pyarrow")
#         df_criterios = pd.read_parquet("src\data\Criterios_general.parquet", engine="pyarrow")
#         df_docs = pd.read_parquet("src\data\Documentacion_general.parquet", engine="pyarrow")
#     except Exception as e:
#         raise RuntimeError(f"❌ Error cargando archivos parquet: {e}")
    
#     try:
#         df_cpv = pd.read_excel("src\data\listado-cpv.xlsx", header=None)
#         df_cpv = df_cpv.iloc[6:, [0, 1]]
#         df_cpv.columns = ["codigo", "descripcion"]
#     except Exception as e:
#         print(f"⚠️ No se pudo cargar listado-cpv.xlsx: {e}")
#         df_cpv = pd.DataFrame(columns=["codigo", "descripcion"])

#     return df_general, df_requisitos, df_criterios, df_docs, df_cpv

# # ============================================================================
# # MÓDULO 1: DESCARGA Y EXTRACCIÓN DE TEXTO (EJECUTAR POR SEPARADO)
# # ============================================================================

# def descargar_pdf(url):
#     """Descarga un PDF desde una URL y devuelve la ruta temporal"""
#     response = requests.get(url, timeout=30)
#     response.raise_for_status()
    
#     temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
#     temp.write(response.content)
#     temp.close()
    
#     return temp.name

# def extract_text_from_pdf(pdf_path, ocr):
#     """Extrae texto de PDF usando PyMuPDF y PaddleOCR como fallback"""
#     text_pages = []
#     doc = fitz.open(pdf_path)

#     for page in doc:
#         text = page.get_text("text")
#         if not text.strip():
#             # Fallback a OCR si no hay texto
#             pix = page.get_pixmap()
#             result = ocr.ocr(pix.tobytes())
#             if result and result[0]:
#                 text = "\n".join([line[1][0] for line in result[0]])
#         text_pages.append(text)

#     doc.close()
#     return "\n".join(text_pages)

# def procesar_y_guardar_textos(df_general, df_docs, dias=15, output_path="data/textos_extraidos.parquet"):
#     """
#     PASO 1: Descarga PDFs, extrae texto y guarda en archivo
#     ESTE PROCESO ES LENTO - EJECUTAR UNA VEZ Y REUTILIZAR
#     """
#     print("🔄 Iniciando descarga y extracción de textos...")
    
#     # Filtrar por días
#     df_general["FECHA_LIMITE"] = pd.to_datetime(df_general["FECHA_LIMITE"], errors="coerce")
#     hoy = pd.Timestamp.today().normalize()
#     limite = hoy + pd.Timedelta(days=dias)
#     df_filtradas = df_general[df_general["FECHA_LIMITE"] >= limite]
#     df_filtradas = df_filtradas.sort_values("FECHA_LIMITE", ascending=True)
    
#     # Filtrar documentos
#     df_docs_filtrados = df_docs[df_docs["pliego_id"].isin(df_filtradas["ID"])]
#     df_docs_filtrados = df_docs_filtrados.dropna(subset=["URI"])
#     df_docs_filtrados = df_docs_filtrados[df_docs_filtrados["DESCRIPCION"].str.endswith(".pdf", na=False)]
    
#     print(f"📄 Documentos a procesar: {len(df_docs_filtrados)}")
    
#     # Inicializar OCR una sola vez
#     ocr = PaddleOCR(lang='es', use_angle_cls=True, show_log=False)
    
#     textos_extraidos = []
#     errores = []
    
#     for idx, row in df_docs_filtrados.iterrows():
#         try:
#             print(f"⏳ Procesando {idx+1}/{len(df_docs_filtrados)}: {row['DESCRIPCION'][:50]}...")
#             ruta_pdf = descargar_pdf(row["URI"])
#             texto = extract_text_from_pdf(ruta_pdf, ocr)
            
#             textos_extraidos.append({
#                 "pliego_id": row["pliego_id"],
#                 "DESCRIPCION": row["DESCRIPCION"],
#                 "URI": row["URI"],
#                 "TEXTO_EXTRAIDO": texto,
#                 "TEXTO_NORM": texto.lower() if texto else ""
#             })
            
#             # Limpiar archivo temporal
#             os.unlink(ruta_pdf)
            
#         except Exception as e:
#             errores.append({"pliego_id": row["pliego_id"], "error": str(e)})
#             print(f"❌ Error en {row['DESCRIPCION']}: {e}")
    
#     # Guardar resultados
#     df_textos = pd.DataFrame(textos_extraidos)
#     df_textos.to_parquet(output_path, engine="pyarrow")
    
#     print(f"\n✅ Textos extraídos: {len(df_textos)}")
#     print(f"❌ Errores: {len(errores)}")
#     print(f"💾 Guardado en: {output_path}")
    
#     if errores:
#         pd.DataFrame(errores).to_csv("data/errores_extraccion.csv", index=False)
    
#     return df_textos

# # ============================================================================
# # MÓDULO 2: FUNCIONES DE ANÁLISIS (RÁPIDO - USAR DESPUÉS DE EXTRACCIÓN)
# # ============================================================================

# def buscar_palabra_exacta(texto, palabra):
#     """Busca palabra completa usando word boundaries, evita falsos positivos"""
#     patron = r'\b' + re.escape(palabra.lower()) + r'\b'
#     return bool(re.search(patron, texto))

# def buscar_variantes(texto, terminos):
#     """Busca cualquier variante de un término (ej: ISO28001, ISO 28001)"""
#     return any(buscar_palabra_exacta(texto, termino) for termino in terminos)

# def analizar_cpv_relevantes(pliego_id, df_general, cpv_relevantes):
#     """Identifica si los CPV del pliego son relevantes para IT"""
#     row = df_general[df_general['ID'] == pliego_id]
    
#     if row.empty or 'CPV' not in row.columns:
#         return False, []
    
#     cpvs_str = str(row['CPV'].values[0])
#     # print("CPVS", cpvs_str[0])
#     if pd.isna(cpvs_str) or cpvs_str == 'nan':
#         return False, []
    
#     # Separar CPVs y obtener los primeros dígitos
#     cpvs = [cpv.strip()[:2] for cpv in cpvs_str.split(',') if cpv.strip()]
#     cpvs = row['CPV'].values[0]
#     # print("CVPS", cpvs.values[0])
#     matches = [cpv for cpv in cpvs if cpv in cpv_relevantes]
#     # print(cpv_relevantes)
#     # for cpv in cpvs:
#     #     print(cpv)
#     #     if cpv in cpv_relevantes:
#     #         print(cpv,True)
    
#     return len(matches) > 0, matches

# def analizar_viabilidad_economica(pliego_id, df_general, min_presupuesto, max_presupuesto):
#     """Filtra por rangos de presupuesto razonables"""
#     row = df_general[df_general['ID'] == pliego_id]
    
#     if row.empty or 'PRESUPUESTO_BASE' not in row.columns:
#         return True, "Presupuesto no disponible", None
    
#     presupuesto = row['PRESUPUESTO_BASE'].values[0]
    
#     if pd.isna(presupuesto):
#         return True, "Presupuesto no especificado", None
    
#     if presupuesto < min_presupuesto:
#         return False, "Presupuesto muy bajo", presupuesto
#     if presupuesto > max_presupuesto:
#         return False, "Presupuesto fuera de rango", presupuesto
    
#     return True, "Presupuesto adecuado", presupuesto

# def eliminar_ultimo_separador(s):
#     if s is None:
#         return s

#     s = str(s).strip()

#     # Contar separadores
#     count_dots = s.count(".")
#     count_commas = s.count(",")

#     total_seps = count_dots + count_commas

#     # Si solo tiene un separador, no tocar nada
#     if total_seps <= 1:
#         return s

#     # Buscar la última posición de punto o coma
#     last_dot = s.rfind(".")
#     last_comma = s.rfind(",")

#     last_sep = max(last_dot, last_comma)

#     # Eliminar únicamente ese separador
#     return s[:last_sep] + s[last_sep+1:]


# def analizar_criterios_adjudicacion(pliego_id, df_criterios):
#     """Identifica qué se valora más: precio vs técnica"""
#     criterios = df_criterios[df_criterios['pliego_id'] == pliego_id]
    
#     if criterios.empty:
#         return {'peso_precio': 0, 'peso_tecnico': 0, 'favorable': False}
    
#     peso_precio = criterios[
#         criterios['DESCRIPCION'].str.contains('precio|económico|coste', case=False, na=False)
#     ]['PESO'].sum()
    
#     peso_tecnico = criterios[
#         criterios['DESCRIPCION'].str.contains('técnico|calidad|solvencia técnica', case=False, na=False)
#     ]['PESO'].sum()

#     peso_tecnico = eliminar_ultimo_separador(peso_tecnico)
    
#     return {
#         'peso_precio': peso_precio,
#         'peso_tecnico': peso_tecnico,
#         'favorable': float(peso_tecnico) >= 40  # Favorece empresas técnicas
#     }

# def analizar_requisitos_tecnicos(pliego_id, df_requisitos):
#     """Extrae requisitos técnicos clave"""
#     reqs = df_requisitos[df_requisitos['pliego_id'] == pliego_id]
    
#     if reqs.empty:
#         return {}
    
#     capacidades_clave = {
#         'experiencia_años': r'experiencia.*?(\d+).*?años?',
#         'facturacion_minima': r'facturación.*?(\d+\.?\d*)',
#         'personal_minimo': r'plantilla.*?(\d+).*?trabajadores?'
#     }
    
#     requisitos_detectados = {}
#     texto_completo = ' '.join(reqs['DESCRIPCION'].fillna('').astype(str).str.lower())
    
#     for req_name, patron in capacidades_clave.items():
#         match = re.search(patron, texto_completo)
#         if match:
#             requisitos_detectados[req_name] = match.group(1)
    
#     return requisitos_detectados

# def calcular_score_mejorado(row, perfil, df_general, df_criterios, df_requisitos):
#     """
#     Sistema de scoring completo y mejorado
    
#     Returns: (score, detalles_dict)
#     """
#     score = 0
#     detalles = {
#         'pliego_id': row['pliego_id'],
#         'matches': {},
#         'penalizaciones': [],
#         'warnings': []
#     }
    
#     # texto = row['TEXTO_NORM']
#     texto = row["TEXTO_EXTRAIDO"]
    
#     # ========== CPV (40 puntos) ==========
#     cpv_match, cpvs = analizar_cpv_relevantes(row['pliego_id'], df_general, perfil['cpv_relevantes'])
#     if cpv_match:
#         score += 40
#         detalles['matches']['cpv'] = cpvs
#     else:
#         detalles['warnings'].append('CPV no relevante para IT')
    
#     # ========== UBICACIÓN (25 puntos) ==========
#     lugares_match = [l for l in perfil['lugares'] if buscar_palabra_exacta(texto, l)]
#     if lugares_match:
#         score += 25
#         detalles['matches']['ubicacion'] = lugares_match
    
#     # ========== SECTORES (15 puntos cada uno, max 45) ==========
#     sectores_match = [s for s in perfil['sectores'] if buscar_palabra_exacta(texto, s)]
#     puntos_sector = min(len(sectores_match) * 15, 45)
#     score += puntos_sector
#     if sectores_match:
#         detalles['matches']['sectores'] = sectores_match
    
#     # ========== PARTNERS/FABRICANTES (20 puntos cada uno, max 60) ==========
#     partners_match = [p for p in perfil['empresas_partner'] if buscar_palabra_exacta(texto, p)]
#     puntos_partner = min(len(partners_match) * 20, 60)
#     score += puntos_partner
#     if partners_match:
#         detalles['matches']['partners'] = partners_match
    
#     # ========== CERTIFICACIONES (30 puntos cada una, max 90) ==========
#     # Agrupar certificaciones por familia para buscar variantes
#     cert_familias = {
#         'ISO28001': ['ISO28001', 'ISO 28001'],
#         'ISO27017': ['ISO27017', 'ISO 27017'],
#         'ISO22301': ['ISO22301', 'ISO 22301'],
#         'NIS2': ['NIS2', 'NI S2'],
#         'ENS': ['ENS', 'Esquema Nacional de Seguridad']
#     }
    
#     certs_match = []
#     for familia, variantes in cert_familias.items():
#         if buscar_variantes(texto, variantes):
#             certs_match.append(familia)
    
#     puntos_cert = min(len(certs_match) * 30, 90)
#     score += puntos_cert
#     if certs_match:
#         detalles['matches']['certificaciones'] = certs_match
    
#     # ========== CRITERIOS DE ADJUDICACIÓN (15 puntos) ==========
#     criterios = analizar_criterios_adjudicacion(row['pliego_id'], df_criterios)
#     if criterios['favorable']:
#         score += 15
#         detalles['matches']['criterios_favorables'] = f"Técnico: {criterios['peso_tecnico']}%, Precio: {criterios['peso_precio']}%"
    
#     # ========== PRESUPUESTO (sin puntos, pero filtro) ==========
#     viable, motivo, presupuesto = analizar_viabilidad_economica(
#         row['pliego_id'], df_general, 
#         perfil['presupuesto_min'], perfil['presupuesto_max']
#     )
#     detalles['presupuesto'] = {'viable': viable, 'motivo': motivo, 'valor': presupuesto}
#     if not viable:
#         score -= 50
#         detalles['penalizaciones'].append(motivo)
    
#     # ========== PENALIZACIONES ==========
    
#     # Certificaciones de descarte (-100 puntos)
#     cert_desc_familias = {
#         'ISO9001': ['ISO9001', 'ISO 9001'],
#         'ISO14001': ['ISO14001', 'ISO 14001']
#     }
    
#     certs_descarte = []
#     for familia, variantes in cert_desc_familias.items():
#         if buscar_variantes(texto, variantes):
#             certs_descarte.append(familia)
    
#     if certs_descarte:
#         score -= 100
#         detalles['penalizaciones'].append(f'Certificaciones de descarte: {certs_descarte}')
    
#     # Términos excluyentes (-200 puntos)
#     terminos_excl = [t for t in perfil['terminos_excluyentes'] if buscar_palabra_exacta(texto, t)]
#     if terminos_excl:
#         score -= 200
#         detalles['penalizaciones'].append(f'Términos excluyentes: {terminos_excl}')
    
#     # ========== REQUISITOS TÉCNICOS (informativo) ==========
#     requisitos = analizar_requisitos_tecnicos(row['pliego_id'], df_requisitos)
#     if requisitos:
#         detalles['requisitos_tecnicos'] = requisitos
    
#     # Evitar score negativo
#     score = max(score, 0)
    
#     return score, detalles

# def analizar_licitaciones_completo(df_textos, perfil, df_general, df_criterios, df_requisitos):
#     """
#     Análisis completo de todas las licitaciones con texto extraído
#     """
#     print("🔍 Iniciando análisis de licitaciones...")
    
#     resultados = []
    
#     for idx, row in df_textos.iterrows():
#         score, detalles = calcular_score_mejorado(
#             row, perfil, df_general, df_criterios, df_requisitos
#         )
        
#         # Agregar información básica del pliego
#         pliego_info = df_general[df_general['ID'] == row['pliego_id']]
#         if not pliego_info.empty:
#             detalles['titulo'] = pliego_info['NOMBRE_PROYECTO'].values[0]
#             detalles['organismo'] = pliego_info.get('ENTIDAD', ['N/A']).values[0]
#             detalles['fecha_limite'] = pliego_info['FECHA_LIMITE'].values[0]
        
#         detalles['score'] = score
#         resultados.append(detalles)
    
#     df_resultados = pd.DataFrame(resultados)
    
#     # Clasificar por prioridad
#     df_resultados['PRIORIDAD'] = pd.cut(
#         df_resultados['score'],
#         bins=[-float('inf'), 0, 50, 100, 150, float('inf')],
#         labels=['Descartar', 'Baja', 'Media', 'Alta', 'Muy Alta']
#     )
    
#     df_resultados = df_resultados.sort_values('score', ascending=False)
    
#     print(f"\n✅ Análisis completado: {len(df_resultados)} licitaciones")
#     print("\n📊 Distribución por prioridad:")
#     print(df_resultados['PRIORIDAD'].value_counts().sort_index())
    
#     return df_resultados

# def generar_reporte_resumen(df_resultados, top_n=10):
#     """Genera un reporte resumido de las mejores oportunidades"""
#     print("\n" + "="*80)
#     print(f"🎯 TOP {top_n} LICITACIONES PRIORITARIAS")
#     print("="*80)
    
#     for idx, row in df_resultados.head(top_n).iterrows():
#         print(f"\n{'─'*80}")
#         print(f"🏆 RANKING #{idx+1} | SCORE: {row['score']} | PRIORIDAD: {row['PRIORIDAD']}")
#         print(f"ID: {row['pliego_id']}")
#         print(f"📋 Título: {row.get('titulo', 'N/A')[:100]}...")
#         print(f"🏛️  Organismo: {row.get('organismo', 'N/A')}")
#         print(f"📅 Fecha límite: {row.get('fecha_limite', 'N/A')}")
        
#         if row.get('presupuesto'):
#             print(f"💰 Presupuesto: {row['presupuesto'].get('valor', 'N/A')} - {row['presupuesto']['motivo']}")
        
#         if row.get('matches'):
#             print(f"\n✅ COINCIDENCIAS:")
#             for key, value in row['matches'].items():
#                 print(f"   • {key}: {value}")
        
#         if row.get('penalizaciones'):
#             print(f"\n⚠️  PENALIZACIONES:")
#             for pen in row['penalizaciones']:
#                 print(f"   • {pen}")
        
#         if row.get('warnings'):
#             print(f"\n⚡ ADVERTENCIAS:")
#             for warn in row['warnings']:
#                 print(f"   • {warn}")

# # ============================================================================
# # EJEMPLO DE USO
# # ============================================================================

# if __name__ == "__main__":
    
#     # Cargar datasets base
#     df_general, df_requisitos, df_criterios, df_docs, df_cpv = load_datasets()
    
#     # ====================
#     # OPCIÓN 1: PRIMERA VEZ - Extraer textos (LENTO)
#     # ====================
#     df_textos = procesar_y_guardar_textos(
#         df_general, df_docs, 
#         dias=15, 
#         output_path="data/textos_extraidos.parquet"
#     )
    
#     # ====================
#     # OPCIÓN 2: USAR TEXTOS YA EXTRAÍDOS (RÁPIDO)
#     # ====================
#     # df_textos = pd.read_parquet("src\Textos_Extraidos.parquet")
#     # print(f"📄 Textos cargados: {len(df_textos)}")
    
#     # Análisis completo
#     df_resultados = analizar_licitaciones_completo(
#         df_textos, perfil_enetic, df_general, df_criterios, df_requisitos
#     )
    
#     # Guardar resultados
#     df_resultados.to_parquet(r"src\data\analisis_resultados.parquet")
#     df_resultados.to_excel(r"src\data\analisis_resultados.xlsx", index=False)
    
#     # Generar reporte
#     generar_reporte_resumen(df_resultados, top_n=10)
    
#     print(f"\n💾 Resultados guardados en:")
#     print(f"   • data/analisis_resultados.parquet")
#     print(f"   • data/analisis_resultados.xlsx")

import pandas as pd
import os
import re
import requests
import tempfile
import json
import torch
import subprocess  # Para Ollama
from paddleocr import PaddleOCR
import fitz  # PyMuPDF

# 🔴 NUEVO: Importaciones de resumidor_IA
from sentence_transformers import SentenceTransformer, util
from rapidfuzz import fuzz

# ============================================================================
# CONFIGURACIÓN Y PERFIL DE EMPRESA
# ============================================================================

perfil_enetic = {
    "lugares": ["Comunidad Valenciana", "Albacete", "Murcia", "Valencia"],
    "sectores": ["Infraestructura IT", "Ciberseguridad", "Servidores", "Storage", "Redes"],
    "empresas_partner": ["DELL", "Huawei", "Veeam", "VMware", "Broadcom", "Watchguard", "Eset", "Qnap"],
    "certificaciones": ["ISO28001", "ISO27017", "ISO22301", "NIS2", "ENS"],
    "certificaciones_descarte": ["ISO9001", "ISO14001"],
    "terminos_excluyentes": ["obra civil", "construcción", "limpieza", "catering", "transporte"],
    "cpv_relevantes": ['48', '72', '30213', '30231', '32420', '48820', '71356', '30000000', '30200000', '32400000', '48000000', '50300000'],
    "presupuesto_min": 10000,
    "presupuesto_max": 500000
}

# ============================================================================
# 🔴 NUEVO: FUNCIONES HELPER DE RESUMIDOR_IA
# ============================================================================

def find_semantic_snippet(text, query, model):
    """Busca el fragmento más relevante semánticamente."""
    try:
        sentences = re.split(r"(?<=[\.\n])\s+", text)
        if len(sentences) < 2: return text[:500]
        
        embeddings = model.encode(sentences, convert_to_tensor=True)
        query_emb = model.encode(query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_emb, embeddings)[0]
        best_idx = torch.argmax(cos_scores).item()
        
        # Tomar contexto (anterior y siguiente oración)
        snippet = " ".join(sentences[max(0, best_idx - 1): best_idx + 2])
        return snippet.strip()
    except Exception as e:
        return ""

def extract_presupuesto_avanzado(text):
    """Extracción robusta de presupuesto (Lógica de resumidor_IA)"""
    patterns = [
        r"presupuesto\s+(?:base\s+)?(?:de\s+)?licitación[:\s]+(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€",
        r"valor\s+estimado[:\s]+(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€",
        r"importe\s+(?:total|máximo)[:\s]+(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€"
    ]
    valores = []
    for pat in patterns:
        matches = re.finditer(pat, text, re.I)
        for m in matches:
            val_str = m.group(1).replace('.', '').replace(',', '.')
            try:
                valores.append(float(val_str))
            except:
                continue
    
    if valores:
        return max(valores) # Retorna float para comparar
    return None

def generar_resumen_ollama(text, model="deepseek-r1:14b"):
    """Genera resumen usando Ollama local"""
    prompt = f"""
    Eres un experto en licitaciones IT. Resume lo siguiente en español.
    Enfócate en: ¿Qué hardware/software/servicio piden exactamente? ¿Hay requisitos técnicos duros?
    
    TEXTO:
    {text[:4000]} 
    """ # Limitamos caracteres para no desbordar contexto
    
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error generando resumen IA: {e}"

# ============================================================================
# FUNCIONES BASE (CARGA Y EXTRACCIÓN)
# ============================================================================

def load_datasets():
    # ... (Mismo código que tenías) ...
    # Simulación para que el script corra si no tienes los archivos exactos ahora
    print("⚠️  Asegúrate de que las rutas a los parquets sean correctas.")
    # Retorna dataframes vacíos o carga real
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ============================================================================
# LÓGICA DE SCORING + SEMÁNTICA
# ============================================================================

def calcular_score_hibrido(row, perfil, df_general, df_criterios, df_requisitos, semantic_model):
    """
    Combina Reglas (analisis_perfil) + Semántica (resumidor_IA)
    """
    score = 0
    detalles = {
        'pliego_id': row['pliego_id'],
        'matches': {},
        'penalizaciones': [],
        'datos_ia': {} # Aquí guardaremos lo extraído por semántica
    }
    
    texto = row.get("TEXTO_EXTRAIDO", "")
    if not texto:
        return 0, detalles

    # --- 1. LÓGICA TRADICIONAL (FILTROS RÁPIDOS) ---
    
    # CPV, Ubicación, Sectores, Partners (Mismo código de analisis_perfil.py)
    # ... (Resumido para brevedad, mantener tu lógica original aquí) ...
    
    # Ejemplo rápido de integración de sectores:
    sectores_match = [s for s in perfil['sectores'] if s.lower() in texto.lower()]
    if sectores_match:
        score += len(sectores_match) * 15
        detalles['matches']['sectores'] = sectores_match

    # --- 2. 🔴 INTEGRACIÓN LÓGICA SEMÁNTICA ---
    
    # Extraer objeto real semánticamente (mejor que el título a veces)
    objeto_semantic = find_semantic_snippet(texto, "objeto del contrato suministro servicios", semantic_model)
    detalles['datos_ia']['objeto_semantic'] = objeto_semantic

    # Extraer presupuesto avanzado
    presupuesto_detectado = extract_presupuesto_avanzado(texto)
    if presupuesto_detectado:
        detalles['datos_ia']['presupuesto_real'] = presupuesto_detectado
        # Validar rango
        if presupuesto_detectado < perfil['presupuesto_min']:
             score -= 50
             detalles['penalizaciones'].append(f"Presupuesto bajo ({presupuesto_detectado}€)")
    
    # Búsqueda semántica de criterios si no existen en df_criterios
    snippet_criterios = find_semantic_snippet(texto, "criterios de adjudicación ponderación precio técnica", semantic_model)
    detalles['datos_ia']['snippet_criterios'] = snippet_criterios

    return score, detalles

# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

def analizar_licitaciones_completo(df_textos, perfil, df_general, df_criterios, df_requisitos):
    print("🧠 Cargando modelo semántico (esto tarda un poco la primera vez)...")
    # 🔴 Cargamos el modelo una sola vez fuera del bucle
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    resultados = []
    
    print(f"🔍 Analizando {len(df_textos)} documentos...")
    for idx, row in df_textos.iterrows():
        # Pasamos el modelo a la función de scoring
        score, detalles = calcular_score_hibrido(
            row, perfil, df_general, df_criterios, df_requisitos, model
        )
        detalles['score'] = score
        resultados.append(detalles)
    
    df_resultados = pd.DataFrame(resultados)
    df_resultados = df_resultados.sort_values('score', ascending=False)
    return df_resultados

def generar_reporte_inteligente(df_resultados, top_n=5, usar_ollama=True):
    """Genera reporte y aplica LLM solo al TOP N"""
    print("\n" + "="*80)
    print(f"🤖 GENERANDO REPORTE IA (TOP {top_n})")
    print("="*80)
    
    # Tomamos solo los top N
    top_df = df_resultados.head(top_n).copy()
    
    for idx, row in top_df.iterrows():
        print(f"\n{'─'*80}")
        print(f"🏆 RANKING #{idx+1} | SCORE: {row['score']}")
        print(f"ID: {row['pliego_id']}")
        
        # Mostrar datos semánticos
        datos_ia = row.get('datos_ia', {})
        print(f"💰 Presupuesto detectado: {datos_ia.get('presupuesto_real', 'N/A')} €")
        print(f"📝 Objeto (Semántico): {datos_ia.get('objeto_semantic', '')[:200]}...")
        
        if usar_ollama:
            print("\n⏳ Generando resumen con IA (DeepSeek)...")
            # Necesitamos el texto original, asumiendo que está en row o buscándolo
            # Nota: En un caso real, pasar el texto completo en 'detalles' ocupa mucha RAM
            # Mejor buscarlo de nuevo o pasarlo referenciado.
            
            # Simulamos que tenemos el texto (aquí deberías recuperar el texto del df_textos original usando el ID)
            # resumen = generar_resumen_ollama(texto_original_del_pliego) 
            print("(Aquí se imprimiría el resumen de Ollama si conectamos el texto original)")
            
# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # 1. Cargar datos (Simulado o real)
    df_textos = pd.read_parquet("src/Textos_Extraidos.parquet") # Descomentar
    
    # # MOCK DATA PARA PROBAR SI NO TIENES EL PARQUET
    # data_mock = [{
    #     "pliego_id": "1001", 
    #     "TEXTO_EXTRAIDO": "Objeto: Suministro de servidores Dell para el ayuntamiento. Presupuesto base de licitación: 45.000,00 €. Se valora ISO 27001."
    # }]
    # df_textos = pd.DataFrame(data_mock)
    
    # 2. Análisis Híbrido
    df_resultados = analizar_licitaciones_completo(
        df_textos, perfil_enetic, None, None, None
    )
    
    # 3. Reporte con IA
    generar_reporte_inteligente(df_resultados, top_n=1)
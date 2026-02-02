# import fitz  # PyMuPDF
# import camelot
# import requests
# import io
# import os
# import tempfile
# import re
# from typing import Dict, List, Optional, Tuple
# from dataclasses import dataclass
# import json

# @dataclass
# class DocumentoExtraido:
#     """Estructura para almacenar un documento extraído"""
#     texto: str
#     tablas: List[str]
#     metadatos: Dict
#     tipo_documento: str
    

# class ExtractorPDFUnificado:
#     """
#     Sistema unificado de extracción de PDFs con:
#     - Detección automática de tipo de documento
#     - Extracción de tablas con Camelot
#     - Limpieza inteligente de texto
#     - Extracción de metadatos estructurados
#     """
    
#     def __init__(self):
#         self.patterns_metadatos = self._compilar_patterns()
    
#     def _compilar_patterns(self) -> Dict:
#         """Compila patrones regex para extracción de metadatos"""
#         return {
#             'presupuesto': [
#                 r'presupuesto\s+(?:base\s+)?(?:de\s+)?licitación[:\s]+(?:€\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
#                 r'valor\s+estimado[:\s]+(?:€\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
#                 r'importe\s+(?:total|máximo)[:\s]+(?:€\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
#             ],
#             'plazo': [
#                 r'plazo\s+de\s+(?:ejecución|entrega)[:\s]+(\d+)\s*(días|meses|años)',
#                 r'duración[:\s]+(\d+)\s*(días|meses|años)',
#             ],
#             'lotes': [
#                 r'(?:número\s+de\s+)?lotes?[:\s]+(\d+)',
#                 r'dividido\s+en\s+(\d+)\s+lotes?',
#             ],
#             'organismo': [
#                 r'(?:organismo|entidad)\s+contratante[:\s]+([^\n]{10,100})',
#                 r'adjudicado\s+por[:\s]+([^\n]{10,100})',
#             ],
#             'expediente': [
#                 r'(?:expediente|código|referencia)[:\s]+([A-Z0-9\-\/]+)',
#             ],
#             'certificaciones': [
#                 r'(ISO\s*\d{4,5}(?:[\-:]\d{4})?)',
#                 r'(ENS\s*(?:Alto|Medio|Bajo)?)',
#                 r'(certificación\s+[^\n]{10,50})',
#             ]
#         }
    
#     def descargar_pdf(self, url_or_path: str) -> Tuple[str, bool]:
#         """
#         Descarga PDF si es URL o usa ruta local.
        
#         Returns:
#             (ruta_archivo, es_temporal)
#         """
#         if url_or_path.startswith(("http://", "https://")):
#             print(f"📥 Descargando PDF desde URL...")
#             response = requests.get(url_or_path, timeout=30)
#             response.raise_for_status()
            
#             # Crear archivo temporal
#             fd, temp_path = tempfile.mkstemp(suffix=".pdf")
#             with os.fdopen(fd, 'wb') as tmp:
#                 tmp.write(response.content)
            
#             return temp_path, True
#         else:
#             return url_or_path, False
    
#     def detectar_tipo_documento(self, texto: str) -> str:
#         """
#         Detecta si es pliego técnico, administrativo o anexo.
        
#         Returns:
#             'tecnico', 'administrativo', 'anexo', 'desconocido'
#         """
#         texto_lower = texto.lower()
        
#         # Palabras clave por tipo
#         keywords_tecnico = [
#             'especificaciones técnicas', 'requisitos funcionales',
#             'alcance del servicio', 'entregables', 'criterios de calidad',
#             'prestaciones técnicas', 'características técnicas'
#         ]
        
#         keywords_admin = [
#             'procedimiento de contratación', 'criterios de adjudicación',
#             'garantías', 'presentación de ofertas', 'apertura de plicas',
#             'modelo de proposición', 'cláusulas administrativas'
#         ]
        
#         keywords_anexo = [
#             'anexo', 'modelo de', 'formulario', 'declaración responsable',
#             'compromiso de', 'certificado de'
#         ]
        
#         # Contar coincidencias
#         score_tecnico = sum(1 for kw in keywords_tecnico if kw in texto_lower)
#         score_admin = sum(1 for kw in keywords_admin if kw in texto_lower)
#         score_anexo = sum(1 for kw in keywords_anexo if kw in texto_lower)
        
#         if score_anexo > max(score_tecnico, score_admin):
#             return 'anexo'
#         elif score_tecnico > score_admin:
#             return 'tecnico'
#         elif score_admin > 0:
#             return 'administrativo'
#         else:
#             return 'desconocido'
    
#     def limpiar_texto(self, texto: str) -> str:
#         """
#         Limpia texto de basura administrativa y artefactos de OCR.
#         """
#         # Eliminar URLs
#         texto = re.sub(r'http[s]?://\S+', '', texto)
        
#         # Eliminar firmas digitales y hashes
#         texto = re.sub(r'verificadorCopiaAutentica[^\n]*', '', texto)
#         texto = re.sub(r'Código de verificación[^\n]*', '', texto)
#         texto = re.sub(r'Firmado por:[^\n]*', '', texto)
#         texto = re.sub(r'Fecha:[^\n]*\d{2}:\d{2}:\d{2}', '', texto)
        
#         # Eliminar números de página repetitivos
#         texto = re.sub(r'Página\s+\d+\s+de\s+\d+', '', texto)
        
#         # Normalizar espacios
#         texto = re.sub(r'\s+', ' ', texto)
#         texto = re.sub(r'\n\s*\n\s*\n+', '\n\n', texto)
        
#         # Reemplazar checkboxes por texto
#         texto = texto.replace("☒", "[X]").replace("☐", "[ ]")
        
#         return texto.strip()
    
#     def extraer_texto_pymupdf(self, ruta_pdf: str) -> str:
#         """Extrae texto usando PyMuPDF"""
#         try:
#             doc = fitz.open(ruta_pdf)
#             texto = ""
            
#             for page in doc:
#                 texto += page.get_text("text") + "\n"
            
#             doc.close()
#             return self.limpiar_texto(texto)
            
#         except Exception as e:
#             print(f"⚠️ Error extrayendo texto: {e}")
#             return ""
    
#     def extraer_tablas_camelot(
#         self, 
#         ruta_pdf: str, 
#         paginas: str = "1-5"
#     ) -> List[Dict]:
#         """
#         Extrae tablas estructuradas con Camelot.
        
#         Returns:
#             Lista de dicts con {tabla_md, pagina, accuracy}
#         """
#         tablas_extraidas = []
        
#         try:
#             tablas = camelot.read_pdf(
#                 ruta_pdf, 
#                 pages=paginas, 
#                 flavor='lattice'
#             )
            
#             if len(tablas) == 0:
#                 # Intentar con flavor 'stream' si lattice falla
#                 tablas = camelot.read_pdf(
#                     ruta_pdf, 
#                     pages=paginas, 
#                     flavor='stream'
#                 )
            
#             for i, tabla in enumerate(tablas):
#                 # Convertir a markdown
#                 tabla_md = tabla.df.to_markdown(index=False)
                
#                 tablas_extraidas.append({
#                     'indice': i,
#                     'pagina': tabla.page,
#                     'accuracy': tabla.accuracy if hasattr(tabla, 'accuracy') else 0,
#                     'tabla_markdown': tabla_md,
#                     'num_filas': len(tabla.df),
#                     'num_columnas': len(tabla.df.columns)
#                 })
            
#             print(f"✓ Extraídas {len(tablas_extraidas)} tablas")
            
#         except Exception as e:
#             print(f"⚠️ Error extrayendo tablas: {e}")
        
#         return tablas_extraidas
    
#     def extraer_metadatos(self, texto: str) -> Dict:
#         """
#         Extrae metadatos estructurados del texto usando regex.
#         """
#         metadatos = {}
        
#         for clave, patterns in self.patterns_metadatos.items():
#             for pattern in patterns:
#                 match = re.search(pattern, texto, re.IGNORECASE)
#                 if match:
#                     valor = match.group(1).strip()
                    
#                     # Procesar según el tipo
#                     if clave == 'presupuesto':
#                         # Convertir a float
#                         valor_num = valor.replace('.', '').replace(',', '.')
#                         try:
#                             metadatos['presupuesto_euros'] = float(valor_num)
#                             metadatos['presupuesto_texto'] = valor
#                         except:
#                             pass
                    
#                     elif clave == 'plazo':
#                         metadatos['plazo_valor'] = match.group(1)
#                         metadatos['plazo_unidad'] = match.group(2)
                    
#                     elif clave == 'lotes':
#                         try:
#                             metadatos['num_lotes'] = int(valor)
#                         except:
#                             pass
                    
#                     elif clave == 'certificaciones':
#                         if 'certificaciones' not in metadatos:
#                             metadatos['certificaciones'] = []
#                         metadatos['certificaciones'].append(valor)
                    
#                     else:
#                         metadatos[clave] = valor
                    
#                     break  # Una vez encontrado, pasar al siguiente
        
#         return metadatos
    
#     def extraer_completo(
#         self, 
#         url_or_path: str,
#         paginas_tablas: str = "1-10"
#     ) -> DocumentoExtraido:
#         """
#         Método principal: extrae texto, tablas y metadatos.
        
#         Args:
#             url_or_path: URL o ruta local del PDF
#             paginas_tablas: Rango de páginas para buscar tablas
        
#         Returns:
#             DocumentoExtraido con toda la información
#         """
#         print(f"\n{'='*60}")
#         print(f"📄 EXTRACCIÓN DE DOCUMENTO")
#         print(f"{'='*60}")
        
#         # Descargar/localizar PDF
#         ruta_pdf, es_temporal = self.descargar_pdf(url_or_path)
        
#         try:
#             # 1. Extraer texto
#             print("\n1️⃣ Extrayendo texto...")
#             texto = self.extraer_texto_pymupdf(ruta_pdf)
#             print(f"   ✓ {len(texto)} caracteres extraídos")
            
#             # 2. Detectar tipo
#             print("\n2️⃣ Detectando tipo de documento...")
#             tipo_doc = self.detectar_tipo_documento(texto)
#             print(f"   ✓ Tipo detectado: {tipo_doc}")
            
#             # 3. Extraer tablas
#             print("\n3️⃣ Extrayendo tablas...")
#             tablas = self.extraer_tablas_camelot(ruta_pdf, paginas_tablas)
            
#             # 4. Extraer metadatos
#             print("\n4️⃣ Extrayendo metadatos...")
#             metadatos = self.extraer_metadatos(texto)
#             metadatos['tipo_documento'] = tipo_doc
#             metadatos['num_tablas'] = len(tablas)
#             print(f"   ✓ {len(metadatos)} campos extraídos")
            
#             # Crear objeto de salida
#             documento = DocumentoExtraido(
#                 texto=texto,
#                 tablas=[t['tabla_markdown'] for t in tablas],
#                 metadatos=metadatos,
#                 tipo_documento=tipo_doc
#             )
            
#             print(f"\n{'='*60}")
#             print(f"✅ EXTRACCIÓN COMPLETADA")
#             print(f"{'='*60}\n")
            
#             return documento
            
#         finally:
#             # Limpiar archivo temporal
#             if es_temporal and os.path.exists(ruta_pdf):
#                 try:
#                     os.remove(ruta_pdf)
#                     print("🧹 Archivo temporal eliminado")
#                 except:
#                     pass


# # =============================================================================
# # EJEMPLO DE USO
# # =============================================================================

# if __name__ == "__main__":
#     extractor = ExtractorPDFUnificado()
    
#     # URL de ejemplo (reemplaza con tu PDF)
#     url_pdf = "https://ejemplo.com/pliego.pdf"
    
#     # Extraer todo
#     documento = extractor.extraer_completo(
#         url_or_path=url_pdf,
#         paginas_tablas="1-10"
#     )
    
#     # Mostrar resultados
#     print("\n📊 RESUMEN DE EXTRACCIÓN:")
#     print(f"Tipo: {documento.tipo_documento}")
#     print(f"Texto: {len(documento.texto)} chars")
#     print(f"Tablas: {len(documento.tablas)}")
#     print(f"\nMetadatos extraídos:")
#     print(json.dumps(documento.metadatos, indent=2, ensure_ascii=False))
    
#     if documento.tablas:
#         print(f"\n📋 Primera tabla extraída:")
#         print(documento.tablas[0][:500])

import fitz  # PyMuPDF
import camelot
import requests
import io
import os
import tempfile
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import gc

@dataclass
class DocumentoExtraido:
    """Estructura para almacenar un documento extraído"""
    texto: str
    tablas: List[str]
    metadatos: Dict
    tipo_documento: str
    

class ExtractorPDFUnificado:
    """
    Sistema unificado de extracción de PDFs con:
    - Detección automática de tipo de documento
    - Extracción de tablas con Camelot
    - Limpieza inteligente de texto
    - Extracción de metadatos estructurados
    """
    
    def __init__(self):
        self.patterns_metadatos = self._compilar_patterns()
    
    def _compilar_patterns(self) -> Dict:
        """Compila patrones regex para extracción de metadatos"""
        return {
            'presupuesto': [
                r'presupuesto\s+(?:base\s+)?(?:de\s+)?licitación[:\s]+(?:€\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
                r'valor\s+estimado[:\s]+(?:€\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
                r'importe\s+(?:total|máximo)[:\s]+(?:€\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            ],
            'plazo': [
                r'plazo\s+de\s+(?:ejecución|entrega)[:\s]+(\d+)\s*(días|meses|años)',
                r'duración[:\s]+(\d+)\s*(días|meses|años)',
            ],
            'lotes': [
                r'(?:número\s+de\s+)?lotes?[:\s]+(\d+)',
                r'dividido\s+en\s+(\d+)\s+lotes?',
            ],
            'organismo': [
                r'(?:organismo|entidad)\s+contratante[:\s]+([^\n]{10,100})',
                r'adjudicado\s+por[:\s]+([^\n]{10,100})',
            ],
            'expediente': [
                r'(?:expediente|código|referencia)[:\s]+([A-Z0-9\-\/]+)',
            ],
            'certificaciones': [
                r'(ISO\s*\d{4,5}(?:[\-:]\d{4})?)',
                r'(ENS\s*(?:Alto|Medio|Bajo)?)',
                r'(certificación\s+[^\n]{10,50})',
            ]
        }
    
    def descargar_pdf(self, url_or_path: str) -> Tuple[str, bool]:
        """
        Descarga PDF si es URL o usa ruta local.
        
        Returns:
            (ruta_archivo, es_temporal)
        """
        if url_or_path.startswith(("http://", "https://")):
            print(f"📥 Descargando PDF desde URL...")
            response = requests.get(url_or_path, timeout=30)
            response.raise_for_status()
            
            # Crear archivo temporal
            fd, temp_path = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(response.content)
            
            return temp_path, True
        else:
            return url_or_path, False
    
    def detectar_tipo_documento(self, texto: str) -> str:
        """
        Detecta si es pliego técnico, administrativo o anexo.
        
        Returns:
            'tecnico', 'administrativo', 'anexo', 'desconocido'
        """
        texto_lower = texto.lower()
        
        # Palabras clave por tipo
        keywords_tecnico = [
            'especificaciones técnicas', 'requisitos funcionales',
            'alcance del servicio', 'entregables', 'criterios de calidad',
            'prestaciones técnicas', 'características técnicas'
        ]
        
        keywords_admin = [
            'procedimiento de contratación', 'criterios de adjudicación',
            'garantías', 'presentación de ofertas', 'apertura de plicas',
            'modelo de proposición', 'cláusulas administrativas'
        ]
        
        keywords_anexo = [
            'anexo', 'modelo de', 'formulario', 'declaración responsable',
            'compromiso de', 'certificado de'
        ]
        
        # Contar coincidencias
        score_tecnico = sum(1 for kw in keywords_tecnico if kw in texto_lower)
        score_admin = sum(1 for kw in keywords_admin if kw in texto_lower)
        score_anexo = sum(1 for kw in keywords_anexo if kw in texto_lower)
        
        if score_anexo > max(score_tecnico, score_admin):
            return 'anexo'
        elif score_tecnico > score_admin:
            return 'tecnico'
        elif score_admin > 0:
            return 'administrativo'
        else:
            return 'desconocido'
    
    def limpiar_texto(self, texto: str) -> str:
        """
        Limpia texto de basura administrativa y artefactos de OCR.
        """
        # Eliminar URLs
        texto = re.sub(r'http[s]?://\S+', '', texto)
        
        # Eliminar firmas digitales y hashes
        texto = re.sub(r'verificadorCopiaAutentica[^\n]*', '', texto)
        texto = re.sub(r'Código de verificación[^\n]*', '', texto)
        texto = re.sub(r'Firmado por:[^\n]*', '', texto)
        texto = re.sub(r'Fecha:[^\n]*\d{2}:\d{2}:\d{2}', '', texto)
        
        # Eliminar números de página repetitivos
        texto = re.sub(r'Página\s+\d+\s+de\s+\d+', '', texto)
        
        # Normalizar espacios
        texto = re.sub(r'\s+', ' ', texto)
        texto = re.sub(r'\n\s*\n\s*\n+', '\n\n', texto)
        
        # Reemplazar checkboxes por texto
        texto = texto.replace("☒", "[X]").replace("☐", "[ ]")
        
        return texto.strip()
    
    def extraer_texto_pymupdf(self, ruta_pdf: str) -> str:
        """Extrae texto usando PyMuPDF"""
        try:
            doc = fitz.open(ruta_pdf)
            texto = ""
            
            for page in doc:
                texto += page.get_text("text") + "\n"
            
            doc.close()
            return self.limpiar_texto(texto)
            
        except Exception as e:
            print(f"⚠️ Error extrayendo texto: {e}")
            return ""
        
    def extraer_tablas_pymupdf(
        self, 
        ruta_pdf: str, 
        paginas: str = "1-10"
    ) -> List[Dict]:
        """
        Extrae tablas estructuradas usando el motor nativo de PyMuPDF.
        Mucho más rápido y estable en Windows que Camelot.
        """
        tablas_extraidas = []
        
        try:
            doc = fitz.open(ruta_pdf)
            
            # 1. Parsear el rango de páginas (ej: "1-5" -> [0, 1, 2, 3, 4])
            lista_paginas = []
            try:
                if "-" in paginas:
                    inicio, fin = map(int, paginas.split("-"))
                    lista_paginas = list(range(inicio - 1, min(fin, len(doc))))
                else:
                    lista_paginas = [int(paginas) - 1]
            except:
                lista_paginas = range(min(10, len(doc))) # Fallback a las primeras 10

            # 2. Iterar por las páginas seleccionadas
            for p_idx in lista_paginas:
                if p_idx >= len(doc): continue
                
                pagina = doc[p_idx]
                # Buscar tablas en la página
                tabs = pagina.find_tables()
                
                for i, tabla in enumerate(tabs):
                    try:
                        # Convertir a DataFrame de Pandas
                        df = tabla.to_pandas()
                        
                        if df.empty or len(df) <= 1:
                            continue
                        
                        # Convertir a markdown
                        tabla_md = df.to_markdown(index=False)
                        
                        tablas_extraidas.append({
                            'indice': i,
                            'pagina': p_idx + 1,
                            'accuracy': 1.0,  # PyMuPDF no da score, asumimos éxito si la extrae
                            'tabla_markdown': tabla_md,
                            'num_filas': len(df),
                            'num_columnas': len(df.columns)
                        })
                    except Exception as e:
                        print(f"⚠️ Error procesando tabla {i} en pág {p_idx + 1}: {e}")
            
            doc.close() # Cerramos el handle del archivo
            print(f"✓ PyMuPDF: Extraídas {len(tablas_extraidas)} tablas")
            
        except Exception as e:
            print(f"⚠️ Error extrayendo tablas con PyMuPDF: {e}")
            
        return tablas_extraidas
    
    # def extraer_tablas_camelot(
    #     self, 
    #     ruta_pdf: str, 
    #     paginas: str = "1-5"
    # ) -> List[Dict]:
    #     """
    #     Extrae tablas estructuradas con Camelot.
        
    #     Returns:
    #         Lista de dicts con {tabla_md, pagina, accuracy}
    #     """
    #     tablas_extraidas = []
        
    #     try:
    #         # Intentar primero con lattice (más preciso para tablas con bordes)
    #         tablas = camelot.read_pdf(
    #             ruta_pdf, 
    #             pages=paginas, 
    #             flavor='lattice',
    #             suppress_stdout=True  # Silenciar warnings
    #         )
            
    #         # Si no encuentra tablas, intentar con stream
    #         if len(tablas) == 0:
    #             tablas = camelot.read_pdf(
    #                 ruta_pdf, 
    #                 pages=paginas, 
    #                 flavor='stream',
    #                 suppress_stdout=True
    #             )
            
    #         for i, tabla in enumerate(tablas):
    #             try:
    #                 # Convertir a markdown
    #                 tabla_md = tabla.df.to_markdown(index=False)
                    
    #                 tablas_extraidas.append({
    #                     'indice': i,
    #                     'pagina': tabla.page,
    #                     'accuracy': tabla.accuracy if hasattr(tabla, 'accuracy') else 0,
    #                     'tabla_markdown': tabla_md,
    #                     'num_filas': len(tabla.df),
    #                     'num_columnas': len(tabla.df.columns)
    #                 })
    #             except Exception as e:
    #                 print(f"⚠️ Error procesando tabla {i}: {e}")
    #                 continue
            
    #         print(f"✓ Extraídas {len(tablas_extraidas)} tablas")
            
    #     except Exception as e:
    #         print(f"⚠️ Error extrayendo tablas con Camelot: {e}")
    #         print("   Continuando sin tablas...")
        
    #     return tablas_extraidas
    
    def extraer_metadatos(self, texto: str) -> Dict:
        """
        Extrae metadatos estructurados del texto usando regex.
        """
        metadatos = {}
        
        for clave, patterns in self.patterns_metadatos.items():
            for pattern in patterns:
                match = re.search(pattern, texto, re.IGNORECASE)
                if match:
                    valor = match.group(1).strip()
                    
                    # Procesar según el tipo
                    if clave == 'presupuesto':
                        # Convertir a float
                        valor_num = valor.replace('.', '').replace(',', '.')
                        try:
                            metadatos['presupuesto_euros'] = float(valor_num)
                            metadatos['presupuesto_texto'] = valor
                        except:
                            pass
                    
                    elif clave == 'plazo':
                        metadatos['plazo_valor'] = match.group(1)
                        metadatos['plazo_unidad'] = match.group(2)
                    
                    elif clave == 'lotes':
                        try:
                            metadatos['num_lotes'] = int(valor)
                        except:
                            pass
                    
                    elif clave == 'certificaciones':
                        if 'certificaciones' not in metadatos:
                            metadatos['certificaciones'] = []
                        metadatos['certificaciones'].append(valor)
                    
                    else:
                        metadatos[clave] = valor
                    
                    break  # Una vez encontrado, pasar al siguiente
        
        return metadatos
    
    # def extraer_completo(
    #     self, 
    #     url_or_path: str,
    #     paginas_tablas: str = "1-10"
    # ) -> DocumentoExtraido:
    #     """
    #     Método principal: extrae texto, tablas y metadatos.
        
    #     Args:
    #         url_or_path: URL o ruta local del PDF
    #         paginas_tablas: Rango de páginas para buscar tablas
        
    #     Returns:
    #         DocumentoExtraido con toda la información
    #     """
    #     print(f"\n{'='*60}")
    #     print(f"📄 EXTRACCIÓN DE DOCUMENTO")
    #     print(f"{'='*60}")
        
    #     # Descargar/localizar PDF
    #     ruta_pdf, es_temporal = self.descargar_pdf(url_or_path)
        
    #     try:
    #         # 1. Extraer texto
    #         print("\n1️⃣ Extrayendo texto...")
    #         texto = self.extraer_texto_pymupdf(ruta_pdf)
    #         print(f"   ✓ {len(texto)} caracteres extraídos")
            
    #         # 2. Detectar tipo
    #         print("\n2️⃣ Detectando tipo de documento...")
    #         tipo_doc = self.detectar_tipo_documento(texto)
    #         print(f"   ✓ Tipo detectado: {tipo_doc}")
            
    #         # 3. Extraer tablas
    #         print("\n3️⃣ Extrayendo tablas...")
    #         tablas = self.extraer_tablas_camelot(ruta_pdf, paginas_tablas)
            
    #         # 4. Extraer metadatos
    #         print("\n4️⃣ Extrayendo metadatos...")
    #         metadatos = self.extraer_metadatos(texto)
    #         metadatos['tipo_documento'] = tipo_doc
    #         metadatos['num_tablas'] = len(tablas)
    #         print(f"   ✓ {len(metadatos)} campos extraídos")
            
    #         # Crear objeto de salida
    #         documento = DocumentoExtraido(
    #             texto=texto,
    #             tablas=[t['tabla_markdown'] for t in tablas],
    #             metadatos=metadatos,
    #             tipo_documento=tipo_doc
    #         )
            
    #         print(f"\n{'='*60}")
    #         print(f"✅ EXTRACCIÓN COMPLETADA")
    #         print(f"{'='*60}\n")
            
    #         return documento
            
    #     finally:
    #         # Limpiar archivo temporal con reintentos (problema común en Windows)
    #         if es_temporal and os.path.exists(ruta_pdf):
    #             import time
    #             for intento in range(3):
    #                 try:
    #                     time.sleep(0.5)  # Esperar a que se libere el archivo
    #                     os.remove(ruta_pdf)
    #                     print("🧹 Archivo temporal eliminado")
    #                     break
    #                 except PermissionError:
    #                     if intento < 2:
    #                         print(f"⏳ Esperando liberación del archivo (intento {intento+1}/3)...")
    #                         time.sleep(1)
    #                     else:
    #                         print(f"⚠️ No se pudo eliminar archivo temporal: {ruta_pdf}")
    #                         print("   (Se eliminará automáticamente en el siguiente reinicio)")
    #                 except Exception as e:
    #                     print(f"⚠️ Error eliminando temporal: {e}")
    #                     break

    def _detectar_paginas_semilla(self, pdf_path):
        """
        Fase 1: Detectar páginas "semilla" que contienen las palabras clave.
        """
        keywords = ["cuadro resumen", "presupuesto base", "valor estimado", 
                    "lote", "criterios de adjudicación", "solvencia", "tabla", "anexo"]
            
        doc = fitz.open(pdf_path)
        paginas_semilla = set()
        
        # Siempre incluimos las primeras 3 páginas (casi siempre empieza ahí)
        for i in range(min(3, len(doc))):
            paginas_semilla.add(i + 1)

        # Escaneo rápido del resto buscando keywords
        for i in range(3, len(doc)):
            texto_pagina = doc[i].get_text("text").lower()
            if any(kw in texto_pagina for kw in keywords):
                paginas_semilla.add(i + 1)
                
        total_paginas = len(doc)
        doc.close()
        
        return sorted(list(paginas_semilla)), total_paginas
    
    import os
    import requests
    import tempfile
    from pathlib import Path

    def _obtener_path_local(self, url_or_path: str) -> str:
        """
        Detecta si el origen es una URL o un archivo local.
        Si es URL, descarga el PDF a un archivo temporal y devuelve su ruta.
        """
        # 1. Verificar si ya es una ruta local existente
        if os.path.exists(url_or_path):
            print(f"📂 Usando archivo local: {url_or_path}")
            return url_or_path

        # 2. Si parece una URL, intentar descargar
        if url_or_path.startswith(("http://", "https://")):
            try:
                print(f"📥 Descargando PDF desde URL...")
                response = requests.get(url_or_path, timeout=30, stream=True)
                response.raise_for_status()

                # Creamos un archivo temporal físico (.pdf)
                # suffix=".pdf" es vital para que Camelot/Ghostscript lo reconozcan
                fd, temp_path = tempfile.mkstemp(suffix=".pdf")
                
                with os.fdopen(fd, 'wb') as tmp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            tmp_file.write(chunk)
                
                print(f"✅ Archivo descargado temporalmente en: {temp_path}")
                
                # Guardamos la ruta para poder borrarla después si fuera necesario
                self.ultimo_archivo_temporal = temp_path
                return temp_path

            except requests.exceptions.RequestException as e:
                raise Exception(f"❌ Error al descargar el PDF desde la URL: {e}")
        
        # 3. Si no es URL ni existe localmente, lanzamos error
        raise FileNotFoundError(f"❌ No se encontró el archivo ni es una URL válida: {url_or_path}")

    # def extraer_completo(self, url_or_path):
    #     """
    #     Orquesta la extracción usando lógica de continuidad.
    #     """
    #     path_local = self._obtener_path_local(url_or_path) 
        
    #     # 1. Obtener páginas iniciales (semillas)
    #     paginas_a_procesar, total_paginas = self._detectar_paginas_semilla(path_local)
        
    #     # Convertimos a conjunto para búsqueda rápida y evitar duplicados
    #     cola_procesamiento = sorted(list(set(paginas_a_procesar)))
    #     paginas_procesadas = set()
        
    #     tablas_md = []
    #     texto_completo = self.extraer_texto_pymupdf(path_local)
    #     metadatas = self.extraer_metadatos

    #     print(f"🕵️ Semillas detectadas: {cola_procesamiento}")
        
    #     # 2. BUCLE DE PROCESAMIENTO DINÁMICO
    #     # Usamos un while porque la lista puede crecer dinámicamente
    #     idx = 0
    #     while idx < len(cola_procesamiento):
    #         pag_actual = cola_procesamiento[idx]
    #         idx += 1
            
    #         if pag_actual in paginas_procesadas:
    #             continue
                
    #         paginas_procesadas.add(pag_actual)
            
            
    #         tablas = None # 1. Inicializamos a None por seguridad
    #         try:
    #             # Ejecutamos Camelot
    #             tablas = camelot.read_pdf(path_local, pages=str(pag_actual), flavor='lattice')
                
    #             if len(tablas) > 0:
    #                 print(f"   ✅ Tabla encontrada en pág {pag_actual}. Procesando...")
    #                 for tabla in tablas:
    #                     if tabla.df.shape[0] > 1: 
    #                         tablas_md.append(tabla.df.to_markdown(index=False))
                    
    #                 # Lógica de continuidad
    #                 siguiente_pag = pag_actual + 1
    #                 if siguiente_pag <= total_paginas:
    #                     if siguiente_pag not in paginas_procesadas and siguiente_pag not in cola_procesamiento:
    #                         print(f"   🔗 Posible continuación en pág {siguiente_pag}.")
    #                         cola_procesamiento.append(siguiente_pag)
    #                         cola_procesamiento.sort()
    #             else:
    #                 print(f"   ❌ Sin tablas en pág {pag_actual}.")
                    
    #         except Exception as e:
    #             print(f"⚠️ Error en pág {pag_actual}: {e}")
                
    #         finally:
    #             # 2. Esto se ejecuta SIEMPRE (haya error o no)
    #             if tablas is not None:
    #                 del tablas
    #             gc.collect() 
    #         # print(f"🧹 Limpieza de pág {pag_actual} completada.")

    #     print(f"📊 Total tablas extraídas: {len(tablas_md)}")
        
    #     return DocumentoExtraido(
    #         texto=texto_completo,
    #         tablas=tablas_md,
    #         metadatos=metadatas,
    #         tipo_documento="pliego"
    #     )

    def extraer_completo(self, url_or_path):
        """
        Orquesta la extracción usando PyMuPDF con lógica de continuidad y filtros espaciales.
        """
        path_local = self._obtener_path_local(url_or_path) 
        
        # 1. Obtener páginas iniciales (semillas)
        paginas_a_procesar, total_paginas = self._detectar_paginas_semilla(path_local)
        
        cola_procesamiento = sorted(list(set(paginas_a_procesar)))
        paginas_procesadas = set()
        tablas_md = []
        
        # Extraer texto y metadatos (Asegúrate de que extraer_metadatos lleve paréntesis si es un método)
        texto_completo = self.extraer_texto_pymupdf(path_local)
        # metadatos = self.extraer_metadatos() if callable(self.extraer_metadatos) else self.extraer_metadatos
        metadatos = self.extraer_metadatos(texto_completo)

        print(f"🕵️ Semillas detectadas: {cola_procesamiento}")

        # Abrimos el documento una sola vez para todo el proceso
        doc = fitz.open(path_local)
        
        try:
            idx = 0
            while idx < len(cola_procesamiento):
                pag_actual = cola_procesamiento[idx]
                idx += 1
                
                if pag_actual in paginas_procesadas or pag_actual > total_paginas:
                    continue
                    
                paginas_procesadas.add(pag_actual)
                
                try:
                    # PyMuPDF usa índices base 0
                    pagina = doc[pag_actual - 1]
                    
                    # Configurar márgenes de seguridad (ajustar según necesidad)
                    # Ignoramos los primeros y últimos 70 puntos (encabezados/pies)
                    MARGEN_SUPERIOR = 70
                    MARGEN_INFERIOR = pagina.rect.height - 70
                    
                    # 2. DETECCIÓN DE TABLAS
                    tabs = pagina.find_tables()
                    tablas_validas_en_pagina = 0
                    
                    if len(tabs.tables) > 0:
                        for i, tabla in enumerate(tabs):
                            x0, y0, x1, y1 = tabla.bbox
                            
                            # FILTRO ESPACIAL: ¿Está la tabla en el área relevante?
                            if y0 < MARGEN_SUPERIOR or y1 > MARGEN_INFERIOR:
                                # print(f"   ⏩ Ignorado recuadro en margen (y0: {y0:.1f})")
                                continue
                                
                            # FILTRO DE TAMAÑO: Evitar ruidos pequeños (sellos, firmas)
                            if (x1 - x0) < 100 or (y1 - y0) < 40:
                                continue

                            # Procesar como DataFrame
                            df = tabla.to_pandas()
                            if not df.empty and len(df) > 1:
                                tablas_md.append(df.to_markdown(index=False))
                                tablas_validas_en_pagina += 1
                        
                        if tablas_validas_en_pagina > 0:
                            print(f"   ✅ {tablas_validas_en_pagina} tabla(s) relevante(s) en pág {pag_actual}")
                            
                            # --- LÓGICA DE CONTINUIDAD ---
                            siguiente_pag = pag_actual + 1
                            if siguiente_pag <= total_paginas:
                                if siguiente_pag not in paginas_procesadas and siguiente_pag not in cola_procesamiento:
                                    print(f"   🔗 Posible continuación en pág {siguiente_pag}.")
                                    cola_procesamiento.append(siguiente_pag)
                                    # No hace falta sort() constante, pero ayuda a la trazabilidad
                                    cola_procesamiento.sort() 
                        else:
                            print(f"   ❌ Solo ruido detectado en pág {pag_actual}.")
                    else:
                        print(f"   ❌ Sin tablas en pág {pag_actual}.")
                        
                except Exception as e:
                    print(f"⚠️ Error procesando pág {pag_actual}: {e}")
                finally:
                    gc.collect()

        finally:
            doc.close() # Cerramos el archivo siempre

        print(f"📊 Total tablas extraídas: {len(tablas_md)}")
        
        return DocumentoExtraido(
            texto=texto_completo,
            tablas=tablas_md,
            metadatos=metadatos,
            tipo_documento="pliego"
        )


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    extractor = ExtractorPDFUnificado()
    
    # URL de ejemplo (reemplaza con tu PDF)
    url_pdf = "https://ejemplo.com/pliego.pdf"
    
    # Extraer todo
    documento = extractor.extraer_completo(
        url_or_path=url_pdf,
        paginas_tablas="1-10"
    )
    
    # Mostrar resultados
    print("\n📊 RESUMEN DE EXTRACCIÓN:")
    print(f"Tipo: {documento.tipo_documento}")
    print(f"Texto: {len(documento.texto)} chars")
    print(f"Tablas: {len(documento.tablas)}")
    print(f"\nMetadatos extraídos:")
    print(json.dumps(documento.metadatos, indent=2, ensure_ascii=False))
    
    if documento.tablas:
        print(f"\n📋 Primera tabla extraída:")
        print(documento.tablas[0][:500])

# import pandas as pd
# import json
# from typing import Dict, List, Optional
# from dataclasses import dataclass, asdict
# import requests
# from datetime import datetime

# @dataclass
# class AnalisisLicitacion:
#     """Estructura para almacenar el análisis completo de una licitación"""
#     pliego_id: str
#     fecha_analisis: str
#     resumen_tecnico: str
#     resumen_administrativo: str
#     certificaciones_necesarias: List[str]
#     presupuesto_sin_iva: Optional[float]
#     presupuesto_con_iva: Optional[float]
#     riesgos_identificados: List[Dict[str, str]]
#     complejidad: str
#     complejidad_score: int
#     partners_relevantes: List[str]
#     campos_enriquecidos: Dict[str, any]
    
#     def to_dict(self):
#         return asdict(self)

# class AnalizadorLicitaciones:
#     """Analizador de licitaciones usando Ollama (Llama 3)"""
    
#     def __init__(self, model: str = "llama3.2:3b", ollama_url: str = "http://localhost:11434"):
#         """
#         Inicializa el analizador con Ollama.
        
#         Args:
#             model: Modelo de Ollama a usar (llama3, llama3:70b, etc.)
#             ollama_url: URL base del servidor Ollama
#         """
#         self.model = model
#         self.ollama_url = ollama_url
#         self.api_endpoint = f"{ollama_url}/api/generate"
        
#         # Verificar que Ollama está disponible
#         try:
#             response = requests.get(f"{ollama_url}/api/tags")
#             if response.status_code == 200:
#                 print(f"✓ Conectado a Ollama en {ollama_url}")
#                 print(f"✓ Usando modelo: {model}")
#             else:
#                 print(f"⚠ Advertencia: Ollama respondió con código {response.status_code}")
#         except Exception as e:
#             print(f"⚠ No se pudo conectar a Ollama: {e}")
#             print(f"Asegúrate de que Ollama está corriendo en {ollama_url}")
    
#     def cargar_documentos(self, ruta_parquet: str) -> pd.DataFrame:
#         """Carga los documentos extraídos desde el archivo parquet"""
#         return pd.read_parquet(ruta_parquet)
    
#     def agrupar_por_licitacion(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
#         """Agrupa los documentos por pliego_id"""
#         return {pliego_id: grupo for pliego_id, grupo in df.groupby('pliego_id')}
    
#     def llamar_ollama(self, prompt: str, max_tokens: int = 8000) -> str:
#         """
#         Realiza una llamada a Ollama para generar una respuesta.
        
#         Args:
#             prompt: El prompt a enviar
#             max_tokens: Número máximo de tokens (nota: Ollama usa num_predict)
        
#         Returns:
#             Respuesta generada por el modelo
#         """
#         payload = {
#             "model": self.model,
#             "prompt": prompt,
#             "stream": False,
#             "options": {
#                 "num_predict": max_tokens,
#                 "temperature": 0.3,
#                 "top_p": 0.9,
#             }
#         }
        
#         try:
#             response = requests.post(
#                 self.api_endpoint,
#                 json=payload,
#                 timeout=600  # 5 minutos de timeout
#             )
#             response.raise_for_status()
            
#             result = response.json()
#             return result.get('response', '')
            
#         except requests.exceptions.Timeout:
#             raise Exception("Timeout: El modelo tardó demasiado en responder")
#         except requests.exceptions.RequestException as e:
#             raise Exception(f"Error en la llamada a Ollama: {str(e)}")
    
#     def chunking_inteligente(self, documentos: pd.DataFrame, max_chars: int = 15000) -> List[str]:
#         """
#         Divide los documentos en chunks manejables si son muy largos.
#         Ollama local puede tener limitaciones de contexto.
        
#         Args:
#             documentos: DataFrame con los documentos
#             max_chars: Máximo de caracteres por chunk
        
#         Returns:
#             Lista de chunks de texto
#         """
#         chunks = []
#         chunk_actual = ""
        
#         for _, doc in documentos.iterrows():
#             tipo = doc.get('TIPO', 'Desconocido')
#             descripcion = doc.get('DESCRIPCION', 'Sin descripción')
#             texto = doc.get('TEXTO_EXTRAIDO', '')
            
#             doc_texto = f"## DOCUMENTO: {tipo}\n**Descripción:** {descripcion}\n**Contenido:**\n{texto}\n\n"
            
#             if len(chunk_actual) + len(doc_texto) > max_chars:
#                 if chunk_actual:
#                     chunks.append(chunk_actual)
#                 chunk_actual = doc_texto
#             else:
#                 chunk_actual += doc_texto
        
#         if chunk_actual:
#             chunks.append(chunk_actual)
        
#         return chunks if chunks else [chunk_actual]
    
#     def analizar_licitacion(self, pliego_id: str, documentos: pd.DataFrame) -> AnalisisLicitacion:
#         """
#         Analiza una licitación completa usando Ollama.
        
#         Args:
#             pliego_id: ID de la licitación
#             documentos: DataFrame con todos los documentos de la licitación
        
#         Returns:
#             AnalisisLicitacion con toda la información extraída
#         """
#         # Dividir en chunks si es necesario
#         chunks = self.chunking_inteligente(documentos, max_chars=15000)
        
#         print(f"  - Documentos divididos en {len(chunks)} chunk(s)")
        
#         # Si hay múltiples chunks, procesarlos por separado y luego consolidar
#         if len(chunks) > 1:
#             return self._analizar_multipart(pliego_id, chunks)
#         else:
#             return self._analizar_single(pliego_id, chunks[0])
    
#     def _analizar_single(self, pliego_id: str, contexto: str) -> AnalisisLicitacion:
#         """Analiza una licitación con un solo chunk"""
        
#         prompt = f"""Eres un experto analista de licitaciones públicas en España. Analiza la documentación y extrae información clave.

# # DOCUMENTACIÓN DE LA LICITACIÓN

# {contexto}

# TAREA: Analiza la documentación y responde EN FORMATO JSON VÁLIDO con esta estructura exacta:

# {{
#   "resumen_tecnico": "Resumen del pliego técnico (máximo 400 palabras): objeto, alcance, requisitos, entregables, criterios de calidad",
#   "resumen_administrativo": "Resumen del pliego administrativo (máximo 400 palabras): procedimiento, plazos, criterios de adjudicación, garantías, forma de pago",
#   "certificaciones_necesarias": ["Lista de certificaciones, acreditaciones o títulos necesarios"],
#   "presupuesto": {{
#     "sin_iva": 0.0,
#     "con_iva": 0.0,
#     "notas": "Detalles adicionales"
#   }},
#   "riesgos": [
#     {{"categoria": "Técnico/Administrativo/Financiero/Temporal", "descripcion": "Descripción del riesgo", "severidad": "Alta/Media/Baja"}}
#   ],
#   "complejidad": {{
#     "nivel": "Muy Alta/Alta/Media/Baja",
#     "score": 5,
#     "justificacion": "Razones de la complejidad"
#   }},
#   "partners_relevantes": ["Empresas, organismos o entidades mencionadas"],
#   "campos_enriquecidos": {{
#     "plazo_ejecucion": "",
#     "sector": "",
#     "tipo_contrato": "Servicios/Obras/Suministros",
#     "organismo_contratante": "",
#     "ubicacion": "",
#     "criterios_adjudicacion": "",
#     "numero_lotes": 0,
#     "posibilidad_variantes": false,
#     "visita_obligatoria": false
#   }}
# }}

# IMPORTANTE:
# - Responde SOLO con JSON válido, sin texto adicional
# - Si no encuentras información, usa null o []
# - Extrae cifras numéricas exactas para presupuesto
# - Score de complejidad: 1 (simple) a 10 (muy compleja)

# JSON:"""

#         try:
#             print(f"  - Llamando a Ollama...")
#             respuesta = self.llamar_ollama(prompt, max_tokens=6000)
            
#             # Limpiar la respuesta
#             respuesta = respuesta.strip()
            
#             # Intentar extraer JSON si hay texto adicional
#             if '```json' in respuesta:
#                 start = respuesta.find('```json') + 7
#                 end = respuesta.find('```', start)
#                 respuesta = respuesta[start:end].strip()
#             elif '```' in respuesta:
#                 start = respuesta.find('```') + 3
#                 end = respuesta.find('```', start)
#                 respuesta = respuesta[start:end].strip()
            
#             # Encontrar el JSON (buscar el primer { y último })
#             first_brace = respuesta.find('{')
#             last_brace = respuesta.rfind('}')
            
#             if first_brace != -1 and last_brace != -1:
#                 respuesta = respuesta[first_brace:last_brace + 1]
            
#             # Parsear el JSON
#             resultado = json.loads(respuesta)
            
#             # Crear objeto de análisis
#             analisis = AnalisisLicitacion(
#                 pliego_id=pliego_id,
#                 fecha_analisis=datetime.now().isoformat(),
#                 resumen_tecnico=resultado.get('resumen_tecnico', ''),
#                 resumen_administrativo=resultado.get('resumen_administrativo', ''),
#                 certificaciones_necesarias=resultado.get('certificaciones_necesarias', []),
#                 presupuesto_sin_iva=resultado.get('presupuesto', {}).get('sin_iva'),
#                 presupuesto_con_iva=resultado.get('presupuesto', {}).get('con_iva'),
#                 riesgos_identificados=resultado.get('riesgos', []),
#                 complejidad=resultado.get('complejidad', {}).get('nivel', 'Desconocida'),
#                 complejidad_score=resultado.get('complejidad', {}).get('score', 5),
#                 partners_relevantes=resultado.get('partners_relevantes', []),
#                 campos_enriquecidos=resultado.get('campos_enriquecidos', {})
#             )
            
#             return analisis
            
#         except json.JSONDecodeError as e:
#             print(f"  ✗ Error parseando JSON: {str(e)}")
#             print(f"  Respuesta del modelo: {respuesta[:500]}...")
#             raise Exception(f"El modelo no generó un JSON válido")
#         except Exception as e:
#             print(f"  ✗ Error analizando: {str(e)}")
#             raise
    
#     def _analizar_multipart(self, pliego_id: str, chunks: List[str]) -> AnalisisLicitacion:
#         """Analiza una licitación dividida en múltiples chunks"""
        
#         print(f"  - Procesando licitación en {len(chunks)} partes...")
        
#         analisis_parciales = []
        
#         # Analizar cada chunk
#         for i, chunk in enumerate(chunks, 1):
#             print(f"    Procesando parte {i}/{len(chunks)}...")
#             try:
#                 analisis_parcial = self._analizar_single(f"{pliego_id}_part{i}", chunk)
#                 analisis_parciales.append(analisis_parcial)
#             except Exception as e:
#                 print(f"    ⚠ Error en parte {i}: {str(e)}")
#                 continue
        
#         if not analisis_parciales:
#             raise Exception("No se pudo analizar ningún chunk correctamente")
        
#         # Consolidar resultados
#         print(f"  - Consolidando resultados...")
#         return self._consolidar_analisis(pliego_id, analisis_parciales)
    
#     def _consolidar_analisis(self, pliego_id: str, analisis_parciales: List[AnalisisLicitacion]) -> AnalisisLicitacion:
#         """Consolida múltiples análisis parciales en uno final"""
        
#         # Concatenar resúmenes
#         resumen_tecnico = " ".join([a.resumen_tecnico for a in analisis_parciales if a.resumen_tecnico])
#         resumen_administrativo = " ".join([a.resumen_administrativo for a in analisis_parciales if a.resumen_administrativo])
        
#         # Unir listas eliminando duplicados
#         certificaciones = list(set(
#             cert for a in analisis_parciales 
#             for cert in a.certificaciones_necesarias
#         ))
        
#         partners = list(set(
#             partner for a in analisis_parciales 
#             for partner in a.partners_relevantes
#         ))
        
#         # Consolidar riesgos
#         riesgos = []
#         for a in analisis_parciales:
#             riesgos.extend(a.riesgos_identificados)
        
#         # Tomar el presupuesto más alto (asumiendo que es el más completo)
#         presupuestos = [(a.presupuesto_sin_iva, a.presupuesto_con_iva) 
#                        for a in analisis_parciales 
#                        if a.presupuesto_sin_iva]
        
#         if presupuestos:
#             presupuesto_sin_iva, presupuesto_con_iva = max(presupuestos, key=lambda x: x[0] or 0)
#         else:
#             presupuesto_sin_iva, presupuesto_con_iva = None, None
        
#         # Complejidad: usar la más alta
#         complejidad_score = max([a.complejidad_score for a in analisis_parciales])
#         complejidades = ["Baja", "Media", "Alta", "Muy Alta"]
#         if complejidad_score <= 3:
#             complejidad = "Baja"
#         elif complejidad_score <= 5:
#             complejidad = "Media"
#         elif complejidad_score <= 7:
#             complejidad = "Alta"
#         else:
#             complejidad = "Muy Alta"
        
#         # Consolidar campos enriquecidos
#         campos_enriquecidos = {}
#         for a in analisis_parciales:
#             campos_enriquecidos.update(a.campos_enriquecidos)
        
#         return AnalisisLicitacion(
#             pliego_id=pliego_id,
#             fecha_analisis=datetime.now().isoformat(),
#             resumen_tecnico=resumen_tecnico[:2000],  # Limitar longitud
#             resumen_administrativo=resumen_administrativo[:2000],
#             certificaciones_necesarias=certificaciones,
#             presupuesto_sin_iva=presupuesto_sin_iva,
#             presupuesto_con_iva=presupuesto_con_iva,
#             riesgos_identificados=riesgos,
#             complejidad=complejidad,
#             complejidad_score=complejidad_score,
#             partners_relevantes=partners,
#             campos_enriquecidos=campos_enriquecidos
#         )
    
#     def procesar_todas_licitaciones(
#         self, 
#         ruta_parquet: str, 
#         ruta_salida: str = "Analisis_licitaciones.parquet"
#     ) -> pd.DataFrame:
#         """
#         Procesa todas las licitaciones del archivo parquet.
        
#         Args:
#             ruta_parquet: Ruta al archivo Textos_extraidos.parquet
#             ruta_salida: Ruta donde guardar los resultados
        
#         Returns:
#             DataFrame con todos los análisis
#         """
#         print("Cargando documentos...")
#         df_documentos = self.cargar_documentos(ruta_parquet)
        
#         print(f"Documentos cargados: {len(df_documentos)}")
        
#         licitaciones = self.agrupar_por_licitacion(df_documentos)
#         print(f"Licitaciones únicas encontradas: {len(licitaciones)}")
        
#         resultados = []
        
#         for idx, (pliego_id, docs) in enumerate(licitaciones.items(), 1):
#             print(f"\n[{idx}/{len(licitaciones)}] Analizando licitación: {pliego_id}")
#             print(f"  - Documentos asociados: {len(docs)}")
            
#             try:
#                 analisis = self.analizar_licitacion(pliego_id, docs)
#                 resultados.append(analisis.to_dict())
#                 print(f"  ✓ Análisis completado")
                
#             except Exception as e:
#                 print(f"  ✗ Error: {str(e)}")
#                 continue
        
#         # Convertir a DataFrame
#         df_resultados = pd.DataFrame(resultados)
        
#         # Guardar resultados
#         df_resultados.to_parquet(ruta_salida, index=False)
#         print(f"\n✓ Resultados guardados en: {ruta_salida}")
#         print(f"✓ Total de licitaciones analizadas: {len(df_resultados)}")
        
#         return df_resultados
    
#     def analizar_licitacion_individual(
#         self, 
#         pliego_id: str, 
#         ruta_parquet: str
#     ) -> Optional[AnalisisLicitacion]:
#         """
#         Analiza una única licitación específica.
        
#         Args:
#             pliego_id: ID de la licitación a analizar
#             ruta_parquet: Ruta al archivo de documentos
        
#         Returns:
#             AnalisisLicitacion o None si no se encuentra
#         """
#         df_documentos = self.cargar_documentos(ruta_parquet)
#         docs = df_documentos[df_documentos['pliego_id'] == pliego_id]
        
#         if docs.empty:
#             print(f"No se encontraron documentos para el pliego_id: {pliego_id}")
#             return None
        
#         return self.analizar_licitacion(pliego_id, docs)


# # =============================================================================
# # EJEMPLO DE USO
# # =============================================================================

# if __name__ == "__main__":
#     # Inicializar el analizador
#     analizador = AnalizadorLicitaciones()
    
#     # OPCIÓN 1: Procesar todas las licitaciones
#     df_analisis = analizador.procesar_todas_licitaciones(
#         # ruta_parquet="Textos_Extraidos_viejo.parquet",
#         ruta_parquet = r"src\Textos_Extraidos_viejo.parquet",
#         ruta_salida="Analisis_licitaciones.parquet"
#     )
    
#     # Mostrar resumen
#     print("\n" + "="*80)
#     print("RESUMEN DEL ANÁLISIS")
#     print("="*80)
#     print(f"Total licitaciones analizadas: {len(df_analisis)}")
#     print(f"\nDistribución por complejidad:")
#     print(df_analisis['complejidad'].value_counts())
    
#     # OPCIÓN 2: Analizar una licitación específica
#     # analisis_individual = analizador.analizar_licitacion_individual(
#     #     pliego_id="LIC-2024-001",
#     #     ruta_parquet="Textos_extraidos_viejo.parquet"
#     # )
#     # 
#     # if analisis_individual:
#     #     print(json.dumps(analisis_individual.to_dict(), indent=2, ensure_ascii=False))


## ----------------------

import pandas as pd
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests
from datetime import datetime

@dataclass
class AnalisisLicitacion:
    """Estructura para almacenar el análisis completo de una licitación"""
    pliego_id: str
    fecha_analisis: str
    resumen_tecnico: str
    resumen_administrativo: str
    certificaciones_necesarias: List[str]
    presupuesto_sin_iva: Optional[float]
    presupuesto_con_iva: Optional[float]
    riesgos_identificados: List[Dict[str, str]]
    complejidad: str
    complejidad_score: int
    partners_relevantes: List[str]
    campos_enriquecidos: Dict[str, any]
    
    def to_dict(self):
        return asdict(self)

class AnalizadorLicitaciones:
    """Analizador de licitaciones usando Ollama (Llama 3)"""
    
    def __init__(self, model: str = "llama3.2:3b", ollama_url: str = "http://localhost:11434"):
        """
        Inicializa el analizador con Ollama.
        
        Args:
            model: Modelo de Ollama a usar (llama3, llama3:70b, etc.)
            ollama_url: URL base del servidor Ollama
        """
        self.model = model
        self.ollama_url = ollama_url
        self.api_endpoint = f"{ollama_url}/api/generate"
        
        # Verificar que Ollama está disponible
        try:
            response = requests.get(f"{ollama_url}/api/tags")
            if response.status_code == 200:
                print(f"✓ Conectado a Ollama en {ollama_url}")
                print(f"✓ Usando modelo: {model}")
            else:
                print(f"⚠ Advertencia: Ollama respondió con código {response.status_code}")
        except Exception as e:
            print(f"⚠ No se pudo conectar a Ollama: {e}")
            print(f"Asegúrate de que Ollama está corriendo en {ollama_url}")
    
    def cargar_documentos(self, ruta_parquet: str) -> pd.DataFrame:
        """Carga los documentos extraídos desde el archivo parquet"""
        return pd.read_parquet(ruta_parquet)
    
    def agrupar_por_licitacion(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Agrupa los documentos por pliego_id"""
        return {pliego_id: grupo for pliego_id, grupo in df.groupby('pliego_id')}
    
    def llamar_ollama(self, prompt: str, max_tokens: int = 8000) -> str:
        """
        Realiza una llamada a Ollama para generar una respuesta.
        
        Args:
            prompt: El prompt a enviar
            max_tokens: Número máximo de tokens (nota: Ollama usa num_predict)
        
        Returns:
            Respuesta generada por el modelo
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.3,
                "top_p": 0.9,
            }
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=600  # 5 minutos de timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.Timeout:
            raise Exception("Timeout: El modelo tardó demasiado en responder")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error en la llamada a Ollama: {str(e)}")
    
    def chunking_inteligente(self, documentos: pd.DataFrame, max_chars: int = 15000) -> List[str]:
        """
        Divide los documentos en chunks manejables si son muy largos.
        Ollama local puede tener limitaciones de contexto.
        
        Args:
            documentos: DataFrame con los documentos
            max_chars: Máximo de caracteres por chunk
        
        Returns:
            Lista de chunks de texto
        """
        chunks = []
        chunk_actual = ""
        
        for _, doc in documentos.iterrows():
            tipo = doc.get('TIPO', 'Desconocido')
            descripcion = doc.get('DESCRIPCION', 'Sin descripción')
            texto = doc.get('TEXTO_EXTRAIDO', '')
            
            doc_texto = f"## DOCUMENTO: {tipo}\n**Descripción:** {descripcion}\n**Contenido:**\n{texto}\n\n"
            
            if len(chunk_actual) + len(doc_texto) > max_chars:
                if chunk_actual:
                    chunks.append(chunk_actual)
                chunk_actual = doc_texto
            else:
                chunk_actual += doc_texto
        
        if chunk_actual:
            chunks.append(chunk_actual)
        
        return chunks if chunks else [chunk_actual]
    
    def analizar_licitacion(self, pliego_id: str, documentos: pd.DataFrame) -> AnalisisLicitacion:
        """
        Analiza una licitación completa usando Ollama.
        
        Args:
            pliego_id: ID de la licitación
            documentos: DataFrame con todos los documentos de la licitación
        
        Returns:
            AnalisisLicitacion con toda la información extraída
        """
        # Dividir en chunks si es necesario
        chunks = self.chunking_inteligente(documentos, max_chars=15000)
        
        print(f"  - Documentos divididos en {len(chunks)} chunk(s)")
        
        # Si hay múltiples chunks, procesarlos por separado y luego consolidar
        if len(chunks) > 1:
            return self._analizar_multipart(pliego_id, chunks)
        else:
            return self._analizar_single(pliego_id, chunks[0])
    
    def _analizar_single(self, pliego_id: str, contexto: str) -> AnalisisLicitacion:
        """Analiza una licitación con un solo chunk"""
        
        prompt = f"""Eres un experto analista de licitaciones públicas en España. Analiza la documentación y extrae información clave.

# DOCUMENTACIÓN DE LA LICITACIÓN

{contexto}

TAREA: Analiza la documentación y responde EN FORMATO JSON VÁLIDO con esta estructura exacta:

{{
  "resumen_tecnico": "Resumen del pliego técnico (máximo 400 palabras): objeto, alcance, requisitos, entregables, criterios de calidad",
  "resumen_administrativo": "Resumen del pliego administrativo (máximo 400 palabras): procedimiento, plazos, criterios de adjudicación, garantías, forma de pago",
  "certificaciones_necesarias": ["Lista de certificaciones, acreditaciones o títulos necesarios"],
  "presupuesto": {{
    "sin_iva": 0.0,
    "con_iva": 0.0,
    "notas": "Detalles adicionales"
  }},
  "riesgos": [
    {{"categoria": "Técnico/Administrativo/Financiero/Temporal", "descripcion": "Descripción del riesgo", "severidad": "Alta/Media/Baja"}}
  ],
  "complejidad": {{
    "nivel": "Muy Alta/Alta/Media/Baja",
    "score": 5,
    "justificacion": "Razones de la complejidad"
  }},
  "partners_relevantes": ["Empresas, organismos o entidades mencionadas"],
  "campos_enriquecidos": {{
    "plazo_ejecucion": "",
    "sector": "",
    "tipo_contrato": "Servicios/Obras/Suministros",
    "organismo_contratante": "",
    "ubicacion": "",
    "criterios_adjudicacion": "",
    "numero_lotes": 0,
    "posibilidad_variantes": false,
    "visita_obligatoria": false
  }}
}}

IMPORTANTE:
- Responde SOLO con JSON válido, sin texto adicional
- Si no encuentras información, usa null o []
- Extrae cifras numéricas exactas para presupuesto
- Score de complejidad: 1 (simple) a 10 (muy compleja)

JSON:"""

        try:
            print(f"  - Llamando a Ollama...")
            respuesta = self.llamar_ollama(prompt, max_tokens=6000)
            
            # Limpiar la respuesta
            respuesta = respuesta.strip()
            
            # Intentar extraer JSON si hay texto adicional
            if '```json' in respuesta:
                start = respuesta.find('```json') + 7
                end = respuesta.find('```', start)
                respuesta = respuesta[start:end].strip()
            elif '```' in respuesta:
                start = respuesta.find('```') + 3
                end = respuesta.find('```', start)
                respuesta = respuesta[start:end].strip()
            
            # Encontrar el JSON (buscar el primer { y último })
            first_brace = respuesta.find('{')
            last_brace = respuesta.rfind('}')
            
            if first_brace != -1 and last_brace != -1:
                respuesta = respuesta[first_brace:last_brace + 1]
            
            # Parsear el JSON
            resultado = json.loads(respuesta)
            
            # Crear objeto de análisis
            analisis = AnalisisLicitacion(
                pliego_id=pliego_id,
                fecha_analisis=datetime.now().isoformat(),
                resumen_tecnico=resultado.get('resumen_tecnico', ''),
                resumen_administrativo=resultado.get('resumen_administrativo', ''),
                certificaciones_necesarias=resultado.get('certificaciones_necesarias', []),
                presupuesto_sin_iva=resultado.get('presupuesto', {}).get('sin_iva'),
                presupuesto_con_iva=resultado.get('presupuesto', {}).get('con_iva'),
                riesgos_identificados=resultado.get('riesgos', []),
                complejidad=resultado.get('complejidad', {}).get('nivel', 'Desconocida'),
                complejidad_score=resultado.get('complejidad', {}).get('score', 5),
                partners_relevantes=resultado.get('partners_relevantes', []),
                campos_enriquecidos=resultado.get('campos_enriquecidos', {})
            )
            
            return analisis
            
        except json.JSONDecodeError as e:
            print(f"  ✗ Error parseando JSON: {str(e)}")
            print(f"  Respuesta del modelo: {respuesta[:500]}...")
            raise Exception(f"El modelo no generó un JSON válido")
        except Exception as e:
            print(f"  ✗ Error analizando: {str(e)}")
            raise
    
    def _analizar_multipart(self, pliego_id: str, chunks: List[str]) -> AnalisisLicitacion:
        """Analiza una licitación dividida en múltiples chunks"""
        
        print(f"  - Procesando licitación en {len(chunks)} partes...")
        
        analisis_parciales = []
        
        # Analizar cada chunk
        for i, chunk in enumerate(chunks, 1):
            print(f"    Procesando parte {i}/{len(chunks)}...")
            try:
                analisis_parcial = self._analizar_single(f"{pliego_id}_part{i}", chunk)
                analisis_parciales.append(analisis_parcial)
            except Exception as e:
                print(f"    ⚠ Error en parte {i}: {str(e)}")
                continue
        
        if not analisis_parciales:
            raise Exception("No se pudo analizar ningún chunk correctamente")
        
        # Consolidar resultados
        print(f"  - Consolidando resultados...")
        return self._consolidar_analisis(pliego_id, analisis_parciales)
    
    def _consolidar_analisis(self, pliego_id: str, analisis_parciales: List[AnalisisLicitacion]) -> AnalisisLicitacion:
        """Consolida múltiples análisis parciales en uno final"""
        
        # Concatenar resúmenes
        resumen_tecnico = " ".join([a.resumen_tecnico for a in analisis_parciales if a.resumen_tecnico])
        resumen_administrativo = " ".join([a.resumen_administrativo for a in analisis_parciales if a.resumen_administrativo])
        
        # Unir listas eliminando duplicados
        certificaciones = list(set(
            cert for a in analisis_parciales 
            for cert in a.certificaciones_necesarias
        ))
        
        partners = list(set(
            partner for a in analisis_parciales 
            for partner in a.partners_relevantes
        ))
        
        # Consolidar riesgos
        riesgos = []
        for a in analisis_parciales:
            riesgos.extend(a.riesgos_identificados)
        
        # Tomar el presupuesto más alto (asumiendo que es el más completo)
        presupuestos = [(a.presupuesto_sin_iva, a.presupuesto_con_iva) 
                       for a in analisis_parciales 
                       if a.presupuesto_sin_iva]
        
        if presupuestos:
            presupuesto_sin_iva, presupuesto_con_iva = max(presupuestos, key=lambda x: x[0] or 0)
        else:
            presupuesto_sin_iva, presupuesto_con_iva = None, None
        
        # Complejidad: usar la más alta
        complejidad_score = max([a.complejidad_score for a in analisis_parciales])
        complejidades = ["Baja", "Media", "Alta", "Muy Alta"]
        if complejidad_score <= 3:
            complejidad = "Baja"
        elif complejidad_score <= 5:
            complejidad = "Media"
        elif complejidad_score <= 7:
            complejidad = "Alta"
        else:
            complejidad = "Muy Alta"
        
        # Consolidar campos enriquecidos
        campos_enriquecidos = {}
        for a in analisis_parciales:
            campos_enriquecidos.update(a.campos_enriquecidos)
        
        return AnalisisLicitacion(
            pliego_id=pliego_id,
            fecha_analisis=datetime.now().isoformat(),
            resumen_tecnico=resumen_tecnico[:2000],  # Limitar longitud
            resumen_administrativo=resumen_administrativo[:2000],
            certificaciones_necesarias=certificaciones,
            presupuesto_sin_iva=presupuesto_sin_iva,
            presupuesto_con_iva=presupuesto_con_iva,
            riesgos_identificados=riesgos,
            complejidad=complejidad,
            complejidad_score=complejidad_score,
            partners_relevantes=partners,
            campos_enriquecidos=campos_enriquecidos
        )
    
    def procesar_todas_licitaciones(
        self, 
        ruta_parquet: str, 
        ruta_salida: str = "Analisis_licitaciones.parquet",
        modo_prueba: bool = False,
        num_prueba: int = 2
    ) -> pd.DataFrame:
        """
        Procesa todas las licitaciones del archivo parquet.
        
        Args:
            ruta_parquet: Ruta al archivo Textos_extraidos.parquet
            ruta_salida: Ruta donde guardar los resultados
            modo_prueba: Si es True, solo procesa las primeras 'num_prueba' licitaciones
            num_prueba: Número de licitaciones a procesar en modo prueba
        
        Returns:
            DataFrame con todos los análisis
        """
        print("Cargando documentos...")
        df_documentos = self.cargar_documentos(ruta_parquet)
        
        print(f"Documentos cargados: {len(df_documentos)}")
        
        licitaciones = self.agrupar_por_licitacion(df_documentos)
        print(f"Licitaciones únicas encontradas: {len(licitaciones)}")
        
        # MODO PRUEBA: Limitar a las primeras N licitaciones
        if modo_prueba:
            licitaciones_items = list(licitaciones.items())[:num_prueba]
            licitaciones = dict(licitaciones_items)
            print(f"\n{'='*80}")
            print(f"🧪 MODO PRUEBA ACTIVADO: Procesando solo {num_prueba} licitaciones")
            print(f"{'='*80}\n")
        
        resultados = []
        
        for idx, (pliego_id, docs) in enumerate(licitaciones.items(), 1):
            print(f"\n[{idx}/{len(licitaciones)}] Analizando licitación: {pliego_id}")
            print(f"  - Documentos asociados: {len(docs)}")
            
            try:
                analisis = self.analizar_licitacion(pliego_id, docs)
                resultados.append(analisis.to_dict())
                print(f"  ✓ Análisis completado")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                continue
        
        # Convertir a DataFrame
        df_resultados = pd.DataFrame(resultados)
        
        # Guardar resultados
        df_resultados.to_parquet(ruta_salida, index=False)
        print(f"\n✓ Resultados guardados en: {ruta_salida}")
        print(f"✓ Total de licitaciones analizadas: {len(df_resultados)}")
        
        if modo_prueba:
            print(f"\n{'='*80}")
            print(f"🧪 PRUEBA COMPLETADA - Desactiva modo_prueba=False para procesar todas")
            print(f"{'='*80}")
        
        return df_resultados
    
    def analizar_licitacion_individual(
        self, 
        pliego_id: str, 
        ruta_parquet: str
    ) -> Optional[AnalisisLicitacion]:
        """
        Analiza una única licitación específica.
        
        Args:
            pliego_id: ID de la licitación a analizar
            ruta_parquet: Ruta al archivo de documentos
        
        Returns:
            AnalisisLicitacion o None si no se encuentra
        """
        df_documentos = self.cargar_documentos(ruta_parquet)
        docs = df_documentos[df_documentos['pliego_id'] == pliego_id]
        
        if docs.empty:
            print(f"No se encontraron documentos para el pliego_id: {pliego_id}")
            return None
        
        return self.analizar_licitacion(pliego_id, docs)


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Inicializar el analizador
    analizador = AnalizadorLicitaciones()
    
    # =========================================================================
    # 🧪 MODO PRUEBA: Descomentar para probar con 2 licitaciones
    # =========================================================================
    # df_analisis = analizador.procesar_todas_licitaciones(
    #     ruta_parquet=r"src\Textos_Extraidos_viejo.parquet",
    #     ruta_salida="Analisis_licitaciones_PRUEBA.parquet",
    #     modo_prueba=True,  # ✅ Cambiar a False para procesar todas
    #     num_prueba=2        # Número de licitaciones para la prueba
    # )
    
    # =========================================================================
    # 📊 MODO COMPLETO: Descomentar para procesar TODAS las licitaciones
    # =========================================================================
    df_analisis = analizador.procesar_todas_licitaciones(
        ruta_parquet=r"src\Textos_Extraidos_viejo.parquet",
        ruta_salida="Analisis_licitaciones_COMPLETO.parquet",
        modo_prueba=False
    )
    
    # Mostrar resumen
    print("\n" + "="*80)
    print("RESUMEN DEL ANÁLISIS")
    print("="*80)
    print(f"Total licitaciones analizadas: {len(df_analisis)}")
    if len(df_analisis) > 0:
        print(f"\nDistribución por complejidad:")
        print(df_analisis['complejidad'].value_counts())
        
        print(f"\nPrimera licitación analizada:")
        print(f"  - ID: {df_analisis.iloc[0]['pliego_id']}")
        print(f"  - Complejidad: {df_analisis.iloc[0]['complejidad']}")
        print(f"  - Score: {df_analisis.iloc[0]['complejidad_score']}")
    
    # =========================================================================
    # OPCIÓN ALTERNATIVA: Analizar una licitación específica por ID
    # =========================================================================
    # analisis_individual = analizador.analizar_licitacion_individual(
    #     pliego_id="TU_PLIEGO_ID_AQUI",
    #     ruta_parquet=r"src\Textos_Extraidos_viejo.parquet"
    # )
    # 
    # if analisis_individual:
    #     print(json.dumps(analisis_individual.to_dict(), indent=2, ensure_ascii=False))

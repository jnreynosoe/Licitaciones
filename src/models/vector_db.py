# import chromadb
# from chromadb.utils import embedding_functions
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# import os
# import camelot

# # Configuración
# PERSIST_PATH = "./chroma_db_licitaciones" # Carpeta donde se guardarán los datos
# MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2" 

# class GestorLicitaciones:
#     def __init__(self):
#         # 1. Iniciamos el cliente persistente (guarda en disco)
#         self.client = chromadb.PersistentClient(path=PERSIST_PATH)
        
#         # 2. Configurar la función de embedding (usa tu modelo actual automáticamente)
#         self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
#             model_name=MODEL_NAME
#         )
        
#         # 3. Crear o cargar la colección (como una tabla de SQL)
#         self.collection = self.client.get_or_create_collection(
#             name="pliegos_licitaciones",
#             embedding_function=self.embedding_fn
#         )
        
#         # 4. Configuramos el splitter inteligente
#         # Este corta por párrafos (\n\n), luego por líneas (\n), luego espacios.
#         # Es mucho mejor que cortar cada 1200 palabras fijas.
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,      # Tamaño del trozo
#             chunk_overlap=400,    # Solapamiento para no perder contexto entre cortes
#             separators=["\n\n", "\n", ". ", " ", ""]
#         )

#     # Ejemplo de cómo añadirlo a tu clase GestorLicitaciones
#     # def indexar_con_tablas(self, pdf_path, pliego_id):
#     #     # 1. Extraer y guardar texto normal
#     #     texto = extraer_texto_pymupdf(pdf_path)
#     #     self.indexar_documento(texto, pliego_id)
        
#     #     # 2. Extraer tablas con Camelot y guardarlas como chunks especiales
#     #     tablas_md = self.obtener_tablas_como_markdown(pdf_path)
#     #     for i, tabla_texto in enumerate(tablas_md):
#     #         self.collection.add(
#     #             documents=[tabla_texto],
#     #             ids=[f"{pliego_id}_table_{i}"],
#     #             metadatas=[{"pliego_id": pliego_id, "tipo": "tabla"}]
#     #         )

#     def indexar_documento(self, texto_completo, pliego_id, metadatos_extra={}):
#         """
#         Recibe el texto del PDF, lo trocea y lo guarda en la base vectorial.
#         """
#         print(f"🔄 Indexando licitación {pliego_id}...")
        
#         # A. Verificar si ya existe para no duplicar
#         existing = self.collection.get(where={"pliego_id": pliego_id})
#         if len(existing['ids']) > 0:
#             print(f"✅ La licitación {pliego_id} ya está en la base de datos.")
#             return

#         # B. Chunking inteligente
#         chunks = self.text_splitter.split_text(texto_completo)
        
#         # C. Preparar datos para Chroma
#         ids = [f"{pliego_id}_{i}" for i in range(len(chunks))]
#         metadatas = []
#         for i in range(len(chunks)):
#             meta = {
#                 "pliego_id": pliego_id, 
#                 "chunk_index": i, 
#                 **metadatos_extra # Ej: {"tipo": "Pliego Técnico"}
#             }
#             metadatas.append(meta)

#         # D. Guardar (Chroma calcula los embeddings automágicamente aquí)
#         self.collection.add(
#             documents=chunks,
#             ids=ids,
#             metadatas=metadatas
#         )
#         print(f"💾 Guardados {len(chunks)} fragmentos en disco.")

#     def buscar_contexto(self, query, pliego_id=None, n_resultados=5):
#         """
#         Busca los fragmentos más relevantes para tu pregunta.
#         """
#         filtros = {}
#         if pliego_id:
#             filtros = {"pliego_id": pliego_id}

#         results = self.collection.query(
#             query_texts=[query],
#             n_results=n_resultados,
#             where=filtros # Filtra para buscar SOLO en un documento específico si quieres
#         )
        
#         # Devolver lista de textos encontrados
#         return results['documents'][0]
    
#     def obtener_tablas_como_markdown(self, pdf_path, paginas='1-10'):
#         # Limitamos a las primeras 10 páginas para ahorrar tiempo (donde suele estar el Cuadro Resumen)
#         tablas = camelot.read_pdf(pdf_path, pages=paginas, flavor='lattice')
        
#         tablas_markdown = []
#         for i, tabla in enumerate(tablas):
#             # Convertimos el DataFrame de Pandas a Markdown
#             md = tabla.df.to_markdown(index=False)
#             tablas_markdown.append(f"\n### TABLA EXTRAÍDA {i+1}\n{md}\n")
        
#         return tablas_markdown

## ----------------------------------

# import chromadb
# from chromadb.utils import embedding_functions
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# import hashlib
# import json
# from typing import List, Dict, Optional, Tuple
# from datetime import datetime
# import pandas as pd

# class GestorLicitacionesMejorado:
#     """
#     Sistema de gestión vectorial optimizado para licitaciones públicas.
    
#     Mejoras:
#     - Caché de embeddings para evitar recálculos
#     - Metadatos estructurados (fechas, presupuestos, tipo doc)
#     - Chunking optimizado por tipo de documento
#     - Búsqueda híbrida (vectorial + filtros)
#     """
    
#     def __init__(
#         self, 
#         persist_path: str = "./chroma_db_licitaciones",
#         model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
#     ):
#         self.persist_path = persist_path
#         self.model_name = model_name
        
#         # Cliente persistente
#         self.client = chromadb.PersistentClient(path=persist_path)
        
#         # Función de embedding
#         self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
#             model_name=model_name
#         )
        
#         # Colecciones separadas por tipo de contenido
#         self.collection_texto = self.client.get_or_create_collection(
#             name="texto_pliegos",
#             embedding_function=self.embedding_fn,
#             metadata={"description": "Texto de pliegos técnicos y administrativos"}
#         )
        
#         self.collection_tablas = self.client.get_or_create_collection(
#             name="tablas_pliegos",
#             embedding_function=self.embedding_fn,
#             metadata={"description": "Tablas estructuradas (cuadros resumen, presupuestos)"}
#         )
        
#         # Configurar splitters especializados
#         self._configurar_splitters()
        
#         # Caché de documentos procesados
#         self.cache_procesados = self._cargar_cache()
    
#     def _configurar_splitters(self):
#         """Configura estrategias de chunking por tipo de documento"""
        
#         # Para texto administrativo (más denso, legal)
#         self.splitter_admin = RecursiveCharacterTextSplitter(
#             chunk_size=800,
#             chunk_overlap=200,
#             separators=["\n\n", "\n", ". ", ".", " ", ""],
#             length_function=len
#         )
        
#         # Para texto técnico (descripciones, requisitos)
#         self.splitter_tecnico = RecursiveCharacterTextSplitter(
#             chunk_size=1200,
#             chunk_overlap=300,
#             separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
#             length_function=len
#         )
        
#         # Para tablas (chunks pequeños, contextuales)
#         self.splitter_tabla = RecursiveCharacterTextSplitter(
#             chunk_size=500,
#             chunk_overlap=50,
#             separators=["\n", "|", " ", ""]
#         )
    
#     def _cargar_cache(self) -> Dict:
#         """Carga registro de documentos ya procesados"""
#         try:
#             with open(f"{self.persist_path}/cache_documentos.json", 'r') as f:
#                 return json.load(f)
#         except FileNotFoundError:
#             return {}
    
#     def _guardar_cache(self):
#         """Guarda el caché de documentos procesados"""
#         with open(f"{self.persist_path}/cache_documentos.json", 'w') as f:
#             json.dump(self.cache_procesados, f, indent=2)
    
#     def _hash_documento(self, texto: str) -> str:
#         """Genera hash único para detectar documentos duplicados"""
#         return hashlib.md5(texto.encode('utf-8')).hexdigest()
    
#     def indexar_documento(
#         self,
#         texto_completo: str,
#         pliego_id: str,
#         tipo_documento: str = "tecnico",  # "tecnico", "administrativo", "anexo"
#         metadatos_extra: Optional[Dict] = None
#     ) -> Dict[str, int]:
#         """
#         Indexa documento con estrategia optimizada por tipo.
        
#         Args:
#             texto_completo: Texto extraído del PDF
#             pliego_id: ID único de la licitación
#             tipo_documento: Tipo de pliego para elegir chunking
#             metadatos_extra: Metadatos adicionales (presupuesto, fecha, etc.)
        
#         Returns:
#             Dict con estadísticas de indexación
#         """
#         print(f"📑 Indexando {tipo_documento} - {pliego_id}...")
        
#         # Calcular hash para detectar duplicados
#         doc_hash = self._hash_documento(texto_completo)
#         cache_key = f"{pliego_id}_{tipo_documento}"
        
#         if cache_key in self.cache_procesados:
#             if self.cache_procesados[cache_key]["hash"] == doc_hash:
#                 print(f"✓ Documento ya indexado (sin cambios)")
#                 return {"chunks_nuevos": 0, "chunks_actualizados": 0}
        
#         # Verificar si ya existe en la base
#         existing = self.collection_texto.get(
#             where={"pliego_id": pliego_id, "tipo_documento": tipo_documento}
#         )
        
#         if len(existing['ids']) > 0:
#             print(f"⚠ Actualizando documento existente...")
#             # Eliminar chunks antiguos
#             self.collection_texto.delete(ids=existing['ids'])
        
#         # Seleccionar splitter según tipo
#         if tipo_documento == "administrativo":
#             splitter = self.splitter_admin
#         elif tipo_documento == "tecnico":
#             splitter = self.splitter_tecnico
#         else:
#             splitter = self.splitter_tecnico
        
#         # Chunking inteligente
#         chunks = splitter.split_text(texto_completo)
        
#         # Preparar metadatos estructurados
#         metadatos_base = {
#             "pliego_id": pliego_id,
#             "tipo_documento": tipo_documento,
#             "fecha_indexacion": datetime.now().isoformat(),
#             "num_chunks": len(chunks)
#         }
        
#         if metadatos_extra:
#             metadatos_base.update(metadatos_extra)
        
#         # Crear IDs únicos
#         ids = [f"{pliego_id}_{tipo_documento}_{i}" for i in range(len(chunks))]
        
#         # Metadatos por chunk
#         metadatas = []
#         for i in range(len(chunks)):
#             meta = {
#                 **metadatos_base,
#                 "chunk_index": i,
#                 "chunk_length": len(chunks[i])
#             }
#             metadatas.append(meta)
        
#         # Guardar en ChromaDB
#         self.collection_texto.add(
#             documents=chunks,
#             ids=ids,
#             metadatas=metadatas
#         )
        
#         # Actualizar caché
#         self.cache_procesados[cache_key] = {
#             "hash": doc_hash,
#             "fecha": datetime.now().isoformat(),
#             "num_chunks": len(chunks)
#         }
#         self._guardar_cache()
        
#         print(f"✓ Indexados {len(chunks)} fragmentos")
        
#         return {
#             "chunks_nuevos": len(chunks),
#             "chunks_actualizados": len(existing['ids']) if existing['ids'] else 0
#         }
    
#     def indexar_tabla(
#         self,
#         tabla_markdown: str,
#         pliego_id: str,
#         nombre_tabla: str,
#         metadatos_extra: Optional[Dict] = None
#     ):
#         """
#         Indexa tabla estructurada (cuadro resumen, presupuestos).
        
#         Args:
#             tabla_markdown: Tabla en formato markdown
#             pliego_id: ID de la licitación
#             nombre_tabla: Nombre descriptivo (ej: "cuadro_resumen")
#             metadatos_extra: Metadatos adicionales
#         """
#         print(f"📊 Indexando tabla: {nombre_tabla}")
        
#         # Metadatos base
#         metadatos = {
#             "pliego_id": pliego_id,
#             "tipo": "tabla",
#             "nombre_tabla": nombre_tabla,
#             "fecha_indexacion": datetime.now().isoformat()
#         }
        
#         if metadatos_extra:
#             metadatos.update(metadatos_extra)
        
#         # Para tablas, guardamos el markdown completo + chunks
#         tabla_id = f"{pliego_id}_tabla_{nombre_tabla}"
        
#         # Guardar tabla completa
#         self.collection_tablas.add(
#             documents=[tabla_markdown],
#             ids=[tabla_id],
#             metadatas=[metadatos]
#         )
        
#         print(f"✓ Tabla indexada: {nombre_tabla}")
    
#     def buscar_contexto(
#         self,
#         query: str,
#         pliego_id: Optional[str] = None,
#         tipo_documento: Optional[str] = None,
#         n_resultados: int = 5,
#         incluir_tablas: bool = False
#     ) -> List[Dict]:
#         """
#         Búsqueda híbrida con filtros avanzados.
        
#         Args:
#             query: Consulta semántica
#             pliego_id: Filtrar por licitación específica
#             tipo_documento: Filtrar por tipo (tecnico/administrativo)
#             n_resultados: Número de resultados
#             incluir_tablas: Incluir tablas en la búsqueda
        
#         Returns:
#             Lista de chunks con metadatos y score
#         """
#         filtros = {}
        
#         if pliego_id:
#             filtros["pliego_id"] = pliego_id
        
#         if tipo_documento:
#             filtros["tipo_documento"] = tipo_documento
        
#         # Búsqueda en textos
#         results_texto = self.collection_texto.query(
#             query_texts=[query],
#             n_results=n_resultados,
#             where=filtros if filtros else None
#         )
        
#         # Búsqueda en tablas (si está habilitado)
#         results_tablas = None
#         if incluir_tablas:
#             filtros_tablas = {"pliego_id": pliego_id} if pliego_id else None
#             results_tablas = self.collection_tablas.query(
#                 query_texts=[query],
#                 n_results=min(2, n_resultados),
#                 where=filtros_tablas
#             )
        
#         # Combinar y estructurar resultados
#         resultados = []
        
#         # Resultados de texto
#         for i, doc in enumerate(results_texto['documents'][0]):
#             resultados.append({
#                 'texto': doc,
#                 'metadatos': results_texto['metadatas'][0][i],
#                 'distancia': results_texto['distances'][0][i],
#                 'tipo': 'texto'
#             })
        
#         # Resultados de tablas
#         if results_tablas:
#             for i, doc in enumerate(results_tablas['documents'][0]):
#                 resultados.append({
#                     'texto': doc,
#                     'metadatos': results_tablas['metadatas'][0][i],
#                     'distancia': results_tablas['distances'][0][i],
#                     'tipo': 'tabla'
#                 })
        
#         # Ordenar por distancia (menor = más relevante)
#         resultados.sort(key=lambda x: x['distancia'])
        
#         return resultados[:n_resultados]
    
#     def buscar_multiquery(
#         self,
#         queries: List[str],
#         pliego_id: str,
#         n_por_query: int = 3
#     ) -> Dict[str, List[Dict]]:
#         """
#         Realiza múltiples búsquedas y las agrupa por tema.
#         Útil para extraer información específica de diferentes secciones.
        
#         Args:
#             queries: Lista de consultas temáticas
#             pliego_id: ID de la licitación
#             n_por_query: Resultados por consulta
        
#         Returns:
#             Dict con resultados agrupados por query
#         """
#         resultados = {}
        
#         for query in queries:
#             resultados[query] = self.buscar_contexto(
#                 query=query,
#                 pliego_id=pliego_id,
#                 n_resultados=n_por_query,
#                 incluir_tablas=True
#             )
        
#         return resultados
    
#     def obtener_estadisticas(self, pliego_id: Optional[str] = None) -> Dict:
#         """Obtiene estadísticas de la base de datos"""
        
#         filtros = {"pliego_id": pliego_id} if pliego_id else None
        
#         # Contar chunks de texto
#         all_texto = self.collection_texto.get(where=filtros)
        
#         # Contar tablas
#         all_tablas = self.collection_tablas.get(where=filtros)
        
#         stats = {
#             "total_chunks_texto": len(all_texto['ids']),
#             "total_tablas": len(all_tablas['ids']),
#             "pliegos_unicos": len(set(all_texto['metadatas'])) if all_texto['metadatas'] else 0
#         }
        
#         if pliego_id:
#             tipos_doc = [m.get('tipo_documento') for m in all_texto['metadatas']]
#             stats['tipos_documentos'] = {tipo: tipos_doc.count(tipo) for tipo in set(tipos_doc)}
        
#         return stats
    
#     def exportar_metadatos(self, pliego_id: str) -> pd.DataFrame:
#         """
#         Exporta todos los metadatos de una licitación a DataFrame.
#         Útil para análisis posterior.
#         """
#         filtros = {"pliego_id": pliego_id}
        
#         texto = self.collection_texto.get(where=filtros)
#         tablas = self.collection_tablas.get(where=filtros)
        
#         datos = []
        
#         # Metadatos de texto
#         for i, meta in enumerate(texto['metadatas']):
#             datos.append({
#                 **meta,
#                 'tipo': 'texto',
#                 'contenido_preview': texto['documents'][i][:100]
#             })
        
#         # Metadatos de tablas
#         for i, meta in enumerate(tablas['metadatas']):
#             datos.append({
#                 **meta,
#                 'tipo': 'tabla',
#                 'contenido_preview': tablas['documents'][i][:100]
#             })
        
#         return pd.DataFrame(datos)


# # =============================================================================
# # EJEMPLO DE USO
# # =============================================================================

# if __name__ == "__main__":
#     # Inicializar gestor mejorado
#     gestor = GestorLicitacionesMejorado()
    
#     # Ejemplo de indexación
#     texto_pliego = """
#     OBJETO DEL CONTRATO
    
#     El objeto del presente contrato es el suministro e instalación de equipamiento
#     informático para las oficinas de la Administración...
    
#     PRESUPUESTO BASE DE LICITACIÓN
    
#     El presupuesto base asciende a 250.000€ (IVA no incluido).
#     """
    
#     # Indexar con metadatos estructurados
#     gestor.indexar_documento(
#         texto_completo=texto_pliego,
#         pliego_id="EXP-2025-001",
#         tipo_documento="tecnico",
#         metadatos_extra={
#             "presupuesto_base": 250000,
#             "organismo": "Ayuntamiento de Valencia",
#             "fecha_publicacion": "2025-01-15"
#         }
#     )
    
#     # Búsqueda avanzada
#     resultados = gestor.buscar_contexto(
#         query="presupuesto equipamiento informático",
#         pliego_id="EXP-2025-001",
#         tipo_documento="tecnico",
#         n_resultados=3,
#         incluir_tablas=True
#     )
    
#     print("\n🔍 RESULTADOS DE BÚSQUEDA:")
#     for i, res in enumerate(resultados, 1):
#         print(f"\n[{i}] Score: {res['distancia']:.4f}")
#         print(f"Tipo: {res['tipo']}")
#         print(f"Texto: {res['texto'][:200]}...")
    
#     # Estadísticas
#     stats = gestor.obtener_estadisticas(pliego_id="EXP-2025-001")
#     print(f"\n📊 ESTADÍSTICAS:")
#     print(stats)

## ----------------------------------------------

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd

class GestorLicitacionesMejorado:
    """
    Sistema de gestión vectorial optimizado para licitaciones públicas.
    
    Mejoras:
    - Caché de embeddings para evitar recálculos
    - Metadatos estructurados (fechas, presupuestos, tipo doc)
    - Chunking optimizado por tipo de documento
    - Búsqueda híbrida (vectorial + filtros)
    """
    
    def __init__(
        self, 
        persist_path: str = "./chroma_db_licitaciones",
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        self.persist_path = persist_path
        self.model_name = model_name
        
        # Cliente persistente
        self.client = chromadb.PersistentClient(path=persist_path)
        
        # Función de embedding
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        
        # Colecciones separadas por tipo de contenido
        self.collection_texto = self.client.get_or_create_collection(
            name="texto_pliegos",
            embedding_function=self.embedding_fn,
            metadata={"description": "Texto de pliegos técnicos y administrativos"}
        )
        
        self.collection_tablas = self.client.get_or_create_collection(
            name="tablas_pliegos",
            embedding_function=self.embedding_fn,
            metadata={"description": "Tablas estructuradas (cuadros resumen, presupuestos)"}
        )
        
        # Configurar splitters especializados
        self._configurar_splitters()
        
        # Caché de documentos procesados
        self.cache_procesados = self._cargar_cache()
    
    def _configurar_splitters(self):
        """Configura estrategias de chunking por tipo de documento"""
        
        # Para texto administrativo (más denso, legal)
        self.splitter_admin = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", ".", " ", ""],
            length_function=len
        )
        
        # Para texto técnico (descripciones, requisitos)
        self.splitter_tecnico = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=300,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        
        # Para tablas (chunks pequeños, contextuales)
        self.splitter_tabla = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n", "|", " ", ""]
        )
    
    def _cargar_cache(self) -> Dict:
        """Carga registro de documentos ya procesados"""
        try:
            with open(f"{self.persist_path}/cache_documentos.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _guardar_cache(self):
        """Guarda el caché de documentos procesados"""
        with open(f"{self.persist_path}/cache_documentos.json", 'w') as f:
            json.dump(self.cache_procesados, f, indent=2)
    
    def _hash_documento(self, texto: str) -> str:
        """Genera hash único para detectar documentos duplicados"""
        return hashlib.md5(texto.encode('utf-8')).hexdigest()
    
    def limpiar_metadatos_para_chroma(self, metadatos: dict) -> dict:
        """
        Convierte valores no permitidos (como listas) en strings planos.
        """
        metadatos_limpios = {}
        for clave, valor in metadatos.items():
            # Si es una lista o tupla, la convertimos a string separado por comas
            if isinstance(valor, (list, tuple)):
                metadatos_limpios[clave] = ", ".join(map(str, valor))
            # Si es un diccionario, lo convertimos a string JSON (o lo ignoramos)
            elif isinstance(valor, dict):
                metadatos_limpios[clave] = str(valor)
            else:
                metadatos_limpios[clave] = valor
        return metadatos_limpios
    
    def indexar_documento(
        self,
        texto_completo: str,
        pliego_id: str,
        tipo_documento: str = "tecnico",  # "tecnico", "administrativo", "anexo"
        metadatos_extra: Optional[Dict] = None
    ) -> Dict[str, int]:
        """
        Indexa documento con estrategia optimizada por tipo.
        
        Args:
            texto_completo: Texto extraído del PDF
            pliego_id: ID único de la licitación
            tipo_documento: Tipo de pliego para elegir chunking
            metadatos_extra: Metadatos adicionales (presupuesto, fecha, etc.)
        
        Returns:
            Dict con estadísticas de indexación
        """
        print(f"📑 Indexando {tipo_documento} - {pliego_id}...")
        
        # Calcular hash para detectar duplicados
        doc_hash = self._hash_documento(texto_completo)
        cache_key = f"{pliego_id}_{tipo_documento}"
        
        if cache_key in self.cache_procesados:
            if self.cache_procesados[cache_key]["hash"] == doc_hash:
                print(f"✓ Documento ya indexado (sin cambios)")
                return {"chunks_nuevos": 0, "chunks_actualizados": 0}
        
        # Verificar si ya existe en la base
        # ChromaDB requiere operador $and para múltiples condiciones
        existing = self.collection_texto.get(
            where={
                "$and": [
                    {"pliego_id": pliego_id},
                    {"tipo_documento": tipo_documento}
                ]
            }
        )
        
        if len(existing['ids']) > 0:
            print(f"⚠ Actualizando documento existente...")
            # Eliminar chunks antiguos
            self.collection_texto.delete(ids=existing['ids'])
        
        # Seleccionar splitter según tipo
        if tipo_documento == "administrativo":
            splitter = self.splitter_admin
        elif tipo_documento == "tecnico":
            splitter = self.splitter_tecnico
        else:
            splitter = self.splitter_tecnico
        
        # Chunking inteligente
        chunks = splitter.split_text(texto_completo)
        
        # Preparar metadatos estructurados
        metadatos_base = {
            "pliego_id": pliego_id,
            "tipo_documento": tipo_documento,
            "fecha_indexacion": datetime.now().isoformat(),
            "num_chunks": len(chunks)
        }
        
        if metadatos_extra:
            metadatos_base.update(metadatos_extra)
        
        # Crear IDs únicos
        ids = [f"{pliego_id}_{tipo_documento}_{i}" for i in range(len(chunks))]
        
        # Metadatos por chunk
        metadatas = []
        for i in range(len(chunks)):
            meta = {
                **metadatos_base,
                "chunk_index": i,
                "chunk_length": len(chunks[i])
            }
            metadatas.append(meta)

        metadatos_extra_limpios = self.limpiar_metadatos_para_chroma(metadatos_extra)
        # 2. Combinar con los metadatos base
        metadatos_finales = {**metadatos_base, **metadatos_extra_limpios}
        
        # 3. Aplicar a cada chunk (Chroma necesita una lista de metadatos, uno por chunk)
        lista_metadatos = [metadatos_finales for _ in chunks]
        
        # Guardar en ChromaDB
        self.collection_texto.add(
            documents=chunks,
            ids=ids,
            metadatas=lista_metadatos
        )
        
        # Actualizar caché
        self.cache_procesados[cache_key] = {
            "hash": doc_hash,
            "fecha": datetime.now().isoformat(),
            "num_chunks": len(chunks)
        }
        self._guardar_cache()
        
        print(f"✓ Indexados {len(chunks)} fragmentos")
        
        return {
            "chunks_nuevos": len(chunks),
            "chunks_actualizados": len(existing['ids']) if existing['ids'] else 0
        }
    
    def indexar_tabla(
        self,
        tabla_markdown: str,
        pliego_id: str,
        nombre_tabla: str,
        metadatos_extra: Optional[Dict] = None
    ):
        """
        Indexa tabla estructurada (cuadro resumen, presupuestos).
        
        Args:
            tabla_markdown: Tabla en formato markdown
            pliego_id: ID de la licitación
            nombre_tabla: Nombre descriptivo (ej: "cuadro_resumen")
            metadatos_extra: Metadatos adicionales
        """
        print(f"📊 Indexando tabla: {nombre_tabla}")
        
        # Metadatos base
        metadatos = {
            "pliego_id": pliego_id,
            "tipo": "tabla",
            "nombre_tabla": nombre_tabla,
            "fecha_indexacion": datetime.now().isoformat()
        }
        
        if metadatos_extra:
            metadatos.update(metadatos_extra)
        
        # Para tablas, guardamos el markdown completo + chunks
        tabla_id = f"{pliego_id}_tabla_{nombre_tabla}"
        
        # Guardar tabla completa
        self.collection_tablas.add(
            documents=[tabla_markdown],
            ids=[tabla_id],
            metadatas=[metadatos]
        )
        
        print(f"✓ Tabla indexada: {nombre_tabla}")
    
    def buscar_contexto(
        self,
        query: str,
        pliego_id: Optional[str] = None,
        tipo_documento: Optional[str] = None,
        n_resultados: int = 5,
        incluir_tablas: bool = False
    ) -> List[Dict]:
        """
        Búsqueda híbrida con filtros avanzados.
        
        Args:
            query: Consulta semántica
            pliego_id: Filtrar por licitación específica
            tipo_documento: Filtrar por tipo (tecnico/administrativo)
            n_resultados: Número de resultados
            incluir_tablas: Incluir tablas en la búsqueda
        
        Returns:
            Lista de chunks con metadatos y score
        """
        # Construir filtros con operador $and si hay múltiples condiciones
        filtros = None
        condiciones = []
        
        if pliego_id:
            condiciones.append({"pliego_id": pliego_id})
        
        if tipo_documento:
            condiciones.append({"tipo_documento": tipo_documento})
        
        if len(condiciones) > 1:
            filtros = {"$and": condiciones}
        elif len(condiciones) == 1:
            filtros = condiciones[0]
        
        # Búsqueda en textos
        results_texto = self.collection_texto.query(
            query_texts=[query],
            n_results=n_resultados,
            where=filtros
        )
        
        # Búsqueda en tablas (si está habilitado)
        results_tablas = None
        if incluir_tablas:
            filtros_tablas = {"pliego_id": pliego_id} if pliego_id else None
            results_tablas = self.collection_tablas.query(
                query_texts=[query],
                n_results=min(2, n_resultados),
                where=filtros_tablas
            )
        
        # Combinar y estructurar resultados
        resultados = []
        
        # Resultados de texto
        for i, doc in enumerate(results_texto['documents'][0]):
            resultados.append({
                'texto': doc,
                'metadatos': results_texto['metadatas'][0][i],
                'distancia': results_texto['distances'][0][i],
                'tipo': 'texto'
            })
        
        # Resultados de tablas
        if results_tablas:
            for i, doc in enumerate(results_tablas['documents'][0]):
                resultados.append({
                    'texto': doc,
                    'metadatos': results_tablas['metadatas'][0][i],
                    'distancia': results_tablas['distances'][0][i],
                    'tipo': 'tabla'
                })
        
        # Ordenar por distancia (menor = más relevante)
        resultados.sort(key=lambda x: x['distancia'])
        
        return resultados[:n_resultados]
    
    def buscar_multiquery(
        self,
        queries: List[str],
        pliego_id: str,
        n_por_query: int = 3
    ) -> Dict[str, List[Dict]]:
        """
        Realiza múltiples búsquedas y las agrupa por tema.
        Útil para extraer información específica de diferentes secciones.
        
        Args:
            queries: Lista de consultas temáticas
            pliego_id: ID de la licitación
            n_por_query: Resultados por consulta
        
        Returns:
            Dict con resultados agrupados por query
        """
        resultados = {}
        
        for query in queries:
            resultados[query] = self.buscar_contexto(
                query=query,
                pliego_id=pliego_id,
                n_resultados=n_por_query,
                incluir_tablas=True
            )
        
        return resultados
    
    def obtener_estadisticas(self, pliego_id: Optional[str] = None) -> Dict:
        """Obtiene estadísticas de la base de datos"""
        
        filtros = {"pliego_id": pliego_id} if pliego_id else None
        
        # Contar chunks de texto
        all_texto = self.collection_texto.get(where=filtros)
        
        # Contar tablas
        all_tablas = self.collection_tablas.get(where=filtros)
        
        stats = {
            "total_chunks_texto": len(all_texto['ids']),
            "total_tablas": len(all_tablas['ids']),
            "pliegos_unicos": len(set(all_texto['metadatas'])) if all_texto['metadatas'] else 0
        }
        
        if pliego_id:
            tipos_doc = [m.get('tipo_documento') for m in all_texto['metadatas']]
            stats['tipos_documentos'] = {tipo: tipos_doc.count(tipo) for tipo in set(tipos_doc)}
        
        return stats
    
    def exportar_metadatos(self, pliego_id: str) -> pd.DataFrame:
        """
        Exporta todos los metadatos de una licitación a DataFrame.
        Útil para análisis posterior.
        """
        filtros = {"pliego_id": pliego_id}
        
        texto = self.collection_texto.get(where=filtros)
        tablas = self.collection_tablas.get(where=filtros)
        
        datos = []
        
        # Metadatos de texto
        for i, meta in enumerate(texto['metadatas']):
            datos.append({
                **meta,
                'tipo': 'texto',
                'contenido_preview': texto['documents'][i][:100]
            })
        
        # Metadatos de tablas
        for i, meta in enumerate(tablas['metadatas']):
            datos.append({
                **meta,
                'tipo': 'tabla',
                'contenido_preview': tablas['documents'][i][:100]
            })
        
        return pd.DataFrame(datos)


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Inicializar gestor mejorado
    gestor = GestorLicitacionesMejorado()
    
    # Ejemplo de indexación
    texto_pliego = """
    OBJETO DEL CONTRATO
    
    El objeto del presente contrato es el suministro e instalación de equipamiento
    informático para las oficinas de la Administración...
    
    PRESUPUESTO BASE DE LICITACIÓN
    
    El presupuesto base asciende a 250.000€ (IVA no incluido).
    """
    
    # Indexar con metadatos estructurados
    gestor.indexar_documento(
        texto_completo=texto_pliego,
        pliego_id="EXP-2025-001",
        tipo_documento="tecnico",
        metadatos_extra={
            "presupuesto_base": 250000,
            "organismo": "Ayuntamiento de Valencia",
            "fecha_publicacion": "2025-01-15"
        }
    )
    
    # Búsqueda avanzada
    resultados = gestor.buscar_contexto(
        query="presupuesto equipamiento informático",
        pliego_id="EXP-2025-001",
        tipo_documento="tecnico",
        n_resultados=3,
        incluir_tablas=True
    )
    
    print("\n🔍 RESULTADOS DE BÚSQUEDA:")
    for i, res in enumerate(resultados, 1):
        print(f"\n[{i}] Score: {res['distancia']:.4f}")
        print(f"Tipo: {res['tipo']}")
        print(f"Texto: {res['texto'][:200]}...")
    
    # Estadísticas
    stats = gestor.obtener_estadisticas(pliego_id="EXP-2025-001")
    print(f"\n📊 ESTADÍSTICAS:")
    print(stats)
"""
Pipeline Completo de Análisis de Licitaciones
==============================================

Integra:
1. Extracción de PDFs (texto + tablas)
2. Indexación vectorial con ChromaDB
3. Generación de resumen con Ollama (RAG)
4. Scoring de compatibilidad empresa-licitación
5. Generación de informe ejecutivo
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
import requests

# Importar módulos propios
from extractor_pdf_unificado import ExtractorPDFUnificado
from vector_db import GestorLicitacionesMejorado
from sistema_scoring import SistemaScoringLicitaciones, PerfilEmpresa


class PipelineAnalisisLicitaciones:
    """
    Pipeline completo para analizar licitaciones y generar informes.
    """
    
    def __init__(
        self,
        persist_path: str = "./chroma_db_licitaciones",
        modelo_ollama: str = "llama3.2:3b",
        url_ollama: str = "http://localhost:11434"
    ):
        """
        Inicializa el pipeline.
        
        Args:
            persist_path: Ruta para base de datos vectorial
            modelo_ollama: Modelo de Ollama para resúmenes
            url_ollama: URL del servidor Ollama
        """
        self.extractor = ExtractorPDFUnificado()
        self.gestor_vectorial = GestorLicitacionesMejorado(persist_path=persist_path)
        self.sistema_scoring = SistemaScoringLicitaciones()
        
        self.modelo_ollama = modelo_ollama
        self.url_ollama = url_ollama
        
        print("✅ Pipeline inicializado correctamente")
    
    def procesar_licitacion(
        self,
        url_or_path: str,
        pliego_id: str,
        perfil_empresa: Optional[PerfilEmpresa] = None,
        paginas_tablas: str = "1-10"
    ) -> Dict:
        """
        Procesa una licitación completa.
        
        Args:
            url_or_path: URL o ruta del PDF
            pliego_id: ID único de la licitación
            perfil_empresa: Perfil de empresa para scoring (opcional)
            paginas_tablas: Páginas para extraer tablas
        
        Returns:
            Dict con análisis completo
        """
        print(f"\n{'='*80}")
        print(f"🚀 PROCESANDO LICITACIÓN: {pliego_id}")
        print(f"{'='*80}\n")
        
        resultados = {
            'pliego_id': pliego_id,
            'url_pdf': url_or_path,
            'metadatos': {},
            'resumen_ia': '',
            'scoring': None,
            'recomendacion': ''
        }
        
        # =================================================================
        # PASO 1: EXTRACCIÓN
        # =================================================================
        print("📄 PASO 1: Extracción de PDF")
        print("-" * 60)
        
        documento = self.extractor.extraer_completo(
            url_or_path=url_or_path,
            # paginas_tablas=paginas_tablas
        )
        
        resultados['metadatos'] = documento.metadatos
        resultados['tipo_documento'] = documento.tipo_documento
        
        # =================================================================
        # PASO 2: INDEXACIÓN VECTORIAL
        # =================================================================
        print("\n🗄️  PASO 2: Indexación Vectorial")
        print("-" * 60)
        
        # Indexar texto
        stats_texto = self.gestor_vectorial.indexar_documento(
            texto_completo=documento.texto,
            pliego_id=pliego_id,
            tipo_documento=documento.tipo_documento,
            metadatos_extra=documento.metadatos
        )
        
        # Indexar tablas
        for i, tabla_md in enumerate(documento.tablas):
            self.gestor_vectorial.indexar_tabla(
                tabla_markdown=tabla_md,
                pliego_id=pliego_id,
                nombre_tabla=f"tabla_{i+1}"
            )
        
        print(f"✓ Texto: {stats_texto['chunks_nuevos']} chunks")
        print(f"✓ Tablas: {len(documento.tablas)} tablas")
        
        # =================================================================
        # PASO 3: BÚSQUEDA CONTEXTUAL (RAG)
        # =================================================================
        print("\n🔍 PASO 3: Recuperación de Contexto (RAG)")
        print("-" * 60)
        
        # Queries específicas para obtener la info más relevante
        queries_clave = [
            "objeto del contrato alcance servicios suministros",
            "presupuesto base licitación valor estimado importe",
            "criterios de adjudicación puntuación valoración",
            "requisitos solvencia técnica económica experiencia",
            "certificaciones ISO ENS acreditaciones necesarias",
            "plazo de ejecución entrega calendario hitos"
        ]
        
        contextos = self.gestor_vectorial.buscar_multiquery(
            queries=queries_clave,
            pliego_id=pliego_id,
            n_por_query=2
        )
        
        # Construir contexto maestro para el LLM
        contexto_para_llm = self._construir_contexto_llm(contextos, documento.tablas)
        
        # =================================================================
        # PASO 4: GENERACIÓN DE RESUMEN CON IA
        # =================================================================
        print("\n🤖 PASO 4: Generación de Resumen con IA")
        print("-" * 60)
        
        resumen_ia = self._generar_resumen_ollama(contexto_para_llm)
        resultados['resumen_ia'] = resumen_ia
        
        # =================================================================
        # PASO 5: SCORING (si se proporciona perfil empresa)
        # =================================================================
        if perfil_empresa:
            print("\n🎯 PASO 5: Scoring de Compatibilidad")
            print("-" * 60)
            
            scoring = self.sistema_scoring.calcular_scoring(
                perfil=perfil_empresa,
                metadatos_licitacion=documento.metadatos,
                texto_licitacion=documento.texto
            )
            
            resultados['scoring'] = scoring.to_dict()
            resultados['recomendacion'] = self._generar_recomendacion(scoring)
        
        # =================================================================
        # PASO 6: GENERAR INFORME FINAL
        # =================================================================
        print("\n📊 PASO 6: Generación de Informe")
        print("-" * 60)
        
        ruta_informe = self._guardar_informe(pliego_id, resultados)
        resultados['ruta_informe'] = str(ruta_informe)
        
        print(f"\n{'='*80}")
        print(f"✅ PROCESAMIENTO COMPLETADO")
        print(f"{'='*80}")
        print(f"\n📁 Informe guardado en: {ruta_informe}")
        
        return resultados
    
    def _construir_contexto_llm(
        self, 
        contextos: Dict[str, List[Dict]], 
        tablas: List[str]
    ) -> str:
        """
        Construye el contexto optimizado para enviar al LLM.
        """
        contexto = "# INFORMACIÓN EXTRAÍDA DEL PLIEGO\n\n"
        
        # Agregar tablas primero (info más estructurada)
        if tablas:
            contexto += "## TABLAS ESTRUCTURADAS (CUADRO RESUMEN)\n\n"
            for i, tabla in enumerate(tablas, 1):
                contexto += f"### Tabla {i}\n{tabla}\n\n"
        
        # Agregar fragmentos por tema
        for query, resultados in contextos.items():
            if resultados:
                contexto += f"## {query.upper()}\n\n"
                for res in resultados:
                    contexto += f"{res['texto']}\n\n"
                contexto += "---\n\n"
        
        return contexto
    
    def _generar_resumen_ollama(self, contexto: str) -> str:
        """
        Genera resumen usando Ollama con prompt optimizado.
        """
        prompt = f"""
### ROL
Eres un Consultor Senior de Licitaciones Públicas en España con 20 años de experiencia.

### TAREA
Analiza la información proporcionada y genera un resumen ejecutivo estructurado.

### INFORMACIÓN DEL PLIEGO
{contexto}

### ESTRUCTURA REQUERIDA
Responde en formato Markdown usando EXACTAMENTE estas secciones:

## 1. OBJETO Y ALCANCE
[Descripción ejecutiva de qué se contrata]

## 2. DATOS ECONÓMICOS
| Concepto | Importe |
|----------|---------|
| Presupuesto Base (sin IVA) | [valor] |
| Presupuesto Total (con IVA) | [valor] |
| Número de Lotes | [valor] |

## 3. REQUISITOS CLAVE
### Solvencia Económica
[requisitos]

### Solvencia Técnica
[requisitos]

### Certificaciones
[lista de certificaciones requeridas]

## 4. CRITERIOS DE ADJUDICACIÓN
[Distribución de puntos: precio vs criterios técnicos]

## 5. PLAZOS CRÍTICOS
- Plazo de ejecución: [X meses/años]
- Fecha límite presentación: [si aparece]

## 6. OBSERVACIONES
[Cualquier información relevante adicional]

### REGLAS
- Si un dato NO aparece, escribe: "No especificado"
- Usa tablas para datos numéricos
- Sé preciso y conciso
- NO inventes información
"""
        
        try:
            response = requests.post(
                f"{self.url_ollama}/api/generate",
                json={
                    "model": self.modelo_ollama,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_ctx": 8192
                    }
                },
                timeout=600
            )
            
            response.raise_for_status()
            resultado = response.json()['response']
            
            # Limpiar tags <think> de DeepSeek si existen
            if '<think>' in resultado:
                resultado = resultado.split('</think>')[-1].strip()
            
            return resultado
            
        except Exception as e:
            print(f"⚠️ Error generando resumen: {e}")
            return f"Error al generar resumen: {str(e)}"
    
    def _generar_recomendacion(self, scoring) -> str:
        """Genera recomendación textual basada en scoring"""
        
        if scoring.nivel_recomendacion == "Alta":
            return (
                "✅ **RECOMENDACIÓN: PRESENTARSE**\n\n"
                f"La licitación presenta un alto grado de compatibilidad ({scoring.score_total:.1f}/100). "
                "Los requisitos se alinean bien con las capacidades de la empresa."
            )
        elif scoring.nivel_recomendacion == "Media":
            return (
                "⚠️ **RECOMENDACIÓN: EVALUAR DETENIDAMENTE**\n\n"
                f"Compatibilidad moderada ({scoring.score_total:.1f}/100). "
                "Revisar los requisitos faltantes antes de decidir."
            )
        else:
            return (
                "❌ **RECOMENDACIÓN: NO PRESENTARSE**\n\n"
                f"Baja compatibilidad ({scoring.score_total:.1f}/100). "
                "La empresa no cumple requisitos clave."
            )
    
    def _guardar_informe(self, pliego_id: str, resultados: Dict) -> Path:
        """
        Guarda informe en formato JSON y Markdown.
        """
        # Crear directorio de informes
        dir_informes = Path("informes_licitaciones")
        dir_informes.mkdir(exist_ok=True)
        
        # Guardar JSON completo
        ruta_json = dir_informes / f"{pliego_id}_informe.json"
        with open(ruta_json, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        # Guardar Markdown legible
        ruta_md = dir_informes / f"{pliego_id}_informe.md"
        with open(ruta_md, 'w', encoding='utf-8') as f:
            f.write(f"# INFORME DE ANÁLISIS - {pliego_id}\n\n")
            f.write(f"**URL:** {resultados['url_pdf']}\n\n")
            f.write(f"**Tipo:** {resultados.get('tipo_documento', 'N/A')}\n\n")
            f.write("---\n\n")
            
            # Resumen IA
            f.write("# RESUMEN EJECUTIVO\n\n")
            f.write(resultados['resumen_ia'])
            f.write("\n\n---\n\n")
            
            # Scoring
            if resultados['scoring']:
                f.write("# ANÁLISIS DE COMPATIBILIDAD\n\n")
                f.write(resultados['recomendacion'])
                f.write("\n\n")
                
                scoring = resultados['scoring']
                f.write(f"**Score Total:** {scoring['score_total']}/100\n\n")
                
                f.write("## Detalles por Categoría\n\n")
                for cat, score in scoring['detalles'].items():
                    f.write(f"- **{cat.replace('_', ' ').title()}:** {score}/100\n")
                
                if scoring['alertas']:
                    f.write("\n## ⚠️ Alertas\n\n")
                    for alerta in scoring['alertas']:
                        f.write(f"- {alerta}\n")
                
                if scoring['oportunidades']:
                    f.write("\n## ✨ Oportunidades\n\n")
                    for op in scoring['oportunidades']:
                        f.write(f"- {op}\n")
        
        return ruta_md


# =============================================================================
# EJEMPLO DE USO COMPLETO
# =============================================================================

if __name__ == "__main__":
    # Inicializar pipeline
    pipeline = PipelineAnalisisLicitaciones(
        modelo_ollama="llama3.2:3b"  # O "deepseek-r1:14b" si lo tienes
    )
    
    # Definir perfil de empresa
    perfil_empresa = PerfilEmpresa(
        nombre="TechSolutions SL",
        sectores=["tecnología", "servicios IT"],
        certificaciones=["ISO 9001:2015", "ISO 27001:2013", "ENS Alto"],
        facturacion_anual=2_500_000,
        experiencia_años=8,
        empleados=45,
        ubicaciones=["Valencia", "Madrid"],
        keywords_experiencia=[
            "Power BI", "migración cloud", "ciberseguridad", 
            "desarrollo software", "consultoría IT", "Azure",
            "transformación digital"
        ],
        presupuesto_minimo=50_000,
        presupuesto_maximo=1_500_000
    )
    
    # URL de ejemplo (usa tu PDF real)
    # url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=jzNIjSG5nKIm/HTkuLBb/EbEgjCR8vVbxA1awHtzOAGQvNEZKc%2BaDRIS/jNotdCIGkLXY%2BDhk/04C8JLnFN3lr4tm0Z9zcIK2ia0/wJNbDV7QB3HKyQaFUExmUVQCerk"
    url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=MjJGBf6MHb29S45JhxzyY/qVU%2BUZ3lctOs9tAWb9iI66qGUcDTonJW4QqvuQ2KiUPO852nvHTmmPVTnL3r37kl%2ByzMtruSvPpOnk/fdsmNSCx2e6p7hqtlp2aFupgHMr"

    # PROCESAR LICITACIÓN
    resultados = pipeline.procesar_licitacion(
        url_or_path=url_pdf,
        pliego_id="SER-25-0135-MEI",
        perfil_empresa=perfil_empresa,
        paginas_tablas="2-13"
    )
    
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    print(f"\n✅ Informe generado: {resultados['ruta_informe']}")
    
    if resultados['scoring']:
        score = resultados['scoring']['score_total']
        nivel = resultados['scoring']['nivel_recomendacion']
        print(f"\n🎯 Score: {score}/100")
        print(f"📈 Recomendación: {nivel}")
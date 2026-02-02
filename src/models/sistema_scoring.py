from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import re

@dataclass
class PerfilEmpresa:
    """Perfil de capacidades de una empresa"""
    nombre: str
    sectores: List[str]  # ["tecnología", "servicios", "construcción"]
    certificaciones: List[str]  # ["ISO 9001", "ISO 27001", "ENS Alto"]
    facturacion_anual: float  # En euros
    experiencia_años: int
    empleados: int
    ubicaciones: List[str]  # ["Valencia", "Madrid"]
    keywords_experiencia: List[str]  # ["Power BI", "migración cloud", "ciberseguridad"]
    presupuesto_minimo: float = 0
    presupuesto_maximo: float = float('inf')
    
    @classmethod
    def desde_dict(cls, data: Dict):
        """Crea perfil desde diccionario"""
        return cls(**data)


@dataclass
class ResultadoScoring:
    """Resultado del análisis de compatibilidad"""
    score_total: float  # 0-100
    es_compatible: bool
    nivel_recomendacion: str  # "Alta", "Media", "Baja", "No recomendado"
    detalles: Dict[str, float]  # Scores por categoría
    requisitos_cumplidos: List[str]
    requisitos_faltantes: List[str]
    alertas: List[str]
    oportunidades: List[str]
    
    def to_dict(self):
        return {
            'score_total': round(self.score_total, 2),
            'es_compatible': self.es_compatible,
            'nivel_recomendacion': self.nivel_recomendacion,
            'detalles': {k: round(v, 2) for k, v in self.detalles.items()},
            'requisitos_cumplidos': self.requisitos_cumplidos,
            'requisitos_faltantes': self.requisitos_faltantes,
            'alertas': self.alertas,
            'oportunidades': self.oportunidades
        }


class SistemaScoringLicitaciones:
    """
    Sistema de scoring avanzado para evaluar compatibilidad empresa-licitación.
    
    Categorías de evaluación:
    1. Solvencia económica (20%)
    2. Certificaciones y acreditaciones (25%)
    3. Experiencia sectorial (20%)
    4. Capacidad técnica (20%)
    5. Ubicación geográfica (10%)
    6. Disponibilidad temporal (5%)
    """
    
    def __init__(self):
        self.pesos = {
            'solvencia_economica': 0.20,
            'certificaciones': 0.25,
            'experiencia_sectorial': 0.20,
            'capacidad_tecnica': 0.20,
            'ubicacion': 0.10,
            'disponibilidad': 0.05
        }
        
        # Umbrales de decisión
        self.umbral_minimo = 50  # Score mínimo para considerar
        self.umbral_recomendado = 70  # Score para recomendar fuertemente
    
    def evaluar_solvencia_economica(
        self, 
        perfil: PerfilEmpresa, 
        metadatos_licitacion: Dict
    ) -> tuple[float, List[str], List[str]]:
        """
        Evalúa si la empresa cumple requisitos de solvencia económica.
        
        Returns:
            (score, requisitos_ok, requisitos_ko)
        """
        score = 0
        requisitos_ok = []
        requisitos_ko = []
        
        presupuesto_licitacion = metadatos_licitacion.get('presupuesto_euros', 0)
        
        # Verificar rango de presupuesto de empresa
        if presupuesto_licitacion > 0:
            if presupuesto_licitacion < perfil.presupuesto_minimo:
                requisitos_ko.append(
                    f"Presupuesto licitación ({presupuesto_licitacion:,.0f}€) "
                    f"menor al mínimo de empresa ({perfil.presupuesto_minimo:,.0f}€)"
                )
                score = 0
            elif presupuesto_licitacion > perfil.presupuesto_maximo:
                requisitos_ko.append(
                    f"Presupuesto licitación ({presupuesto_licitacion:,.0f}€) "
                    f"supera capacidad máxima ({perfil.presupuesto_maximo:,.0f}€)"
                )
                score = 30  # Penalización pero no descalificante
            else:
                requisitos_ok.append(
                    f"Presupuesto compatible: {presupuesto_licitacion:,.0f}€"
                )
                score = 100
        
        # Regla heurística: facturación anual >= 1.5x presupuesto licitación
        if presupuesto_licitacion > 0:
            ratio_requerido = presupuesto_licitacion * 1.5
            if perfil.facturacion_anual >= ratio_requerido:
                requisitos_ok.append(
                    f"Facturación suficiente: {perfil.facturacion_anual:,.0f}€ "
                    f">= {ratio_requerido:,.0f}€"
                )
                score = max(score, 100)
            else:
                requisitos_ko.append(
                    f"Facturación insuficiente: {perfil.facturacion_anual:,.0f}€ "
                    f"< {ratio_requerido:,.0f}€ (1.5x presupuesto)"
                )
                score = min(score, 40)
        
        return score, requisitos_ok, requisitos_ko
    
    def evaluar_certificaciones(
        self, 
        perfil: PerfilEmpresa, 
        metadatos_licitacion: Dict
    ) -> tuple[float, List[str], List[str]]:
        """
        Evalúa cumplimiento de certificaciones requeridas.
        """
        requisitos_ok = []
        requisitos_ko = []
        
        certs_requeridas = metadatos_licitacion.get('certificaciones', [])
        
        if not certs_requeridas:
            return 100, ["No se requieren certificaciones específicas"], []
        
        # Normalizar nombres de certificaciones
        certs_empresa = [c.upper() for c in perfil.certificaciones]
        
        certs_encontradas = []
        certs_faltantes = []
        
        for cert_req in certs_requeridas:
            cert_req_norm = cert_req.upper()
            
            # Búsqueda flexible (permite ISO 27001 vs ISO/IEC 27001)
            encontrada = False
            for cert_emp in certs_empresa:
                if self._certificaciones_equivalentes(cert_req_norm, cert_emp):
                    encontrada = True
                    certs_encontradas.append(cert_req)
                    break
            
            if encontrada:
                requisitos_ok.append(f"✓ {cert_req}")
            else:
                requisitos_ko.append(f"✗ {cert_req} (faltante)")
                certs_faltantes.append(cert_req)
        
        # Score proporcional
        if len(certs_requeridas) > 0:
            score = (len(certs_encontradas) / len(certs_requeridas)) * 100
        else:
            score = 100
        
        return score, requisitos_ok, requisitos_ko
    
    def _certificaciones_equivalentes(self, cert1: str, cert2: str) -> bool:
        """Compara certificaciones de forma flexible"""
        # Extraer números (ej: ISO 27001)
        nums1 = re.findall(r'\d+', cert1)
        nums2 = re.findall(r'\d+', cert2)
        
        # Si ambas tienen el mismo número principal, son equivalentes
        if nums1 and nums2:
            return nums1[0] == nums2[0]
        
        # Comparación exacta de texto
        return cert1 in cert2 or cert2 in cert1
    
    def evaluar_experiencia_sectorial(
        self, 
        perfil: PerfilEmpresa, 
        metadatos_licitacion: Dict,
        texto_licitacion: str
    ) -> tuple[float, List[str], List[str]]:
        """
        Evalúa experiencia en el sector y keywords técnicas.
        """
        requisitos_ok = []
        requisitos_ko = []
        
        texto_lower = texto_licitacion.lower()
        
        # Evaluar keywords de experiencia
        keywords_encontradas = []
        for kw in perfil.keywords_experiencia:
            if kw.lower() in texto_lower:
                keywords_encontradas.append(kw)
        
        if keywords_encontradas:
            requisitos_ok.append(
                f"Experiencia relevante: {', '.join(keywords_encontradas)}"
            )
        
        # Score basado en coincidencias
        if len(perfil.keywords_experiencia) > 0:
            ratio_keywords = len(keywords_encontradas) / len(perfil.keywords_experiencia)
            score_keywords = ratio_keywords * 100
        else:
            score_keywords = 50  # Neutral si no hay keywords
        
        # Evaluar experiencia en años (mínimo común: 3 años)
        if perfil.experiencia_años >= 3:
            requisitos_ok.append(f"Experiencia: {perfil.experiencia_años} años")
            score_experiencia = 100
        else:
            requisitos_ko.append(f"Experiencia limitada: {perfil.experiencia_años} años")
            score_experiencia = perfil.experiencia_años * 33  # 0, 33, 66 para 0,1,2 años
        
        # Score combinado (70% keywords, 30% años)
        score = (score_keywords * 0.7) + (score_experiencia * 0.3)
        
        return score, requisitos_ok, requisitos_ko
    
    def evaluar_capacidad_tecnica(
        self, 
        perfil: PerfilEmpresa,
        metadatos_licitacion: Dict
    ) -> tuple[float, List[str], List[str]]:
        """
        Evalúa capacidad técnica (empleados, infraestructura).
        """
        requisitos_ok = []
        requisitos_ko = []
        
        # Evaluar número de empleados (heurística: 1 empleado por cada 50k€)
        presupuesto = metadatos_licitacion.get('presupuesto_euros', 0)
        empleados_requeridos = max(2, presupuesto / 50000)
        
        if perfil.empleados >= empleados_requeridos:
            requisitos_ok.append(
                f"Plantilla adecuada: {perfil.empleados} empleados "
                f"(requerido: ~{int(empleados_requeridos)})"
            )
            score = 100
        else:
            requisitos_ko.append(
                f"Plantilla limitada: {perfil.empleados} empleados "
                f"(recomendado: {int(empleados_requeridos)})"
            )
            score = (perfil.empleados / empleados_requeridos) * 100
        
        return min(score, 100), requisitos_ok, requisitos_ko
    
    def evaluar_ubicacion(
        self, 
        perfil: PerfilEmpresa,
        metadatos_licitacion: Dict
    ) -> tuple[float, List[str], List[str]]:
        """
        Evalúa compatibilidad geográfica.
        """
        requisitos_ok = []
        requisitos_ko = []
        
        ubicacion_licitacion = metadatos_licitacion.get('ubicacion', '').lower()
        
        if not ubicacion_licitacion:
            return 100, ["Ubicación no especificada"], []
        
        # Verificar si alguna sede de empresa está en la región
        ubicaciones_empresa = [u.lower() for u in perfil.ubicaciones]
        
        coincide = any(ub in ubicacion_licitacion or ubicacion_licitacion in ub 
                      for ub in ubicaciones_empresa)
        
        if coincide:
            requisitos_ok.append(f"Ubicación compatible: {ubicacion_licitacion}")
            score = 100
        else:
            requisitos_ko.append(
                f"Ubicación alejada: {ubicacion_licitacion} "
                f"(sedes: {', '.join(perfil.ubicaciones)})"
            )
            score = 50  # No descalificante pero penaliza
        
        return score, requisitos_ok, requisitos_ko
    
    def calcular_scoring(
        self,
        perfil: PerfilEmpresa,
        metadatos_licitacion: Dict,
        texto_licitacion: str = ""
    ) -> ResultadoScoring:
        """
        Calcula scoring completo y genera recomendación.
        
        Args:
            perfil: Perfil de la empresa
            metadatos_licitacion: Metadatos extraídos del pliego
            texto_licitacion: Texto completo del pliego
        
        Returns:
            ResultadoScoring con análisis completo
        """
        print(f"\n{'='*60}")
        print(f"🎯 ANÁLISIS DE COMPATIBILIDAD")
        print(f"{'='*60}")
        
        scores = {}
        todos_requisitos_ok = []
        todos_requisitos_ko = []
        
        # 1. Solvencia económica
        print("\n1️⃣ Solvencia Económica...")
        score, req_ok, req_ko = self.evaluar_solvencia_economica(perfil, metadatos_licitacion)
        scores['solvencia_economica'] = score
        todos_requisitos_ok.extend(req_ok)
        todos_requisitos_ko.extend(req_ko)
        
        # 2. Certificaciones
        print("2️⃣ Certificaciones...")
        score, req_ok, req_ko = self.evaluar_certificaciones(perfil, metadatos_licitacion)
        scores['certificaciones'] = score
        todos_requisitos_ok.extend(req_ok)
        todos_requisitos_ko.extend(req_ko)
        
        # 3. Experiencia sectorial
        print("3️⃣ Experiencia Sectorial...")
        score, req_ok, req_ko = self.evaluar_experiencia_sectorial(
            perfil, metadatos_licitacion, texto_licitacion
        )
        scores['experiencia_sectorial'] = score
        todos_requisitos_ok.extend(req_ok)
        todos_requisitos_ko.extend(req_ko)
        
        # 4. Capacidad técnica
        print("4️⃣ Capacidad Técnica...")
        score, req_ok, req_ko = self.evaluar_capacidad_tecnica(perfil, metadatos_licitacion)
        scores['capacidad_tecnica'] = score
        todos_requisitos_ok.extend(req_ok)
        todos_requisitos_ko.extend(req_ko)
        
        # 5. Ubicación
        print("5️⃣ Ubicación...")
        score, req_ok, req_ko = self.evaluar_ubicacion(perfil, metadatos_licitacion)
        scores['ubicacion'] = score
        todos_requisitos_ok.extend(req_ok)
        todos_requisitos_ko.extend(req_ko)
        
        # 6. Disponibilidad (placeholder - puede extenderse)
        scores['disponibilidad'] = 100  # Por defecto asumimos disponibilidad
        
        # Calcular score total ponderado
        score_total = sum(scores[k] * self.pesos[k] for k in self.pesos.keys())
        
        # Generar alertas y oportunidades
        alertas = self._generar_alertas(scores, todos_requisitos_ko)
        oportunidades = self._generar_oportunidades(scores, metadatos_licitacion)
        
        # Determinar nivel de recomendación
        if score_total >= self.umbral_recomendado:
            nivel = "Alta"
            es_compatible = True
        elif score_total >= self.umbral_minimo:
            nivel = "Media"
            es_compatible = True
        elif score_total >= 30:
            nivel = "Baja"
            es_compatible = False
        else:
            nivel = "No recomendado"
            es_compatible = False
        
        resultado = ResultadoScoring(
            score_total=score_total,
            es_compatible=es_compatible,
            nivel_recomendacion=nivel,
            detalles=scores,
            requisitos_cumplidos=todos_requisitos_ok,
            requisitos_faltantes=todos_requisitos_ko,
            alertas=alertas,
            oportunidades=oportunidades
        )
        
        self._imprimir_resultado(resultado)
        
        return resultado
    
    def _generar_alertas(self, scores: Dict, requisitos_ko: List[str]) -> List[str]:
        """Genera alertas basadas en scores bajos"""
        alertas = []
        
        for categoria, score in scores.items():
            if score < 50:
                alertas.append(
                    f"⚠️ {categoria.replace('_', ' ').title()}: Score bajo ({score:.0f}/100)"
                )
        
        # Alertas críticas
        if scores.get('certificaciones', 100) < 30:
            alertas.append(
                "🚨 CRÍTICO: Faltan certificaciones obligatorias"
            )
        
        if scores.get('solvencia_economica', 100) < 40:
            alertas.append(
                "🚨 CRÍTICO: Solvencia económica insuficiente"
            )
        
        return alertas
    
    def _generar_oportunidades(self, scores: Dict, metadatos: Dict) -> List[str]:
        """Identifica oportunidades basadas en fortalezas"""
        oportunidades = []
        
        if scores.get('certificaciones', 0) >= 90:
            oportunidades.append(
                "✨ Certificaciones completas - Ventaja competitiva alta"
            )
        
        if scores.get('experiencia_sectorial', 0) >= 80:
            oportunidades.append(
                "✨ Experiencia probada en el sector"
            )
        
        num_lotes = metadatos.get('num_lotes', 0)
        if num_lotes > 1:
            oportunidades.append(
                f"💡 Licitación dividida en {num_lotes} lotes - Posibilidad de presentarse a lotes específicos"
            )
        
        return oportunidades
    
    def _imprimir_resultado(self, resultado: ResultadoScoring):
        """Imprime resultado formateado"""
        print(f"\n{'='*60}")
        print(f"📊 RESULTADO DEL SCORING")
        print(f"{'='*60}")
        print(f"\n🎯 Score Total: {resultado.score_total:.1f}/100")
        print(f"📈 Recomendación: {resultado.nivel_recomendacion}")
        print(f"✅ Compatible: {'SÍ' if resultado.es_compatible else 'NO'}")
        
        print(f"\n📋 Detalles por Categoría:")
        for categoria, score in resultado.detalles.items():
            emoji = "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
            print(f"  {emoji} {categoria.replace('_', ' ').title()}: {score:.1f}/100")
        
        if resultado.alertas:
            print(f"\n⚠️  ALERTAS:")
            for alerta in resultado.alertas:
                print(f"  • {alerta}")
        
        if resultado.oportunidades:
            print(f"\n✨ OPORTUNIDADES:")
            for op in resultado.oportunidades:
                print(f"  • {op}")
        
        print(f"\n{'='*60}\n")


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
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
            "desarrollo software", "consultoría IT"
        ],
        presupuesto_minimo=50_000,
        presupuesto_maximo=1_500_000
    )
    
    # Metadatos de licitación (extraídos previamente)
    metadatos_licitacion = {
        'presupuesto_euros': 450_000,
        'certificaciones': ['ISO 27001', 'ENS Alto'],
        'num_lotes': 3,
        'ubicacion': 'Valencia',
        'organismo': 'Ayuntamiento de Valencia'
    }
    
    texto_licitacion = """
    Migración de sistemas legacy a cloud computing con Azure.
    Desarrollo de dashboards en Power BI.
    Implementación de medidas de ciberseguridad.
    """
    
    # Calcular scoring
    sistema = SistemaScoringLicitaciones()
    resultado = sistema.calcular_scoring(
        perfil=perfil_empresa,
        metadatos_licitacion=metadatos_licitacion,
        texto_licitacion=texto_licitacion
    )
    
    # Exportar a JSON
    with open("resultado_scoring.json", "w", encoding="utf-8") as f:
        json.dump(resultado.to_dict(), f, indent=2, ensure_ascii=False)
    
    print("💾 Resultado guardado en 'resultado_scoring.json'")
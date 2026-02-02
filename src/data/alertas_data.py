import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Set, Tuple
import pandas as pd
import re
import numpy as np


class Gestor_Alertas:
    def __init__(self, archivo_usuarios="usuarios.json", archivo_alertas="alertas.json"):
        """
        Inicializa el gestor de alertas.
        
        Args:
            archivo_usuarios: Ruta al archivo JSON con los usuarios
            archivo_alertas: Ruta al archivo JSON donde se guardarán las alertas
        """
        self.archivo_usuarios = archivo_usuarios
        self.archivo_alertas = archivo_alertas
        self.usuarios = self._cargar_usuarios()
        self.alertas_existentes = self._cargar_alertas()
        
    def _cargar_usuarios(self) -> Dict:
        """Carga el archivo de usuarios."""
        if not os.path.exists(self.archivo_usuarios):
            print(f"⚠️ Archivo {self.archivo_usuarios} no encontrado")
            return {}
        
        try:
            with open(self.archivo_usuarios, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error cargando usuarios: {e}")
            return {}
    
    def _cargar_alertas(self) -> Dict:
        """Carga las alertas existentes o crea un archivo nuevo."""
        if not os.path.exists(self.archivo_alertas):
            return {}
        
        try:
            with open(self.archivo_alertas, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error cargando alertas: {e}")
            return {}
    
    def _guardar_alertas(self):
        """Guarda las alertas en el archivo JSON."""
        try:
            with open(self.archivo_alertas, 'w', encoding='utf-8') as f:
                json.dump(self.alertas_existentes, f, indent=2, ensure_ascii=False)
            print(f"✅ Alertas guardadas en {self.archivo_alertas}")
        except Exception as e:
            print(f"❌ Error guardando alertas: {e}")
    
    def _generar_id_alerta(self) -> str:
        """Genera un ID único para una alerta."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        contador = len(self.alertas_existentes)
        return f"ALT_{timestamp}_{contador:06d}"
    
    def _generar_hash_busqueda(self, nombre_busqueda: str) -> str:
        """Genera un hash único para identificar una búsqueda."""
        hash_obj = hashlib.md5(nombre_busqueda.encode())
        return f"bq_{hash_obj.hexdigest()[:8]}"
    
    def _normalizar_texto(self, texto: str) -> str:
        """Normaliza texto para comparaciones (minúsculas, sin acentos)."""
        if not texto:
            return ""
        
        # Convertir a minúsculas
        texto = texto.lower()
        
        # Quitar acentos
        reemplazos = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
            'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
            'ñ': 'n'
        }
        for acento, sin_acento in reemplazos.items():
            texto = texto.replace(acento, sin_acento)
        
        return texto
    
    def _extraer_cpv_code(self, cpv_str: str) -> str:
        """Extrae el código CPV de un string tipo '30177000-0 - Descripción'."""
        if not cpv_str:
            return ""
        
        # Extraer el código antes del guion
        match = re.match(r'^(\d{8}-\d)', cpv_str)
        if match:
            return match.group(1)
        
        return cpv_str.strip()
    
    def _comprobar_cpv(self, licitacion_cpvs: List, busqueda_cpvs: List) -> bool:
        """
        Comprueba si algún CPV de la licitación coincide con los CPVs de la búsqueda.
        """
        print("CPV  DE USUARIO" ,busqueda_cpvs)
        if isinstance(licitacion_cpvs, np.ndarray):
            licitacion_cpvs = licitacion_cpvs.tolist()
        print("CPV LICITACION", licitacion_cpvs)
        if not busqueda_cpvs or not licitacion_cpvs:
            return False
        
        # Extraer códigos CPV limpios
        cpvs_busqueda = set(self._extraer_cpv_code(cpv) for cpv in busqueda_cpvs)
        cpvs_licitacion = set(self._extraer_cpv_code(cpv) for cpv in licitacion_cpvs)
        
        # Comprobar coincidencias exactas
        coincidencias_exactas = cpvs_licitacion & cpvs_busqueda
        if coincidencias_exactas:
            return True
        
        # Comprobar coincidencias por prefijo (primeros 4-6 dígitos)
        for cpv_lic in cpvs_licitacion:
            for cpv_bus in cpvs_busqueda:
                # Coincidencia por categoría (primeros 4 dígitos)
                if cpv_lic[:4] == cpv_bus[:4]:
                    return True
        
        return False
    
    def _comprobar_palabras_clave(self, licitacion: Dict, palabras_clave: List) -> bool:
        """
        Comprueba si alguna palabra clave aparece como palabra completa
        en el nombre del proyecto.
        """
        if not palabras_clave:
            return False

        nombre_proyecto = self._normalizar_texto(
            str(licitacion.get('NOMBRE_PROYECTO', ''))
        )

        # Separar el nombre del proyecto en palabras
        palabras_proyecto = set(nombre_proyecto.split())

        for palabra in palabras_clave:
            palabra_norm = self._normalizar_texto(palabra)
            if palabra_norm in palabras_proyecto:
                return True

        return False

    
    def _comprobar_lugar(self, licitacion: Dict, lugar_busqueda: str) -> bool:
        """Comprueba si la ubicación de la licitación coincide con el lugar buscado."""
        if not lugar_busqueda:
            return True  # Si no hay filtro de lugar, siempre coincide
        
        ubicacion = self._normalizar_texto(str(licitacion.get('UBICACION', '')))
        lugar_norm = self._normalizar_texto(lugar_busqueda)
        
        return lugar_norm in ubicacion
    
    def _comprobar_importe(self, licitacion: Dict, importe_min: float, importe_max: float) -> bool:
        """Comprueba si el importe de la licitación está dentro del rango."""
        try:
            importe_str = str(licitacion.get('IMPORTE', '0'))
            # Limpiar el string de importe
            importe_str = importe_str.replace('€', '').replace(',', '').strip()
            importe = float(importe_str)
            
            return importe_min <= importe <= importe_max
        except:
            return True  # Si no se puede parsear, no filtramos
    
    def _comprobar_entidades(self, licitacion: Dict, entidades: List) -> bool:
        """Comprueba si el sector público coincide con las entidades buscadas."""
        if not entidades:
            return True  # Si no hay filtro de entidades, siempre coincide
        
        sector = str(licitacion.get('SECTOR_PUBLICO', ''))
        return sector in entidades
    
    def _comprobar_estados(self, licitacion: Dict, estados: List) -> bool:
        """Comprueba si el estado de la licitación coincide."""
        if not estados:
            return True  # Si no hay filtro de estados, siempre coincide
        
        estado = str(licitacion.get('ESTADO', ''))
        return estado in estados
    
    def _alerta_ya_existe(self, usuario: str, licitacion_id: str, nombre_busqueda: str) -> bool:
        """Verifica si ya existe una alerta para esta combinación."""
        for alerta_id, alerta in self.alertas_existentes.items():
            if (alerta['usuario'] == usuario and 
                alerta['licitacion_id'] == licitacion_id and
                alerta['busqueda']['nombre'] == nombre_busqueda):
                return True
        return False
    
    def _evaluar_coincidencia(self, licitacion: Dict, filtros: Dict) -> Tuple[bool, List[str]]:
        """
        Evalúa si una licitación coincide con los filtros de búsqueda.
        
        Returns:
            Tuple(coincide, lista_de_coincidencias)
        """
        coincidencias = []
        
        # Comprobar CPV
        cpv_match = self._comprobar_cpv(
            licitacion.get('CPV', []), 
            filtros.get('cpv', [])
        )
        if cpv_match:
            coincidencias.append('cpv')
        
        # Comprobar palabras clave
        palabras_match = self._comprobar_palabras_clave(
            licitacion, 
            filtros.get('palabras_clave', [])
        )
        if palabras_match:
            coincidencias.append('palabras_clave')
        
        # Si no hay coincidencias en CPV ni palabras clave, no continuar
        if not coincidencias:
            return False, []
        
        # Comprobar otros filtros (deben cumplirse todos)
        if not self._comprobar_lugar(licitacion, filtros.get('lugar', '')):
            return False, []
        
        if not self._comprobar_importe(
            licitacion, 
            filtros.get('importe_min', 0), 
            filtros.get('importe_max', float('inf'))
        ):
            return False, []
        
        if not self._comprobar_entidades(licitacion, filtros.get('entidades', [])):
            return False, []
        
        if not self._comprobar_estados(licitacion, filtros.get('estados', [])):
            return False, []
        
        # TODO: Implementar filtros de fecha si es necesario
        
        return True, coincidencias
    
    def procesar_nuevas_licitaciones(self, df_nuevas: pd.DataFrame) -> Dict:
        """
        Procesa un DataFrame con nuevas licitaciones y genera alertas.
        
        Args:
            df_nuevas: DataFrame con las licitaciones nuevas/actualizadas
            
        Returns:
            Dict con estadísticas de alertas generadas
        """
        print("\n" + "=" * 100)
        print("🔔 INICIANDO PROCESO DE GENERACIÓN DE ALERTAS")
        print("=" * 100)
        
        alertas_generadas = 0
        usuarios_notificados = set()
        
        # Recorrer cada usuario
        for nombre_usuario, datos_usuario in self.usuarios.items():
            # Verificar si tiene alertas activas
            if not datos_usuario.get('configuracion', {}).get('alertas_activas', True):
                print(f"⏭️  Usuario {nombre_usuario}: alertas desactivadas")
                continue
            
            busquedas = datos_usuario.get('busquedas_guardadas', [])
            if not busquedas:
                continue
            
            print(f"\n👤 Procesando usuario: {nombre_usuario}")
            print(f"   Búsquedas guardadas: {len(busquedas)}")
            
            # Recorrer cada búsqueda guardada
            for busqueda in busquedas:
                nombre_busqueda = busqueda.get('nombre', '')
                filtros = busqueda.get('filtros', {})
                
                print(f"\n   🔍 Evaluando búsqueda: '{nombre_busqueda}'")
                alertas_busqueda = 0
                
                # Recorrer cada licitación nueva
                for idx, licitacion in df_nuevas.iterrows():
                    licitacion_dict = licitacion.to_dict()
                    licitacion_id = licitacion_dict.get('ID', '')
                    
                    # Verificar si ya existe alerta para esta combinación
                    if self._alerta_ya_existe(nombre_usuario, licitacion_id, nombre_busqueda):
                        continue
                    
                    # Evaluar coincidencia
                    coincide, tipos_coincidencia = self._evaluar_coincidencia(
                        licitacion_dict, 
                        filtros
                    )
                    
                    if coincide:
                        # Crear alerta
                        id_alerta = self._generar_id_alerta()
                        hash_busqueda = self._generar_hash_busqueda(nombre_busqueda)
                        
                        alerta = {
                            "id_alerta": id_alerta,
                            "usuario": nombre_usuario,
                            "licitacion_id": licitacion_id,
                            "busqueda": {
                                "nombre": nombre_busqueda,
                                "hash": hash_busqueda
                            },
                            "estado": "nueva",
                            "leida": False,
                            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "metadatos": {
                                "origen": "ingestion",
                                "coincidencias": tipos_coincidencia,
                                "licitacion_info": {
                                    "nombre": licitacion_dict.get('NOMBRE_PROYECTO', ''),
                                    "entidad": licitacion_dict.get('ENTIDAD', ''),
                                    "importe": licitacion_dict.get('IMPORTE', ''),
                                    "estado": licitacion_dict.get('ESTADO', ''),
                                    "fecha_limite": licitacion_dict.get('FECHA_LIMITE', ''),
                                    "url": licitacion_dict.get('URL', '')
                                }
                            }
                        }
                        
                        self.alertas_existentes[id_alerta] = alerta
                        alertas_generadas += 1
                        alertas_busqueda += 1
                        usuarios_notificados.add(nombre_usuario)
                        
                        print(f"      ✨ Alerta generada para licitación {licitacion_id}")
                        print(f"         Coincidencias: {', '.join(tipos_coincidencia)}")
                
                if alertas_busqueda > 0:
                    print(f"      📊 Total alertas para esta búsqueda: {alertas_busqueda}")
        
        # Guardar alertas
        if alertas_generadas > 0:
            self._guardar_alertas()
        
        # Mostrar resumen
        print("\n" + "=" * 100)
        print("📊 RESUMEN DE ALERTAS GENERADAS")
        print("=" * 100)
        print(f"✅ Total de alertas generadas: {alertas_generadas}")
        print(f"👥 Usuarios notificados: {len(usuarios_notificados)}")
        print(f"📋 Total de alertas en sistema: {len(self.alertas_existentes)}")
        print("=" * 100 + "\n")
        
        return {
            "alertas_generadas": alertas_generadas,
            "usuarios_notificados": list(usuarios_notificados),
            "total_alertas": len(self.alertas_existentes)
        }
    
    def obtener_alertas_usuario(self, nombre_usuario: str, solo_no_leidas: bool = False) -> List[Dict]:
        """
        Obtiene todas las alertas de un usuario.
        
        Args:
            nombre_usuario: Nombre del usuario
            solo_no_leidas: Si True, solo devuelve alertas no leídas
            
        Returns:
            Lista de alertas del usuario
        """
        alertas = []
        
        for alerta_id, alerta in self.alertas_existentes.items():
            if alerta['usuario'] == nombre_usuario:
                if solo_no_leidas and alerta['leida']:
                    continue
                alertas.append(alerta)
        
        # Ordenar por fecha (más recientes primero)
        alertas.sort(key=lambda x: x['fecha_creacion'], reverse=True)
        
        return alertas
    
    def marcar_alerta_leida(self, id_alerta: str):
        """Marca una alerta como leída."""
        if id_alerta in self.alertas_existentes:
            self.alertas_existentes[id_alerta]['leida'] = True
            self.alertas_existentes[id_alerta]['estado'] = 'leida'
            self._guardar_alertas()
            print(f"✅ Alerta {id_alerta} marcada como leída")
        else:
            print(f"⚠️ Alerta {id_alerta} no encontrada")
    
    def eliminar_alerta(self, id_alerta: str):
        """Elimina una alerta del sistema."""
        if id_alerta in self.alertas_existentes:
            del self.alertas_existentes[id_alerta]
            self._guardar_alertas()
            print(f"✅ Alerta {id_alerta} eliminada")
        else:
            print(f"⚠️ Alerta {id_alerta} no encontrada")
    
    def limpiar_alertas_antiguas(self, dias: int = 30):
        """
        Elimina alertas leídas más antiguas que X días.
        
        Args:
            dias: Número de días de antigüedad
        """
        from datetime import timedelta
        
        fecha_limite = datetime.now() - timedelta(days=dias)
        alertas_eliminadas = 0
        
        ids_a_eliminar = []
        for alerta_id, alerta in self.alertas_existentes.items():
            if alerta['leida']:
                fecha_creacion = datetime.strptime(
                    alerta['fecha_creacion'], 
                    "%Y-%m-%d %H:%M:%S"
                )
                if fecha_creacion < fecha_limite:
                    ids_a_eliminar.append(alerta_id)
        
        for alerta_id in ids_a_eliminar:
            del self.alertas_existentes[alerta_id]
            alertas_eliminadas += 1
        
        if alertas_eliminadas > 0:
            self._guardar_alertas()
            print(f"✅ {alertas_eliminadas} alertas antiguas eliminadas")
        else:
            print("ℹ️  No hay alertas antiguas para eliminar")


# ============================================================================
# INTEGRACIÓN CON EL SCRIPT PRINCIPAL
# ============================================================================

def integrar_alertas_en_main():
    """
    Ejemplo de cómo integrar el gestor de alertas en la función main() existente.
    """
    print("""
    # En la función main(), después de procesar los feeds y antes de guardar:
    
    # Inicializar gestor de alertas
    gestor_alertas = Gestor_Alertas(
        archivo_usuarios="usuarios.json",
        archivo_alertas="alertas.json"
    )
    
    # Procesar solo las licitaciones nuevas/actualizadas de este feed
    # (df_general_temp contiene solo las del feed actual)
    if not df_general_temp.empty:
        gestor_alertas.procesar_nuevas_licitaciones(df_general_temp)
    
    # Limpiar alertas antiguas (opcional, cada X feeds)
    if feeds_procesados % 10 == 0:
        gestor_alertas.limpiar_alertas_antiguas(dias=30)
    """)


if __name__ == "__main__":
    # Ejemplo de uso
    print("Ejemplo de uso del Gestor de Alertas")
    print("=" * 100)
    
    # Crear gestor
    gestor = Gestor_Alertas()
    
    # Simular DataFrame con nuevas licitaciones
    df_ejemplo = pd.DataFrame([
        {
            'ID': '202500000180',
            'ENTIDAD': 'Ministerio de Hacienda',
            'CPV': ['30177000-0 - Sistemas automáticos de etiquetado', '48730000-4 - Paquetes de software de seguridad'],
            'IMPORTE': '50000',
            'ESTADO': 'Publicada',
            'NOMBRE_PROYECTO': 'Implementación de Power BI en departamento',
            'SECTOR_PUBLICO': 'COMUNIDADES Y CIUDADES AUTÓNOMAS',
            'UBICACION': 'Andalucía',
            'FECHA_LIMITE': '2026-02-15',
            'URL': 'https://ejemplo.es/licitacion'
        }
    ])
    
    # Procesar alertas
    stats = gestor.procesar_nuevas_licitaciones(df_ejemplo)
    print(f"\nEstadísticas: {stats}")
    
    # Obtener alertas de un usuario
    alertas = gestor.obtener_alertas_usuario("Admin", solo_no_leidas=True)
    print(f"\nAlertas no leídas para Admin: {len(alertas)}")
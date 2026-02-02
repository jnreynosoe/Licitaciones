import os
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from bs4 import BeautifulSoup

class AnalizadorAdjudicaciones:
    """
    Analizador de archivos XML de adjudicaciones públicas.
    Extrae información de empresas ganadoras e importes adjudicados.
    """
    
    def __init__(self, carpeta_xmls: str = "xmls_adjudicacion"):
        self.carpeta_xmls = carpeta_xmls
        self.datos_completos = []
        self.resumen_empresas = None
        
    def extraer_winning_party(self, root: ET.Element) -> List[Dict[str, str]]:
        """Extrae información de las empresas ganadoras (WinningParty)"""
        resultados = []
        
        # Buscar todos los WinningParty en el XML
        for party in root.findall('.//{*}WinningParty'):
            try:
                nif = party.find('.//{*}PartyIdentification/{*}ID')
                # id_licitacion = party.find('.//{*}AdditionalDocumentReference/{*}UUID')
                nombre = party.find('.//{*}PartyName/{*}Name')
                provincia = party.find('.//{*}CountrySubentity')
                ciudad = party.find('.//{*}CityName')
                codigo_postal = party.find('.//{*}PostalZone')
                direccion = party.find('.//{*}AddressLine/{*}Line')
                telefono = party.find('.//{*}Telephone')
                email = party.find('.//{*}ElectronicMail')
                
                resultados.append({
                    'nif': nif.text.strip() if nif is not None else '',
                    # 'id_licitacion': id_licitacion.text.strip() if id_licitacion is not None else '',
                    'nombre': nombre.text.strip() if nombre is not None else '',
                    'provincia': provincia.text.strip() if provincia is not None else '',
                    'ciudad': ciudad.text.strip() if ciudad is not None else '',
                    'codigo_postal': codigo_postal.text.strip() if codigo_postal is not None else '',
                    'direccion': direccion.text.strip() if direccion is not None else '',
                    'telefono': telefono.text.strip() if telefono is not None else '',
                    'email': email.text.strip() if email is not None else ''
                })
            except Exception as e:
                print(f"Error extrayendo WinningParty: {e}")
                
        return resultados
    
    def extraer_datos_encabezado(self, root: ET.Element) -> Dict[str, str]:
        """Extrae UUID y ID de Expediente del encabezado del XML"""
        # El UUID suele estar bajo el tag {*}:UUID
        uuid = root.find('.//{*}UUID')
        # El ContractFolderID es el número de expediente
        expediente = root.find('.//{*}ContractFolderID')
        
        return {
            'uuid_licitacion': uuid.text.strip() if uuid is not None else 'N/A',
            'id_expediente': expediente.text.strip() if expediente is not None else 'N/A'
        }
    
    def extraer_cpvs(self, root: ET.Element) -> str:
        """
        Extrae todos los códigos CPV del XML.
        Retorna una cadena con los códigos separados por comas.
        """
        cpvs = []
        # Buscar los códigos de clasificación (CPV)
        for cpv_node in root.findall('.//{*}RequiredCommodityClassification/{*}ItemClassificationCode'):
            codigo = cpv_node.text.strip() if cpv_node.text else ""
            nombre = cpv_node.get('name', '')
            if codigo:
                # Guardamos formato "Código (Nombre)"
                cpvs.append(f"{codigo} - {nombre}" if nombre else codigo)
        
        return "; ".join(cpvs) if cpvs else "No definido"
    
    def extraer_awarded_amounts(self, root: ET.Element) -> List[Dict[str, float]]:
        """Extrae los importes adjudicados (AwardedTenderedProject)"""
        resultados = []
        
        for project in root.findall('.//{*}AwardedTenderedProject'):
            try:
                importe_sin_iva = project.find('.//{*}TaxExclusiveAmount')
                importe_con_iva = project.find('.//{*}PayableAmount')
                
                resultados.append({
                    'importe_sin_iva': float(importe_sin_iva.text.strip()) if importe_sin_iva is not None else 0.0,
                    'importe_con_iva': float(importe_con_iva.text.strip()) if importe_con_iva is not None else 0.0
                })
            except Exception as e:
                print(f"Error extrayendo AwardedTenderedProject: {e}")
                
        return resultados
    
    def procesar_xml(self, ruta_archivo: str) -> List[Dict[str, Any]]:
        """Procesa un archivo XML individual"""
        try:
            tree = ET.parse(ruta_archivo)
            root = tree.getroot()

            encabezado = self.extraer_datos_encabezado(root)
            cpvs = self.extraer_cpvs(root)  
            # print(cpvs)          
            empresas = self.extraer_winning_party(root)
            importes = self.extraer_awarded_amounts(root)
            
            # Combinar datos (asumiendo correspondencia 1:1)
            datos_archivo = []
            max_length = max(len(empresas), len(importes))
            
            for i in range(max_length):
                dato = {
                    'archivo': os.path.basename(ruta_archivo),
                    'uuid': encabezado['uuid_licitacion'],
                    'expediente': encabezado['id_expediente'],
                    'cpvs': cpvs,
                    **(empresas[i] if i < len(empresas) else {}),
                    **(importes[i] if i < len(importes) else {'importe_sin_iva': 0.0, 'importe_con_iva': 0.0})
                }
                datos_archivo.append(dato)
                
            return datos_archivo
            
        except Exception as e:
            print(f"Error procesando {ruta_archivo}: {e}")
            return []
    
    def procesar_carpeta(self) -> pd.DataFrame:
        """Procesa todos los archivos XML de la carpeta"""
        carpeta = Path(self.carpeta_xmls)
        
        if not carpeta.exists():
            raise FileNotFoundError(f"La carpeta '{self.carpeta_xmls}' no existe")
        
        archivos_xml = list(carpeta.glob("*.xml"))
        
        if not archivos_xml:
            raise FileNotFoundError(f"No se encontraron archivos XML en '{self.carpeta_xmls}'")
        
        print(f"Procesando {len(archivos_xml)} archivos XML...")
        
        for archivo in archivos_xml:
            datos = self.procesar_xml(str(archivo))
            self.datos_completos.extend(datos)
        
        print(f"Total de registros extraídos: {len(self.datos_completos)}")
        
        return pd.DataFrame(self.datos_completos)
    
    def calcular_resumen(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula el resumen por empresa"""
        # Agrupar por empresa (usando NIF o nombre)
        df['clave_empresa'] = df['nif'].fillna('') + '_' + df['nombre'].fillna('')
        
        resumen = df.groupby('uuid').agg({
            'uuid':'first',
            'expediente':'first',
            'nombre': 'first',
            'nif': 'first',
            'archivo': 'count',  # Número de adjudicaciones
            'importe_sin_iva': 'sum',
            'importe_con_iva': 'sum',
            'cpvs':'first',
            'provincia': 'first',
            'ciudad': 'first',
            'email': 'first',
            'telefono': 'first'
        }).reset_index(drop=True)
        
        # Renombrar columnas
        resumen.columns = [
            'id_licitacion', 'expediente', 'nombre', 'nif', 'num_adjudicaciones', 
            'importe_total_sin_iva', 'importe_total_con_iva', 'cpvs',
            'provincia', 'ciudad', 'email', 'telefono'
        ]
        
        # Calcular porcentaje del total
        total_general = resumen['importe_total_con_iva'].sum()
        resumen['porcentaje'] = (resumen['importe_total_con_iva'] / total_general * 100).round(2)
        
        # Ordenar por importe descendente
        resumen = resumen.sort_values('importe_total_con_iva', ascending=False).reset_index(drop=True)
        
        self.resumen_empresas = resumen
        return resumen
    
    def exportar_excel(self, nombre_archivo: str = "analisis_adjudicaciones.xlsx"):
        """Exporta los resultados a un archivo Excel con múltiples hojas"""
        if not self.datos_completos:
            raise ValueError("No hay datos para exportar. Ejecuta primero procesar_carpeta()")
        
        df_completo = pd.DataFrame(self.datos_completos)
        
        if self.resumen_empresas is None:
            self.calcular_resumen(df_completo)
        
        # Crear archivo Excel con múltiples hojas
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            # Hoja 1: Resumen por empresa
            self.resumen_empresas.to_excel(
                writer, 
                sheet_name='Resumen Empresas', 
                index=False
            )
            
            # Hoja 2: Detalle completo
            df_detalle = df_completo[[
                'uuid', 'expediente', 'archivo', 'nif', 'nombre', 'importe_sin_iva', 'importe_con_iva', 'cpvs',
                'provincia', 'ciudad', 'codigo_postal', 'direccion', 'telefono', 'email'
            ]].copy()
            df_detalle.to_excel(
                writer, 
                sheet_name='Detalle Adjudicaciones', 
                index=False
            )
            
            # Hoja 3: Estadísticas generales
            estadisticas = pd.DataFrame({
                'Concepto': [
                    'Total Adjudicaciones',
                    'Total Empresas Únicas',
                    'Importe Total (sin IVA)',
                    'Importe Total (con IVA)'
                ],
                'Valor': [
                    len(self.datos_completos),
                    len(self.resumen_empresas),
                    f"{self.resumen_empresas['importe_total_sin_iva'].sum():,.2f} €",
                    f"{self.resumen_empresas['importe_total_con_iva'].sum():,.2f} €"
                ]
            })
            estadisticas.to_excel(
                writer, 
                sheet_name='Estadísticas', 
                index=False
            )
        
        print(f"\n✅ Archivo Excel generado: {nombre_archivo}")
    
    def mostrar_resumen(self, top_n: int = 10):
        """Muestra un resumen en consola de las principales empresas"""
        if self.resumen_empresas is None:
            raise ValueError("No hay resumen calculado. Ejecuta primero calcular_resumen()")
        
        print("\n" + "="*80)
        print(f"RESUMEN DE ADJUDICACIONES - TOP {top_n} EMPRESAS")
        print("="*80)
        
        total_general = self.resumen_empresas['importe_total_con_iva'].sum()
        total_adjudicaciones = self.resumen_empresas['num_adjudicaciones'].sum()
        
        print(f"\n📊 ESTADÍSTICAS GENERALES:")
        print(f"   • Total de adjudicaciones: {total_adjudicaciones}")
        print(f"   • Total de empresas únicas: {len(self.resumen_empresas)}")
        print(f"   • Importe total (con IVA): {total_general:,.2f} €")
        
        print(f"\n🏆 TOP {top_n} EMPRESAS POR IMPORTE:\n")
        
        for idx, row in self.resumen_empresas.head(top_n).iterrows():
            print(f"{idx+1}. {row['nombre']}")
            print(f"   NIF: {row['nif']}")
            print(f"   Adjudicaciones: {row['num_adjudicaciones']}")
            print(f"   Importe total: {row['importe_total_con_iva']:,.2f} € ({row['porcentaje']:.2f}%)")
            print()


def main():
    """Función principal para ejecutar el análisis"""
    
    # Configurar la carpeta de XMLs
    CARPETA_XMLS = "xmls_adjudicacion"
    
    # Crear analizador
    analizador = AnalizadorAdjudicaciones(CARPETA_XMLS)
    
    try:
        # Procesar todos los XMLs
        df_completo = analizador.procesar_carpeta()
        
        # Calcular resumen
        df_resumen = analizador.calcular_resumen(df_completo)
        
        # Mostrar resumen en consola
        analizador.mostrar_resumen(top_n=15)
        
        # Exportar a Excel
        analizador.exportar_excel("analisis_adjudicaciones.xlsx")
        
        print("\n✨ Proceso completado exitosamente!")
        
    except Exception as e:
        import traceback
        print(f"\n❌ Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
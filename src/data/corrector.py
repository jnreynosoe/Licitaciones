import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from lxml import etree
from datetime import datetime
import traceback
import time
from typing import Optional, Tuple

class VerificadorEstadosLicitacion:
    """
    Clase para verificar y actualizar estados de licitaciones
    comparando la base de datos con el estado publicado en la web.
    """
    
    def __init__(self, ruta_parquet: str):
        """
        Inicializa el verificador con la ruta del archivo parquet.
        
        Args:
            ruta_parquet: Ruta al archivo Pliegos_General.parquet
        """
        self.ruta_parquet = ruta_parquet
        self.df = pd.read_parquet(ruta_parquet)
        self.mapeo_estados = {
            'publicada': 'PUB',
            'publicado': 'PUB',
            'anuncio previo': 'PRE',
            'resuelta': 'RES',
            'adjudicada': 'ADJ',
            'evaluacion': 'EV',
            'evaluación': 'EV',
            'anulada': 'ANUL',
        }
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        self.cambios_realizados = []
        self.adjudicaciones_extraidas = []
        
    def extraer_estado_web(self, url: str) -> Optional[str]:
        """
        Extrae el estado de la licitación desde el HTML de la página.
        
        Args:
            url: URL de la licitación
            
        Returns:
            Estado extraído o None si hay error
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=(20, 60))
            
            if response.status_code != 200:
                print(f"⚠️ Error al acceder a {url}: código {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar el span con id que contiene "text_Estado"
            estado_span = soup.find('span', {'id': lambda x: x and 'text_Estado' in x})
            
            if estado_span:
                estado_texto = estado_span.get('title', '').strip()
                if not estado_texto:
                    estado_texto = estado_span.get_text().strip()
                return estado_texto
            
            print(f"⚠️ No se encontró el elemento de estado en {url}")
            return None
            
        except requests.Timeout:
            print(f"⚠️ Timeout al acceder a {url}")
            return None
        except Exception as e:
            print(f"⚠️ Error al extraer estado de {url}: {e}")
            return None
    
    def normalizar_estado(self, estado_texto: str) -> Optional[str]:
        """
        Convierte el texto del estado web al código de la base de datos.
        
        Args:
            estado_texto: Texto del estado desde la web
            
        Returns:
            Código de estado normalizado o None
        """
        if not estado_texto:
            return None
        
        estado_lower = estado_texto.lower().strip()
        return self.mapeo_estados.get(estado_lower)
    
    def extraer_info_adjudicacion(self, url_licitacion: str, id_interno: str) -> pd.DataFrame:
        """
        Accede a la URL de la licitación, busca el XML de adjudicación y extrae 
        los datos del adjudicatario sin guardar archivos en disco.
        """
        try:
            response = requests.get(url_licitacion, headers=self.headers, timeout=(20, 60))
            if response.status_code != 200: 
                print(f"⚠️ Error al acceder a la URL: {response.status_code}")
                return pd.DataFrame()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            tabla = soup.find('table', {'id': 'myTablaDetalleVISUOE'})
            
            if not tabla: 
                print(f"⚠️ No se encontró la tabla de documentos")
                return pd.DataFrame()
            
            registros_adj = []
            filas = tabla.find('tbody').find_all('tr')
            
            for fila in filas:
                tipo_doc = fila.find('td', class_='tipoDocumento')
                if tipo_doc and 'Adjudicaci' in tipo_doc.get_text():
                    enlaces_xml = fila.find_all('a', href=True)
                    
                    for enlace_xml in enlaces_xml:
                        img_xml = enlace_xml.find('img', alt='Documento xml') if enlace_xml else None
                        
                        if img_xml:
                            url_xml = urljoin('https://contrataciondelestado.es', enlace_xml['href'])
                            print(f"📥 Descargando XML de adjudicación desde: {url_xml}")
                            
                            # Descarga el XML a memoria
                            xml_res = requests.get(url_xml, headers=self.headers, timeout=20)
                            root = etree.fromstring(xml_res.content)
                            
                            # Detectar el namespace correcto automáticamente
                            namespaces_codice = {
                                'cac': 'urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2',
                                'cbc': 'urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2'
                            }
                            
                            namespaces_oasis = {
                                'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
                            }
                            
                            # Intentar detectar cuál namespace usar
                            ns = namespaces_codice
                            test_element = root.find('.//{urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2}TenderResult')
                            if test_element is None:
                                ns = namespaces_oasis
                                print("📋 Usando namespace OASIS")
                            else:
                                print("📋 Usando namespace CODICE")
                            
                            # Buscar todos los TenderResult
                            tender_results = root.findall('.//cac:TenderResult', ns)
                            print(f"🔍 Encontrados {len(tender_results)} TenderResult")
                            
                            for idx, tender_result in enumerate(tender_results, 1):
                                print(f"   Procesando TenderResult #{idx}")
                                
                                # Extraer importes de adjudicación
                                legal_monetary = tender_result.find('.//cac:AwardedTenderedProject/cac:LegalMonetaryTotal', ns)
                                importe_sin_iva = None
                                importe_con_iva = None
                                
                                if legal_monetary is not None:
                                    tax_exclusive = legal_monetary.find('cbc:TaxExclusiveAmount', ns)
                                    payable_amount = legal_monetary.find('cbc:PayableAmount', ns)
                                    
                                    if tax_exclusive is not None:
                                        importe_sin_iva = tax_exclusive.text
                                        print(f"      💰 Importe sin IVA: {importe_sin_iva}€")
                                    if payable_amount is not None:
                                        importe_con_iva = payable_amount.text
                                        print(f"      💰 Importe con IVA: {importe_con_iva}€")
                                
                                # Extraer información del adjudicatario
                                winning_party = tender_result.find('.//cac:WinningParty', ns)
                                
                                if winning_party is not None:
                                    # Datos básicos
                                    nif_elem = winning_party.find('.//cac:PartyIdentification/cbc:ID', ns)
                                    nombre_elem = winning_party.find('.//cac:PartyName/cbc:Name', ns)
                                    
                                    # Datos de contacto
                                    telefono_elem = winning_party.find('.//cac:AgentParty/cac:Contact/cbc:Telephone', ns)
                                    email_elem = winning_party.find('.//cac:AgentParty/cac:Contact/cbc:ElectronicMail', ns)
                                    
                                    # Si no se encuentran en AgentParty, buscar en Contact directo
                                    if telefono_elem is None:
                                        telefono_elem = winning_party.find('.//cac:Contact/cbc:Telephone', ns)
                                    if email_elem is None:
                                        email_elem = winning_party.find('.//cac:Contact/cbc:ElectronicMail', ns)
                                        
                                    provincia_elem = winning_party.find('.//{*}CountrySubentity')
                                    ciudad_elem = winning_party.find('.//{*}CityName')
                                    codigo_postal_elem = winning_party.find('.//{*}PostalZone')
                                    direccion_elem = winning_party.find('.//{*}AddressLine/{*}Line')
                                    
                                    nif = nif_elem.text if nif_elem is not None else None
                                    nombre = nombre_elem.text if nombre_elem is not None else None
                                    telefono = telefono_elem.text if telefono_elem is not None else None
                                    email = email_elem.text if email_elem is not None else None
                                    provincia = provincia_elem.text if provincia_elem is not None else None
                                    ciudad = ciudad_elem.text if ciudad_elem is not None else None
                                    codigo_postal = codigo_postal_elem.text if codigo_postal_elem is not None else None
                                    direccion = direccion_elem.text if direccion_elem is not None else None
                                    
                                    registro = {
                                        "ID_INTERNO": id_interno,
                                        "NIF_ADJUDICATARIO": nif,
                                        "NOMBRE_ADJUDICATARIO": nombre,
                                        "PROVINCIA": provincia,
                                        "CIUDAD": ciudad,
                                        "CODIGO_POSTAL": codigo_postal,
                                        "DIRECCION": direccion,
                                        "TELEFONO": telefono,
                                        "EMAIL": email,
                                        "IMPORTE_SIN_IVA": importe_sin_iva,
                                        "IMPORTE_CON_IVA": importe_con_iva,
                                        "FECHA_EXTRACCION": datetime.now().strftime("%Y-%m-%d")
                                    }
                                    
                                    registros_adj.append(registro)
                                    print(f"      ✅ Adjudicatario: {nombre}")
                                    print(f"         NIF: {nif}")
                                    print(f"         Tel: {telefono}")
                                    print(f"         Email: {email}")
            
            if registros_adj:
                print(f"✅ Total adjudicatarios extraídos: {len(registros_adj)}")
                return pd.DataFrame(registros_adj)
            else:
                print(f"ℹ️ No se encontraron adjudicatarios en el XML")
                return pd.DataFrame()
                
        except requests.Timeout:
            print(f"⚠️ Timeout al intentar acceder a {url_licitacion}")
            return pd.DataFrame()
        except etree.XMLSyntaxError as e:
            print(f"⚠️ Error al parsear XML de adjudicación para {id_interno}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"⚠️ Error general en extracción de adjudicación para {id_interno}: {e}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def procesar_licitacion(self, idx: int, row: pd.Series) -> Tuple[bool, Optional[str]]:
        """
        Procesa una licitación individual: verifica estado y extrae adjudicaciones si aplica.
        
        Args:
            idx: Índice de la fila
            row: Serie de pandas con los datos de la licitación
            
        Returns:
            Tupla (cambio_realizado, nuevo_estado)
        """
        url = row.get('URI') or row.get('URL')
        estado_bd = row.get('ESTADO').split()[0]
        id_interno = row.get('ID_INTERNO') or idx
        
        if pd.isna(url) or not url:
            print(f"⚠️ Registro {idx}: Sin URL")
            return False, None
        
        print(f"\n{'='*80}")
        print(f"🔍 Procesando [{idx+1}/{len(self.df)}]: {url}")
        print(f"   Estado BD: {estado_bd}")
        
        # Extraer estado de la web
        estado_web_texto = self.extraer_estado_web(url)
        
        if not estado_web_texto:
            print(f"   ❌ No se pudo extraer el estado de la web")
            return False, None
        
        print(f"   Estado Web: {estado_web_texto}")
        
        # Normalizar estado
        estado_web_codigo = self.normalizar_estado(estado_web_texto)
        
        if not estado_web_codigo:
            print(f"   ⚠️ Estado web '{estado_web_texto}' no reconocido en el mapeo")
            return False, None
        
        print(f"   Estado Web (código): {estado_web_codigo}")
        
        # Comparar estados
        if estado_bd != estado_web_codigo:
            print(f"   🔄 CAMBIO DETECTADO: {estado_bd} → {estado_web_codigo}")
            
            cambio = {
                'ID_INTERNO': id_interno,
                'URL': url,
                'ESTADO_ANTERIOR': estado_bd,
                'ESTADO_NUEVO': estado_web_codigo,
                'ESTADO_WEB_TEXTO': estado_web_texto,
                'FECHA_VERIFICACION': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.cambios_realizados.append(cambio)
            
            # Si el nuevo estado es Resuelta o Adjudicada, extraer adjudicaciones
            if estado_web_codigo in ['RES', 'ADJ']:
                print(f"   📋 Extrayendo información de adjudicación...")
                df_adj = self.extraer_info_adjudicacion(url, id_interno)
                
                if not df_adj.empty:
                    self.adjudicaciones_extraidas.append(df_adj)
                    print(f"   ✅ Adjudicaciones extraídas: {len(df_adj)}")
            
            return True, estado_web_codigo
        else:
            print(f"   ✅ Estado coincide, no hay cambios")
            return False, None
    
    def verificar_y_actualizar(self, delay_segundos: float = 1.0, limite: Optional[int] = None):
        """
        Verifica todos los registros y actualiza los estados que han cambiado.
        
        Args:
            delay_segundos: Tiempo de espera entre peticiones para evitar sobrecarga
            limite: Número máximo de registros a procesar (None para todos)
        """
        print(f"\n🚀 Iniciando verificación de {len(self.df)} licitaciones")
        print(f"⏱️ Delay entre peticiones: {delay_segundos}s")
        
        if limite:
            print(f"⚠️ Procesando solo los primeros {limite} registros")
            df_procesar = self.df.head(limite)
        else:
            df_procesar = self.df
        
        # Procesar cada licitación
        for idx, row in df_procesar.iterrows():
            cambio, nuevo_estado = self.procesar_licitacion(idx, row)
            
            if cambio and nuevo_estado:
                # Actualizar el DataFrame
                self.df.at[idx, 'ESTADO'] = nuevo_estado
            
            # Delay entre peticiones
            if idx < len(df_procesar) - 1:
                time.sleep(delay_segundos)
        
        print(f"\n{'='*80}")
        print(f"✅ Verificación completada")
        print(f"   Total procesados: {len(df_procesar)}")
        print(f"   Cambios detectados: {len(self.cambios_realizados)}")
        print(f"   Adjudicaciones extraídas: {len(self.adjudicaciones_extraidas)}")
    
    def guardar_resultados(self, 
                          ruta_parquet_actualizado: str = "Pliegos_General_actualizado.parquet",
                          ruta_cambios: str = "cambios_estados.csv",
                          ruta_adjudicaciones: str = "adjudicaciones.parquet"):
        """
        Guarda los resultados: DataFrame actualizado, log de cambios y adjudicaciones.
        
        Args:
            ruta_parquet_actualizado: Ruta para guardar el parquet actualizado
            ruta_cambios: Ruta para guardar el CSV de cambios
            ruta_adjudicaciones: Ruta para guardar el parquet de adjudicaciones
        """
        # Guardar DataFrame actualizado
        self.df.to_parquet(ruta_parquet_actualizado, index=False)
        print(f"\n💾 DataFrame actualizado guardado en: {ruta_parquet_actualizado}")
        
        # Guardar cambios
        if self.cambios_realizados:
            df_cambios = pd.DataFrame(self.cambios_realizados)
            df_cambios.to_csv(ruta_cambios, index=False, encoding='utf-8-sig')
            print(f"📋 Log de cambios guardado en: {ruta_cambios}")
        else:
            print(f"ℹ️ No se detectaron cambios, no se genera archivo de log")
        
        # Guardar adjudicaciones
        if self.adjudicaciones_extraidas:
            df_adj_total = pd.concat(self.adjudicaciones_extraidas, ignore_index=True)
            df_adj_total.to_parquet(ruta_adjudicaciones, index=False)
            print(f"🏆 Adjudicaciones guardadas en: {ruta_adjudicaciones}")
            print(f"   Total registros: {len(df_adj_total)}")
        else:
            print(f"ℹ️ No se extrajeron adjudicaciones")
    
    def generar_reporte(self):
        """
        Genera un reporte resumen de la verificación.
        """
        print(f"\n{'='*80}")
        print(f"📊 REPORTE DE VERIFICACIÓN")
        print(f"{'='*80}")
        print(f"Total registros procesados: {len(self.df)}")
        print(f"Cambios de estado detectados: {len(self.cambios_realizados)}")
        
        if self.cambios_realizados:
            df_cambios = pd.DataFrame(self.cambios_realizados)
            print(f"\nDistribución de cambios:")
            print(df_cambios['ESTADO_NUEVO'].value_counts())
        
        if self.adjudicaciones_extraidas:
            df_adj = pd.concat(self.adjudicaciones_extraidas, ignore_index=True)
            print(f"\nAdjudicaciones extraídas: {len(df_adj)}")
            print(f"Adjudicatarios únicos: {df_adj['NIF_ADJUDICATARIO'].nunique()}")
        
        print(f"{'='*80}\n")


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Crear el verificador
    verificador = VerificadorEstadosLicitacion("/home/enetic/Desktop/Licitaciones/src/data/Pliegos_general.parquet")
    
    # Opción 1: Procesar un número limitado de registros (para pruebas)
    # verificador.verificar_y_actualizar(delay_segundos=2.0, limite=10)
    
    # Opción 2: Procesar todos los registros
    verificador.verificar_y_actualizar(delay_segundos=1.5)
    
    # Guardar resultados
    verificador.guardar_resultados(
        ruta_parquet_actualizado="Pliegos_General_actualizado.parquet",
        ruta_cambios="cambios_estados.csv",
        ruta_adjudicaciones="adjudicaciones.parquet"
    )
    
    # Generar reporte
    verificador.generar_reporte()
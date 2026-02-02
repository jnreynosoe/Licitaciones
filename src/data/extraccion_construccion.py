import requests
from lxml import etree
import sys
from contextlib import redirect_stdout
from pathlib import Path
from jsonpath_ng.ext import parse
import os
import shutil
import json
import re
from urllib.parse import urlparse, unquote
import zipfile
import io
import pandas as pd
import traceback
from datetime import datetime, date
from bs4 import BeautifulSoup
from urllib.parse import urljoin


try:
    from alertas_data import Gestor_Alertas
except:
    from .alertas_data import Gestor_Alertas

def generar_feed():
    dt = datetime.now()
    mes_num = dt.strftime("%m")   # '01'–'12'
    anio_str = dt.strftime("%Y") # '2026'
    FEED_BASE = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_"
    anio_mes = anio_str+mes_num
    return FEED_BASE+anio_mes+".zip"

# Configuración inicial
FEED = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"
# FEEDZIP = generar_feed()
FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202511.zip"
# # FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202512.zip"
print(FEEDZIP)
parser = etree.XMLParser(recover=True)

# Rutas de archivos
DATA_DIR = "src/data"
CHECKPOINT_FILE = "ultimo_feed_procesado.txt"
LOG_FILE = "extraccion_mensual.txt"

# ============================================================================
# FUNCIONES DE EXTRACCIÓN XML -> DICT
# ============================================================================

def recorrer_xml(nodo):
    """Recorre un nodo XML y devuelve una estructura anidada tipo dict."""
    tag = etree.QName(nodo).localname
    texto = nodo.text.strip() if nodo.text and nodo.text.strip() else None

    if len(nodo) == 0:
        return {tag: texto}

    contenido = []
    for hijo in nodo:
        contenido.append(recorrer_xml(hijo))

    if texto:
        contenido.insert(0, {"_text": texto})

    return {tag: contenido}


def extraer_info(xml_root, claves_interes):
    """Recorre el XML y extrae solo las secciones relevantes (por etiqueta)."""
    info = {k: [] for k in claves_interes}

    for elem in xml_root.iter():
        tag = etree.QName(elem).localname
        if tag in claves_interes:
            info[tag].append(recorrer_xml(elem)[tag])

    return info


# ============================================================================
# FUNCIONES DE PROCESAMIENTO JSON -> DATAFRAMES
# ============================================================================

def extraccion_data_relevante(json_data):
    """Extrae información relevante del JSON y genera DataFrames."""
    registros = []
    fecha_limite = None
    fecha_publicacion = None
    
    # Summary
    datos = json_data['summary'][0].split(";")
    
    # Link
    try:
        link = json_data["link"]
    except:
        link = "https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
    
    # Updated
    updated = json_data["updated"][0]
    
    for i in range(len(datos)):
        datos[i] = datos[i].split(":")[1]
    
    id_, entidad, importe, estado = datos
    
    # Fecha límite
    jsonpath_expr_data = parse('$..TenderSubmissionDeadlinePeriod[*].EndDate')
    fecha_res = [match.value for match in jsonpath_expr_data.find(json_data)]
    if len(fecha_res) > 0:
        fecha_limite = fecha_res[0]
    
    # Fecha publicación
    jsonpath_expr_date = parse('$..IssueDate')
    fecha_pub_res = [match.value for match in jsonpath_expr_date.find(json_data)]
    if fecha_pub_res:
        fecha_publicacion = fecha_pub_res[0]
        print(f"📅 Fecha de publicación encontrada: {fecha_publicacion}")
    
    # ProcurementProject
    data = json_data["ProcurementProject"][0]
    name = next((d["Name"] for d in data if "Name" in d), None)
    
    jsonpath_expr = parse('$..RequiredCommodityClassification[*].ItemClassificationCode')
    codes = [match.value for match in jsonpath_expr.find(data)]

    ## Extraccion de datos geograficos    
    country_expr = parse('$..RealizedLocation[*].CountrySubentity')
    city_res = [match.value for match in country_expr.find(data)]
    
    data_01= json_data["ContractFolderStatus"][0]
    entidades_expr = parse('$..ParentLocatedParty[*].PartyName[*].Name')
    entidades_res = [match.value for match in entidades_expr.find(data_01)]
    
    ID_expr = parse('$..ContractFolderID')
    ID_res = [match.value for match in ID_expr.find(data_01)]
    
    print("-----" * 100)
    print("Entidades", entidades_res)
    jerarquia_path = entidades_res[-2]
    if len(entidades_res)>=3:
        sub_jerarquia_path = entidades_res[-3]
    else:
        sub_jerarquia_path = None
    
    ciudades_parser = parse('$..CityName')
    city_aux = [match.value for match in ciudades_parser.find(data_01)]
    if isinstance(city_aux, list):
        city_aux = city_aux[0]
    if jerarquia_path == "ENTIDADES LOCALES":
        ubicacion_aux = sub_jerarquia_path
    else:
        ubicacion_aux = city_aux

    
    # Guardar en lista de registros
    registros.append({
        "ID": id_,
        "ENTIDAD": entidad,
        "CPV": codes,
        "IMPORTE": importe,
        "ESTADO": estado,
        "NOMBRE_PROYECTO": name,
        "FECHA_PUBLICACION": fecha_publicacion,
        "FECHA_ACTUALIZACION": updated,
        "FECHA_LIMITE": fecha_limite,
        "SECTOR_PUBLICO":jerarquia_path,
        "UBICACION":ubicacion_aux,
        "URL": link,
    })
    
    df = pd.DataFrame(registros)
    
    # TendererQualificationRequest
    if len(json_data["TendererQualificationRequest"]) > 0:
        tenderer = extraccion_tenderer(json_data['TendererQualificationRequest'][0], id_)
    else:
        tenderer = pd.DataFrame([])
    
    # AwardingTerms
    if len(json_data["AwardingTerms"]) > 0:
        awarding = extraccion_awarding(json_data["AwardingTerms"][0], id_)
    else:
        awarding = pd.DataFrame([])
    
    # Documentos
    docs = extraccion_docs(json_data, id_)

    # Solo intentamos extraer si el estado es ADJ (Adjudicada) o RES (Resuelta)
    if estado.strip() in ['ADJ', 'RES']:
        print(f"🔎 Detectada licitación resuelta/adjudicada: {id_}. Extrayendo detalles...")
        df_adjudicatarios = extraer_info_adjudicacion(link, id_)
    else:
        df_adjudicatarios = pd.DataFrame()

    return df, tenderer, awarding, docs, df_adjudicatarios


def extraccion_tenderer(info_tenderer, id):
    """Extrae criterios técnicos, financieros y requisitos específicos."""
    registros = []
    
    jsonpath_expr_data = parse('$..TechnicalEvaluationCriteria[*]')
    technical_criteria = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
    jsonpath_expr_data = parse('$..FinancialEvaluationCriteria[*]')
    financial_criteria = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
    jsonpath_expr_data = parse('$..SpecificTendererRequirement[*]')
    specific_tendering = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
    if len(technical_criteria) > 0:
        for i in range(int(len(technical_criteria) / 2)):
            descripcion = list(technical_criteria[(i * 2) + 1].values())[0]
            code_type = list(technical_criteria[(i * 2)].values())[0]
            registros.append({
                "pliego_id": id,
                "TIPO": "Criterios Tecnicos",
                "DESCRIPCION": descripcion,
                "CODIGO_TIPO": code_type
            })
    
    if len(financial_criteria) > 0:
        for i in range(int(len(financial_criteria) / 2)):
            descripcion = list(financial_criteria[(i * 2) + 1].values())[0]
            code_type = list(financial_criteria[(i * 2)].values())[0]
            registros.append({
                "pliego_id": id,
                "TIPO": "Criterios Financieros",
                "DESCRIPCION": descripcion,
                "CODIGO_TIPO": code_type
            })
    
    if len(specific_tendering) > 0:
        for i in range(int(len(specific_tendering) / 2)):
            descripcion = list(specific_tendering[(i * 2) + 1].values())[0]
            code_type = list(specific_tendering[(i * 2)].values())[0]
            registros.append({
                "pliego_id": id,
                "TIPO": "Requisitos",
                "DESCRIPCION": descripcion,
                "CODIGO_TIPO": code_type
            })
    
    return pd.DataFrame(registros)


def extraccion_awarding(info_awarding, id):
    """Extrae criterios de adjudicación."""
    registros = []
    
    for sub_info in info_awarding:
        for criterio in sub_info.values():
            for criter in criterio:
                tipo = None
                descripcion = None
                code_type = None
                weight_numeric = None
                notas = None
                
                if list(criter.keys())[0] == "Description":
                    descripcion = list(criter.values())[0]
                if list(criter.keys())[0] in ["RequirementTypeCode", "EvaluationCriteriaTypeCode", "AwardingCriteriaSubTypeCode"]:
                    code_type = list(criter.values())[0]
                if list(criter.keys())[0] in ["AwardingCriteriaTypeCode"]:
                    tipo = list(criter.values())[0]
                if list(criter.keys())[0] in ["WeightNumeric"]:
                    weight_numeric = list(criter.values())[0]
                if list(criter.keys())[0] in ["Note"]:
                    notas = list(criter.values())[0]
            
            registros.append({
                "pliego_id": id,
                "TIPO": tipo,
                "DESCRIPCION": descripcion,
                "CODIGO_TIPO": code_type,
                "PESO": weight_numeric,
                "NOTAS": notas,
            })
    
    return pd.DataFrame(registros)


def extraccion_docs(info_docs, id):
    """Extrae documentación legal, técnica y adicional."""
    registros = []
    
    legal_expr_data = parse('$..LegalDocumentReference[*]')
    legal_document = [match.value for match in legal_expr_data.find(info_docs)]
    
    additional_expr_data = parse('$..AdditionalDocumentReference[*]')
    additional_document = [match.value for match in additional_expr_data.find(info_docs)]
    
    technical_expr_data = parse('$..TechnicalDocumentReference[*]')
    technical_document = [match.value for match in technical_expr_data.find(info_docs)]
    
    tipos = {
        "Documentacion Legal": legal_document,
        "Documentacion Adicional": additional_document,
        "Documentacion Tecnica": technical_document
    }
    
    for tipo, documentos in tipos.items():
        for doc in documentos:
            if isinstance(doc, list):
                ids_extraidos = []
                uris_extraidos = []
                for elemento in doc:
                    if isinstance(elemento, dict):
                        id_data = parse('$..ID[*]')
                        ids = [match.value for match in id_data.find(elemento)]
                        URI_data = parse('$..URI[*]')
                        uris = [match.value for match in URI_data.find(elemento)]
                        
                        if ids:
                            ids_extraidos.extend(ids)
                        if uris:
                            uris_extraidos.extend(uris)
                
                for i in range(max(len(ids_extraidos), len(uris_extraidos))):
                    descripcion = ids_extraidos[i] if i < len(ids_extraidos) else None
                    uri = uris_extraidos[i] if i < len(uris_extraidos) else None
                    
                    if descripcion or uri:
                        registros.append({
                            "pliego_id": id,
                            "TIPO": tipo,
                            "DESCRIPCION": descripcion,
                            "URI": uri,
                            "CODIGO_TIPO": tipo.split()[-1],
                        })
            
            elif isinstance(doc, dict) and 'ID' in doc:
                registros.append({
                    "pliego_id": id,
                    "TIPO": tipo,
                    "DESCRIPCION": doc.get('ID'),
                    "URI": doc.get('URI'),
                    "CODIGO_TIPO": tipo.split()[-1],
                })
    
    return pd.DataFrame(registros)


def extraer_info_adjudicacion(url_licitacion, id_pliego):
    """
    Accede a la URL de la licitación, busca el XML de adjudicación y extrae 
    los datos del adjudicatario sin guardar archivos en disco.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url_licitacion, headers=headers, timeout=(20,60))
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
                        xml_res = requests.get(url_xml, headers=headers, timeout=20)
                        root = etree.fromstring(xml_res.content)
                        
                        # IMPORTANTE: Detectar el namespace correcto automáticamente
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
                                
                                # Datos de contacto - ACTUALIZADO para buscar en AgentParty
                                telefono_elem = winning_party.find('.//cac:AgentParty/cac:Contact/cbc:Telephone', ns)
                                email_elem = winning_party.find('.//cac:AgentParty/cac:Contact/cbc:ElectronicMail', ns)
                                
                                # Si no se encuentran en AgentParty, buscar en Contact directo
                                if telefono_elem is None:
                                    telefono_elem = winning_party.find('.//cac:Contact/cbc:Telephone', ns)
                                if email_elem is None:
                                    email_elem = winning_party.find('.//cac:Contact/cbc:ElectronicMail', ns)
                                
                                nif = nif_elem.text if nif_elem is not None else None
                                nombre = nombre_elem.text if nombre_elem is not None else None
                                telefono = telefono_elem.text if telefono_elem is not None else None
                                email = email_elem.text if email_elem is not None else None
                                
                                registro = {
                                    "pliego_id": id_pliego,
                                    "NIF_ADJUDICATARIO": nif,
                                    "NOMBRE_ADJUDICATARIO": nombre,
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
        print(f"⚠️ Error al parsear XML de adjudicación para {id_pliego}: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"⚠️ Error general en extracción de adjudicación para {id_pliego}: {e}")
        traceback.print_exc()
        return pd.DataFrame()


# ============================================================================
# FUNCIONES DE GESTIÓN DE ESTADO INCREMENTAL
# ============================================================================

def cargar_dataframes_existentes():
    """Carga los DataFrames existentes si existen, sino crea vacíos."""
    dfs = {}
    archivos = {
        'general': f"{DATA_DIR}/Pliegos_general.parquet",
        'tendering': f"{DATA_DIR}/Requisitos_general.parquet",
        'awarding': f"{DATA_DIR}/Criterios_general.parquet",
        'docs': f"{DATA_DIR}/Documentacion_general.parquet",
        'df_adjudicatarios': f"{DATA_DIR}/Adjudicatarios_general.parquet"
    }
    
    for key, archivo in archivos.items():
        if os.path.exists(archivo):
            dfs[key] = pd.read_parquet(archivo, engine="pyarrow")
            print(f"✅ Cargado {key}: {len(dfs[key])} registros existentes")
        else:
            dfs[key] = pd.DataFrame()
            print(f"ℹ️  Creando nuevo DataFrame para {key}")
    
    return dfs['general'], dfs['tendering'], dfs['awarding'], dfs['docs'], dfs['df_adjudicatarios']


def obtener_ultimo_feed_procesado():
    """Lee el último feed procesado desde el archivo de checkpoint."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            ultimo_feed = f.read().strip()
            if ultimo_feed:
                print(f"📍 Último feed procesado: {ultimo_feed}")
                return ultimo_feed
    print("📍 No hay checkpoint previo, procesando desde el inicio")
    return None


def guardar_checkpoint(nombre_feed):
    """Guarda el nombre del último feed procesado."""
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        f.write(nombre_feed)


def actualizar_o_insertar_licitacion(df_existente, df_nuevo):
    """
    Actualiza registros existentes o inserta nuevos basándose en el ID.
    Conserva todas las licitaciones, incluyendo las de estado terminal.
    """
    if df_existente.empty:
        return df_nuevo
    
    if df_nuevo.empty:
        return df_existente
    
    # Identificar IDs nuevos
    ids_nuevos = df_nuevo['ID'].values
    
    for id_nuevo in ids_nuevos:
        registro_nuevo = df_nuevo[df_nuevo['ID'] == id_nuevo]
        estado_nuevo = registro_nuevo['ESTADO'].values[0].strip()
        
        # Si existe, actualizar (conservando todas las licitaciones)
        if id_nuevo in df_existente['ID'].values:
            estado_anterior = df_existente[df_existente['ID'] == id_nuevo]['ESTADO'].values[0]
            print(f"🔄 Actualizando licitación {id_nuevo}: {estado_anterior} → {estado_nuevo}")
            df_existente = df_existente[df_existente['ID'] != id_nuevo]
            df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
        else:
            # Si no existe, insertar
            print(f"✨ Nueva licitación {id_nuevo} - Estado: {estado_nuevo}")
            df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
    
    return df_existente


def actualizar_tablas_relacionadas(df_existente, df_nuevo, id_column='pliego_id'):
    """
    Actualiza tablas relacionadas (requisitos, criterios, docs, adjudicatarios).
    IMPORTANTE: Para adjudicatarios, solo AGREGA nuevos registros, nunca elimina.
    Para otras tablas, reemplaza registros del mismo ID.
    """
    if df_existente.empty:
        return df_nuevo
    
    if df_nuevo.empty:
        return df_existente
    
    # Identificar IDs en la nueva carga
    ids_nuevos = df_nuevo[id_column].unique()
    
    for id_nuevo in ids_nuevos:
        # CLAVE: Para adjudicatarios, solo agregamos si no existe ya
        # Para otras tablas, eliminamos y reemplazamos
        
        # Verificar si ya existe este pliego_id en los registros existentes
        registros_existentes = df_existente[df_existente[id_column] == id_nuevo]
        registros_nuevos = df_nuevo[df_nuevo[id_column] == id_nuevo]
        
        if not registros_existentes.empty:
            # Si es tabla de adjudicatarios, verificamos NIF para evitar duplicados
            if 'NIF_ADJUDICATARIO' in df_existente.columns:
                # Solo agregar adjudicatarios que no existan (por NIF)
                for _, nuevo_reg in registros_nuevos.iterrows():
                    nif_nuevo = nuevo_reg['NIF_ADJUDICATARIO']
                    if nif_nuevo not in df_existente[df_existente[id_column] == id_nuevo]['NIF_ADJUDICATARIO'].values:
                        print(f"➕ Agregando nuevo adjudicatario {nif_nuevo} para {id_nuevo}")
                        df_existente = pd.concat([df_existente, pd.DataFrame([nuevo_reg])], ignore_index=True)
                    else:
                        print(f"⏭️  Adjudicatario {nif_nuevo} ya existe para {id_nuevo}, saltando")
            else:
                # Para otras tablas (requisitos, criterios, docs), reemplazar
                print(f"🔄 Actualizando registros relacionados para {id_nuevo}")
                df_existente = df_existente[df_existente[id_column] != id_nuevo]
                df_existente = pd.concat([df_existente, registros_nuevos], ignore_index=True)
        else:
            # No existe, agregar todos los registros nuevos
            print(f"✨ Agregando nuevos registros para {id_nuevo}")
            df_existente = pd.concat([df_existente, registros_nuevos], ignore_index=True)
    
    return df_existente


# ============================================================================
# FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# ============================================================================

def procesar_feed(feed_url, df_general, df_tendering, df_awarding, df_docs, df_adjudicaciones):
    """Procesa un feed ATOM y acumula los datos en los DataFrames proporcionados."""
    
    r = requests.get(feed_url, timeout=60)
    r.raise_for_status()
    root = etree.fromstring(r.content, parser=parser)
    
    entries = root.xpath("//atom:entry", namespaces={"atom": "http://www.w3.org/2005/Atom"})
    print(f"Entradas encontradas en el feed: {len(entries)}")
    
    claves = [
        "summary", "updated", "AwardingTerms", "TenderingTerms",
        "RequiredFinancialGuarantee", "ContractFolderStatus",
        "TendererQualificationRequest", "ExternalReference",
        "ProcurementProject", "Party", "ProcurementProjectLot",
        "ExternalData", "AdditionalDocumentReference",
        "LegalDocumentReference", "TechnicalDocumentReference",
        "TenderSubmissionDeadlinePeriod",
    ]
    
    # DataFrames temporales para este feed
    df_general_temp = pd.DataFrame()
    df_tendering_temp = pd.DataFrame()
    df_awarding_temp = pd.DataFrame()
    df_docs_temp = pd.DataFrame()
    df_adjudicatarios_temp = pd.DataFrame()
    
    for i, entry in enumerate(entries, start=1):
        # Metadatos ATOM
        summary = entry.xpath("string(atom:summary)", namespaces={"atom": "http://www.w3.org/2005/Atom"}).strip()
        enlace = entry.xpath("string(atom:link/@href)", namespaces={"atom": "http://www.w3.org/2005/Atom"})
        
        print('-' * 100)
        print(f"Procesando entrada {i}: {summary[:80]}...")
        
        # Extraer información del XML
        dict_info = extraer_info(entry, claves)
        dict_info['link'] = enlace
        
        try:
            # Procesar directamente en memoria
            df_temp, df_tend, df_award, df_doc, df_adjudicatarios = extraccion_data_relevante(dict_info)
            
            # Acumular en temporales de este feed
            df_general_temp = pd.concat([df_general_temp, df_temp], ignore_index=True)
            df_tendering_temp = pd.concat([df_tendering_temp, df_tend], ignore_index=True)
            df_awarding_temp = pd.concat([df_awarding_temp, df_award], ignore_index=True)
            df_docs_temp = pd.concat([df_docs_temp, df_doc], ignore_index=True)
            
            # IMPORTANTE: Acumular adjudicatarios solo si hay datos
            if not df_adjudicatarios.empty:
                print(f"📊 Adjudicatarios encontrados en esta entrada: {len(df_adjudicatarios)}")
                df_adjudicatarios_temp = pd.concat([df_adjudicatarios_temp, df_adjudicatarios], ignore_index=True)
            
            print(f"✅ Procesado correctamente")
            
        except Exception as e:
            print(f"⚠️ Error procesando entrada {i}: {e}")
            traceback.print_exc()
    
    # Actualizar DataFrames principales con lógica incremental
    print("\n" + "=" * 100)
    print("Actualizando base de datos...")
    df_general = actualizar_o_insertar_licitacion(df_general, df_general_temp)
    df_tendering = actualizar_tablas_relacionadas(df_tendering, df_tendering_temp)
    df_awarding = actualizar_tablas_relacionadas(df_awarding, df_awarding_temp)
    df_docs = actualizar_tablas_relacionadas(df_docs, df_docs_temp)
    
    # IMPORTANTE: Actualizar adjudicatarios usando la función que NO elimina registros
    if not df_adjudicatarios_temp.empty:
        print(f"📊 Actualizando tabla de adjudicatarios con {len(df_adjudicatarios_temp)} nuevos registros")
        df_adjudicaciones = actualizar_tablas_relacionadas(df_adjudicaciones, df_adjudicatarios_temp)
    else:
        print("ℹ️  No hay adjudicatarios nuevos en este feed")
    
    return df_general, df_tendering, df_awarding, df_docs, df_adjudicaciones


def natural_sort_key(s):
    """Ordena strings con números de forma natural."""
    return [int(text) if text.isdigit() else text
            for text in re.split(r'(\d+)', s)]


def main():
    """Función principal que coordina todo el proceso incremental."""
    
    # Crear directorio de datos si no existe
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Cargar DataFrames existentes
    print("=" * 100)
    print("Cargando datos existentes...")
    print("=" * 100)
    df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios = cargar_dataframes_existentes()
    
    # Obtener último feed procesado
    ultimo_feed = obtener_ultimo_feed_procesado()
    
    # Descargar y descomprimir el ZIP
    print("\n" + "=" * 100)
    print(f"Descargando ZIP desde {FEEDZIP}...")
    print("=" * 100)
    response = requests.get(FEEDZIP)
    zip_data = zipfile.ZipFile(io.BytesIO(response.content))
    
    # Ordenar archivos del ZIP
    feed_base = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
    zip_data_sorted = sorted(zip_data.namelist(), key=natural_sort_key)
    zip_data_sorted.append(zip_data_sorted.pop(0))
    
    # Determinar desde dónde empezar a procesar
    comenzar = (ultimo_feed is None)
    feeds_procesados = 0
    
    # Redirigir salida a archivo
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        with redirect_stdout(f):
            print(f"\n{'=' * 100}")
            print(f"Inicio de procesamiento: {datetime.now()}")
            print('=' * 100)
            
            for fin_feed in zip_data_sorted:
                # Si ya procesamos este feed, saltar hasta encontrar el siguiente
                if not comenzar:
                    if fin_feed == ultimo_feed:
                        comenzar = True
                        print(f"⏭️  Saltando {fin_feed} (ya procesado)")
                        continue
                    else:
                        continue
                
                print(f"\n{'=' * 100}")
                print(f"Procesando archivo: {fin_feed}")
                print('=' * 100)
                
                FEED = feed_base + fin_feed
                
                try:
                    df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios = procesar_feed(
                        FEED, df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios
                    )

                    # Gestor de alertas
                    df_general_temp = df_general.copy()
                    if not df_general_temp.empty:
                        gestor_alertas = Gestor_Alertas(
                            archivo_usuarios="usuarios.json",
                            archivo_alertas="alertas.json"
                        )
                        gestor_alertas.procesar_nuevas_licitaciones(df_general_temp)
                    
                    # Guardar checkpoint después de cada feed
                    if fin_feed != "licitacionesPerfilesContratanteCompleto3.atom":
                        guardar_checkpoint(fin_feed)
                    feeds_procesados += 1
                    
                    # Guardar DataFrames periódicamente (cada 5 feeds)
                    if feeds_procesados % 5 == 0:
                        print("\n💾 Guardando progreso intermedio...")
                        guardar_dataframes(df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios)
                    
                except Exception as e:
                    print(f"❌ Error crítico procesando {fin_feed}: {e}")
                    traceback.print_exc()
                    continue
            
            print(f"\n{'=' * 100}")
            print(f"Fin de procesamiento: {datetime.now()}")
            print(f"Feeds procesados en esta ejecución: {feeds_procesados}")
            print('=' * 100)
    
    # Guardar DataFrames finales
    print("\n" + "=" * 100)
    print("Guardando resultados finales en archivos Parquet...")
    print("=" * 100)
    guardar_dataframes(df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios)
    
    print(f"\n✅ Proceso completado exitosamente!")
    print(f"📊 Total de registros en base de datos:")
    print(f"   - Pliegos generales: {len(df_general)}")
    print(f"   - Requisitos: {len(df_tendering)}")
    print(f"   - Criterios: {len(df_awarding)}")
    print(f"   - Documentos: {len(df_docs)}")
    print(f"   - Empresas Adjudicatarias: {len(df_adjudicatarios)}")
    print(f"   - Feeds procesados: {feeds_procesados}")


def guardar_dataframes(df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios):
    """Guarda los DataFrames en archivos Parquet."""
    df_general.to_parquet(f"{DATA_DIR}/Pliegos_general.parquet", index=False, engine="pyarrow")
    df_tendering.to_parquet(f"{DATA_DIR}/Requisitos_general.parquet", index=False, engine="pyarrow")
    df_awarding.to_parquet(f"{DATA_DIR}/Criterios_general.parquet", index=False, engine="pyarrow")
    
    # Limpiar documentos
    df_docs = df_docs.dropna()
    df_docs.to_parquet(f"{DATA_DIR}/Documentacion_general.parquet", index=False, engine="pyarrow")
    
    # IMPORTANTE: Guardar adjudicatarios sin eliminar duplicados por NIF
    # (ya se manejan en actualizar_tablas_relacionadas)
    if not df_adjudicatarios.empty:
        df_adjudicatarios.to_parquet(f"{DATA_DIR}/Adjudicatarios_general.parquet", index=False, engine="pyarrow")
        print(f"✅ Guardados {len(df_adjudicatarios)} registros de adjudicatarios")
    else:
        print("ℹ️  No hay adjudicatarios para guardar")
    
    print("✅ DataFrames guardados correctamente")


if __name__ == "__main__":
    main()

##--------------------------------
## PRE CORRECCION!
##--------------------------------
# import requests
# from lxml import etree
# import sys
# from contextlib import redirect_stdout
# from pathlib import Path
# from jsonpath_ng.ext import parse
# import os
# import shutil
# import json
# import re
# from urllib.parse import urlparse, unquote
# import zipfile
# import io
# import pandas as pd
# import traceback
# from datetime import datetime, date
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin


# try:
#     from alertas_data import Gestor_Alertas 
# except:
#     from .alertas_data import Gestor_Alertas

# def generar_feed():
#     dt = datetime.now()
#     mes_num = dt.strftime("%m")   # '01'–'12'
#     anio_str = dt.strftime("%Y") # '2026'
#     FEED_BASE = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_"
#     anio_mes = anio_str+mes_num
#     return FEED_BASE+anio_mes+".zip"

# # Configuración inicial
# FEED = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"
# FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202511.zip"
# # FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202512.zip"
# ## FELIZ AÑO NUEVO!
# # FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202601.zip"
# # FEEDZIP = generar_feed()
# print(FEEDZIP)
# parser = etree.XMLParser(recover=True)

# # Rutas de archivos
# DATA_DIR = "src/data"
# CHECKPOINT_FILE = "ultimo_feed_procesado.txt"
# LOG_FILE = "extraccion_mensual.txt"

# # ============================================================================
# # FUNCIONES DE EXTRACCIÓN XML -> DICT
# # ============================================================================

# def recorrer_xml(nodo):
#     """Recorre un nodo XML y devuelve una estructura anidada tipo dict."""
#     tag = etree.QName(nodo).localname
#     texto = nodo.text.strip() if nodo.text and nodo.text.strip() else None

#     if len(nodo) == 0:
#         return {tag: texto}

#     contenido = []
#     for hijo in nodo:
#         contenido.append(recorrer_xml(hijo))

#     if texto:
#         contenido.insert(0, {"_text": texto})

#     return {tag: contenido}


# def extraer_info(xml_root, claves_interes):
#     """Recorre el XML y extrae solo las secciones relevantes (por etiqueta)."""
#     info = {k: [] for k in claves_interes}

#     for elem in xml_root.iter():
#         tag = etree.QName(elem).localname
#         if tag in claves_interes:
#             info[tag].append(recorrer_xml(elem)[tag])

#     return info


# # ============================================================================
# # FUNCIONES DE PROCESAMIENTO JSON -> DATAFRAMES
# # ============================================================================

# def extraccion_data_relevante(json_data):
#     """Extrae información relevante del JSON y genera DataFrames."""
#     registros = []
#     fecha_limite = None
#     fecha_publicacion = None
    
#     # Summary
#     datos = json_data['summary'][0].split(";")
    
#     # Link
#     try:
#         link = json_data["link"]
#     except:
#         link = "https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
    
#     # Updated
#     updated = json_data["updated"][0]
    
#     for i in range(len(datos)):
#         datos[i] = datos[i].split(":")[1]
    
#     id_, entidad, importe, estado = datos
    
#     # Fecha límite
#     jsonpath_expr_data = parse('$..TenderSubmissionDeadlinePeriod[*].EndDate')
#     fecha_res = [match.value for match in jsonpath_expr_data.find(json_data)]
#     if len(fecha_res) > 0:
#         fecha_limite = fecha_res[0]
    
#     # Fecha publicación
#     jsonpath_expr_date = parse('$..IssueDate')
#     fecha_pub_res = [match.value for match in jsonpath_expr_date.find(json_data)]
#     if fecha_pub_res:
#         fecha_publicacion = fecha_pub_res[0]
#         print(f"📅 Fecha de publicación encontrada: {fecha_publicacion}")
    
#     # ProcurementProject
#     data = json_data["ProcurementProject"][0]
#     name = next((d["Name"] for d in data if "Name" in d), None)
    
#     jsonpath_expr = parse('$..RequiredCommodityClassification[*].ItemClassificationCode')
#     codes = [match.value for match in jsonpath_expr.find(data)]

#     ## Extraccion de datos geograficos    
#     # data = info["ProcurementProject"][0]  # accede a la lista interna
#     # name = next((d["Name"] for d in data if "Name" in d), None)
#     country_expr = parse('$..RealizedLocation[*].CountrySubentity')
#     city_res = [match.value for match in country_expr.find(data)]#[0]
#     # print("RESULTADO SOBRE EXTRACCION CIUDADES",city_res)
#     data_01= json_data["ContractFolderStatus"][0]
#     entidades_expr = parse('$..ParentLocatedParty[*].PartyName[*].Name')
#     entidades_res = [match.value for match in entidades_expr.find(data_01)]#[0]
#     # print("RESULTADO SOBRE EXTRACCION ENTIDADES", entidades_res)
#     ID_expr = parse('$..ContractFolderID')
#     ID_res = [match.value for match in ID_expr.find(data_01)]#[0]
#     # print("RESULTADO SOBRE EXTRACCION ID", ID_res)
#     print("-----" * 100)
#     print("Entidades", entidades_res)
#     jerarquia_path = entidades_res[-2]
#     if len(entidades_res)>=3:
#         sub_jerarquia_path = entidades_res[-3]
#     else:
#         sub_jerarquia_path = None
    
#     ciudades_parser = parse('$..CityName')
#     city_aux = [match.value for match in ciudades_parser.find(data_01)]#[0]
#     if isinstance(city_aux, list):
#         city_aux = city_aux[0]
#     if jerarquia_path == "ENTIDADES LOCALES":
#         ubicacion_aux = sub_jerarquia_path
#     else:
#         ubicacion_aux = city_aux
#     # folder_path = os.path.join(base_dir,jerarquia_path,sub_jerarquia_path, title_clean)

    
#     # Guardar en lista de registros
#     registros.append({
#         "ID": id_,
#         "ENTIDAD": entidad,
#         "CPV": codes,
#         "IMPORTE": importe,
#         "ESTADO": estado,
#         "NOMBRE_PROYECTO": name,
#         "FECHA_PUBLICACION": fecha_publicacion,
#         "FECHA_ACTUALIZACION": updated,
#         "FECHA_LIMITE": fecha_limite,
#         "SECTOR_PUBLICO":jerarquia_path,
#         "UBICACION":ubicacion_aux,
#         "URL": link,
#     })
    
#     df = pd.DataFrame(registros)
    
#     # TendererQualificationRequest
#     if len(json_data["TendererQualificationRequest"]) > 0:
#         tenderer = extraccion_tenderer(json_data['TendererQualificationRequest'][0], id_)
#     else:
#         tenderer = pd.DataFrame([])
    
#     # AwardingTerms
#     if len(json_data["AwardingTerms"]) > 0:
#         awarding = extraccion_awarding(json_data["AwardingTerms"][0], id_)
#     else:
#         awarding = pd.DataFrame([])
    
#     # Documentos
#     docs = extraccion_docs(json_data, id_)

#     # Solo intentamos extraer si el estado es ADJ (Adjudicada) o RES (Resuelta)
#     if estado.strip() in ['ADJ', 'RES']:
#         print(f"🔎 Detectada licitación resuelta/adjudicada: {id_}. Extrayendo detalles...")
#         df_adjudicatarios = extraer_info_adjudicacion(link, id_)
#     else:
#         df_adjudicatarios = pd.DataFrame()

#     return df, tenderer, awarding, docs, df_adjudicatarios


# def extraccion_tenderer(info_tenderer, id):
#     """Extrae criterios técnicos, financieros y requisitos específicos."""
#     registros = []
    
#     jsonpath_expr_data = parse('$..TechnicalEvaluationCriteria[*]')
#     technical_criteria = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
#     jsonpath_expr_data = parse('$..FinancialEvaluationCriteria[*]')
#     financial_criteria = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
#     jsonpath_expr_data = parse('$..SpecificTendererRequirement[*]')
#     specific_tendering = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
#     if len(technical_criteria) > 0:
#         for i in range(int(len(technical_criteria) / 2)):
#             descripcion = list(technical_criteria[(i * 2) + 1].values())[0]
#             code_type = list(technical_criteria[(i * 2)].values())[0]
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": "Criterios Tecnicos",
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type
#             })
    
#     if len(financial_criteria) > 0:
#         for i in range(int(len(financial_criteria) / 2)):
#             descripcion = list(financial_criteria[(i * 2) + 1].values())[0]
#             code_type = list(financial_criteria[(i * 2)].values())[0]
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": "Criterios Financieros",
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type
#             })
    
#     if len(specific_tendering) > 0:
#         for i in range(int(len(specific_tendering) / 2)):
#             descripcion = list(specific_tendering[(i * 2) + 1].values())[0]
#             code_type = list(specific_tendering[(i * 2)].values())[0]
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": "Requisitos",
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type
#             })
    
#     return pd.DataFrame(registros)


# def extraccion_awarding(info_awarding, id):
#     """Extrae criterios de adjudicación."""
#     registros = []
    
#     for sub_info in info_awarding:
#         for criterio in sub_info.values():
#             for criter in criterio:
#                 tipo = None
#                 descripcion = None
#                 code_type = None
#                 weight_numeric = None
#                 notas = None
                
#                 if list(criter.keys())[0] == "Description":
#                     descripcion = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["RequirementTypeCode", "EvaluationCriteriaTypeCode", "AwardingCriteriaSubTypeCode"]:
#                     code_type = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["AwardingCriteriaTypeCode"]:
#                     tipo = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["WeightNumeric"]:
#                     weight_numeric = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["Note"]:
#                     notas = list(criter.values())[0]
            
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": tipo,
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type,
#                 "PESO": weight_numeric,
#                 "NOTAS": notas,
#             })
    
#     return pd.DataFrame(registros)


# def extraccion_docs(info_docs, id):
#     """Extrae documentación legal, técnica y adicional."""
#     registros = []
    
#     legal_expr_data = parse('$..LegalDocumentReference[*]')
#     legal_document = [match.value for match in legal_expr_data.find(info_docs)]
    
#     additional_expr_data = parse('$..AdditionalDocumentReference[*]')
#     additional_document = [match.value for match in additional_expr_data.find(info_docs)]
    
#     technical_expr_data = parse('$..TechnicalDocumentReference[*]')
#     technical_document = [match.value for match in technical_expr_data.find(info_docs)]
    
#     tipos = {
#         "Documentacion Legal": legal_document,
#         "Documentacion Adicional": additional_document,
#         "Documentacion Tecnica": technical_document
#     }
    
#     for tipo, documentos in tipos.items():
#         for doc in documentos:
#             if isinstance(doc, list):
#                 ids_extraidos = []
#                 uris_extraidos = []
#                 for elemento in doc:
#                     if isinstance(elemento, dict):
#                         id_data = parse('$..ID[*]')
#                         ids = [match.value for match in id_data.find(elemento)]
#                         URI_data = parse('$..URI[*]')
#                         uris = [match.value for match in URI_data.find(elemento)]
                        
#                         if ids:
#                             ids_extraidos.extend(ids)
#                         if uris:
#                             uris_extraidos.extend(uris)
                
#                 for i in range(max(len(ids_extraidos), len(uris_extraidos))):
#                     descripcion = ids_extraidos[i] if i < len(ids_extraidos) else None
#                     uri = uris_extraidos[i] if i < len(uris_extraidos) else None
                    
#                     if descripcion or uri:
#                         registros.append({
#                             "pliego_id": id,
#                             "TIPO": tipo,
#                             "DESCRIPCION": descripcion,
#                             "URI": uri,
#                             "CODIGO_TIPO": tipo.split()[-1],
#                         })
            
#             elif isinstance(doc, dict) and 'ID' in doc:
#                 registros.append({
#                     "pliego_id": id,
#                     "TIPO": tipo,
#                     "DESCRIPCION": doc.get('ID'),
#                     "URI": doc.get('URI'),
#                     "CODIGO_TIPO": tipo.split()[-1],
#                 })
    
#     return pd.DataFrame(registros)


# #Metodo para extraer informacion de las adjudicadas.

# def extraer_info_adjudicacion(url_licitacion, id_pliego):
#     """
#     Accede a la URL de la licitación, busca el XML de adjudicación y extrae 
#     los datos del adjudicatario sin guardar archivos en disco.
#     """
#     try:
#         headers = {'User-Agent': 'Mozilla/5.0'}
#         response = requests.get(url_licitacion, headers=headers, timeout=20)
#         if response.status_code != 200: 
#             print(f"⚠️ Error al acceder a la URL: {response.status_code}")
#             return pd.DataFrame()

#         soup = BeautifulSoup(response.content, 'html.parser')
#         tabla = soup.find('table', {'id': 'myTablaDetalleVISUOE'})
#         if not tabla: 
#             print(f"⚠️ No se encontró la tabla de documentos")
#             return pd.DataFrame()

#         registros_adj = []
#         filas = tabla.find('tbody').find_all('tr')
#         print('FILAS',filas)
        
#         for fila in filas:
#             tipo_doc = fila.find('td', class_='tipoDocumento')
#             if tipo_doc and 'Adjudicaci' in tipo_doc.get_text():
#                 enlaces_xml = fila.find_all('a', href=True)

#                 for enlace_xml in enlaces_xml:

#                     img_xml = enlace_xml.find('img', alt='Documento xml') if enlace_xml else None
#                     print('IMAGE',img_xml)
                    
#                     if img_xml:
#                         url_xml = urljoin('https://contrataciondelestado.es', enlace_xml['href'])
#                         print(f"📥 Descargando XML de adjudicación desde: {url_xml}")
                        
#                         # Descarga el XML a memoria
#                         xml_res = requests.get(url_xml, headers=headers, timeout=20)
#                         root = etree.fromstring(xml_res.content)
                        
#                         # IMPORTANTE: Detectar el namespace correcto automáticamente
#                         # Pueden ser de dos tipos diferentes de XMLs
#                         namespaces_codice = {
#                             'cac': 'urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2',
#                             'cbc': 'urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2'
#                         }
                        
#                         namespaces_oasis = {
#                             'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
#                             'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
#                         }
                        
#                         # Intentar detectar cuál namespace usar
#                         # Buscar todos los WinningParty
#                         # winning_parties = root.findall('.//cac:WinningParty', namespaces_codice)
#                         # print(winning_parties)
#                         winning_parties = root.findall('.//cac:WinningParty', namespaces_oasis)
#                         print(winning_parties)
#                         ns = namespaces_codice
#                         test_element = root.find('.//{urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2}TenderResult')
#                         if test_element is None:
#                             ns = namespaces_oasis
#                             print("📋 Usando namespace OASIS")
#                         else:
#                             print("📋 Usando namespace CODICE")
                        
#                         # Buscar todos los TenderResult
#                         tender_results = root.findall('.//cac:TenderResult', ns)
#                         print(f"🔍 Encontrados {len(tender_results)} TenderResult")
                        
#                         for idx, tender_result in enumerate(tender_results, 1):
#                             print(f"   Procesando TenderResult #{idx}")
                            
#                             # Extraer importes de adjudicación
#                             legal_monetary = tender_result.find('.//cac:AwardedTenderedProject/cac:LegalMonetaryTotal', ns)
#                             importe_sin_iva = None
#                             importe_con_iva = None
                            
#                             if legal_monetary is not None:
#                                 tax_exclusive = legal_monetary.find('cbc:TaxExclusiveAmount', ns)
#                                 payable_amount = legal_monetary.find('cbc:PayableAmount', ns)
                                
#                                 if tax_exclusive is not None:
#                                     importe_sin_iva = tax_exclusive.text
#                                     print(f"      💰 Importe sin IVA: {importe_sin_iva}€")
#                                 if payable_amount is not None:
#                                     importe_con_iva = payable_amount.text
#                                     print(f"      💰 Importe con IVA: {importe_con_iva}€")
                            
#                             # Extraer información del adjudicatario
#                             winning_party = tender_result.find('.//cac:WinningParty', ns)
                            
#                             if winning_party is not None:
#                                 # Datos básicos
#                                 nif_elem = winning_party.find('.//cac:PartyIdentification/cbc:ID', ns)
#                                 nombre_elem = winning_party.find('.//cac:PartyName/cbc:Name', ns)
                                
#                                 # Datos de contacto - ACTUALIZADO para buscar en AgentParty
#                                 telefono_elem = winning_party.find('.//cac:AgentParty/cac:Contact/cbc:Telephone', ns)
#                                 email_elem = winning_party.find('.//cac:AgentParty/cac:Contact/cbc:ElectronicMail', ns)
                                
#                                 # Si no se encuentran en AgentParty, buscar en Contact directo
#                                 if telefono_elem is None:
#                                     telefono_elem = winning_party.find('.//cac:Contact/cbc:Telephone', ns)
#                                 if email_elem is None:
#                                     email_elem = winning_party.find('.//cac:Contact/cbc:ElectronicMail', ns)
                                
#                                 nif = nif_elem.text if nif_elem is not None else None
#                                 nombre = nombre_elem.text if nombre_elem is not None else None
#                                 telefono = telefono_elem.text if telefono_elem is not None else None
#                                 email = email_elem.text if email_elem is not None else None
                                
#                                 registro = {
#                                     "pliego_id": id_pliego,
#                                     "NIF_ADJUDICATARIO": nif,
#                                     "NOMBRE_ADJUDICATARIO": nombre,
#                                     "TELEFONO": telefono,
#                                     "EMAIL": email,
#                                     "IMPORTE_SIN_IVA": importe_sin_iva,
#                                     "IMPORTE_CON_IVA": importe_con_iva,
#                                     "FECHA_EXTRACCION": datetime.now().strftime("%Y-%m-%d")
#                                 }
                                
#                                 registros_adj.append(registro)
#                                 print(f"      ✅ Adjudicatario: {nombre}")
#                                 print(f"         NIF: {nif}")
#                                 print(f"         Tel: {telefono}")
#                                 print(f"         Email: {email}")
        
#         if registros_adj:
#             print(f"✅ Total adjudicatarios extraídos: {len(registros_adj)}")
#             return pd.DataFrame(registros_adj)
#         else:
#             print(f"ℹ️ No se encontraron adjudicatarios en el XML")
#             return pd.DataFrame()
            
#     except requests.Timeout:
#         print(f"⚠️ Timeout al intentar acceder a {url_licitacion}")
#         return pd.DataFrame()
#     except etree.XMLSyntaxError as e:
#         print(f"⚠️ Error al parsear XML de adjudicación para {id_pliego}: {e}")
#         return pd.DataFrame()
#     except Exception as e:
#         print(f"⚠️ Error general en extracción de adjudicación para {id_pliego}: {e}")
#         traceback.print_exc()
#         return pd.DataFrame()

# # def extraer_info_adjudicacion(url_licitacion, id_pliego):
# #     """
# #     Accede a la URL de la licitación, busca el XML de adjudicación y extrae 
# #     los datos del adjudicatario sin guardar archivos en disco.
# #     """
# #     try:
# #         headers = {'User-Agent': 'Mozilla/5.0'}
# #         response = requests.get(url_licitacion, headers=headers, timeout=20)
# #         if response.status_code != 200: return pd.DataFrame()

# #         soup = BeautifulSoup(response.content, 'html.parser')
# #         tabla = soup.find('table', {'id': 'myTablaDetalleVISUOE'})
# #         if not tabla: return pd.DataFrame()

# #         registros_adj = []
# #         filas = tabla.find('tbody').find_all('tr')
        
# #         for fila in filas:
# #             tipo_doc = fila.find('td', class_='tipoDocumento')
# #             if tipo_doc and 'Adjudicaci' in tipo_doc.get_text():
# #                 enlace_xml = fila.find('a', href=True)
# #                 img_xml = enlace_xml.find('img', alt='Documento xml') if enlace_xml else None
                
# #                 if img_xml:
# #                     url_xml = urljoin('https://contrataciondelestado.es', enlace_xml['href'])
# #                     # Descarga el XML a memoria
# #                     xml_res = requests.get(url_xml, headers=headers, timeout=20)
# #                     root = etree.fromstring(xml_res.content)
                    
# #                     # Namespaces para búsqueda
# #                     ns = {'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
# #                           'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}
                    
# #                     winning_parties = root.findall('.//cac:WinningParty', ns)
# #                     for party in winning_parties:
# #                         nif = party.find('.//cac:PartyIdentification/cbc:ID', ns)
# #                         nombre = party.find('.//cac:PartyName/cbc:Name', ns)
                        
# #                         registros_adj.append({
# #                             "pliego_id": id_pliego,
# #                             "NIF_ADJUDICATARIO": nif.text if nif is not None else None,
# #                             "NOMBRE_ADJUDICATARIO": nombre.text if nombre is not None else None,
# #                             "FECHA_EXTRACCION": datetime.now().strftime("%Y-%m-%d")
# #                         })
# #         return pd.DataFrame(registros_adj)
# #     except Exception as e:
# #         print(f"⚠️ Error en extracción de adjudicación para {id_pliego}: {e}")
# #         return pd.DataFrame()


# # ============================================================================
# # FUNCIONES DE GESTIÓN DE ESTADO INCREMENTAL
# # ============================================================================

# def cargar_dataframes_existentes():
#     """Carga los DataFrames existentes si existen, sino crea vacíos."""
#     dfs = {}
#     archivos = {
#         'general': f"{DATA_DIR}/Pliegos_general.parquet",
#         'tendering': f"{DATA_DIR}/Requisitos_general.parquet",
#         'awarding': f"{DATA_DIR}/Criterios_general.parquet",
#         'docs': f"{DATA_DIR}/Documentacion_general.parquet",
#         'df_adjudicatarios': f"{DATA_DIR}/Adjudicatarios_general.parquet"
#     }
    
#     for key, archivo in archivos.items():
#         if os.path.exists(archivo):
#             dfs[key] = pd.read_parquet(archivo, engine="pyarrow")
#             print(f"✅ Cargado {key}: {len(dfs[key])} registros existentes")
#         else:
#             dfs[key] = pd.DataFrame()
#             print(f"ℹ️  Creando nuevo DataFrame para {key}")
    
#     return dfs['general'], dfs['tendering'], dfs['awarding'], dfs['docs'], dfs['df_adjudicatarios']


# def obtener_ultimo_feed_procesado():
#     """Lee el último feed procesado desde el archivo de checkpoint."""
#     if os.path.exists(CHECKPOINT_FILE):
#         with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
#             ultimo_feed = f.read().strip()
#             if ultimo_feed:
#                 print(f"📍 Último feed procesado: {ultimo_feed}")
#                 return ultimo_feed
#     print("📍 No hay checkpoint previo, procesando desde el inicio")
#     return None


# def guardar_checkpoint(nombre_feed):
#     """Guarda el nombre del último feed procesado."""
#     with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
#         f.write(nombre_feed)


# def actualizar_o_insertar_licitacion(df_existente, df_nuevo):
#     """
#     Actualiza registros existentes o inserta nuevos basándose en el ID.
#     Conserva todas las licitaciones, incluyendo las de estado terminal.
#     """
#     if df_existente.empty:
#         return df_nuevo
    
#     if df_nuevo.empty:
#         return df_existente
    
#     # Identificar IDs nuevos
#     ids_nuevos = df_nuevo['ID'].values
    
#     for id_nuevo in ids_nuevos:
#         registro_nuevo = df_nuevo[df_nuevo['ID'] == id_nuevo]
#         estado_nuevo = registro_nuevo['ESTADO'].values[0].strip()
        
#         # Si existe, actualizar (conservando todas las licitaciones)
#         if id_nuevo in df_existente['ID'].values:
#             estado_anterior = df_existente[df_existente['ID'] == id_nuevo]['ESTADO'].values[0]
#             print(f"🔄 Actualizando licitación {id_nuevo}: {estado_anterior} → {estado_nuevo}")
#             df_existente = df_existente[df_existente['ID'] != id_nuevo]
#             df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
#         else:
#             # Si no existe, insertar
#             print(f"✨ Nueva licitación {id_nuevo} - Estado: {estado_nuevo}")
#             df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
    
#     return df_existente


# def actualizar_tablas_relacionadas(df_existente, df_nuevo, id_column='pliego_id'):
#     """
#     Actualiza tablas relacionadas (requisitos, criterios, docs).
#     Elimina registros relacionados con IDs que ya no existen.
#     """
#     if df_existente.empty:
#         return df_nuevo
    
#     if df_nuevo.empty:
#         return df_existente
    
#     # Identificar IDs en la nueva carga
#     ids_nuevos = df_nuevo[id_column].unique()
    
#     for id_nuevo in ids_nuevos:
#         # Eliminar registros antiguos del mismo ID
#         if id_nuevo in df_existente[id_column].values:
#             print(f"🔄 Actualizando registros relacionados para {id_nuevo}")
#             df_existente = df_existente[df_existente[id_column] != id_nuevo]
        
#         # Agregar nuevos registros
#         registros_nuevos = df_nuevo[df_nuevo[id_column] == id_nuevo]
#         df_existente = pd.concat([df_existente, registros_nuevos], ignore_index=True)
    
#     return df_existente


# # ============================================================================
# # FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# # ============================================================================

# def procesar_feed(feed_url, df_general, df_tendering, df_awarding, df_docs, df_adjudicaciones):
#     """Procesa un feed ATOM y acumula los datos en los DataFrames proporcionados."""
    
#     r = requests.get(feed_url, timeout=60)
#     r.raise_for_status()
#     root = etree.fromstring(r.content, parser=parser)
    
#     entries = root.xpath("//atom:entry", namespaces={"atom": "http://www.w3.org/2005/Atom"})
#     print(f"Entradas encontradas en el feed: {len(entries)}")
    
#     claves = [
#         "summary", "updated", "AwardingTerms", "TenderingTerms",
#         "RequiredFinancialGuarantee", "ContractFolderStatus",
#         "TendererQualificationRequest", "ExternalReference",
#         "ProcurementProject", "Party", "ProcurementProjectLot",
#         "ExternalData", "AdditionalDocumentReference",
#         "LegalDocumentReference", "TechnicalDocumentReference",
#         "TenderSubmissionDeadlinePeriod",
#     ]
    
#     # DataFrames temporales para este feed
#     df_general_temp = pd.DataFrame()
#     df_tendering_temp = pd.DataFrame()
#     df_awarding_temp = pd.DataFrame()
#     df_docs_temp = pd.DataFrame()
#     df_adjudicatarios_temp = pd.DataFrame()
    
#     for i, entry in enumerate(entries, start=1):
#         # Metadatos ATOM
#         summary = entry.xpath("string(atom:summary)", namespaces={"atom": "http://www.w3.org/2005/Atom"}).strip()
#         enlace = entry.xpath("string(atom:link/@href)", namespaces={"atom": "http://www.w3.org/2005/Atom"})
        
#         print('-' * 100)
#         print(f"Procesando entrada {i}: {summary[:80]}...")
        
#         # Extraer información del XML
#         dict_info = extraer_info(entry, claves)
#         dict_info['link'] = enlace
        
#         try:
#             # Procesar directamente en memoria
#             df_temp, df_tend, df_award, df_doc, df_adjudicatarios = extraccion_data_relevante(dict_info)
            
#             # Acumular en temporales de este feed
#             df_general_temp = pd.concat([df_general_temp, df_temp], ignore_index=True)
#             df_tendering_temp = pd.concat([df_tendering_temp, df_tend], ignore_index=True)
#             df_awarding_temp = pd.concat([df_awarding_temp, df_award], ignore_index=True)
#             df_docs_temp = pd.concat([df_docs_temp, df_doc], ignore_index=True)
#             df_adjudicatarios_temp = pd.concat([df_adjudicatarios_temp, df_adjudicatarios], ignore_index=True)
            
#             print(f"✅ Procesado correctamente")
            
#         except Exception as e:
#             print(f"⚠️ Error procesando entrada {i}: {e}")
#             traceback.print_exc()
    
#     # Actualizar DataFrames principales con lógica incremental
#     print("\n" + "=" * 100)
#     print("Actualizando base de datos...")
#     df_general = actualizar_o_insertar_licitacion(df_general, df_general_temp)
#     df_tendering = actualizar_tablas_relacionadas(df_tendering, df_tendering_temp)
#     df_awarding = actualizar_tablas_relacionadas(df_awarding, df_awarding_temp)
#     df_docs = actualizar_tablas_relacionadas(df_docs, df_docs_temp)
#     df_adjudicatarios = actualizar_tablas_relacionadas(df_adjudicatarios, df_adjudicatarios_temp)
    
#     return df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios


# def natural_sort_key(s):
#     """Ordena strings con números de forma natural."""
#     return [int(text) if text.isdigit() else text
#             for text in re.split(r'(\d+)', s)]


# def main():
#     """Función principal que coordina todo el proceso incremental."""
    
#     # Crear directorio de datos si no existe
#     os.makedirs(DATA_DIR, exist_ok=True)
    
#     # Cargar DataFrames existentes
#     print("=" * 100)
#     print("Cargando datos existentes...")
#     print("=" * 100)
#     df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios = cargar_dataframes_existentes()
    
#     # Obtener último feed procesado
#     ultimo_feed = obtener_ultimo_feed_procesado()
    
#     # Descargar y descomprimir el ZIP
#     print("\n" + "=" * 100)
#     print(f"Descargando ZIP desde {FEEDZIP}...")
#     print("=" * 100)
#     response = requests.get(FEEDZIP)
#     zip_data = zipfile.ZipFile(io.BytesIO(response.content))
    
#     # Ordenar archivos del ZIP
#     feed_base = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
#     zip_data_sorted = sorted(zip_data.namelist(), key=natural_sort_key)
#     zip_data_sorted.append(zip_data_sorted.pop(0))
    
#     # Determinar desde dónde empezar a procesar
#     # ultimo_feed = 'licitacionesPerfilesContratanteCompleto3_20251207_170155.atom' ## Para pruebas rapidas
#     comenzar = (ultimo_feed is None)
#     feeds_procesados = 0
    
#     # Redirigir salida a archivo
#     with open(LOG_FILE, "a", encoding="utf-8") as f:
#         with redirect_stdout(f):
#             print(f"\n{'=' * 100}")
#             print(f"Inicio de procesamiento: {datetime.now()}")
#             print('=' * 100)
            
#             for fin_feed in zip_data_sorted:
#                 # Si ya procesamos este feed, saltar hasta encontrar el siguiente
#                 if not comenzar:
#                     if fin_feed == ultimo_feed:
#                         comenzar = True
#                         print(f"⏭️  Saltando {fin_feed} (ya procesado)")
#                         continue
#                     else:
#                         continue
                
#                 print(f"\n{'=' * 100}")
#                 print(f"Procesando archivo: {fin_feed}")
#                 print('=' * 100)
                
#                 FEED = feed_base + fin_feed
                
#                 try:
#                     df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios = procesar_feed(
#                         FEED, df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios
#                     )

#                     # Gestor de alertas
#                     df_general_temp = df_general.copy()
#                     if not df_general_temp.empty:
#                         gestor_alertas = Gestor_Alertas(
#                             archivo_usuarios="usuarios.json",
#                             archivo_alertas="alertas.json"
#                         )
#                         gestor_alertas.procesar_nuevas_licitaciones(df_general_temp)
                    
#                     # Guardar checkpoint después de cada feed
                    
#                     if fin_feed != "licitacionesPerfilesContratanteCompleto3.atom":
#                         guardar_checkpoint(fin_feed)
#                     feeds_procesados += 1
                    
#                     # Guardar DataFrames periódicamente (cada 5 feeds)
#                     if feeds_procesados % 5 == 0:
#                         print("\n💾 Guardando progreso intermedio...")
#                         guardar_dataframes(df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios)
                    
#                 except Exception as e:
#                     print(f"❌ Error crítico procesando {fin_feed}: {e}")
#                     traceback.print_exc()
#                     continue
            
#             print(f"\n{'=' * 100}")
#             print(f"Fin de procesamiento: {datetime.now()}")
#             print(f"Feeds procesados en esta ejecución: {feeds_procesados}")
#             print('=' * 100)
    
#     # Guardar DataFrames finales
#     print("\n" + "=" * 100)
#     print("Guardando resultados finales en archivos Parquet...")
#     print("=" * 100)
#     guardar_dataframes(df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios)
    
#     print(f"\n✅ Proceso completado exitosamente!")
#     print(f"📊 Total de registros en base de datos:")
#     print(f"   - Pliegos generales: {len(df_general)}")
#     print(f"   - Requisitos: {len(df_tendering)}")
#     print(f"   - Criterios: {len(df_awarding)}")
#     print(f"   - Documentos: {len(df_docs)}")
#     print(f"   - Empresas Adjudicatarias: {len(df_adjudicatarios)}")
#     print(f"   - Feeds procesados: {feeds_procesados}")


# def guardar_dataframes(df_general, df_tendering, df_awarding, df_docs, df_adjudicatarios):
#     """Guarda los DataFrames en archivos Parquet."""
#     df_general.to_parquet(f"{DATA_DIR}/Pliegos_general.parquet", index=False, engine="pyarrow")
#     df_tendering.to_parquet(f"{DATA_DIR}/Requisitos_general.parquet", index=False, engine="pyarrow")
#     df_awarding.to_parquet(f"{DATA_DIR}/Criterios_general.parquet", index=False, engine="pyarrow")
#     ##Primero haré un borrado de todos los NAN/NONE 
#     df_docs = df_docs.dropna()
#     df_docs.to_parquet(f"{DATA_DIR}/Documentacion_general.parquet", index=False, engine="pyarrow")
#     df_adjudicatarios.to_parquet(f"{DATA_DIR}/Adjudicatarios_general.parquet", index=False, engine="pyarrow")
#     print("✅ DataFrames guardados correctamente")


# if __name__ == "__main__":
#     main()

#-----------------------------------------------------------------------
# import requests
# from lxml import etree
# import sys
# from contextlib import redirect_stdout
# from pathlib import Path
# from jsonpath_ng.ext import parse
# import os
# import json
# import re
# from urllib.parse import urlparse, unquote
# import zipfile
# import io
# import pandas as pd
# import traceback
# from datetime import datetime, date
# import sqlalchemy
# from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Text, Float, DateTime, Integer
# from sqlalchemy.dialects.mysql import LONGTEXT
# import pymysql

# # ============================================================================
# # CONFIGURACIÓN DE BASE DE DATOS
# # ============================================================================

# # Configuración de conexión a MariaDB
# DB_CONFIG = {
#     'host': os.getenv('DB_HOST', 'localhost'),
#     'port': int(os.getenv('DB_PORT', 3306)),
#     'user': os.getenv('DB_USER', 'root'),
#     'password': os.getenv('DB_PASSWORD', ''),
#     'database': os.getenv('DB_NAME', 'licitaciones_db'),
#     'charset': 'utf8mb4'
# }

# # Configuración inicial
# FEED = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"
# FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202512.zip"
# parser = etree.XMLParser(recover=True)

# # Rutas de archivos
# DATA_DIR = "src/data"
# CHECKPOINT_FILE = "ultimo_feed_procesado.txt"
# LOG_FILE = "extraccion_mensual.txt"

# # ============================================================================
# # FUNCIONES DE CONEXIÓN A BASE DE DATOS
# # ============================================================================

# def crear_engine():
#     """Crea el engine de SQLAlchemy para conectar con MariaDB."""
#     connection_string = (
#         f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
#         f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
#         f"?charset={DB_CONFIG['charset']}"
#     )
#     engine = create_engine(connection_string, pool_pre_ping=True, pool_recycle=3600)
#     return engine

# def crear_tablas(engine):
#     """Crea las tablas en la base de datos si no existen."""
#     metadata = MetaData()
    
#     # Tabla principal de pliegos
#     pliegos = Table(
#         'pliegos_general', metadata,
#         Column('ID', String(100), primary_key=True),
#         Column('ENTIDAD', Text),
#         Column('CPV', Text),  # Almacenaremos como JSON string
#         Column('IMPORTE', String(50)),
#         Column('ESTADO', String(100)),
#         Column('NOMBRE_PROYECTO', Text),
#         Column('FECHA_PUBLICACION', String(50)),
#         Column('FECHA_ACTUALIZACION', String(50)),
#         Column('FECHA_LIMITE', String(50)),
#         Column('SECTOR_PUBLICO', String(200)),
#         Column('UBICACION', String(200)),
#         Column('URL', Text),
#         Column('fecha_carga', DateTime, default=datetime.now),
#         mysql_charset='utf8mb4'
#     )
    
#     # Tabla de requisitos/criterios técnicos y financieros
#     requisitos = Table(
#         'requisitos_general', metadata,
#         Column('id', Integer, primary_key=True, autoincrement=True),
#         Column('pliego_id', String(100)),
#         Column('TIPO', String(100)),
#         Column('DESCRIPCION', Text),
#         Column('CODIGO_TIPO', String(100)),
#         Column('fecha_carga', DateTime, default=datetime.now),
#         mysql_charset='utf8mb4'
#     )
    
#     # Tabla de criterios de adjudicación
#     criterios = Table(
#         'criterios_general', metadata,
#         Column('id', Integer, primary_key=True, autoincrement=True),
#         Column('pliego_id', String(100)),
#         Column('TIPO', String(100)),
#         Column('DESCRIPCION', Text),
#         Column('CODIGO_TIPO', String(100)),
#         Column('PESO', String(50)),
#         Column('NOTAS', Text),
#         Column('fecha_carga', DateTime, default=datetime.now),
#         mysql_charset='utf8mb4'
#     )
    
#     # Tabla de documentación
#     documentacion = Table(
#         'documentacion_general', metadata,
#         Column('id', Integer, primary_key=True, autoincrement=True),
#         Column('pliego_id', String(100)),
#         Column('TIPO', String(100)),
#         Column('DESCRIPCION', Text),
#         Column('URI', Text),
#         Column('CODIGO_TIPO', String(100)),
#         Column('fecha_carga', DateTime, default=datetime.now),
#         mysql_charset='utf8mb4'
#     )
    
#     # Crear todas las tablas
#     metadata.create_all(engine)
#     print("✅ Tablas creadas o verificadas en la base de datos")

# # ============================================================================
# # FUNCIONES DE EXTRACCIÓN XML -> DICT (Sin cambios)
# # ============================================================================

# def recorrer_xml(nodo):
#     """Recorre un nodo XML y devuelve una estructura anidada tipo dict."""
#     tag = etree.QName(nodo).localname
#     texto = nodo.text.strip() if nodo.text and nodo.text.strip() else None

#     if len(nodo) == 0:
#         return {tag: texto}

#     contenido = []
#     for hijo in nodo:
#         contenido.append(recorrer_xml(hijo))

#     if texto:
#         contenido.insert(0, {"_text": texto})

#     return {tag: contenido}


# def extraer_info(xml_root, claves_interes):
#     """Recorre el XML y extrae solo las secciones relevantes (por etiqueta)."""
#     info = {k: [] for k in claves_interes}

#     for elem in xml_root.iter():
#         tag = etree.QName(elem).localname
#         if tag in claves_interes:
#             info[tag].append(recorrer_xml(elem)[tag])

#     return info


# # ============================================================================
# # FUNCIONES DE PROCESAMIENTO JSON -> DATAFRAMES (Sin cambios significativos)
# # ============================================================================

# def extraccion_data_relevante(json_data):
#     """Extrae información relevante del JSON y genera DataFrames."""
#     registros = []
#     fecha_limite = None
#     fecha_publicacion = None
    
#     # Summary
#     datos = json_data['summary'][0].split(";")
    
#     # Link
#     try:
#         link = json_data["link"]
#     except:
#         link = "https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
    
#     # Updated
#     updated = json_data["updated"][0]
    
#     for i in range(len(datos)):
#         datos[i] = datos[i].split(":")[1]
    
#     id_, entidad, importe, estado = datos
    
#     # Fecha límite
#     jsonpath_expr_data = parse('$..TenderSubmissionDeadlinePeriod[*].EndDate')
#     fecha_res = [match.value for match in jsonpath_expr_data.find(json_data)]
#     if len(fecha_res) > 0:
#         fecha_limite = fecha_res[0]
    
#     # Fecha publicación
#     jsonpath_expr_date = parse('$..IssueDate')
#     fecha_pub_res = [match.value for match in jsonpath_expr_date.find(json_data)]
#     if fecha_pub_res:
#         fecha_publicacion = fecha_pub_res[0]
#         print(f"📅 Fecha de publicación encontrada: {fecha_publicacion}")
    
#     # ProcurementProject
#     data = json_data["ProcurementProject"][0]
#     name = next((d["Name"] for d in data if "Name" in d), None)
    
#     jsonpath_expr = parse('$..RequiredCommodityClassification[*].ItemClassificationCode')
#     codes = [match.value for match in jsonpath_expr.find(data)]

#     ## Extraccion de datos geograficos    
#     # data = info["ProcurementProject"][0]  # accede a la lista interna
#     # name = next((d["Name"] for d in data if "Name" in d), None)
#     country_expr = parse('$..RealizedLocation[*].CountrySubentity')
#     city_res = [match.value for match in country_expr.find(data)]#[0]
#     # print("RESULTADO SOBRE EXTRACCION CIUDADES",city_res)
#     data_01= json_data["ContractFolderStatus"][0]
#     entidades_expr = parse('$..ParentLocatedParty[*].PartyName[*].Name')
#     entidades_res = [match.value for match in entidades_expr.find(data_01)]#[0]
#     # print("RESULTADO SOBRE EXTRACCION ENTIDADES", entidades_res)
#     ID_expr = parse('$..ContractFolderID')
#     ID_res = [match.value for match in ID_expr.find(data_01)]#[0]
#     # print("RESULTADO SOBRE EXTRACCION ID", ID_res)
#     print("-----" * 100)
#     print("Entidades", entidades_res)
#     jerarquia_path = entidades_res[-2]
#     if len(entidades_res)>=3:
#         sub_jerarquia_path = entidades_res[-3]
#     else:
#         sub_jerarquia_path = None
    
#     ciudades_parser = parse('$..CityName')
#     city_aux = [match.value for match in ciudades_parser.find(data_01)]#[0]
#     if isinstance(city_aux, list):
#         city_aux = city_aux[0]
#     if jerarquia_path == "ENTIDADES LOCALES":
#         ubicacion_aux = sub_jerarquia_path
#     else:
#         ubicacion_aux = city_aux
#     # folder_path = os.path.join(base_dir,jerarquia_path,sub_jerarquia_path, title_clean)
    
#     # Guardar en lista de registros
#     registros.append({
#         "ID": id_,
#         "ENTIDAD": entidad,
#         "CPV": json.dumps(codes),  # Convertir lista a JSON string
#         "IMPORTE": importe,
#         "ESTADO": estado,
#         "NOMBRE_PROYECTO": name,
#         "FECHA_PUBLICACION": fecha_publicacion,
#         "FECHA_ACTUALIZACION": updated,
#         "FECHA_LIMITE": fecha_limite,
#         "SECTOR_PUBLICO": jerarquia_path,
#         "UBICACION": ubicacion_aux,
#         "URL": link,
#     })
    
#     df = pd.DataFrame(registros)
    
#     # TendererQualificationRequest
#     if len(json_data["TendererQualificationRequest"]) > 0:
#         tenderer = extraccion_tenderer(json_data['TendererQualificationRequest'][0], id_)
#     else:
#         tenderer = pd.DataFrame([])
    
#     # AwardingTerms
#     if len(json_data["AwardingTerms"]) > 0:
#         awarding = extraccion_awarding(json_data["AwardingTerms"][0], id_)
#     else:
#         awarding = pd.DataFrame([])
    
#     # Documentos
#     docs = extraccion_docs(json_data, id_)
    
#     return df, tenderer, awarding, docs


# def extraccion_tenderer(info_tenderer, id):
#     """Extrae criterios técnicos, financieros y requisitos específicos."""
#     registros = []
    
#     jsonpath_expr_data = parse('$..TechnicalEvaluationCriteria[*]')
#     technical_criteria = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
#     jsonpath_expr_data = parse('$..FinancialEvaluationCriteria[*]')
#     financial_criteria = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
#     jsonpath_expr_data = parse('$..SpecificTendererRequirement[*]')
#     specific_tendering = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
#     if len(technical_criteria) > 0:
#         for i in range(int(len(technical_criteria) / 2)):
#             descripcion = list(technical_criteria[(i * 2) + 1].values())[0]
#             code_type = list(technical_criteria[(i * 2)].values())[0]
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": "Criterios Tecnicos",
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type
#             })
    
#     if len(financial_criteria) > 0:
#         for i in range(int(len(financial_criteria) / 2)):
#             descripcion = list(financial_criteria[(i * 2) + 1].values())[0]
#             code_type = list(financial_criteria[(i * 2)].values())[0]
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": "Criterios Financieros",
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type
#             })
    
#     if len(specific_tendering) > 0:
#         for i in range(int(len(specific_tendering) / 2)):
#             descripcion = list(specific_tendering[(i * 2) + 1].values())[0]
#             code_type = list(specific_tendering[(i * 2)].values())[0]
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": "Requisitos",
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type
#             })
    
#     return pd.DataFrame(registros)


# def extraccion_awarding(info_awarding, id):
#     """Extrae criterios de adjudicación."""
#     registros = []
    
#     for sub_info in info_awarding:
#         for criterio in sub_info.values():
#             for criter in criterio:
#                 tipo = None
#                 descripcion = None
#                 code_type = None
#                 weight_numeric = None
#                 notas = None
                
#                 if list(criter.keys())[0] == "Description":
#                     descripcion = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["RequirementTypeCode", "EvaluationCriteriaTypeCode", "AwardingCriteriaSubTypeCode"]:
#                     code_type = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["AwardingCriteriaTypeCode"]:
#                     tipo = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["WeightNumeric"]:
#                     weight_numeric = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["Note"]:
#                     notas = list(criter.values())[0]
            
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": tipo,
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type,
#                 "PESO": weight_numeric,
#                 "NOTAS": notas,
#             })
    
#     return pd.DataFrame(registros)


# def extraccion_docs(info_docs, id):
#     """Extrae documentación legal, técnica y adicional."""
#     registros = []
    
#     legal_expr_data = parse('$..LegalDocumentReference[*]')
#     legal_document = [match.value for match in legal_expr_data.find(info_docs)]
    
#     additional_expr_data = parse('$..AdditionalDocumentReference[*]')
#     additional_document = [match.value for match in additional_expr_data.find(info_docs)]
    
#     technical_expr_data = parse('$..TechnicalDocumentReference[*]')
#     technical_document = [match.value for match in technical_expr_data.find(info_docs)]
    
#     tipos = {
#         "Documentacion Legal": legal_document,
#         "Documentacion Adicional": additional_document,
#         "Documentacion Tecnica": technical_document
#     }
    
#     for tipo, documentos in tipos.items():
#         for doc in documentos:
#             if isinstance(doc, list):
#                 ids_extraidos = []
#                 uris_extraidos = []
#                 for elemento in doc:
#                     if isinstance(elemento, dict):
#                         id_data = parse('$..ID[*]')
#                         ids = [match.value for match in id_data.find(elemento)]
#                         URI_data = parse('$..URI[*]')
#                         uris = [match.value for match in URI_data.find(elemento)]
                        
#                         if ids:
#                             ids_extraidos.extend(ids)
#                         if uris:
#                             uris_extraidos.extend(uris)
                
#                 for i in range(max(len(ids_extraidos), len(uris_extraidos))):
#                     descripcion = ids_extraidos[i] if i < len(ids_extraidos) else None
#                     uri = uris_extraidos[i] if i < len(uris_extraidos) else None
                    
#                     if descripcion or uri:
#                         registros.append({
#                             "pliego_id": id,
#                             "TIPO": tipo,
#                             "DESCRIPCION": descripcion,
#                             "URI": uri,
#                             "CODIGO_TIPO": tipo.split()[-1],
#                         })
            
#             elif isinstance(doc, dict) and 'ID' in doc:
#                 registros.append({
#                     "pliego_id": id,
#                     "TIPO": tipo,
#                     "DESCRIPCION": doc.get('ID'),
#                     "URI": doc.get('URI'),
#                     "CODIGO_TIPO": tipo.split()[-1],
#                 })
    
#     return pd.DataFrame(registros)


# # ============================================================================
# # FUNCIONES DE GESTIÓN CON BASE DE DATOS
# # ============================================================================

# def cargar_dataframes_desde_db(engine):
#     """Carga los DataFrames desde la base de datos."""
#     try:
#         df_general = pd.read_sql_table('pliegos_general', engine)
#         print(f"✅ Cargado pliegos_general: {len(df_general)} registros")
#     except:
#         df_general = pd.DataFrame()
#         print(f"ℹ️  Tabla pliegos_general vacía o no existe")
    
#     try:
#         df_tendering = pd.read_sql_table('requisitos_general', engine)
#         print(f"✅ Cargado requisitos_general: {len(df_tendering)} registros")
#     except:
#         df_tendering = pd.DataFrame()
#         print(f"ℹ️  Tabla requisitos_general vacía o no existe")
    
#     try:
#         df_awarding = pd.read_sql_table('criterios_general', engine)
#         print(f"✅ Cargado criterios_general: {len(df_awarding)} registros")
#     except:
#         df_awarding = pd.DataFrame()
#         print(f"ℹ️  Tabla criterios_general vacía o no existe")
    
#     try:
#         df_docs = pd.read_sql_table('documentacion_general', engine)
#         print(f"✅ Cargado documentacion_general: {len(df_docs)} registros")
#     except:
#         df_docs = pd.DataFrame()
#         print(f"ℹ️  Tabla documentacion_general vacía o no existe")
    
#     return df_general, df_tendering, df_awarding, df_docs


# def obtener_ultimo_feed_procesado():
#     """Lee el último feed procesado desde el archivo de checkpoint."""
#     if os.path.exists(CHECKPOINT_FILE):
#         with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
#             ultimo_feed = f.read().strip()
#             if ultimo_feed:
#                 print(f"📍 Último feed procesado: {ultimo_feed}")
#                 return ultimo_feed
#     print("📍 No hay checkpoint previo, procesando desde el inicio")
#     return None


# def guardar_checkpoint(nombre_feed):
#     """Guarda el nombre del último feed procesado."""
#     with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
#         f.write(nombre_feed)


# def actualizar_o_insertar_licitacion(df_existente, df_nuevo):
#     """
#     Actualiza registros existentes o inserta nuevos basándose en el ID.
#     Conserva todas las licitaciones, incluyendo las de estado terminal.
#     """
#     if df_existente.empty:
#         return df_nuevo
    
#     if df_nuevo.empty:
#         return df_existente
    
#     # Identificar IDs nuevos
#     ids_nuevos = df_nuevo['ID'].values
    
#     for id_nuevo in ids_nuevos:
#         registro_nuevo = df_nuevo[df_nuevo['ID'] == id_nuevo]
#         estado_nuevo = registro_nuevo['ESTADO'].values[0].strip()
        
#         # Si existe, actualizar
#         if id_nuevo in df_existente['ID'].values:
#             estado_anterior = df_existente[df_existente['ID'] == id_nuevo]['ESTADO'].values[0]
#             print(f"🔄 Actualizando licitación {id_nuevo}: {estado_anterior} → {estado_nuevo}")
#             df_existente = df_existente[df_existente['ID'] != id_nuevo]
#             df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
#         else:
#             # Si no existe, insertar
#             print(f"✨ Nueva licitación {id_nuevo} - Estado: {estado_nuevo}")
#             df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
    
#     return df_existente


# def actualizar_tablas_relacionadas(df_existente, df_nuevo, id_column='pliego_id'):
#     """
#     Actualiza tablas relacionadas (requisitos, criterios, docs).
#     """
#     if df_existente.empty:
#         return df_nuevo
    
#     if df_nuevo.empty:
#         return df_existente
    
#     # Identificar IDs en la nueva carga
#     ids_nuevos = df_nuevo[id_column].unique()
    
#     for id_nuevo in ids_nuevos:
#         # Eliminar registros antiguos del mismo ID
#         if id_nuevo in df_existente[id_column].values:
#             print(f"🔄 Actualizando registros relacionados para {id_nuevo}")
#             df_existente = df_existente[df_existente[id_column] != id_nuevo]
        
#         # Agregar nuevos registros
#         registros_nuevos = df_nuevo[df_nuevo[id_column] == id_nuevo]
#         df_existente = pd.concat([df_existente, registros_nuevos], ignore_index=True)
    
#     return df_existente


# def guardar_en_db(engine, df_general, df_tendering, df_awarding, df_docs):
#     """Guarda los DataFrames en la base de datos MariaDB."""
#     print("\n💾 Guardando datos en la base de datos...")
    
#     # Limpiar datos antes de guardar
#     df_docs_limpio = df_docs.dropna(how='all')
    
#     # Guardar cada tabla usando replace para actualizar registros existentes
#     with engine.begin() as conn:
#         # Para pliegos_general, usar replace ya que tiene primary key
#         if not df_general.empty:
#             df_general.to_sql('pliegos_general', conn, if_exists='replace', 
#                             index=False, method='multi', chunksize=1000)
#             print(f"✅ Guardados {len(df_general)} pliegos_general")
        
#         # Para las demás tablas, eliminar y reinsertar
#         if not df_tendering.empty:
#             conn.execute(text("TRUNCATE TABLE requisitos_general"))
#             df_tendering.to_sql('requisitos_general', conn, if_exists='append', 
#                               index=False, method='multi', chunksize=1000)
#             print(f"✅ Guardados {len(df_tendering)} requisitos")
        
#         if not df_awarding.empty:
#             conn.execute(text("TRUNCATE TABLE criterios_general"))
#             df_awarding.to_sql('criterios_general', conn, if_exists='append', 
#                              index=False, method='multi', chunksize=1000)
#             print(f"✅ Guardados {len(df_awarding)} criterios")
        
#         if not df_docs_limpio.empty:
#             conn.execute(text("TRUNCATE TABLE documentacion_general"))
#             df_docs_limpio.to_sql('documentacion_general', conn, if_exists='append', 
#                                  index=False, method='multi', chunksize=1000)
#             print(f"✅ Guardados {len(df_docs_limpio)} documentos")


# # ============================================================================
# # FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# # ============================================================================

# def procesar_feed(feed_url, df_general, df_tendering, df_awarding, df_docs):
#     """Procesa un feed ATOM y acumula los datos en los DataFrames proporcionados."""
    
#     r = requests.get(feed_url, timeout=60)
#     r.raise_for_status()
#     root = etree.fromstring(r.content, parser=parser)
    
#     entries = root.xpath("//atom:entry", namespaces={"atom": "http://www.w3.org/2005/Atom"})
#     print(f"Entradas encontradas en el feed: {len(entries)}")
    
#     claves = [
#         "summary", "updated", "AwardingTerms", "TenderingTerms",
#         "RequiredFinancialGuarantee", "ContractFolderStatus",
#         "TendererQualificationRequest", "ExternalReference",
#         "ProcurementProject", "Party", "ProcurementProjectLot",
#         "ExternalData", "AdditionalDocumentReference",
#         "LegalDocumentReference", "TechnicalDocumentReference",
#         "TenderSubmissionDeadlinePeriod",
#     ]
    
#     # DataFrames temporales para este feed
#     df_general_temp = pd.DataFrame()
#     df_tendering_temp = pd.DataFrame()
#     df_awarding_temp = pd.DataFrame()
#     df_docs_temp = pd.DataFrame()
    
#     for i, entry in enumerate(entries, start=1):
#         # Metadatos ATOM
#         summary = entry.xpath("string(atom:summary)", namespaces={"atom": "http://www.w3.org/2005/Atom"}).strip()
#         enlace = entry.xpath("string(atom:link/@href)", namespaces={"atom": "http://www.w3.org/2005/Atom"})
        
#         print('-' * 100)
#         print(f"Procesando entrada {i}: {summary[:80]}...")
        
#         # Extraer información del XML
#         dict_info = extraer_info(entry, claves)
#         dict_info['link'] = enlace
        
#         try:
#             # Procesar directamente en memoria
#             df_temp, df_tend, df_award, df_doc = extraccion_data_relevante(dict_info)
            
#             # Acumular en temporales de este feed
#             df_general_temp = pd.concat([df_general_temp, df_temp], ignore_index=True)
#             df_tendering_temp = pd.concat([df_tendering_temp, df_tend], ignore_index=True)
#             df_awarding_temp = pd.concat([df_awarding_temp, df_award], ignore_index=True)
#             df_docs_temp = pd.concat([df_docs_temp, df_doc], ignore_index=True)
            
#             print(f"✅ Procesado correctamente")
            
#         except Exception as e:
#             print(f"⚠️ Error procesando entrada {i}: {e}")
#             traceback.print_exc()
    
#     # Actualizar DataFrames principales con lógica incremental
#     print("\n" + "=" * 100)
#     print("Actualizando datos en memoria...")
#     df_general = actualizar_o_insertar_licitacion(df_general, df_general_temp)
#     df_tendering = actualizar_tablas_relacionadas(df_tendering, df_tendering_temp)
#     df_awarding = actualizar_tablas_relacionadas(df_awarding, df_awarding_temp)
#     df_docs = actualizar_tablas_relacionadas(df_docs, df_docs_temp)
    
#     return df_general, df_tendering, df_awarding, df_docs


# def natural_sort_key(s):
#     """Ordena strings con números de forma natural."""
#     return [int(text) if text.isdigit() else text
#             for text in re.split(r'(\d+)', s)]


# def main():
#     """Función principal que coordina todo el proceso incremental."""
    
#     # Crear directorio de datos si no existe
#     os.makedirs(DATA_DIR, exist_ok=True)
    
#     # Crear conexión a base de datos
#     print("=" * 100)
#     print("Conectando a base de datos MariaDB...")
#     print("=" * 100)
    
#     try:
#         engine = crear_engine()
#         # Verificar conexión
#         with engine.connect() as conn:
#             print("✅ Conexión exitosa a la base de datos")
        
#         # Crear tablas si no existen
#         crear_tablas(engine)
        
#     except Exception as e:
#         print(f"❌ Error conectando a la base de datos: {e}")
#         print("Verifica que MariaDB esté corriendo y las credenciales sean correctas")
#         return
    
#     # Cargar DataFrames desde la base de datos
#     print("\n" + "=" * 100)
#     print("Cargando datos existentes desde la base de datos...")
#     print("=" * 100)
#     df_general, df_tendering, df_awarding, df_docs = cargar_dataframes_desde_db(engine)
    
#     # Obtener último feed procesado
#     ultimo_feed = obtener_ultimo_feed_procesado()
    
#     # Descargar y descomprimir el ZIP
#     print("\n" + "=" * 100)
#     print(f"Descargando ZIP desde {FEEDZIP}...")
#     print("=" * 100)
#     response = requests.get(FEEDZIP)
#     zip_data = zipfile.ZipFile(io.BytesIO(response.content))
    
#     # Ordenar archivos del ZIP
#     feed_base = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
#     zip_data_sorted = sorted(zip_data.namelist(), key=natural_sort_key)
#     zip_data_sorted.append(zip_data_sorted.pop(0))
    
#     # Determinar desde dónde empezar a procesar
#     ultimo_feed = 'licitacionesPerfilesContratanteCompleto3_20251207_170155.atom' ## Para pruebas rapidas
#     comenzar = (ultimo_feed is None)
#     feeds_procesados = 0
    
#     # Redirigir salida a archivo
#     with open(LOG_FILE, "a", encoding="utf-8") as f:
#         with redirect_stdout(f):
#             print(f"\n{'=' * 100}")
#             print(f"Inicio de procesamiento: {datetime.now()}")
#             print('=' * 100)
            
#             for fin_feed in zip_data_sorted:
#                 # Si ya procesamos este feed, saltar hasta encontrar el siguiente
#                 if not comenzar:
#                     if fin_feed == ultimo_feed:
#                         comenzar = True
#                         print(f"⏭️  Saltando {fin_feed} (ya procesado)")
#                         continue
#                     else:
#                         continue
                
#                 print(f"\n{'=' * 100}")
#                 print(f"Procesando archivo: {fin_feed}")
#                 print('=' * 100)
                
#                 FEED = feed_base + fin_feed
                
#                 try:
#                     df_general, df_tendering, df_awarding, df_docs = procesar_feed(
#                         FEED, df_general, df_tendering, df_awarding, df_docs
#                     )
                    
#                     # Guardar checkpoint después de cada feed
#                     if fin_feed != "licitacionesPerfilesContratanteCompleto3.atom":
#                         guardar_checkpoint(fin_feed)
#                     feeds_procesados += 1
                    
#                     # Guardar en base de datos periódicamente (cada 5 feeds)
#                     if feeds_procesados % 5 == 0:
#                         print("\n💾 Guardando progreso intermedio en base de datos...")
#                         guardar_en_db(engine, df_general, df_tendering, df_awarding, df_docs)
                    
#                 except Exception as e:
#                     print(f"❌ Error crítico procesando {fin_feed}: {e}")
#                     traceback.print_exc()
#                     continue
            
#             print(f"\n{'=' * 100}")
#             print(f"Fin de procesamiento: {datetime.now()}")
#             print(f"Feeds procesados en esta ejecución: {feeds_procesados}")
#             print('=' * 100)
    
#     # Guardar datos finales en base de datos
#     print("\n" + "=" * 100)
#     print("Guardando resultados finales en base de datos...")
#     print("=" * 100)
#     guardar_en_db(engine, df_general, df_tendering, df_awarding, df_docs)
    
#     print(f"\n✅ Proceso completado exitosamente!")
#     print(f"📊 Total de registros en base de datos:")
#     print(f"   - Pliegos generales: {len(df_general)}")
#     print(f"   - Requisitos: {len(df_tendering)}")
#     print(f"   - Criterios: {len(df_awarding)}")
#     print(f"   - Documentos: {len(df_docs)}")
#     print(f"   - Feeds procesados: {feeds_procesados}")
    
#     # Cerrar conexión
#     engine.dispose()


# if __name__ == "__main__":
#     main()

# # ------------------------------------

# import requests
# from lxml import etree
# import sys
# from contextlib import redirect_stdout
# from pathlib import Path
# from jsonpath_ng.ext import parse
# import os
# import json
# import re
# from urllib.parse import urlparse, unquote
# import zipfile
# import io
# import pandas as pd
# import traceback
# from datetime import datetime, date
# import sqlalchemy
# from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Text, Float, DateTime, Integer

# # ============================================================================
# # CONFIGURACIÓN DE BASE DE DATOS
# # ============================================================================

# # Configuración de conexión - SQLite o MariaDB
# USE_SQLITE = os.getenv('USE_SQLITE', 'True').lower() == 'true'  # Por defecto usa SQLite

# if USE_SQLITE:
#     # SQLite - base de datos local en archivo
#     DB_FILE = os.getenv('DB_FILE', 'licitaciones.db')
#     print(f"ℹ️  Modo SQLite: usando archivo {DB_FILE}")
# else:
#     # MariaDB - base de datos remota
#     # DB_CONFIG = {
#     #     'host': os.getenv('DB_HOST', 'localhost'),
#     #     'port': int(os.getenv('DB_PORT', 3306)),
#     #     'user': os.getenv('DB_USER', 'root'),
#     #     'password': os.getenv('DB_PASSWORD', ''),
#     #     'database': os.getenv('DB_NAME', 'licitaciones_db'),
#     #     'charset': 'utf8mb4'
#     # }
#     db_config = {
#         'user': 'BI',
#         'password': 'masterkey',
#         'host': '192.168.49.79',
#         'database': 'bbddlicitaciones',
#         'port': 3307 
#     }

#     print(f"ℹ️  Modo MariaDB: conectando a {DB_CONFIG['host']}:{DB_CONFIG['port']}")

# # Configuración inicial
# FEED = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"
# FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202512.zip"
# parser = etree.XMLParser(recover=True)

# # Rutas de archivos
# DATA_DIR = "src/data"
# CHECKPOINT_FILE = "ultimo_feed_procesado.txt"
# LOG_FILE = "extraccion_mensual.txt"

# # ============================================================================
# # FUNCIONES DE CONEXIÓN A BASE DE DATOS
# # ============================================================================

# def crear_engine():
#     """Crea el engine de SQLAlchemy para conectar con SQLite o MariaDB."""
#     if USE_SQLITE:
#         # SQLite - archivo local
#         connection_string = f"sqlite:///{DB_FILE}"
#         engine = create_engine(connection_string, echo=False)
#         print(f"✅ Engine SQLite creado: {DB_FILE}")
#     else:
#         # MariaDB - servidor remoto
#         connection_string = (
#             f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
#             f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
#             f"?charset={DB_CONFIG['charset']}"
#         )
#         engine = create_engine(connection_string, pool_pre_ping=True, pool_recycle=3600)
#         print(f"✅ Engine MariaDB creado")
    
#     return engine

# def crear_tablas(engine):
#     """Crea las tablas en la base de datos si no existen."""
#     metadata = MetaData()
    
#     # Configuración específica según el tipo de BD
#     if USE_SQLITE:
#         kwargs_tabla = {}
#     else:
#         kwargs_tabla = {'mysql_charset': 'utf8mb4'}
    
#     # Tabla principal de pliegos
#     pliegos = Table(
#         'pliegos_general', metadata,
#         Column('ID', String(100), primary_key=True),
#         Column('ENTIDAD', Text),
#         Column('CPV', Text),  # Almacenaremos como JSON string
#         Column('IMPORTE', String(50)),
#         Column('ESTADO', String(100)),
#         Column('NOMBRE_PROYECTO', Text),
#         # Column('FECHA_PUBLICACION', String(50)),
#         Column('FECHA_ACTUALIZACION', String(50)),
#         Column('FECHA_LIMITE', String(50)),
#         Column('SECTOR_PUBLICO', String(200)),
#         Column('UBICACION', String(200)),
#         Column('URL', Text),
#         # Column('fecha_carga', DateTime, default=datetime.now),
#         **kwargs_tabla
#     )
    
#     # Tabla de requisitos/criterios técnicos y financieros
#     requisitos = Table(
#         'requisitos_general', metadata,
#         Column('id', Integer, primary_key=True, autoincrement=True),
#         Column('pliego_id', String(100)),
#         Column('TIPO', String(100)),
#         Column('DESCRIPCION', Text),
#         Column('CODIGO_TIPO', String(100)),
#         Column('fecha_carga', DateTime, default=datetime.now),
#         **kwargs_tabla
#     )
    
#     # Tabla de criterios de adjudicación
#     criterios = Table(
#         'criterios_general', metadata,
#         Column('id', Integer, primary_key=True, autoincrement=True),
#         Column('pliego_id', String(100)),
#         Column('TIPO', String(100)),
#         Column('DESCRIPCION', Text),
#         Column('CODIGO_TIPO', String(100)),
#         Column('PESO', String(50)),
#         Column('NOTAS', Text),
#         Column('fecha_carga', DateTime, default=datetime.now),
#         **kwargs_tabla
#     )
    
#     # Tabla de documentación
#     documentacion = Table(
#         'documentacion_general', metadata,
#         Column('id', Integer, primary_key=True, autoincrement=True),
#         Column('pliego_id', String(100)),
#         Column('TIPO', String(100)),
#         Column('DESCRIPCION', Text),
#         Column('URI', Text),
#         Column('CODIGO_TIPO', String(100)),
#         Column('fecha_carga', DateTime, default=datetime.now),
#         **kwargs_tabla
#     )
    
#     # Crear todas las tablas
#     metadata.create_all(engine)
#     print("✅ Tablas creadas o verificadas en la base de datos")

# # ============================================================================
# # FUNCIONES DE EXTRACCIÓN XML -> DICT (Sin cambios)
# # ============================================================================

# def recorrer_xml(nodo):
#     """Recorre un nodo XML y devuelve una estructura anidada tipo dict."""
#     tag = etree.QName(nodo).localname
#     texto = nodo.text.strip() if nodo.text and nodo.text.strip() else None

#     if len(nodo) == 0:
#         return {tag: texto}

#     contenido = []
#     for hijo in nodo:
#         contenido.append(recorrer_xml(hijo))

#     if texto:
#         contenido.insert(0, {"_text": texto})

#     return {tag: contenido}


# def extraer_info(xml_root, claves_interes):
#     """Recorre el XML y extrae solo las secciones relevantes (por etiqueta)."""
#     info = {k: [] for k in claves_interes}

#     for elem in xml_root.iter():
#         tag = etree.QName(elem).localname
#         if tag in claves_interes:
#             info[tag].append(recorrer_xml(elem)[tag])

#     return info


# # ============================================================================
# # FUNCIONES DE PROCESAMIENTO JSON -> DATAFRAMES (Sin cambios significativos)
# # ============================================================================

# def extraccion_data_relevante(json_data):
#     """Extrae información relevante del JSON y genera DataFrames."""
#     registros = []
#     fecha_limite = None
#     fecha_publicacion = None
    
#     # Summary
#     datos = json_data['summary'][0].split(";")
    
#     # Link
#     try:
#         link = json_data["link"]
#     except:
#         link = "https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
    
#     # Updated
#     updated = json_data["updated"][0]
    
#     for i in range(len(datos)):
#         datos[i] = datos[i].split(":")[1]
    
#     id_, entidad, importe, estado = datos
    
#     # Fecha límite
#     jsonpath_expr_data = parse('$..TenderSubmissionDeadlinePeriod[*].EndDate')
#     fecha_res = [match.value for match in jsonpath_expr_data.find(json_data)]
#     if len(fecha_res) > 0:
#         fecha_limite = fecha_res[0]
    
#     # Fecha publicación
#     jsonpath_expr_date = parse('$..IssueDate')
#     fecha_pub_res = [match.value for match in jsonpath_expr_date.find(json_data)]
#     if fecha_pub_res:
#         fecha_publicacion = fecha_pub_res[0]
#         print(f"📅 Fecha de publicación encontrada: {fecha_publicacion}")
    
#     # ProcurementProject
#     data = json_data["ProcurementProject"][0]
#     name = next((d["Name"] for d in data if "Name" in d), None)
    
#     jsonpath_expr = parse('$..RequiredCommodityClassification[*].ItemClassificationCode')
#     codes = [match.value for match in jsonpath_expr.find(data)]

#     # Extracción de datos geográficos    
#     country_expr = parse('$..RealizedLocation[*].CountrySubentity')
#     city_res = [match.value for match in country_expr.find(data)]
    
#     data_01 = json_data["ContractFolderStatus"][0]
#     entidades_expr = parse('$..ParentLocatedParty[*].PartyName[*].Name')
#     entidades_res = [match.value for match in entidades_expr.find(data_01)]
    
#     ID_expr = parse('$..ContractFolderID')
#     ID_res = [match.value for match in ID_expr.find(data_01)]
    
#     print("-----" * 100)
#     print("Entidades", entidades_res)
#     jerarquia_path = entidades_res[-2] if len(entidades_res) >= 2 else None
    
#     if len(entidades_res) >= 3:
#         sub_jerarquia_path = entidades_res[-3]
#     else:
#         sub_jerarquia_path = None
    
#     ciudades_parser = parse('$..CityName')
#     city_aux = [match.value for match in ciudades_parser.find(data_01)]
#     if isinstance(city_aux, list) and len(city_aux) > 0:
#         city_aux = city_aux[0]
    
#     if jerarquia_path == "ENTIDADES LOCALES":
#         ubicacion_aux = sub_jerarquia_path
#     else:
#         ubicacion_aux = city_aux if city_aux else None
    
#     # Guardar en lista de registros
#     registros.append({
#         "ID": id_,
#         "ENTIDAD": entidad,
#         "CPV": json.dumps(codes),  # Convertir lista a JSON string
#         "IMPORTE": importe,
#         "ESTADO": estado,
#         "NOMBRE_PROYECTO": name,
#         "FECHA_PUBLICACION": fecha_publicacion,
#         "FECHA_ACTUALIZACION": updated,
#         "FECHA_LIMITE": fecha_limite,
#         "SECTOR_PUBLICO": jerarquia_path,
#         "UBICACION": ubicacion_aux,
#         "URL": link,
#     })
    
#     df = pd.DataFrame(registros)
    
#     # TendererQualificationRequest
#     if len(json_data["TendererQualificationRequest"]) > 0:
#         tenderer = extraccion_tenderer(json_data['TendererQualificationRequest'][0], id_)
#     else:
#         tenderer = pd.DataFrame([])
    
#     # AwardingTerms
#     if len(json_data["AwardingTerms"]) > 0:
#         awarding = extraccion_awarding(json_data["AwardingTerms"][0], id_)
#     else:
#         awarding = pd.DataFrame([])
    
#     # Documentos
#     docs = extraccion_docs(json_data, id_)
    
#     return df, tenderer, awarding, docs


# def extraccion_tenderer(info_tenderer, id):
#     """Extrae criterios técnicos, financieros y requisitos específicos."""
#     registros = []
    
#     jsonpath_expr_data = parse('$..TechnicalEvaluationCriteria[*]')
#     technical_criteria = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
#     jsonpath_expr_data = parse('$..FinancialEvaluationCriteria[*]')
#     financial_criteria = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
#     jsonpath_expr_data = parse('$..SpecificTendererRequirement[*]')
#     specific_tendering = [match.value for match in jsonpath_expr_data.find(info_tenderer)]
    
#     if len(technical_criteria) > 0:
#         for i in range(int(len(technical_criteria) / 2)):
#             descripcion = list(technical_criteria[(i * 2) + 1].values())[0]
#             code_type = list(technical_criteria[(i * 2)].values())[0]
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": "Criterios Tecnicos",
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type
#             })
    
#     if len(financial_criteria) > 0:
#         for i in range(int(len(financial_criteria) / 2)):
#             descripcion = list(financial_criteria[(i * 2) + 1].values())[0]
#             code_type = list(financial_criteria[(i * 2)].values())[0]
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": "Criterios Financieros",
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type
#             })
    
#     if len(specific_tendering) > 0:
#         for i in range(int(len(specific_tendering) / 2)):
#             descripcion = list(specific_tendering[(i * 2) + 1].values())[0]
#             code_type = list(specific_tendering[(i * 2)].values())[0]
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": "Requisitos",
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type
#             })
    
#     return pd.DataFrame(registros)


# def extraccion_awarding(info_awarding, id):
#     """Extrae criterios de adjudicación."""
#     registros = []
    
#     for sub_info in info_awarding:
#         for criterio in sub_info.values():
#             for criter in criterio:
#                 tipo = None
#                 descripcion = None
#                 code_type = None
#                 weight_numeric = None
#                 notas = None
                
#                 if list(criter.keys())[0] == "Description":
#                     descripcion = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["RequirementTypeCode", "EvaluationCriteriaTypeCode", "AwardingCriteriaSubTypeCode"]:
#                     code_type = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["AwardingCriteriaTypeCode"]:
#                     tipo = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["WeightNumeric"]:
#                     weight_numeric = list(criter.values())[0]
#                 if list(criter.keys())[0] in ["Note"]:
#                     notas = list(criter.values())[0]
            
#             registros.append({
#                 "pliego_id": id,
#                 "TIPO": tipo,
#                 "DESCRIPCION": descripcion,
#                 "CODIGO_TIPO": code_type,
#                 "PESO": weight_numeric,
#                 "NOTAS": notas,
#             })
    
#     return pd.DataFrame(registros)


# def extraccion_docs(info_docs, id):
#     """Extrae documentación legal, técnica y adicional."""
#     registros = []
    
#     legal_expr_data = parse('$..LegalDocumentReference[*]')
#     legal_document = [match.value for match in legal_expr_data.find(info_docs)]
    
#     additional_expr_data = parse('$..AdditionalDocumentReference[*]')
#     additional_document = [match.value for match in additional_expr_data.find(info_docs)]
    
#     technical_expr_data = parse('$..TechnicalDocumentReference[*]')
#     technical_document = [match.value for match in technical_expr_data.find(info_docs)]
    
#     tipos = {
#         "Documentacion Legal": legal_document,
#         "Documentacion Adicional": additional_document,
#         "Documentacion Tecnica": technical_document
#     }
    
#     for tipo, documentos in tipos.items():
#         for doc in documentos:
#             if isinstance(doc, list):
#                 ids_extraidos = []
#                 uris_extraidos = []
#                 for elemento in doc:
#                     if isinstance(elemento, dict):
#                         id_data = parse('$..ID[*]')
#                         ids = [match.value for match in id_data.find(elemento)]
#                         URI_data = parse('$..URI[*]')
#                         uris = [match.value for match in URI_data.find(elemento)]
                        
#                         if ids:
#                             ids_extraidos.extend(ids)
#                         if uris:
#                             uris_extraidos.extend(uris)
                
#                 for i in range(max(len(ids_extraidos), len(uris_extraidos))):
#                     descripcion = ids_extraidos[i] if i < len(ids_extraidos) else None
#                     uri = uris_extraidos[i] if i < len(uris_extraidos) else None
                    
#                     if descripcion or uri:
#                         registros.append({
#                             "pliego_id": id,
#                             "TIPO": tipo,
#                             "DESCRIPCION": descripcion,
#                             "URI": uri,
#                             "CODIGO_TIPO": tipo.split()[-1],
#                         })
            
#             elif isinstance(doc, dict) and 'ID' in doc:
#                 registros.append({
#                     "pliego_id": id,
#                     "TIPO": tipo,
#                     "DESCRIPCION": doc.get('ID'),
#                     "URI": doc.get('URI'),
#                     "CODIGO_TIPO": tipo.split()[-1],
#                 })
    
#     return pd.DataFrame(registros)


# # ============================================================================
# # FUNCIONES DE GESTIÓN CON BASE DE DATOS
# # ============================================================================

# def cargar_dataframes_desde_db(engine):
#     """Carga los DataFrames desde la base de datos."""
#     try:
#         df_general = pd.read_sql_table('pliegos_general', engine)
#         print(f"✅ Cargado pliegos_general: {len(df_general)} registros")
#     except:
#         df_general = pd.DataFrame()
#         print(f"ℹ️  Tabla pliegos_general vacía o no existe")
    
#     try:
#         df_tendering = pd.read_sql_table('requisitos_general', engine)
#         print(f"✅ Cargado requisitos_general: {len(df_tendering)} registros")
#     except:
#         df_tendering = pd.DataFrame()
#         print(f"ℹ️  Tabla requisitos_general vacía o no existe")
    
#     try:
#         df_awarding = pd.read_sql_table('criterios_general', engine)
#         print(f"✅ Cargado criterios_general: {len(df_awarding)} registros")
#     except:
#         df_awarding = pd.DataFrame()
#         print(f"ℹ️  Tabla criterios_general vacía o no existe")
    
#     try:
#         df_docs = pd.read_sql_table('documentacion_general', engine)
#         print(f"✅ Cargado documentacion_general: {len(df_docs)} registros")
#     except:
#         df_docs = pd.DataFrame()
#         print(f"ℹ️  Tabla documentacion_general vacía o no existe")
    
#     return df_general, df_tendering, df_awarding, df_docs


# def obtener_ultimo_feed_procesado():
#     """Lee el último feed procesado desde el archivo de checkpoint."""
#     if os.path.exists(CHECKPOINT_FILE):
#         with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
#             ultimo_feed = f.read().strip()
#             if ultimo_feed:
#                 print(f"📍 Último feed procesado: {ultimo_feed}")
#                 return ultimo_feed
#     print("📍 No hay checkpoint previo, procesando desde el inicio")
#     return None


# def guardar_checkpoint(nombre_feed):
#     """Guarda el nombre del último feed procesado."""
#     with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
#         f.write(nombre_feed)


# def actualizar_o_insertar_licitacion(df_existente, df_nuevo):
#     """
#     Actualiza registros existentes o inserta nuevos basándose en el ID.
#     Conserva todas las licitaciones, incluyendo las de estado terminal.
#     """
#     if df_existente.empty:
#         return df_nuevo
    
#     if df_nuevo.empty:
#         return df_existente
    
#     # Identificar IDs nuevos
#     ids_nuevos = df_nuevo['ID'].values
    
#     for id_nuevo in ids_nuevos:
#         registro_nuevo = df_nuevo[df_nuevo['ID'] == id_nuevo]
#         estado_nuevo = registro_nuevo['ESTADO'].values[0].strip()
        
#         # Si existe, actualizar
#         if id_nuevo in df_existente['ID'].values:
#             estado_anterior = df_existente[df_existente['ID'] == id_nuevo]['ESTADO'].values[0]
#             print(f"🔄 Actualizando licitación {id_nuevo}: {estado_anterior} → {estado_nuevo}")
#             df_existente = df_existente[df_existente['ID'] != id_nuevo]
#             df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
#         else:
#             # Si no existe, insertar
#             print(f"✨ Nueva licitación {id_nuevo} - Estado: {estado_nuevo}")
#             df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
    
#     return df_existente


# def actualizar_tablas_relacionadas(df_existente, df_nuevo, id_column='pliego_id'):
#     """
#     Actualiza tablas relacionadas (requisitos, criterios, docs).
#     """
#     if df_existente.empty:
#         return df_nuevo
    
#     if df_nuevo.empty:
#         return df_existente
    
#     # Identificar IDs en la nueva carga
#     ids_nuevos = df_nuevo[id_column].unique()
    
#     for id_nuevo in ids_nuevos:
#         # Eliminar registros antiguos del mismo ID
#         if id_nuevo in df_existente[id_column].values:
#             print(f"🔄 Actualizando registros relacionados para {id_nuevo}")
#             df_existente = df_existente[df_existente[id_column] != id_nuevo]
        
#         # Agregar nuevos registros
#         registros_nuevos = df_nuevo[df_nuevo[id_column] == id_nuevo]
#         df_existente = pd.concat([df_existente, registros_nuevos], ignore_index=True)
    
#     return df_existente


# def guardar_en_db(engine, df_general, df_tendering, df_awarding, df_docs):
#     """Guarda los DataFrames en la base de datos SQLite o MariaDB."""
#     print("\n💾 Guardando datos en la base de datos...")
    
#     # Limpiar datos antes de guardar
#     df_docs_limpio = df_docs.dropna(how='all')
    
#     # Guardar cada tabla
#     with engine.begin() as conn:
#         # Para pliegos_general, usar replace ya que tiene primary key
#         if not df_general.empty:
#             df_general.to_sql('pliegos_general', conn, if_exists='replace', 
#                             index=False, method='multi', chunksize=1000)
#             print(f"✅ Guardados {len(df_general)} pliegos_general")
        
#         # Para las demás tablas, eliminar y reinsertar
#         if not df_tendering.empty:
#             if USE_SQLITE:
#                 conn.execute(text("DELETE FROM requisitos_general"))
#             else:
#                 conn.execute(text("TRUNCATE TABLE requisitos_general"))
#             df_tendering.to_sql('requisitos_general', conn, if_exists='append', 
#                               index=False, method='multi', chunksize=1000)
#             print(f"✅ Guardados {len(df_tendering)} requisitos")
        
#         if not df_awarding.empty:
#             if USE_SQLITE:
#                 conn.execute(text("DELETE FROM criterios_general"))
#             else:
#                 conn.execute(text("TRUNCATE TABLE criterios_general"))
#             df_awarding.to_sql('criterios_general', conn, if_exists='append', 
#                              index=False, method='multi', chunksize=1000)
#             print(f"✅ Guardados {len(df_awarding)} criterios")
        
#         if not df_docs_limpio.empty:
#             if USE_SQLITE:
#                 conn.execute(text("DELETE FROM documentacion_general"))
#             else:
#                 conn.execute(text("TRUNCATE TABLE documentacion_general"))
#             df_docs_limpio.to_sql('documentacion_general', conn, if_exists='append', 
#                                  index=False, method='multi', chunksize=1000)
#             print(f"✅ Guardados {len(df_docs_limpio)} documentos")


# # ============================================================================
# # FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# # ============================================================================

# def procesar_feed(feed_url, df_general, df_tendering, df_awarding, df_docs):
#     """Procesa un feed ATOM y acumula los datos en los DataFrames proporcionados."""
    
#     r = requests.get(feed_url, timeout=60)
#     r.raise_for_status()
#     root = etree.fromstring(r.content, parser=parser)
    
#     entries = root.xpath("//atom:entry", namespaces={"atom": "http://www.w3.org/2005/Atom"})
#     print(f"Entradas encontradas en el feed: {len(entries)}")
    
#     claves = [
#         "summary", "updated", "AwardingTerms", "TenderingTerms",
#         "RequiredFinancialGuarantee", "ContractFolderStatus",
#         "TendererQualificationRequest", "ExternalReference",
#         "ProcurementProject", "Party", "ProcurementProjectLot",
#         "ExternalData", "AdditionalDocumentReference",
#         "LegalDocumentReference", "TechnicalDocumentReference",
#         "TenderSubmissionDeadlinePeriod",
#     ]
    
#     # DataFrames temporales para este feed
#     df_general_temp = pd.DataFrame()
#     df_tendering_temp = pd.DataFrame()
#     df_awarding_temp = pd.DataFrame()
#     df_docs_temp = pd.DataFrame()
    
#     for i, entry in enumerate(entries, start=1):
#         # Metadatos ATOM
#         summary = entry.xpath("string(atom:summary)", namespaces={"atom": "http://www.w3.org/2005/Atom"}).strip()
#         enlace = entry.xpath("string(atom:link/@href)", namespaces={"atom": "http://www.w3.org/2005/Atom"})
        
#         print('-' * 100)
#         print(f"Procesando entrada {i}: {summary[:80]}...")
        
#         # Extraer información del XML
#         dict_info = extraer_info(entry, claves)
#         dict_info['link'] = enlace
        
#         try:
#             # Procesar directamente en memoria
#             df_temp, df_tend, df_award, df_doc = extraccion_data_relevante(dict_info)
            
#             # Acumular en temporales de este feed
#             df_general_temp = pd.concat([df_general_temp, df_temp], ignore_index=True)
#             df_tendering_temp = pd.concat([df_tendering_temp, df_tend], ignore_index=True)
#             df_awarding_temp = pd.concat([df_awarding_temp, df_award], ignore_index=True)
#             df_docs_temp = pd.concat([df_docs_temp, df_doc], ignore_index=True)
            
#             print(f"✅ Procesado correctamente")
            
#         except Exception as e:
#             print(f"⚠️ Error procesando entrada {i}: {e}")
#             traceback.print_exc()
    
#     # Actualizar DataFrames principales con lógica incremental
#     print("\n" + "=" * 100)
#     print("Actualizando datos en memoria...")
#     df_general = actualizar_o_insertar_licitacion(df_general, df_general_temp)
#     df_tendering = actualizar_tablas_relacionadas(df_tendering, df_tendering_temp)
#     df_awarding = actualizar_tablas_relacionadas(df_awarding, df_awarding_temp)
#     df_docs = actualizar_tablas_relacionadas(df_docs, df_docs_temp)
    
#     return df_general, df_tendering, df_awarding, df_docs


# def natural_sort_key(s):
#     """Ordena strings con números de forma natural."""
#     return [int(text) if text.isdigit() else text
#             for text in re.split(r'(\d+)', s)]


# def main():
#     """Función principal que coordina todo el proceso incremental."""
    
#     # Crear directorio de datos si no existe
#     os.makedirs(DATA_DIR, exist_ok=True)
    
#     # Crear conexión a base de datos
#     print("=" * 100)
#     if USE_SQLITE:
#         print(f"Conectando a base de datos SQLite: {DB_FILE}...")
#     else:
#         print("Conectando a base de datos MariaDB...")
#     print("=" * 100)
    
#     try:
#         engine = crear_engine()
#         # Verificar conexión
#         with engine.connect() as conn:
#             print("✅ Conexión exitosa a la base de datos")
        
#         # Crear tablas si no existen
#         crear_tablas(engine)
        
#     except Exception as e:
#         print(f"❌ Error conectando a la base de datos: {e}")
#         if USE_SQLITE:
#             print(f"Verifica los permisos del archivo {DB_FILE}")
#         else:
#             print("Verifica que MariaDB esté corriendo y las credenciales sean correctas")
#         return
    
#     # Cargar DataFrames desde la base de datos
#     print("\n" + "=" * 100)
#     print("Cargando datos existentes desde la base de datos...")
#     print("=" * 100)
#     df_general, df_tendering, df_awarding, df_docs = cargar_dataframes_desde_db(engine)
    
#     # Obtener último feed procesado
#     ultimo_feed = obtener_ultimo_feed_procesado()
    
#     # Descargar y descomprimir el ZIP
#     print("\n" + "=" * 100)
#     print(f"Descargando ZIP desde {FEEDZIP}...")
#     print("=" * 100)
#     response = requests.get(FEEDZIP)
#     zip_data = zipfile.ZipFile(io.BytesIO(response.content))
    
#     # Ordenar archivos del ZIP
#     feed_base = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
#     zip_data_sorted = sorted(zip_data.namelist(), key=natural_sort_key)
#     zip_data_sorted.append(zip_data_sorted.pop(0))
    
#     # Determinar desde dónde empezar a procesar
#     # ultimo_feed = 'licitacionesPerfilesContratanteCompleto3_20251207_170155.atom' ## Para pruebas rapidas
#     comenzar = (ultimo_feed is None)
#     feeds_procesados = 0
    
#     # Redirigir salida a archivo
#     with open(LOG_FILE, "a", encoding="utf-8") as f:
#         with redirect_stdout(f):
#             print(f"\n{'=' * 100}")
#             print(f"Inicio de procesamiento: {datetime.now()}")
#             print('=' * 100)
            
#             for fin_feed in zip_data_sorted:
#                 # Si ya procesamos este feed, saltar hasta encontrar el siguiente
#                 if not comenzar:
#                     if fin_feed == ultimo_feed:
#                         comenzar = True
#                         print(f"⏭️  Saltando {fin_feed} (ya procesado)")
#                         continue
#                     else:
#                         continue
                
#                 print(f"\n{'=' * 100}")
#                 print(f"Procesando archivo: {fin_feed}")
#                 print('=' * 100)
                
#                 FEED = feed_base + fin_feed
                
#                 try:
#                     df_general, df_tendering, df_awarding, df_docs = procesar_feed(
#                         FEED, df_general, df_tendering, df_awarding, df_docs
#                     )
                    
#                     # Guardar checkpoint después de cada feed
#                     guardar_checkpoint(fin_feed)
#                     feeds_procesados += 1
                    
#                     # Guardar en base de datos periódicamente (cada 5 feeds)
#                     if feeds_procesados % 5 == 0:
#                         print("\n💾 Guardando progreso intermedio en base de datos...")
#                         guardar_en_db(engine, df_general, df_tendering, df_awarding, df_docs)
                    
#                 except Exception as e:
#                     print(f"❌ Error crítico procesando {fin_feed}: {e}")
#                     traceback.print_exc()
#                     continue
            
#             print(f"\n{'=' * 100}")
#             print(f"Fin de procesamiento: {datetime.now()}")
#             print(f"Feeds procesados en esta ejecución: {feeds_procesados}")
#             print('=' * 100)
    
#     # Guardar datos finales en base de datos
#     print("\n" + "=" * 100)
#     print("Guardando resultados finales en base de datos...")
#     print("=" * 100)
#     guardar_en_db(engine, df_general, df_tendering, df_awarding, df_docs)
    
#     print(f"\n✅ Proceso completado exitosamente!")
#     print(f"📊 Total de registros en base de datos:")
#     print(f"   - Pliegos generales: {len(df_general)}")
#     print(f"   - Requisitos: {len(df_tendering)}")
#     print(f"   - Criterios: {len(df_awarding)}")
#     print(f"   - Documentos: {len(df_docs)}")
#     print(f"   - Feeds procesados: {feeds_procesados}")
    
#     # Cerrar conexión
#     engine.dispose()


# if __name__ == "__main__":
#     main()
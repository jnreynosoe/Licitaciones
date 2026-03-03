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
import hashlib


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

def generar_log_file():
    dt = datetime.now()
    mes_num = dt.strftime("%m")   # '01'–'12'
    anio_str = dt.strftime("%Y") # '2026'
    FEED_BASE = "extraccion_mensual_"
    anio_mes = anio_str+mes_num
    return FEED_BASE+anio_mes+".txt"

# Configuración inicial
FEED = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"
FEEDZIP = generar_feed()
# FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202511.zip"
# FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202512.zip"
# FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202602.zip"
# FEEDZIP = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202603.zip"
print(FEEDZIP)
parser = etree.XMLParser(recover=True)

# Rutas de archivos
DATA_DIR = "src/data"
CHECKPOINT_FILE = "ultimo_feed_procesado_cambiar.txt"
LOG_FILE = generar_log_file()
# LOG_FILE = "extraccion_mensual.txt"

# ============================================================================
# FUNCIONES AUXILIARES PARA ID INTERNO
# ============================================================================

def generar_id_interno(id_licitacion, nombre_proyecto):
    """
    Genera un ID interno único basado en ID_licitacion + NOMBRE_PROYECTO.
    Usa hash MD5 para crear un identificador consistente y único.
    """
    if not nombre_proyecto:
        nombre_proyecto = ""
    
    # Normalizar valores para el hash
    clave_unica = f"{id_licitacion}|{nombre_proyecto}".lower().strip()
    
    # Generar hash MD5
    hash_obj = hashlib.md5(clave_unica.encode('utf-8'))
    id_interno = hash_obj.hexdigest()
    
    return id_interno


def obtener_o_crear_id_interno(df_existente, id_licitacion, nombre_proyecto):
    """
    Busca si ya existe una licitación con el mismo ID_licitacion + NOMBRE_PROYECTO.
    Si existe, devuelve su ID_INTERNO. Si no, genera uno nuevo.
    """
    if df_existente.empty:
        return generar_id_interno(id_licitacion, nombre_proyecto)
    
    # Buscar licitación existente con mismo ID y nombre
    mascara = (
        (df_existente['ID'] == id_licitacion) & 
        (df_existente['NOMBRE_PROYECTO'] == nombre_proyecto)
    )
    
    licitaciones_existentes = df_existente[mascara]
    
    if not licitaciones_existentes.empty:
        # Ya existe, devolver su ID_INTERNO
        id_interno_existente = licitaciones_existentes.iloc[0]['ID_INTERNO']
        print(f"🔍 Licitación existente encontrada. ID_INTERNO: {id_interno_existente}")
        return id_interno_existente
    else:
        # No existe, generar nuevo ID_INTERNO
        nuevo_id_interno = generar_id_interno(id_licitacion, nombre_proyecto)
        print(f"✨ Nueva licitación. Generando ID_INTERNO: {nuevo_id_interno}")
        return nuevo_id_interno


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

def extraccion_data_relevante(json_data, df_general_existente):
    """
    Extrae información relevante del JSON y genera DataFrames.
    MODIFICADO: Ahora recibe df_general_existente para generar/recuperar ID_INTERNO.
    """
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

    # ============================================================================
    # CLAVE: Generar o recuperar ID_INTERNO
    # ============================================================================
    id_interno = obtener_o_crear_id_interno(df_general_existente, id_, name)
    print("ID INTERNO", id_interno)
    
    # Guardar en lista de registros
    registros.append({
        "ID_INTERNO": id_interno,  # ← NUEVO: Primary Key verdadera
        "ID": id_,                  # ← Ahora solo es una clave empresarial
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
        tenderer = extraccion_tenderer(json_data['TendererQualificationRequest'][0], id_interno)
    else:
        tenderer = pd.DataFrame([])
    
    # AwardingTerms
    if len(json_data["AwardingTerms"]) > 0:
        awarding = extraccion_awarding(json_data["AwardingTerms"][0], id_interno)
    else:
        awarding = pd.DataFrame([])
    
    # Documentos
    docs = extraccion_docs(json_data, id_interno)

    # Solo intentamos extraer si el estado es ADJ (Adjudicada) o RES (Resuelta)
    if estado.strip() in ['ADJ', 'RES']:
        print(f"🔎 Detectada licitación resuelta/adjudicada: {id_}. Extrayendo detalles...")
        df_adjudicatarios = extraer_info_adjudicacion(link, id_interno)
    else:
        df_adjudicatarios = pd.DataFrame()

    return df, tenderer, awarding, docs, df_adjudicatarios


def extraccion_tenderer(info_tenderer, id_interno):
    """
    Extrae criterios técnicos, financieros y requisitos específicos.
    MODIFICADO: Ahora usa ID_INTERNO como FK.
    """
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
                "ID_INTERNO": id_interno,  # ← MODIFICADO: Ahora usa ID_INTERNO
                "TIPO": "Criterios Tecnicos",
                "DESCRIPCION": descripcion,
                "CODIGO_TIPO": code_type
            })
    
    if len(financial_criteria) > 0:
        for i in range(int(len(financial_criteria) / 2)):
            descripcion = list(financial_criteria[(i * 2) + 1].values())[0]
            code_type = list(financial_criteria[(i * 2)].values())[0]
            registros.append({
                "ID_INTERNO": id_interno,
                "TIPO": "Criterios Financieros",
                "DESCRIPCION": descripcion,
                "CODIGO_TIPO": code_type
            })
    
    if len(specific_tendering) > 0:
        for i in range(int(len(specific_tendering) / 2)):
            descripcion = list(specific_tendering[(i * 2) + 1].values())[0]
            code_type = list(specific_tendering[(i * 2)].values())[0]
            registros.append({
                "ID_INTERNO": id_interno,
                "TIPO": "Requisitos",
                "DESCRIPCION": descripcion,
                "CODIGO_TIPO": code_type
            })
    
    return pd.DataFrame(registros)


def extraccion_awarding(info_awarding, id_interno):
    """
    Extrae criterios de adjudicación.
    MODIFICADO: Ahora usa ID_INTERNO como FK.
    """
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
                "ID_INTERNO": id_interno,  # ← MODIFICADO: Ahora usa ID_INTERNO
                "TIPO": tipo,
                "DESCRIPCION": descripcion,
                "CODIGO_TIPO": code_type,
                "PESO": weight_numeric,
                "NOTAS": notas,
            })
    
    return pd.DataFrame(registros)


def extraccion_docs(info_docs, id_interno):
    """
    Extrae documentación legal, técnica y adicional.
    MODIFICADO: Ahora usa ID_INTERNO como FK.
    """
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
                            "ID_INTERNO": id_interno,  # ← MODIFICADO: Ahora usa ID_INTERNO
                            "TIPO": tipo,
                            "DESCRIPCION": descripcion,
                            "URI": uri,
                            "CODIGO_TIPO": tipo.split()[-1],
                        })
            
            elif isinstance(doc, dict) and 'ID' in doc:
                registros.append({
                    "ID_INTERNO": id_interno,
                    "TIPO": tipo,
                    "DESCRIPCION": doc.get('ID'),
                    "URI": doc.get('URI'),
                    "CODIGO_TIPO": tipo.split()[-1],
                })
    
    return pd.DataFrame(registros)


def extraer_info_adjudicacion(url_licitacion, id_interno):
    """
    Accede a la URL de la licitación, busca el XML de adjudicación y extrae 
    los datos del adjudicatario sin guardar archivos en disco.
    MODIFICADO: Ahora usa ID_INTERNO como FK.
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
                                    "ID_INTERNO": id_interno,  # ← MODIFICADO: Ahora usa ID_INTERNO
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
    Actualiza registros existentes o inserta nuevos basándose en ID_INTERNO.
    MODIFICADO: Ahora usa ID_INTERNO como PK verdadera.
    Solo actualiza si ID_INTERNO coincide (mismo ID + mismo NOMBRE_PROYECTO).
    """
    if df_existente.empty:
        return df_nuevo
    
    if df_nuevo.empty:
        return df_existente
    
    # Identificar IDs internos nuevos
    ids_internos_nuevos = df_nuevo['ID_INTERNO'].values
    
    for id_interno_nuevo in ids_internos_nuevos:
        registro_nuevo = df_nuevo[df_nuevo['ID_INTERNO'] == id_interno_nuevo]
        estado_nuevo = registro_nuevo['ESTADO'].values[0].strip()
        id_empresarial = registro_nuevo['ID'].values[0]
        nombre_proyecto = registro_nuevo['NOMBRE_PROYECTO'].values[0]
        
        # Si existe este ID_INTERNO, actualizar
        if id_interno_nuevo in df_existente['ID_INTERNO'].values:
            estado_anterior = df_existente[df_existente['ID_INTERNO'] == id_interno_nuevo]['ESTADO'].values[0]
            print(f"🔄 Actualizando licitación ID_INTERNO={id_interno_nuevo[:8]}... ({id_empresarial}): {estado_anterior} → {estado_nuevo}")
            df_existente = df_existente[df_existente['ID_INTERNO'] != id_interno_nuevo]
            df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
        else:
            # No existe, insertar nueva licitación
            print(f"✨ Nueva licitación ID_INTERNO={id_interno_nuevo[:8]}... ({id_empresarial}) - Estado: {estado_nuevo}")
            df_existente = pd.concat([df_existente, registro_nuevo], ignore_index=True)
    
    return df_existente


def actualizar_tablas_relacionadas(df_existente, df_nuevo, id_column='ID_INTERNO'):
    """
    Actualiza tablas relacionadas (requisitos, criterios, docs, adjudicatarios).
    MODIFICADO: Ahora usa ID_INTERNO como FK.
    
    Para adjudicatarios: Solo agrega si no existe el NIF para ese ID_INTERNO.
    Para otras tablas: Reemplaza todos los registros del mismo ID_INTERNO.
    """
    if df_existente.empty:
        return df_nuevo
    
    if df_nuevo.empty:
        return df_existente
    
    # Identificar IDs internos en la nueva carga
    ids_internos_nuevos = df_nuevo[id_column].unique()
    
    for id_interno_nuevo in ids_internos_nuevos:
        # Verificar si ya existe este ID_INTERNO
        registros_existentes = df_existente[df_existente[id_column] == id_interno_nuevo]
        registros_nuevos = df_nuevo[df_nuevo[id_column] == id_interno_nuevo]
        
        if not registros_existentes.empty:
            # Si es tabla de adjudicatarios, verificamos NIF para evitar duplicados
            if 'NIF_ADJUDICATARIO' in df_existente.columns:
                for _, nuevo_reg in registros_nuevos.iterrows():
                    nif_nuevo = nuevo_reg['NIF_ADJUDICATARIO']
                    # Verificar si este NIF ya existe para este ID_INTERNO
                    mascara_duplicado = (
                        (df_existente[id_column] == id_interno_nuevo) &
                        (df_existente['NIF_ADJUDICATARIO'] == nif_nuevo)
                    )
                    
                    if not df_existente[mascara_duplicado].empty:
                        print(f"⏭️  Adjudicatario {nif_nuevo} ya existe para ID_INTERNO={id_interno_nuevo[:8]}..., saltando")
                    else:
                        print(f"➕ Agregando nuevo adjudicatario {nif_nuevo} para ID_INTERNO={id_interno_nuevo[:8]}...")
                        df_existente = pd.concat([df_existente, pd.DataFrame([nuevo_reg])], ignore_index=True)
            else:
                # Para otras tablas (requisitos, criterios, docs), reemplazar
                print(f"🔄 Actualizando registros relacionados para ID_INTERNO={id_interno_nuevo[:8]}...")
                df_existente = df_existente[df_existente[id_column] != id_interno_nuevo]
                df_existente = pd.concat([df_existente, registros_nuevos], ignore_index=True)
        else:
            # No existe, agregar todos los registros nuevos
            print(f"✨ Agregando nuevos registros para ID_INTERNO={id_interno_nuevo[:8]}...")
            df_existente = pd.concat([df_existente, registros_nuevos], ignore_index=True)
    
    return df_existente


# ============================================================================
# FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# ============================================================================

def procesar_feed(feed_url, df_general, df_tendering, df_awarding, df_docs, df_adjudicaciones):
    """
    Procesa un feed ATOM y acumula los datos en los DataFrames proporcionados.
    MODIFICADO: Ahora pasa df_general a extraccion_data_relevante para gestión de ID_INTERNO.
    """
    
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
            # MODIFICADO: Ahora pasamos df_general para gestión de ID_INTERNO
            df_temp, df_tend, df_award, df_doc, df_adjudicatarios = extraccion_data_relevante(
                dict_info, 
                df_general  # ← Pasar df_general existente
            )
            
            # Acumular en temporales de este feed
            df_general_temp = pd.concat([df_general_temp, df_temp], ignore_index=True)
            df_tendering_temp = pd.concat([df_tendering_temp, df_tend], ignore_index=True)
            df_awarding_temp = pd.concat([df_awarding_temp, df_award], ignore_index=True)
            df_docs_temp = pd.concat([df_docs_temp, df_doc], ignore_index=True)
            
            # Acumular adjudicatarios solo si hay datos
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
    
    # Actualizar adjudicatarios
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
    
    # Guardar adjudicatarios
    if not df_adjudicatarios.empty:
        df_adjudicatarios.to_parquet(f"{DATA_DIR}/Adjudicatarios_general.parquet", index=False, engine="pyarrow")
        print(f"✅ Guardados {len(df_adjudicatarios)} registros de adjudicatarios")
    else:
        print("ℹ️  No hay adjudicatarios para guardar")
    
    print("✅ DataFrames guardados correctamente")


if __name__ == "__main__":
    main()

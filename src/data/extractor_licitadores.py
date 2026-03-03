import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
import sys, os
from urllib.parse import urljoin
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.extractor_licitaciones import analizar_licitadores_con_llm, mostrar_resultados, exportar_resultados
from utils.filtrador import filtrando_df_general, filtrando_palabras

# ==========================================
# CONFIGURACIÓN
# ==========================================
BATCH_SIZE = 5  # Guardar cada 5 licitaciones procesadas correctamente
ARCHIVO_SALIDA = 'licitadores_llm_progress.json'

# ==========================================
# 1. MÉTODO EXTERNO (Simulación)
# ==========================================
def procesar_pdf_externo(url_pdf, tender_id):
    """
    Este es el método que ya tienes generado aparte.
    Aquí recibes la URL final del PDF para descargarlo o procesarlo.
    """
    
    try:
        # Llamada a tu función LLM
        # Asumo que esta función devuelve un diccionario o lista con los datos
        resultado = analizar_licitadores_con_llm(
            url_pdf, 
            modelo="qwen2.5:32b", 
            usar_tablas=True
        )
        return resultado
        
    except Exception as e:
        print(f"   [ERROR LLM] Fallo al analizar {tender_id}: {e}")
        return None    


# ==========================================
# 2. FUNCIONES DE EXTRACCIÓN
# ==========================================

def buscar_pdf_en_html_principal(soup):
    """
    Busca la fila que contiene "Acta de Mesa de Contratación" y extrae el PDF.
    """
    try:
        # Buscamos un texto que contenga "Acta de Mesa"
        # Usamos expresiones regulares para ser flexibles con mayúsculas/tildes
        target_text = re.compile(r"Acta de Mesa de Contrataci", re.IGNORECASE)
        
        # Buscamos el elemento que contiene el texto (usualmente un span o div)
        element = soup.find(string=target_text)
        
        if element:
            # Subimos hasta encontrar la fila (tr) contenedora
            row = element.find_parent('tr')
            if row:
                # Dentro de la fila, buscamos el enlace (a) que suele tener una imagen de 'Ver' o 'pdf'
                # En tu snippet, el link tiene id que contiene 'linkVerDocPadreGen'
                link = row.find('a', href=True, id=re.compile(r"linkVerDocPadreGen"))
                
                # Si no encuentra por ID, intentamos buscar cualquier href que apunte a 'GetDocumentByIdServlet'
                if not link:
                    link = row.find('a', href=re.compile(r"GetDocumentByIdServlet"))
                
                if link:
                    return link['href']
    except Exception as e:
        print(f"Error parseando HTML: {e}")
    
    return None

def buscar_pdf_en_xml_adjudicacion(soup_html, session):
    """
    Fallback: Busca la fila de 'Adjudicación', extrae el link del XML,
    lo descarga y busca el nodo MinutesDocumentReference -> ACTA_ADJ.
    """
    xml_url = None
    
    # 1. Encontrar el link al XML en la tabla de documentos
    try:
        # soup = BeautifulSoup(response.content, 'html.parser')
        tabla = soup_html.find('table', {'id': 'myTablaDetalleVISUOE'})
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
    except Exception as e:
        print(f"Error buscando link XML: {e}")
        return None
    
    xml_url = url_xml
    if not xml_url:
        return None

    print(f"   -> Inspeccionando XML de Adjudicación: {xml_url}")

    # 2. Descargar y Parsear el XML
    try:
        # Es importante añadir el host si la URL es relativa, aunque en el snippet es absoluta.
        if xml_url.startswith('/'):
            xml_url = 'https://contrataciondelestado.es' + xml_url

        r_xml = session.get(xml_url, timeout=10)
        print(r_xml)
        
        # Usamos 'xml' como parser (requiere lxml instalado)
        soup_xml = BeautifulSoup(r_xml.content, 'xml')

        # 3. Buscar la estructura específica
        # Buscamos todos los MinutesDocumentReference
        minutes_refs = soup_xml.find_all('MinutesDocumentReference') # bs4 ignora el namespace cac: si no es estricto, o lo busca como tag

        if not minutes_refs:
            # Intento alternativo con namespace explicito si bs4 lo parsea así
            minutes_refs = soup_xml.find_all('cac:MinutesDocumentReference')

        for ref in minutes_refs:
            # Buscar el TypeCode
            type_code = ref.find('DocumentTypeCode') or ref.find('cbc:DocumentTypeCode')
            
            if type_code and type_code.text.strip() == 'ACTA_ADJ':
                # Hemos encontrado el acta, buscamos la URI
                attachment = ref.find('Attachment') or ref.find('cac:Attachment')
                if attachment:
                    ext_ref = attachment.find('ExternalReference') or attachment.find('cac:ExternalReference')
                    if ext_ref:
                        uri = ext_ref.find('URI') or ext_ref.find('cbc:URI')
                        # print(uri)
                        if uri:
                            return uri.text.strip()
                            
    except Exception as e:
        print(f"Error procesando contenido XML: {e}")

    return None

# ==========================================
# 3. LOGICA PRINCIPAL
# ==========================================

def main():
    print("Cargando dataset...")
    # Cargar datos
    try:
        df = pd.read_parquet('src/data/Pliegos_general.parquet')
    except FileNotFoundError:
        print("Error: No se encuentra el archivo Pliegos_general.parquet")
        return

    # Filtrar por ESTADO (ADJ o RES)
    # Ajusta los nombres de estado según vengan exactamente en tu parquet
    cpvs_interes = [
        "30000000-9 - Máquinas, equipo y artículos de oficina y de informática, excepto mobiliario y paquetes de software",
        "30100000-0 - Máquinas, equipo y artículos de oficina, excepto ordenadores, impresoras y mobiliario",
        "30200000-1 - Equipo y material informático",
        "30210000-4 - Máquinas procesadoras de datos (hardware)",
        "30230000-0 - Equipo relacionado con la informática",
        "32000000-3 - Equipos de radio, televisión, comunicaciones y telecomunicaciones y equipos conexos",
        "32400000-7 - Redes",
        "32500000-8 - Equipo y material para telecomunicaciones",
        "48510000-6 - Paquetes de software de comunicación",
        "48600000-4 - Paquetes de software de bases de datos y de funcionamiento",
        "48620000-0 - Sistemas operativos",
        "48710000-8 - Paquetes de software de copia de seguridad o recuperación",
        "48730000-4 - Paquetes de software de seguridad",
        "48760000-3 - Paquetes de software de protección antivirus",
        "48780000-9 - Paquetes de software de gestión de sistemas, almacenamiento y contenido",
        "48800000-6 - Sistemas y servidores de información",
        "50300000-8 - Servicios de reparación, mantenimiento y servicios asociados relacionados con ordenadores personales, equipo de oficina, telecomunicaciones y equipo audiovisual",
        "51300000-5 - Servicios de instalación de equipos de comunicaciones",
        "51600000-8 - Servicios de instalación de ordenadores y equipo de oficina",
        "48820000-2 - Servidores"
    ]
    filtros = {'cpv':cpvs_interes,
               'estado':['ADJ', 'RES', 'Adjudicada', 'Resuelta']}
    # print(filtros.get('cpv'))
    
    # print(df['ESTADO'].head())
    # df_filtered = df[df['ESTADO'].str.strip().isin(['ADJ', 'RES', 'Adjudicada', 'Resuelta'])]
    df_filtered = filtrando_df_general(df, filtros)
    
    # --- CAMBIO 1: CARGAR PROCESADOS PREVIAMENTE ---
    nombre_json = 'licitadores_llm_final.json'
    dict_resultados_global = {}
    
    if os.path.exists(nombre_json):
        try:
            with open(nombre_json, 'r', encoding='utf-8') as f:
                dict_resultados_global = json.load(f)
            print(f"Se han cargado {len(dict_resultados_global)} licitaciones ya procesadas.")
        except Exception as e:
            print(f"Error al cargar el JSON existente: {e}")
            dict_resultados_global = {}
    # -----------------------------------------------

    print(f"Total expedientes tras filtro inicial: {len(df_filtered)}")

    inicio_proceso = time.perf_counter()

    # Configurar sesión con headers para parecer un navegador real
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # DICCIONARIO ACUMULATIVO (ESTADO GLOBAL)
    dict_resultados_global = {}
    contador_batch = 0

    for index, row in df_filtered.iterrows():
        tender_url = row.get('URL') # Asegúrate que la columna se llama URL
        tender_id = row.get('ID_INTERNO') # O el ID que uses para identificarlo
        id_licitacion = row.get('ID') # O el ID que uses para identificarlo
        
        if not tender_url:
            continue

        print(f"[{index}] Analizando: {tender_id}: {id_licitacion}")

        try:
            # A) Entrar al Link HTML
            response = session.get(tender_url, timeout=15)
            if response.status_code != 200:
                print(f"   Error cargando página: {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # B) Estrategia 1: Buscar directamente en el HTML (Mesa de contratación)
            pdf_link = buscar_pdf_en_html_principal(soup)
            
            if pdf_link:
                print("   -> PDF encontrado en HTML (Acta Mesa).")
                # print(pdf_link)
                procesado=procesar_pdf_externo(pdf_link, tender_id)
                dict_resultados_global[tender_id]=procesado
                contador_batch+=1
                # 2. EVALUAR SI TOCA GUARDAR (BATCH)
                if contador_batch >= BATCH_SIZE:
                    print(f"--- Guardando lote de {BATCH_SIZE} licitaciones ---")
                    exportar_resultados(
                        dict_resultados_global, 
                        formato='json', 
                        nombre_archivo='licitadores_llm_final' # Sobrescribe el archivo con todo lo acumulado
                    )
                    contador_batch = 0 # Reiniciar contador parcial (no el dict)
            else:
                # C) Estrategia 2: Buscar en el XML de Adjudicación
                print("   -> No hallado en HTML. Buscando en XML de Adjudicación...")
                pdf_link_xml = buscar_pdf_en_xml_adjudicacion(soup, session)
                print(pdf_link_xml)
                
                if pdf_link_xml:
                    print("   -> PDF encontrado en XML (ACTA_ADJ).")
                    procesado=procesar_pdf_externo(pdf_link_xml, tender_id)
                    dict_resultados_global[tender_id]=procesado
                    contador_batch+=1
                    
                    # 2. EVALUAR SI TOCA GUARDAR (BATCH)
                    if contador_batch >= BATCH_SIZE:
                        print(f"--- Guardando lote de {BATCH_SIZE} licitaciones ---")
                        exportar_resultados(
                            dict_resultados_global, 
                            formato='json', 
                            nombre_archivo='licitadores_llm_final' # Sobrescribe el archivo con todo lo acumulado
                        )
                        contador_batch = 0 # Reiniciar contador parcial (no el dict)
                else:
                    print("   -> [WARN] No se encontró Acta ni en HTML ni en XML.")

            # Pausa de cortesía para no saturar el servidor (Importante)
            time.sleep(1) 
            # 2. MARCAR EL FINAL
            fin_proceso = time.perf_counter()
            
            # 3. CALCULAR DURACIÓN
            duracion_total = fin_proceso - inicio_proceso
            minutos = int(duracion_total // 60)
            segundos = duracion_total % 60
            
            # 4. MOSTRAR TIEMPO EN PANTALLA
            print(f"{'='*60}")
            print(f"⏱️  TIEMPO DE EJECUCIÓN TOTAL: {minutos}m {segundos:.2f}s")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"   Error general en fila {index}: {e}")

if __name__ == "__main__":
    main()
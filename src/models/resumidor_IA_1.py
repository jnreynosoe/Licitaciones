import fitz  # PyMuPDF
import re
import json
from sentence_transformers import SentenceTransformer, util
import torch
from rapidfuzz import fuzz
try:
    from vector_db import GestorLicitaciones
except:
    from .vector_db import GestorLicitaciones

import io
import requests

def extract_text_from_pdf(path_or_url):
    """
    Extrae texto de un PDF, desde una ruta local o una URL.
    """
    try:
        # Detectar si es URL
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            print(f"Descargando PDF desde URL: {path_or_url}")
            response = requests.get(path_or_url, timeout=20)
            response.raise_for_status()
            pdf_bytes = io.BytesIO(response.content)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            print(f"Abrir PDF local: {path_or_url}")
            doc = fitz.open(path_or_url)

        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"

        text = re.sub(r"\s+", " ", text)
        return text.strip()

    except Exception as e:
        print(f"⚠️ Error leyendo PDF ({path_or_url}): {e}")
        return ""


# =========================================
# MËTODO PARA DIVIDIR EL TEXTO EN CHUNKS
# =========================================
def dividir_en_chunks(texto, max_palabras=1200):
    palabras = texto.split()
    chunks = []
    for i in range(0, len(palabras), max_palabras):
        chunk = " ".join(palabras[i:i + max_palabras])
        chunks.append(chunk)
    return chunks

# ==========================================
# 2️⃣  FUNCIÓN DE BÚSQUEDA SEMÁNTICA
# ==========================================
def find_semantic_snippet(text, query, model, window=250):
    """
    Busca el fragmento más relevante dentro del texto
    según una consulta semántica.
    """
    sentences = re.split(r"(?<=[\.\n])\s+", text)
    embeddings = model.encode(sentences, convert_to_tensor=True)
    query_emb = model.encode(query, convert_to_tensor=True)
    cos_scores = util.cos_sim(query_emb, embeddings)[0]
    best_idx = torch.argmax(cos_scores).item()
    snippet = " ".join(sentences[max(0, best_idx - 1): best_idx + 2])
    return snippet.strip()


# ==========================================
# 3️⃣  FUNCIÓN DE BÚSQUEDA HEURÍSTICA (REGEX + FUZZY)
# ==========================================
def search_value(patterns, text):
    for pat in patterns:
        m = re.search(pat, text, flags=re.I)
        if m:
            return m.group(1).strip() if m.groups() else m.group(0).strip()
    return None


# ==========================================
# 4️⃣  EXTRACCIÓN DE PRESUPUESTOS
# ==========================================
def extract_presupuesto(text):
    """Extracción robusta de presupuesto con contexto"""
    patterns = [
        r"presupuesto\s+(?:base\s+)?(?:de\s+)?licitación[:\s]+(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€",
        r"valor\s+estimado[:\s]+(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€",
        r"importe\s+(?:total|máximo)[:\s]+(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€",
        r"(?:€|EUR)\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)"
    ]
    
    for pat in patterns:
        matches = re.finditer(pat, text, re.I)
        # Devolver el valor más alto encontrado (suele ser el correcto)
        valores = []
        for m in matches:
            val_str = m.group(1).replace('.', '').replace(',', '.')
            try:
                valores.append(float(val_str))
            except:
                continue
        if valores:
            return f"{max(valores):,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    return None

# ==========================================
# 4️⃣  PIPELINE PRINCIPAL DE ANÁLISIS
# ==========================================
def analizar_pliego(path_pdf, text=None):
    # Extraer texto
    # print(path_pdf)
    if text is None:
        text = extract_text_from_pdf(path_pdf)

    # Cargar modelo semántico
    # model = SentenceTransformer("all-MiniLM-L6-v2")
    # Inicializas el gestor (solo una vez al principio)
    gestor = GestorLicitaciones()

    # PASO 1: Ingesta (Solo se hace la primera vez que ves el PDF)
    # Asumiendo que 'text' es lo que extrajiste del PDF y 'id_licitacion' es único
    gestor.indexar_documento(text, pliego_id="EXP-2025-001", metadatos_extra={"origen": "Pliego Tecnico"})

    # PASO 2: Recuperación (RAG)
    # Ahora pides exactamente lo que necesitas y le pasas ESO a Ollama
    contexto_objeto = gestor.buscar_contexto("objeto del contrato suministro servicios alcance", pliego_id="EXP-2025-001")
    contexto_solvencia = gestor.buscar_contexto("solvencia técnica requisitos facturación certificados ISO", pliego_id="EXP-2025-001")

    # Unimos los fragmentos recuperados para dárselos al LLM
    texto_para_llm = "\n---\n".join(contexto_objeto + contexto_solvencia)

    # Llamada a Ollama (Tu función resumir_texto)
    # Ahora el prompt es mucho más rico porque tiene los trozos exactos
    # resumen = resumir_texto(texto_para_llm)
    # --- DURACIÓN / PLAZO ---
    duracion = search_value([
        r"(?:duración|plazo).{0,50}?(\d+\s*(años|meses|días))"
    ], text)

    presupuesto_mejorado = extract_presupuesto(text)
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # --- CRITERIOS DE ADJUDICACIÓN ---
    criterios = find_semantic_snippet(text, "criterios de adjudicación", model)

    # --- REQUISITOS DEL LICITADOR ---
    requisitos = find_semantic_snippet(text, "requisitos del licitador", model)

    # --- CRITERIOS DE VALORACIÓN ---
    valoracion = find_semantic_snippet(text, "criterios de valoración", model)

    # --- CRITERIOS DE VALORACIÓN ---
    plazos_ejecucion = find_semantic_snippet(text, "plazos de entrega de materiales", model)

    # --- BUSCAR CERTIFICACIONES / ISO ---
    palabras_cert = ["certificación", "ISO","IEC","ISO/IEC", "ENS", "LINCE", "acreditación"]
    certificaciones = []
    for p in palabras_cert:
        if fuzz.partial_ratio(p.lower(), text.lower()) > 80:
            frag = find_semantic_snippet(text, p, model)
            certificaciones.append(frag)

    # --- CONSTRUCCIÓN DEL RESULTADO JSON ---
    data = {
        "contrato": {
            "objeto": contexto_objeto,
            "duracion": duracion,
            "presupuesto_estimado": contexto_objeto,
        },
        "plazo estimado":{
            "duracion de ejecucion": duracion,
            "plazo de entrega": plazos_ejecucion,
        },
        "criterios": {
            "criterios_adjudicacion": criterios,
            "criterios_valoracion": valoracion,
        },
        "requisitos": {
            "requisitos_licitador": requisitos,
            "certificaciones_detectadas": certificaciones,
        },
        'presupuesto_procesado': presupuesto_mejorado,
    }

    return data


# ==========================================
# 5️⃣  RESUMEN AUTOMÁTICO CON MODELO LOCAL
# ==========================================
# def resumir_texto(text, model="deepseek-r1:14b"):
def resumir_texto(text, model="deepseek-r1:14b"):
    import subprocess
    import json

    # prompt = f"""
    # Eres un asistente experto en licitaciones públicas españolas.
    # Tu tarea es generar un resumen detallado.

    # INSTRUCCIONES:
    # - Resume SOLO basándote en la información proporcionada.
    # - Concéntrate en qué se espera del proveedor (mobiliario, suministros, servicios, etc.)
    # - Si faltan datos, indícalo con claridad.
    # - Usa un lenguaje claro y profesional.
    # - Organiza la información con viñetas.
    # - Destaca información importante.

    # TEXTO A RESUMIR:
    # {text}
    # """

    prompt = f"""
    ### ROL
    Actúa como un Consultor Senior de Licitaciones Públicas en España con 20 años de experiencia en análisis de Pliegos (PCA y PPT).

    ### TAREA
    Realiza un análisis técnico y administrativo riguroso del texto proporcionado. Extrae únicamente la información vinculante y crítica para decidir si una empresa debe presentarse.

    ### ESTRUCTURA DE RESPUESTA (Obligatoria)
    1. **OBJETO Y ALCANCE**: Resumen ejecutivo de qué se compra/contrata.
    2. **DATOS ECONÓMICOS**: Presupuesto Base (sin IVA), Valor Estimado y existencia de lotes.
    3. **SOLVENCIA ECONÓMICA Y TÉCNICA**: Requisitos mínimos de facturación y experiencia previa requerida.
    4. **CERTIFICACIONES Y NORMATIVA**: (Ej: ISO 9001, 27001, ENS, Esquema Nacional de Seguridad).
    5. **CRITERIOS DE ADJUDICACIÓN**: Puntuación (precio vs técnica).
    6. **PLAZOS CRÍTICOS**: Plazo de ejecución y fechas clave si aparecen.

    ### REGLAS CRÍTICAS
    - Si un dato no aparece, escribe: "No especificado en este fragmento".
    - Usa tablas Markdown para los datos numéricos si es posible.
    - Mantén un tono técnico, evita adjetivos innecesarios.

    ### TEXTO DEL PLIEGO:
    {text}
    """

    try:
        # CLAVE: Especificar encoding UTF-8
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            encoding='utf-8',  # ← ESTO ES LO IMPORTANTE
            errors='replace',   # ← Reemplaza caracteres problemáticos
            timeout=900,
            check=True
        )
        
        return result.stdout.strip()
    
    except subprocess.TimeoutExpired:
        return "Error: El proceso tardó demasiado tiempo"
    except subprocess.CalledProcessError as e:
        return f"Error al ejecutar Ollama: {e.stderr}"
    except FileNotFoundError:
        return "Error: Ollama no está instalado o no está en el PATH"
    except Exception as e:
        return f"Error inesperado: {str(e)}"
    
import json

def resumir_texto_api(text, model="deepseek-r1:14b"):
    url = "http://localhost:11434/api/generate"
    
    prompt = generar_prompt_licitacion(text)
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False, # Para recibir la respuesta de golpe
        "options": {
            "num_ctx": 8192,  # Aumenta la ventana de contexto si el pliego es largo
            "temperature": 0.1 # Baja temperatura = más precisión, menos creatividad
        }
    }

    try:
        # Timeout de 1200 segundos (20 minutos)
        response = requests.post(url, json=payload, timeout=1200)
        response.raise_for_status()
        
        # DeepSeek-R1 a veces devuelve el "pensamiento" entre etiquetas <think>
        # Puedes decidir si limpiarlo o mostrarlo.
        full_response = response.json()['response']
        return full_response
        
    except requests.exceptions.Timeout:
        return "Error: La IA agotó el tiempo de espera (Timeout)."
    except Exception as e:
        return f"Error en la conexión con Ollama: {str(e)}"
    
def generar_prompt_licitacion(text):
    return f"""
    ### ROL
    Actúa como un Consultor Senior de Licitaciones Públicas en España con 20 años de experiencia en análisis de Pliegos (PCA y PPT).

    ### TAREA
    Realiza un análisis técnico y administrativo riguroso del texto proporcionado. Extrae únicamente la información vinculante y crítica para decidir si una empresa debe presentarse.

    ### ESTRUCTURA DE RESPUESTA (Obligatoria)
    1. **OBJETO Y ALCANCE**: Resumen ejecutivo de qué se compra/contrata.
    2. **DATOS ECONÓMICOS**: Presupuesto Base (sin IVA), Valor Estimado y existencia de lotes.
    3. **SOLVENCIA ECONÓMICA Y TÉCNICA**: Requisitos mínimos de facturación y experiencia previa requerida.
    4. **CERTIFICACIONES Y NORMATIVA**: (Ej: ISO 9001, 27001, ENS, Esquema Nacional de Seguridad).
    5. **CRITERIOS DE ADJUDICACIÓN**: Puntuación (precio vs técnica).
    6. **PLAZOS CRÍTICOS**: Plazo de ejecución y fechas clave si aparecen.

    ### REGLAS CRÍTICAS
    - Si un dato no aparece, escribe: "No especificado en este fragmento".
    - Usa tablas Markdown para los datos numéricos si es posible.
    - Mantén un tono técnico, evita adjetivos innecesarios.

    ### TEXTO DEL PLIEGO:
    {text}
    """

# ----------------------------------------------
# def resumir_texto(text, model="deepseek:14b"):
#     """
#     Llama a un modelo local (por ejemplo DeepSeek o Groq)
#     usando Ollama o HuggingFace. 
#     Aquí se deja preparado para DeepSeek en Ollama.
#     """
#     try:
#         import subprocess, json
#         # Correccion sobre el Prompt
#         prompt = (
#             f"""Eres un asistente experto en licitaciones públicas españolas. 
#             Tu tarea es generar un resumen detallaado para ayudar al usuario a entender
#             los detalles de una licitación específica.

#             INSTRUCCIONES:
#             - Resume SOLO basándote en la información proporcionada en los documentos
#             - Concentrate en que es lo que se espera del usuario, por ejemplo: entrega de mobiliario, suministros, desarrollo etc.
#             - Si no tienes información para resumir, indícalo claramente
#             - Usa un lenguaje claro y profesional
#             - Si detectas información importante, destácala
#             - Estructura tus respuestas con viñetas cuando sea apropiado"""
#         )
#         cmd = ["ollama", "run", model, "--json"]
#         proc = subprocess.run(cmd, input=prompt.encode("utf-8"), capture_output=True)
#         out = proc.stdout.decode("utf-8")
#         # algunos modelos devuelven JSON, otros texto plano
#         try:
#             response = json.loads(out)
#             resumen = response.get("response", out)
#         except Exception:
#             resumen = out
#         return resumen.strip()
#     except Exception as e:
#         return f"[No se pudo resumir automáticamente: {e}]"

def limpiar_basura_pliegos(texto):
    lineas = texto.split('\n')
    texto_filtrado = []
    
    # Palabras que suelen indicar que la línea es basura administrativa/firma
    keywords_basura = [
        "Firmado por:", "Copia Auténtica", "verificadorCopiaAutentica", 
        "Página:", "Código de verificación", "Cargo:", "Fecha:", "http"
    ]
    
    for linea in lineas:
        # Si la línea tiene más de 2 palabras prohibidas, o es muy corta, la descartamos
        if any(key in linea for key in keywords_basura):
            continue
        # Eliminar las marcas de checkboxes que a veces confunden
        linea = linea.replace("☒", " [SI] ").replace("☐", " [NO] ")
        texto_filtrado.append(linea)
    
    return "\n".join(texto_filtrado)

import os
import requests
import tempfile
import fitz
import camelot
from pathlib import Path

def extraer_contexto_maestro(path_or_url, paginas_resumen="1-5"):
    """
    Descarga el PDF si es necesario y extrae tablas y texto de forma segura.
    """
    temp_file_path = None
    
    try:
        # 1. GESTIÓN DE LA RUTA (Local vs URL)
        if path_or_url.startswith(("http://", "https://")):
            print(f"📥 Descargando PDF para análisis de tablas...")
            response = requests.get(path_or_url, timeout=30)
            response.raise_for_status()
            
            # Creamos un archivo temporal físico (Camelot lo necesita en disco)
            fd, temp_file_path = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(response.content)
            path_a_procesar = temp_file_path
        else:
            path_a_procesar = path_or_url

        contexto_maestro = ""

        # 2. EXTRAER TABLAS CON CAMELOT
        # Usamos try/except específico para Camelot por si falla Ghostscript
        try:
            print(f"📊 Extrayendo tablas (Camelot)...")
            tablas = camelot.read_pdf(path_a_procesar, pages=paginas_resumen, flavor='lattice')
            if len(tablas) > 0:
                contexto_maestro += "\n### TABLAS ESTRUCTURADAS (CUADRO RESUMEN) ###\n"
                for i, tabla in enumerate(tablas):
                    contexto_maestro += f"\n[Tabla {i+1}]:\n{tabla.df.to_markdown(index=False)}\n"
        except Exception as e:
            print(f"⚠️ Camelot no pudo procesar tablas: {e}")

        # 3. EXTRAER TEXTO CON PYMUPDF
        print(f"📄 Extrayendo texto de apoyo...")
        doc = fitz.open(path_a_procesar)
        
        # Parsear el rango de páginas (ej: "1-5")
        inicio, fin = map(int, paginas_resumen.split('-'))
        texto_apoyo = ""
        for i in range(inicio-1, min(fin, len(doc))):
            texto_apoyo += doc[i].get_text("text") + "\n"
        
        doc.close() # CRÍTICO: Cerramos el archivo para evitar el PermissionError
        
        contexto_maestro += f"\n### TEXTO ADICIONAL ###\n{texto_apoyo}"
        return contexto_maestro

    except Exception as e:
        return f"❌ Error fatal en la extracción: {str(e)}"

    finally:
        # 4. LIMPIEZA DE ARCHIVOS TEMPORALES
        # Esto soluciona el error de "archivo siendo utilizado por otro proceso"
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print("🧹 Limpieza de archivos temporales completada.")
            except Exception as e:
                print(f"⚠️ No se pudo borrar el temporal: {e}")

def generar_prompt_final(contexto_maestro, fragmentos_busqueda):
    # Unimos los fragmentos que el buscador vectorial encontró en el resto del pliego
    contexto_adicional = "\n---\n".join(fragmentos_busqueda)
    
    return f"""
        Actúa como un analista experto en licitaciones públicas. 
        A continuación te proporciono información clave extraída de un Pliego Administrativo/Técnico.

        ### 1. INFORMACIÓN ESTRUCTURADA (Tablas de importancia crítica)
        {contexto_maestro}

        ### 2. DETALLES ADICIONALES (Encontrados en el resto del pliego)
        {contexto_adicional}

        ### TAREA:
        Genera un resumen ejecutivo. Es vital que:
        - Si hay una tabla, extraigas los importes de cada LOTE (Presupuesto Base, IVA y Valor Estimado).
        - Identifiques los plazos de ejecución y prórrogas.
        - Cruces la información: si en la tabla dice 'Lote 1' y en el texto dice 'Migración Power BI', relaciónalos.

        ### FORMATO:
        Responde en formato Markdown limpio, usando tablas para los datos económicos.
        """


# ==========================================
# 6️⃣  EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    path = "Pliegos\ENTIDADES LOCALES\Comunidad Valenciana\112_2025\TechnicalDocumentReference\PPT.pdf"  # 🔧 coloca aquí tu archivo
    # url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=m9t1F73gX22ok0N70SbGheMuwM01a5uDplNBXFufz5pfCS1JcaRLpdBSHsWih1HvKFUCRWakgo%2BndsMj4Sfwn1h2Kb/wnRzjqsmHbiIdSXh7QB3HKyQaFUExmUVQCerk&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D"
    # url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=TdV3QlxxZrfBnzVcVKR0FzWmfzwROK7s0Vpzr4Ccq7AQQOchN8PVC7q/UK0tJls6nc9w66J/3VSzIwfoHUJlzOUO3BaHEoYi7H40ekuI4VP3GVhXrFFqN7yFncy7YfRK"
    # url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=bp6fcNQe93A%2Bn298IiTo2m7KY1oUI/jCi2xUFVgsXVq5sZxoSOCyXWlMuytYpmiUSWAlpDG6Ld0iGcSfZ/sSQMTV7jPtbZnV5bJ5pBd85U7DdQD9RyhUmzT4jZ2In4zL"
    # url_pdf ="https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=MN%2BlH0uhLuhwrPlkLivu%2By1%2Bb7o4Ti4bRiDWzWf/i4DZ/x%2Bt4Cm2YQKW3N%2BnSSFRC6DyaSnKsAlsNIthQiFnU%2BDDbmwnK1cLNV7J4Ts/Jki1aXEvq3KHa/AEHgtDrQw0"
    # url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=tIrZCRUwj9W3/yAADMTSj49ffQB76SS3SxS2nI5BMV3ozVAUn0IOfVoulebS2Rz3gIDmyScje4Wcj4iX8i5M0BrR%2B%2BSMzH7X7ZwdqM7IqniB0nvVKRzfe4rpHcnlPhSZ"
    # url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=RP%2Bk7tiueJBaIoKQF95g/7ZnexIinmVOu9F/U9IX1rRGEa6zk/Xo1XHMCK4B2fWUV94ElrfO0m2AkSUsTdX4Qa95XaicqgiP8tum1hFD%2B/m1aXEvq3KHa/AEHgtDrQw0"
    # url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=jzNIjSG5nKIm/HTkuLBb/EbEgjCR8vVbxA1awHtzOAGQvNEZKc%2BaDRIS/jNotdCIGkLXY%2BDhk/04C8JLnFN3lr4tm0Z9zcIK2ia0/wJNbDV7QB3HKyQaFUExmUVQCerk"
    # url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=UQ1Vec%2BBnnvGeGrvhqjVorSHy%2BUVWpM/WbTNoAZsBVmR/SJwv8o9ZnwkFdI5Hp/uK1uiYaQ/PU9nWB8Fpf%2BsRmux7yITvSmJYm%2BDDXi9jhJ7QB3HKyQaFUExmUVQCerk" 
    url_pdf = "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D&DocumentIdParam=MjJGBf6MHb29S45JhxzyY/qVU%2BUZ3lctOs9tAWb9iI66qGUcDTonJW4QqvuQ2KiUPO852nvHTmmPVTnL3r37kl%2ByzMtruSvPpOnk/fdsmNSCx2e6p7hqtlp2aFupgHMr"

    text = extract_text_from_pdf(url_pdf)
    # resultado = analizar_pliego(url_pdf, text)

    # print("\n🔹 Información estructurada detectada:\n")
    # print(json.dumps(resultado, indent=2, ensure_ascii=False))
    # print(text)

    gestor = GestorLicitaciones()

    # PASO 1: Ingesta (Solo se hace la primera vez que ves el PDF)
    # Asumiendo que 'text' es lo que extrajiste del PDF y 'id_licitacion' es único
    # gestor.indexar_documento(text, pliego_id="SER-25-0135-MEI", metadatos_extra={"origen": "Pliego Tecnico"})

    # # PASO 2: Recuperación (RAG)
    # # Ahora pides exactamente lo que necesitas y le pasas ESO a Ollama
    # contexto_objeto = gestor.buscar_contexto("objeto del contrato suministro servicios alcance", pliego_id="SER-25-0135-MEI")
    # contexto_solvencia = gestor.buscar_contexto("solvencia técnica requisitos facturación certificados ISO", pliego_id="SER-25-0135-MEI")

    # # Unimos los fragmentos recuperados para dárselos al LLM
    # texto_para_llm = "\n---\n".join(contexto_objeto + contexto_solvencia)
    # # texto_para_llm = limpiar_basura_pliegos(texto_para_llm)

    # # Llamada a Ollama (Tu función resumir_texto)
    # # Ahora el prompt es mucho más rico porque tiene los trozos exactos
    # print("TEXTO PARA RESUMIR")
    # print(texto_para_llm)
    # resumen = resumir_texto_api(texto_para_llm, model="llama3.2:3b")
    # # resumen = resumir_texto(text)
    # print("\n🔹 Resumen general:\n")
    # print(resumen)

    # 1. Extraemos lo más importante con Camelot
    contexto_top = extraer_contexto_maestro(url_pdf)

    # 2. (Opcional) Buscamos en el resto del pliego cosas específicas (solvencia, ISOs)
    # fragmentos = gestor_vectorial.buscar_contexto("solvencia técnica ISO 27001", n_resultados=3)
    fragmentos = [] # Si el PDF es corto, puedes dejarlo vacío

    # 3. Construimos el prompt
    prompt_final = generar_prompt_final(contexto_top, fragmentos)

    # 4. Llamamos a la IA (Ollama con modelo ligero o API)
    resultado = resumir_texto_api(prompt_final, model="llama3.2:3b")
    print(resultado)

    # # # Guardar a JSON
    # with open("pliego_resumen.json", "w", encoding="utf-8") as f:
    #     json.dump(resultado, f, ensure_ascii=False, indent=2)

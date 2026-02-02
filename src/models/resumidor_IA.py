import fitz  # PyMuPDF
import re
import json
from sentence_transformers import SentenceTransformer, util
import torch
from rapidfuzz import fuzz

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
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # --- OBJETO DEL CONTRATO ---
    objeto = find_semantic_snippet(text, "objeto del contrato", model)

    # --- PRESUPUESTO ---
    presupuesto = search_value([
        r"presupuesto.*?([\d\.,]+\s*(€|euros))",
        r"importe\s+total.*?([\d\.,]+\s*(€|euros))",
        r"valor\s+estimado.*?([\d\.,]+\s*(€|euros))"
    ], text)

    # --- DURACIÓN / PLAZO ---
    duracion = search_value([
        r"(?:duración|plazo).{0,50}?(\d+\s*(años|meses|días))"
    ], text)

    presupuesto_mejorado = extract_presupuesto(text)

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
            "objeto": objeto,
            "duracion": duracion,
            "presupuesto_estimado": presupuesto,
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

    prompt = f"""
    Eres un asistente experto en licitaciones públicas españolas.
    Tu tarea es generar un resumen detallado.

    INSTRUCCIONES:
    - Resume SOLO basándote en la información proporcionada.
    - Concéntrate en qué se espera del proveedor (mobiliario, suministros, servicios, etc.)
    - Si faltan datos, indícalo con claridad.
    - Usa un lenguaje claro y profesional.
    - Organiza la información con viñetas.
    - Destaca información importante.

    TEXTO A RESUMIR:
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
    resultado = analizar_pliego(url_pdf, text)

    print("\n🔹 Información estructurada detectada:\n")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    # print(text)
    # resumen = resumir_texto(text)
    # print("\n🔹 Resumen general:\n")
    # print(resumen)

    # Guardar a JSON
    with open("pliego_resumen.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

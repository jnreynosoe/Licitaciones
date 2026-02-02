import json
import pandas as pd
from paddleocr import PaddleOCR
import fitz #PyMuPDF

from pathlib import Path

import camelot

import subprocess
import pprint

OLLAMA_PATH = r"C:\Users\jnreynoso\AppData\Local\Programs\Ollama\ollama.exe"



def extract_text_from_pdf(pdf_path):
    text_pages = []
    doc = fitz.open(pdf_path)
    for page in doc:
        text = page.get_text("text")
        if not text.strip():
            # fallback OCR si no hay texto
            ocr = PaddleOCR(lang='es')
            result = ocr.ocr(page.get_pixmap().tobytes())
            text = "\n".join([line[1][0] for line in result[0]])
        text_pages.append(text)
    return "\n".join(text_pages)

def extract_pdf_blocks(path):
    doc = fitz.open(path)
    all_blocks = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in list(b.keys()):
                for line in b["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        # print(span.keys())
                        print("-"*1000)
                        if text and float(span["size"])>9:

                            # print(f"{text}\nFlags {span["flags"]},Bidi {span["bidi"]}, Char_Flags {span["char_flags"]}, Alpha {span["alpha"]}, Ascender {span["ascender"]}, Descender {span["descender"]}")
                            all_blocks.append({
                                "page": page.number + 1,
                                "text": text,
                                "size": span["size"],
                                "font": span["font"],
                                "bbox": span["bbox"],
                            })
    print("-------"*100)
    print("BLOQUES")
    pprint.pprint(all_blocks)
    return all_blocks

def clean_blocks(blocks):
    cleaned = []
    for b in blocks:
        text = b["text"]
        # Eliminar numeraciones de página, encabezados repetidos, etc.
        if len(text) < 3:
            continue
        if re.match(r"^Página\s+\d+", text, re.IGNORECASE):
            continue
        if re.match(r"^\d+$", text):
            continue
        cleaned.append(b)
    return cleaned

def heuristic_class(block):
    text = block["text"]
    size = block["size"]

    # Título visual
    if size > 14 or text.isupper():
        return "TITULO"
    # Posible tabla
    if len(text.split()) > 5 and all(c.isupper() or c.isspace() for c in text[:30]):
        return "TABLA"
    return "CUERPO"

# --- Clasificación con Ollama ---
def classify_with_ollama(text):
    prompt = (
        f"Clasifica el siguiente fragmento de texto de un documento PDF "
        f"en una de las categorías: TITULO, SUBTITULO, CUERPO u OTRO, "
        f"considera, el porcentaje de mayusculas y si el texto esta en negrita (Bold) en el fragmento.\n"
        f"Devuelve solo la categoría.\n\nTexto:\n{text}"
    )

    result = subprocess.run(
        [OLLAMA_PATH, "run", "mistral", "--json"],
        input=prompt.encode(),
        capture_output=True,
    )
    try:
        output = json.loads(result.stdout.decode())
        return output.get("response", "").strip().upper() or "CUERPO"
    except Exception:
        return "CUERPO"

# --- Combinación heurística + IA ---
def classify_blocks(blocks):
    classified = []
    for b in blocks:
        h_type = heuristic_class(b)
        # Solo consultar a Ollama si hay duda
        if h_type == "CUERPO" and len(b["text"].split()) < 50:
            o_type = classify_with_ollama(b["text"])
            if o_type in ["TITULO", "TABLA", "ANEXO"]:
                h_type = o_type
        b["type"] = h_type
        classified.append(b)
    return classified

# --- Agrupación en secciones ---
def build_sections(blocks):
    sections = []
    current = {"titulo": None, "contenido": []}

    for b in blocks:
        if b["type"] == "TITULO":
            if current["titulo"]:
                sections.append(current)
            current = {"titulo": b["text"], "contenido": []}
        else:
            current["contenido"].append(b["text"])

    if current["titulo"]:
        sections.append(current)
    return sections

# print("🧠 Clasificando con reglas y Ollama...")
# classified = classify_blocks(bloques_limpios)

# print("🗂️ Construyendo secciones...")
# sections = build_sections(classified)

def extraer_tablas_camelot(pdf_path):
    tablas = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')  # 'stream' si no hay bordes
    print(f"Tablas detectadas: {len(tablas)}")
    for i, tabla in enumerate(tablas):
        print(f"\nTabla {i+1}")
        print(tabla.df.head())
    return tablas

def es_anexo(titulo):
    return bool(re.match(r"^\s*ANEXO\s+[IVXLC0-9]+", titulo.upper()))

def agrupar_anexos(lista):
    anexos = []
    otros = []
    actual = None

    for item in lista:
        titulo = item["titulo"].strip()
        if es_anexo(titulo):
            # Si había uno en curso, se guarda
            if actual:
                anexos.append(actual)
            # Inicia nuevo anexo
            actual = {
                "titulo": titulo,
                "contenido": list(item["contenido"])  # copia
            }
        else:
            # Si estamos dentro de un anexo, lo acumulamos
            if actual:
                actual["contenido"].append(titulo)
                actual["contenido"].extend(item["contenido"])
            else:
                # No estamos dentro de un anexo → contenido general
                otros.append(item)

    # Añadir el último anexo
    if actual:
        anexos.append(actual)

    return anexos, otros

import re

def detectar_anexos_inverso(sections):
    anexos_reales = []
    cuerpo = []
    en_anexos = False

    # Recorremos de atrás hacia adelante
    for item in reversed(sections):
        titulo = item["titulo"].strip()
        if re.match(r"^\s*ANEXO\s+[IVXLC0-9]+", titulo.upper()):
            en_anexos = True
            anexos_reales.append(item)
            # Si encontramos ANEXO I, dejamos de buscar
            if re.match(r"^\s*ANEXO\s+I(\.|$)", titulo.upper()):
                break
        elif en_anexos:
            anexos_reales.append(item)
        else:
            cuerpo.append(item)     

def main():
    base_dir = "Pliegos"
    df_awarding_filtrado = pd.read_parquet("Criterios_general.parquet", engine="pyarrow")
    df_tenderer_filtrado = pd.read_parquet("Requisitos_general.parquet", engine="pyarrow")
    df_general_filtrado = pd.read_parquet("Pliegos_general.parquet", engine="pyarrow")
    for index, row in df_general_filtrado.iterrows():
        id_ = row["ID"]
        id_=id_.replace("/","_")
        id_=id_.replace(" ","")
        resultados = [ruta for ruta in Path(base_dir).rglob(id_) if ruta.is_dir()]
        if resultados:
            print(f"✅ Licitación {id_} encontrada en:")
            
            for carpeta_principal in resultados:
                print(f"   📂 {carpeta_principal}")
                
                # Rutas de subcarpetas esperadas
                subcarpetas = ["TechnicalDocumentReference", "LegalDocumentReference"]
                
                for sub in subcarpetas:
                    sub_path = carpeta_principal / sub
                    
                    if sub_path.exists() and sub_path.is_dir():
                        # Buscar PDFs dentro de la subcarpeta
                        pdfs = list(sub_path.rglob("*.pdf"))
                        
                        if pdfs:
                            print(f"   📑 PDFs en {sub}:")
                            for pdf in pdfs:
                                print(f"      - {pdf}")
                        else:
                            print(f"   ⚠️ No se encontraron PDFs en {sub}")
                    else:
                        print(f"   🚫 No existe la carpeta {sub}")
        # print(row['ID'], row['edad'])

from contextlib import redirect_stdout
import sys

if __name__ == "__main__":
    # with open("salida.txt", "w", encoding="utf-8") as f:
    #     with redirect_stdout(f):
            sys.stdout = open("debug_log_tratamiento.txt", "w", encoding="utf-8")
            sys.stderr = sys.stdout 
            main()

    

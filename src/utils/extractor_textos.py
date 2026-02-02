import os
import pandas as pd
from paddleocr import PaddleOCR
import fitz  # PyMuPDF
import requests
import tempfile
import argparse
from datetime import datetime

# OCR global para solo ser inicializado una vez
ocr = PaddleOCR(lang='es')


def descargar_pdf(url):
    """Descarga un PDF desde una URL y devuelve la ruta temporal."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp.write(response.content)
    temp.close()
    
    return temp.name


def extract_text_from_pdf(pdf_path):
    """Extrae texto de un PDF usando PyMuPDF y OCR como fallback."""
    text_pages = []
    doc = fitz.open(pdf_path)
    
    for page in doc:
        text = page.get_text("text")
        if not text.strip():
            # Fallback OCR si no hay texto
            pix = page.get_pixmap()
            result = ocr.ocr(pix.tobytes())
            if result and result[0]:
                text = "\n".join([line[1][0] for line in result[0]])
        text_pages.append(text)
    
    doc.close()
    return "\n".join(text_pages)


def cargar_df_textos(path="Textos_Extraidos.parquet"):
    """Carga el DataFrame de textos extraídos previamente."""
    if os.path.exists(path):
        return pd.read_parquet(path, engine="pyarrow")
    else:
        return pd.DataFrame(columns=["pliego_id", "TEXTO_EXTRAIDO"])


def procesar_docs(df_docs_filtrados, df_existente):
    """Procesa documentos nuevos que no están en el parquet existente."""
    # Filtrar los que NO están ya en el Parquet
    procesar = df_docs_filtrados[~df_docs_filtrados["pliego_id"].isin(df_existente["pliego_id"])]
    
    if procesar.empty:
        print("✅ No hay nuevos documentos por procesar.")
        return pd.DataFrame()
    
    print(f"📄 Procesando {len(procesar)} documentos nuevos...")
    
    textos = []
    for idx, url in enumerate(procesar["URI"], 1):
        try:
            print(f"  [{idx}/{len(procesar)}] Descargando: {url[:50]}...")
            ruta_pdf = descargar_pdf(url)
            texto = extract_text_from_pdf(ruta_pdf)
            os.unlink(ruta_pdf)  # Eliminar archivo temporal
            print(f"  ✓ Extraído ({len(texto)} caracteres)")
        except Exception as e:
            texto = f"Error procesando {url}: {e}"
            print(f"  ✗ Error: {e}")
        textos.append(texto)
    
    procesar = procesar.copy()
    procesar["TEXTO_EXTRAIDO"] = textos
    return procesar


def load_datasets(base_path=r"src\data"):
    """Carga todos los datasets necesarios."""
    print(f"📁 Cargando datasets desde: {os.path.abspath(base_path)}")
    
    try:
        df_general = pd.read_parquet("src\data\Pliegos_general.parquet", engine="pyarrow")
        df_requisitos = pd.read_parquet(os.path.join(base_path, "Requisitos_general.parquet"), engine="pyarrow")
        df_criterios = pd.read_parquet(os.path.join(base_path, "Criterios_general.parquet"), engine="pyarrow")
        df_docs = pd.read_parquet(os.path.join(base_path, "Documentacion_general.parquet"), engine="pyarrow")
        
        print(f"  ✓ Pliegos: {len(df_general)} registros")
        print(f"  ✓ Requisitos: {len(df_requisitos)} registros")
        print(f"  ✓ Criterios: {len(df_criterios)} registros")
        print(f"  ✓ Documentación: {len(df_docs)} registros")
        
    except Exception as e:
        raise RuntimeError(f"❌ Error cargando los archivos parquet: {e}")
    
    # Cargar CPV desde Excel
    try:
        df_cpv = pd.read_excel(os.path.join(base_path, "listado-cpv.xlsx"), header=None)
        df_cpv = df_cpv.iloc[6:, [0, 1]]
        df_cpv.columns = ["codigo", "descripcion"]
        print(f"  ✓ CPV: {len(df_cpv)} códigos")
    except Exception as e:
        print(f"  ⚠️  No se pudo cargar listado-cpv.xlsx: {e}")
        df_cpv = pd.DataFrame(columns=["codigo", "descripcion"])
    
    return df_general, df_requisitos, df_criterios, df_docs, df_cpv


def filtrar_por_dias(df_general, dias):
    """Filtra licitaciones por fecha límite."""
    # Asegurar tipo datetime
    df_general["FECHA_LIMITE"] = pd.to_datetime(df_general["FECHA_LIMITE"], errors="coerce")
    
    hoy = pd.Timestamp.today().normalize()
    limite = hoy + pd.Timedelta(days=dias)
    
    # Filtrar las fechas a partir de la fecha límite
    df_filtrado = df_general[df_general["FECHA_LIMITE"] >= limite]
    
    # Calcular porcentaje respecto al total
    porcentaje = (len(df_filtrado) / len(df_general)) * 100 if len(df_general) > 0 else 0
    
    return df_filtrado, porcentaje


def main(dias_adelante=15, base_path=r"src\data", output_path="Textos_Extraidos.parquet"):
    """
    Función principal para procesar PDFs de licitaciones.
    
    Args:
        dias_adelante: Días hacia adelante para filtrar licitaciones
        base_path: Ruta base donde están los datos
        output_path: Ruta donde guardar el parquet de salida
    """
    print("=" * 60)
    print("🚀 INICIANDO PROCESAMIENTO DE LICITACIONES")
    print("=" * 60)
    print(f"⏰ Fecha actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Filtrando licitaciones con fecha límite >= {dias_adelante} días")
    print()
    
    # 1. Cargar datasets
    df_general, df_requisitos, df_criterios, df_docs, df_cpv = load_datasets(base_path)
    print()
    
    # 2. Cargar textos previamente procesados
    print("📚 Cargando textos previamente procesados...")
    df_previos = cargar_df_textos(output_path)
    print(f"  ✓ {len(df_previos)} documentos ya procesados")
    print()
    
    # 3. Filtrar licitaciones por fecha
    print(f"🔍 Filtrando licitaciones...")
    df_filtradas, pct = filtrar_por_dias(df_general, dias_adelante)
    df_filtradas = df_filtradas.sort_values("FECHA_LIMITE", ascending=True)
    print(f"  ✓ {len(df_filtradas)} licitaciones filtradas ({pct:.1f}% del total)")
    print()
    
    # 4. Obtener documentos asociados
    print("📋 Obteniendo documentos asociados...")
    df_docs_filtrados = df_docs[df_docs["pliego_id"].isin(df_filtradas["ID"])]
    df_docs_filtrados = df_docs_filtrados.dropna()
    print(f"  ✓ {len(df_docs_filtrados)} documentos encontrados")
    print()
    
    # 5. Procesar SOLO los nuevos documentos
    df_nuevos = procesar_docs(df_docs_filtrados, df_previos)
    print()
    
    # 6. Combinar y guardar
    if not df_nuevos.empty:
        print("💾 Guardando resultados...")
        df_textos_actualizado = pd.concat([df_previos, df_nuevos], ignore_index=True)
        df_textos_actualizado.to_parquet(output_path, index=False, engine="pyarrow")
        print(f"  ✓ Guardado en: {output_path}")
        print(f"  ✓ Total documentos: {len(df_textos_actualizado)}")
        print(f"  ✓ Nuevos procesados: {len(df_nuevos)}")
    else:
        print("ℹ️  No hay cambios que guardar")
    
    print()
    print("=" * 60)
    print("✅ PROCESAMIENTO COMPLETADO")
    print("=" * 60)
    
    return df_textos_actualizado if not df_nuevos.empty else df_previos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Procesa PDFs de licitaciones y extrae texto"
    )
    parser.add_argument(
        "--dias",
        type=int,
        default=15,
        help="Días hacia adelante para filtrar licitaciones (default: 15)"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=r"src\data",
        help="Ruta base de los datos (default: data)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="Textos_Extraidos.parquet",
        help="Archivo de salida (default: Textos_Extraidos.parquet)"
    )
    
    args = parser.parse_args()
    
    try:
        df_resultado = main(
            dias_adelante=args.dias,
            base_path=args.data_path,
            output_path=args.output
        )
        print(f"\n📊 Resultado final: {len(df_resultado)} documentos procesados")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
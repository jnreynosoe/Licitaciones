import pandas as pd

# Archivos
ARCHIVO_EXCEL = 'analisis_adjudicaciones.xlsx'
ARCHIVO_PARQUET = r'src\data\Pliegos_general.parquet'

# Cargar datos
print("Cargando archivos...")
df_excel = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Detalle Adjudicaciones')
df_parquet = pd.read_parquet(ARCHIVO_PARQUET)

# COLUMNA CLAVE (Cambia esto por la columna que estás usando para unir, ej: 'expediente' o 'URL')
# Asegúrate de usar el nombre exacto que tiene en cada archivo
col_excel = 'expediente'     # Nombre en tu Excel
col_parquet = 'ID'   # Nombre en tu Parquet (¡Ojo con mayúsculas!)

print(f"\n--- DIAGNÓSTICO DE LA COLUMNA CLAVE ---")

# 1. Chequeo de Nombres de Columna
if col_excel not in df_excel.columns:
    print(f"❌ ERROR: La columna '{col_excel}' no existe en el Excel.")
    print(f"Columnas disponibles en Excel: {list(df_excel.columns)}")
if col_parquet not in df_parquet.columns:
    print(f"❌ ERROR: La columna '{col_parquet}' no existe en el Parquet.")
    print(f"Columnas disponibles en Parquet: {list(df_parquet.columns)}")

# 2. Chequeo de Tipos de Dato (Dtypes)
if col_excel in df_excel.columns and col_parquet in df_parquet.columns:
    print(f"\nTipo de dato en Excel: {df_excel[col_excel].dtype}")
    print(f"Tipo de dato en Parquet: {df_parquet[col_parquet].dtype}")

    # 3. Muestra visual "cruda" (con comillas para ver espacios)
    val_excel = df_excel[col_excel].dropna().iloc[0]
    # Buscamos ese valor en el parquet para comparar
    print(f"\nComparando valor de ejemplo: '{val_excel}'")
    
    match = df_parquet[df_parquet[col_parquet] == val_excel]
    
    if match.empty:
        print(f"⚠️ El valor '{val_excel}' NO se encuentra directamente en el Parquet.")
        print("Posibles causas:")
        # Intentamos buscarlo limpiando
        match_limpio = df_parquet[df_parquet[col_parquet].astype(str).str.strip() == str(val_excel).strip()]
        if not match_limpio.empty:
            val_parquet = match_limpio.iloc[0][col_parquet]
            print(f"   -> ¡ENCONTRADO PERO SUCIO! En Parquet es: '{val_parquet}' (Diferente formato o espacios)")
        else:
            print("   -> No aparece ni limpiando. Revisa si el ID es exactamente el mismo.")
    else:
        print("✅ El valor coincide perfectamente. El problema debe estar en otros registros.")
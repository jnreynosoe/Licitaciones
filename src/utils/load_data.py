import os
import pandas as pd
import tabulate
def load_datasets():
    # Calcula la ruta base del proyecto (no solo del archivo actual)
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    base_path = r"src/data"
    print(f"Buscando archivos en: {os.path.abspath(base_path)}")
    try:
        df_general = pd.read_parquet(os.path.join(base_path, "Pliegos_general.parquet"), engine="pyarrow")
        df_requisitos = pd.read_parquet(os.path.join(base_path, "Requisitos_general.parquet"), engine="pyarrow")
        df_criterios = pd.read_parquet(os.path.join(base_path, "Criterios_general.parquet"), engine="pyarrow")
        df_docs = pd.read_parquet(os.path.join(base_path, "Documentacion_general.parquet"), engine="pyarrow")

        # return df_general, df_requisitos, df_criterios, df_docs

    except Exception as e:
        raise RuntimeError(f"❌ Error cargando los archivos parquet: {e}")
    
    # Ejemplo adicional: CPV desde Excel
    try:
        df_cpv = pd.read_excel(os.path.join(base_path, "listado-cpv.xlsx"), header=None)
        df_cpv = df_cpv.iloc[6:, [0, 1]]  # columnas y filas que mencionaste
        df_cpv.columns = ["codigo", "descripcion"]
    except Exception as e:
        print(f"⚠️ No se pudo cargar listado-cpv.xlsx: {e}")
        df_cpv = pd.DataFrame(columns=["codigo", "descripcion"])

    return df_general, df_requisitos, df_criterios, df_docs, df_cpv

def load_dataset(base_path, dataset_name):
    try:
        df = pd.read_parquet(os.path.join(base_path, dataset_name), engine="pyarrow")


    except Exception as e:
        raise RuntimeError(f"❌ Error cargando los archivos parquet: {e}")
    

    return df

# from tabulate import tabulate
# print(tabulate(load_datasets()[3]))
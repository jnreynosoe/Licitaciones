import pandas as pd
import ast
import re
from datetime import datetime

def filtrando_df_general(df_general, filtros):
    df_filtrado = df_general.copy()

    import re

    # --- Filtro por palabras clave ---
    if filtros.get("palabras_clave"):
        palabras = [p.lower() for p in filtros["palabras_clave"]]

        def contiene_palabras(texto):
            if not isinstance(texto, str):
                return False
            
            texto = texto.lower()

            # Construir patrón que busque coincidencias exactas de cada palabra
            patrones = [rf"\b{re.escape(p)}\b" for p in palabras]

            return any(re.search(pat, texto) for pat in patrones)

        mask_general = df_filtrado["NOMBRE_PROYECTO"].apply(contiene_palabras)
        df_filtrado = df_filtrado[mask_general]
    # if filtros.get("palabras_clave"):
    #     palabras = [p.lower() for p in filtros["palabras_clave"]]
        
    #     def contiene_palabras(texto):
    #         if not isinstance(texto, str):
    #             return False
    #         t = texto.lower()
    #         return any(p in t for p in palabras)

    #     # Filtra por coincidencias en campos generales
    #     mask_general = df_filtrado["NOMBRE_PROYECTO"].apply(contiene_palabras)
        
    #     df_filtrado = df_filtrado[mask_general]

    # --- Filtro por CPV (lista de códigos dentro de cada celda) ---
    if filtros.get("cpv"):
        codigos_cpv = [c.split("-")[0] for c in filtros["cpv"]]

        def tiene_cpv_en_filtros(cpv_list):
            if isinstance(cpv_list, str):
                try:
                    cpv_list = ast.literal_eval(cpv_list)
                except Exception:
                    return False
            return any(c in cpv_list for c in codigos_cpv)
        
        df_filtrado = df_filtrado[df_filtrado["CPV"].apply(tiene_cpv_en_filtros)]

    if filtros.get("lugar") and filtros.get("lugar")=="Todos":
        filtros["lugar"]=None

    # --- Filtro por lugar ---
    if filtros.get("lugar"):
        df_filtrado = df_filtrado[df_filtrado["UBICACION"].str.contains(
            filtros.get("lugar"), case=False, na=False
        )]

    # --- NUEVO: Filtro por estado ---}
    if filtros.get("estados"):
        # print("Valores filtro ESTADO:", filtros["estados"])
        # print("Valores únicos ESTADO DF:", df_filtrado["ESTADO"].unique())

        df_filtrado = df_filtrado[
            df_filtrado["ESTADO"].astype(str).str.strip().isin(
                [str(x).strip() for x in filtros["estados"]]
        )
    ]
        # print("FILTROS APLICADOS", filtros)

    # --- NUEVO: Filtro por fecha límite ---
    if filtros.get("fecha_desde") or filtros.get("fecha_hasta"):
        def parsear_fecha(fecha_str):
            """Intenta parsear una fecha en múltiples formatos comunes"""
            if pd.isna(fecha_str) or not isinstance(fecha_str, str):
                return None
            
            formatos = [
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%Y/%m/%d",
                "%d.%m.%Y",
            ]
            
            for formato in formatos:
                try:
                    return datetime.strptime(fecha_str.strip(), formato)
                except ValueError:
                    continue
            return None
        
        # Crear columna temporal con fechas parseadas
        df_filtrado["FECHA_LIMITE_DT"] = df_filtrado["FECHA_LIMITE"].apply(parsear_fecha)
        
        if filtros.get("fecha_desde"):
            df_filtrado = df_filtrado[
                (df_filtrado["FECHA_LIMITE_DT"].isna()) | 
                (df_filtrado["FECHA_LIMITE_DT"] >= filtros["fecha_desde"])
            ]
        
        if filtros.get("fecha_hasta"):
            df_filtrado = df_filtrado[
                (df_filtrado["FECHA_LIMITE_DT"].isna()) | 
                (df_filtrado["FECHA_LIMITE_DT"] <= filtros["fecha_hasta"])
            ]
        
        # Eliminar columna temporal
        # print("FECHAS LIMIT", df_filtrado["FECHA_LIMITE_DT"].iloc[0],filtros["fecha_desde"], filtros["fecha_hasta"])
        df_filtrado = df_filtrado.drop(columns=["FECHA_LIMITE_DT"])

    # --- NUEVO: Filtro por fecha de publicación ---
    if filtros.get("fecha_desde_publicado") or filtros.get("fecha_hasta_publicado"):
        def parsear_fecha(fecha_str):
            """Intenta parsear una fecha en múltiples formatos comunes"""
            if pd.isna(fecha_str) or not isinstance(fecha_str, str):
                return None
            
            formatos = [
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%Y/%m/%d",
                "%d.%m.%Y",
            ]
            
            for formato in formatos:
                try:
                    return datetime.strptime(fecha_str.strip(), formato)
                except ValueError:
                    continue
            return None
        
        # Crear columna temporal con fechas parseadas
        df_filtrado["FECHA_PUBLICACION_DT"] = df_filtrado["FECHA_PUBLICACION"].apply(parsear_fecha)
        # print('FECHAS PUBLICACION',df_filtrado["FECHA_PUBLICACION_DT"], filtros["fecha_desde_publicado"], filtros["fecha_hasta_publicado"])
        
        if filtros.get("fecha_desde_publicado"):
            df_filtrado = df_filtrado[
                (df_filtrado["FECHA_PUBLICACION_DT"].isna()) | 
                (df_filtrado["FECHA_PUBLICACION_DT"] >= filtros["fecha_desde_publicado"])
            ]
        
        if filtros.get("fecha_hasta_publicado"):
            df_filtrado = df_filtrado[
                (df_filtrado["FECHA_PUBLICACION_DT"].isna()) | 
                (df_filtrado["FECHA_PUBLICACION_DT"] <= filtros["fecha_hasta_publicado"])
            ]
        
        # Eliminar columna temporal
        df_filtrado = df_filtrado.drop(columns=["FECHA_PUBLICACION_DT"])

    # --- Filtro por importe (limpia texto como "79.000 EUR" o "79 000 EUR") ---
    if "importe_min" in filtros and "importe_max" in filtros:
        def limpiar_importe(x):
            if isinstance(x, str):
                limpio = re.sub(r"[^\d.,]", "", x)
                limpio = limpio.replace(",", ".")
                try:
                    return float(limpio)
                except ValueError:
                    return None
            return x

        df_filtrado["IMPORTE_NUM"] = df_filtrado["IMPORTE"].apply(limpiar_importe)

        df_filtrado = df_filtrado[
            (df_filtrado["IMPORTE_NUM"] >= filtros["importe_min"]) &
            (df_filtrado["IMPORTE_NUM"] <= filtros["importe_max"])
        ]

    # --- Filtro por entidad ---
    # print(df_filtrado["ENTIDAD"])
    # df_filtrado["ENTIDAD_REAL"] = df_filtrado["ruta_json"].str.split("\\").str[1]## Se comento porque en la tabla Pliegos se agrego esta columna
    # print(df_filtrado["SECTOR_PUBLICO"])
    if filtros.get("entidades"):
        df_filtrado = df_filtrado[df_filtrado["SECTOR_PUBLICO"].isin(filtros["entidades"])]

    return df_filtrado


def criterios_filtrado(criterios_general, df_filtrado):
    """
    Filtra la tabla de criterios en base a los pliegos del dataframe general filtrado.
    """
    if criterios_general is None or df_filtrado is None or df_filtrado.empty:
        return criterios_general.iloc[0:0]

    ids_validos = set(df_filtrado["ID"].unique())
    return criterios_general[criterios_general["pliego_id"].isin(ids_validos)]


def requisitos_filtrado(requisitos_general, df_filtrado):
    """
    Filtra la tabla de requisitos en base a los pliegos del dataframe general filtrado.
    """
    if requisitos_general is None or df_filtrado is None or df_filtrado.empty:
        return requisitos_general.iloc[0:0]

    ids_validos = set(df_filtrado["ID"].unique())
    return requisitos_general[requisitos_general["pliego_id"].isin(ids_validos)]


def documentos_filtrado(documentos_general, df_filtrado):
    """
    Filtra la tabla de documentos en base a los pliegos del dataframe general filtrado.
    """
    if documentos_general is None or df_filtrado is None or df_filtrado.empty:
        return documentos_general.iloc[0:0]

    ids_validos = set(df_filtrado["ID"].unique())
    return documentos_general[documentos_general["pliego_id"].isin(ids_validos)]


def filtrar_bd(df_general, df_criterios, df_requisitos, df_documentos, filtros, df_textos):
    general_filtrado = filtrando_df_general(df_general, filtros)
    criterios_filtrados = criterios_filtrado(df_criterios, general_filtrado)
    requisitos_filtrados = requisitos_filtrado(df_requisitos, general_filtrado)
    documentos_filtrados = documentos_filtrado(df_documentos, general_filtrado)

    # --- Extensión del filtro por palabras clave ---
    if filtros.get("palabras_clave"):
        palabras = [p.lower() for p in filtros["palabras_clave"]]

        def contiene_palabras(texto):
            if not isinstance(texto, str):
                return False
            t = texto.lower()
            return any(p in t for p in palabras)

        ids_encontrados = set(general_filtrado["ID"])

        # Buscar coincidencias en criterios
        if df_criterios is not None and not df_criterios.empty:
            ids_en_criterios = set(
                df_criterios.loc[
                    df_criterios["DESCRIPCION"].apply(contiene_palabras), 
                    "pliego_id"
                ]
            )
            ids_encontrados |= ids_en_criterios

        # Buscar coincidencias en requisitos
        if df_requisitos is not None and not df_requisitos.empty:
            ids_en_requisitos = set(
                df_requisitos.loc[
                    df_requisitos["DESCRIPCION"].apply(contiene_palabras), 
                    "pliego_id"
                ]
            )
            ids_encontrados |= ids_en_requisitos

        # Buscar coincidencias en documentos (solo si el checkbox está activado)
        # if filtros.get("incluir_pdf") and df_documentos is not None and not df_documentos.empty:
        #     ids_en_docs = set(
        #         df_documentos.loc[
        #             df_documentos["texto_extraido"].apply(contiene_palabras), 
        #             "pliego_id"
        #         ]
        #     )
        #     ids_encontrados |= ids_en_docs

        if filtros.get("incluir_pdf") and df_textos is not None and not df_textos.empty:
            ids_en_docs = set(
                df_textos.loc[
                    df_textos["TEXTO_EXTRAIDO"].apply(contiene_palabras), 
                    "pliego_id"
                ]
            )
            ids_encontrados |= ids_en_docs

        # Mantener solo los IDs donde haya coincidencias
        general_filtrado = general_filtrado[general_filtrado["ID"].isin(ids_encontrados)]

        # Actualizar tablas relacionadas
        criterios_filtrados = criterios_filtrado(df_criterios, general_filtrado)
        requisitos_filtrados = requisitos_filtrado(df_requisitos, general_filtrado)
        documentos_filtrados = documentos_filtrado(df_documentos, general_filtrado)

    return general_filtrado, criterios_filtrados, requisitos_filtrados, documentos_filtrados
##DESCOMENTAR PARA VOLVER A ANTERIOR
# def filtrar_bd(df_general, df_criterios, df_requisitos, df_documentos, filtros):
#     """
#     Aplica todos los filtros sobre la base de datos principal y sus tablas relacionadas.
#     """
#     # Filtrado principal
#     general_filtrado = filtrando_df_general(df_general, filtros)

#     # Tablas relacionadas (solo las filas correspondientes a los IDs filtrados)
#     criterios_filtrados = criterios_filtrado(df_criterios, general_filtrado)
#     requisitos_filtrados = requisitos_filtrado(df_requisitos, general_filtrado)
#     documentos_filtrados = documentos_filtrado(df_documentos, general_filtrado)

#     return general_filtrado, criterios_filtrados, requisitos_filtrados, documentos_filtrados
# import os
# base_path = r"src\data"
# df_general = pd.read_parquet(os.path.join(base_path, "Pliegos_general.parquet"), engine="pyarrow")
# # print(df_general["CPV"], df_general["IMPORTE"])
# df_requisitos = pd.read_parquet(os.path.join(base_path, "Requisitos_general.parquet"), engine="pyarrow")
# df_criterios = pd.read_parquet(os.path.join(base_path, "Criterios_general.parquet"), engine="pyarrow")
# df_docs = pd.read_parquet(os.path.join(base_path, "Documentacion_general.parquet"), engine="pyarrow")

# # Supongamos:
# filtros = {
#     "cpv": ["34955100-7 - Redes"],
#     "lugar": [],
#     "importe_min": 0,
#     "importe_max": 500000,
#     "entidades": []
# }

# general_f, criterios_f, requisitos_f, docs_f = filtrar_bd(
#     df_general, df_criterios, df_requisitos, df_docs, filtros
# )

# print("General filtrado:", len(general_f))
# print("Criterios filtrados:", len(criterios_f))
# print("Requisitos filtrados:", len(requisitos_f))
# print("Docs filtrados:", len(docs_f))

def filtrando_palabras(df_general, df_criterios, df_requisitos, df_documentos, palabras):
    pass
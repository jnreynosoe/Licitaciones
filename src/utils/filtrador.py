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
        mask_id = df_filtrado["ID"].apply(contiene_palabras)

        df_filtrado = df_filtrado[mask_general | mask_id]
        # df_filtrado = df_filtrado[mask_general]
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
        # print("ENTRO")
        codigos_cpv = [c.split("-")[0] for c in filtros["cpv"]]
        # print(codigos_cpv)

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

    # ids_validos = set(df_filtrado["ID"].unique())
    # return criterios_general[criterios_general["pliego_id"].isin(ids_validos)]
    ids_validos = set(df_filtrado["ID_INTERNO"].unique()) ## POST CAMBIO
    return criterios_general[criterios_general["ID_INTERNO"].isin(ids_validos)]## POST CAMBIO


def requisitos_filtrado(requisitos_general, df_filtrado):
    """
    Filtra la tabla de requisitos en base a los pliegos del dataframe general filtrado.
    """
    if requisitos_general is None or df_filtrado is None or df_filtrado.empty:
        return requisitos_general.iloc[0:0]

    # ids_validos = set(df_filtrado["ID"].unique())
    # return requisitos_general[requisitos_general["pliego_id"].isin(ids_validos)]
    ids_validos = set(df_filtrado["ID_INTERNO"].unique())
    return requisitos_general[requisitos_general["ID_INTERNO"].isin(ids_validos)]


def documentos_filtrado(documentos_general, df_filtrado):
    """
    Filtra la tabla de documentos en base a los pliegos del dataframe general filtrado.
    """
    if documentos_general is None or df_filtrado is None or df_filtrado.empty:
        return documentos_general.iloc[0:0]

    # ids_validos = set(df_filtrado["ID"].unique())
    # return documentos_general[documentos_general["pliego_id"].isin(ids_validos)]
    ids_validos = set(df_filtrado["ID_INTERNO"].unique())
    return documentos_general[documentos_general["ID_INTERNO"].isin(ids_validos)]

def adjudicatarios_filtrado(documentos_general, df_filtrado):
    """
    Filtra la tabla de documentos en base a los pliegos del dataframe general filtrado.
    """
    if documentos_general is None or df_filtrado is None or df_filtrado.empty:
        return documentos_general.iloc[0:0]

    # ids_validos = set(df_filtrado["ID"].unique())
    # return documentos_general[documentos_general["pliego_id"].isin(ids_validos)]
    ids_validos = set(df_filtrado["ID_INTERNO"].unique())
    return documentos_general[documentos_general["ID_INTERNO"].isin(ids_validos)]

def filtrar_bd(df_general, df_criterios, df_requisitos, df_documentos, filtros, df_textos, df_adjudicatarios):
    general_filtrado = filtrando_df_general(df_general, filtros)
    criterios_filtrados = criterios_filtrado(df_criterios, general_filtrado)
    requisitos_filtrados = requisitos_filtrado(df_requisitos, general_filtrado)
    documentos_filtrados = documentos_filtrado(df_documentos, general_filtrado)
    adjudicatarios_filtrados = adjudicatarios_filtrado(df_adjudicatarios, general_filtrado)

    # --- Extensión del filtro por palabras clave ---
    if filtros.get("palabras_clave"):
        palabras = [p.lower() for p in filtros["palabras_clave"]]

        def contiene_palabras(texto):
            if not isinstance(texto, str):
                return False
            t = texto.lower()
            return any(p in t for p in palabras)
        
        ## ESTO ES PARA PERMITIR BUSQUEDAS POR ID LICITACION --------
        ids_encontrados = set(general_filtrado["ID_INTERNO"])
        
        ## BUSCAMOS COINCIDENCIAS DIRECTAS DE ID
        ids_coincidencia_directa = set(
            df_general.loc[df_general["ID"].apply(contiene_palabras),
                           "ID_INTERNO"]
        )
        ids_encontrados |= ids_coincidencia_directa

        # Buscar coincidencias en criterios
        if df_criterios is not None and not df_criterios.empty:
            ids_en_criterios = set(
                df_criterios.loc[
                    df_criterios["DESCRIPCION"].apply(contiene_palabras), 
                    "ID_INTERNO"
                ]
            )
            ids_encontrados |= ids_en_criterios

        # Buscar coincidencias en requisitos
        if df_requisitos is not None and not df_requisitos.empty:
            ids_en_requisitos = set(
                df_requisitos.loc[
                    df_requisitos["DESCRIPCION"].apply(contiene_palabras), 
                    "ID_INTERNO"
                ]
            )
            ids_encontrados |= ids_en_requisitos
            
        # Buscar coincidencias en adjudicatarios
        if df_adjudicatarios is not None and not df_adjudicatarios.empty:
            ids_en_adjudicatarios = set(
                df_adjudicatarios.loc[
                    df_adjudicatarios["NOMBRE_ADJUDICATARIO"].apply(contiene_palabras), 
                    "ID_INTERNO"
                ].astype(str).str.strip()
            )
            ids_encontrados |= ids_en_adjudicatarios
        

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
                    "ID_INTERNO"
                ]
            )
            ids_encontrados |= ids_en_docs
        print("IDS ENCONTRADOS", ids_encontrados)
        print(ids_en_adjudicatarios)

        # Mantener solo los IDs donde haya coincidencias
        general_filtrado["ID_INTERNO"] = general_filtrado["ID_INTERNO"].astype(str).str.strip()
        # print(general_filtrado.head())
        if ids_en_adjudicatarios:
            # general_filtrado = df_general[df_general["ID_INTERNO"].isin(ids_encontrados)]
            general_filtrado = general_filtrado[general_filtrado["ID_INTERNO"].isin(ids_encontrados)]
            # pass
        else:
            general_filtrado = general_filtrado[general_filtrado["ID_INTERNO"].isin(ids_encontrados)]
        print("GENERAL FILTRADO", general_filtrado.head())

        # Actualizar tablas relacionadas
        criterios_filtrados = criterios_filtrado(df_criterios, general_filtrado)
        requisitos_filtrados = requisitos_filtrado(df_requisitos, general_filtrado)
        documentos_filtrados = documentos_filtrado(df_documentos, general_filtrado)

    return general_filtrado, criterios_filtrados, requisitos_filtrados, documentos_filtrados

def filtrando_palabras(df_general, df_criterios, df_requisitos, df_documentos, palabras):
    pass
# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns

# # 1. Configuración de la "Watchlist" (Empresas a monitorear)
# nifs_interes = [
#     'B98513260', 'A97929566', 'B05424700', 'B96273032', 
#     'B46992731', 'B19925676', 'B98064462', 'B97701312', 
#     'A97390793', 'A46752374', 'B98336704'
# ]

# def generar_informe_competencia(archivo):
#     # Cargar datos
#     archivo_detalle = pd.read_excel(archivo, sheet_name='Detalle Adjudicaciones')
#     archivo_estadisticas = pd.read_excel(archivo, sheet_name='Estadísticas')
#     # df = pd.read_csv(archivo_detalle)
#     df=archivo_detalle
#     # stats_gen = pd.read_csv(archivo_estadisticas)
#     stats_gen = archivo_estadisticas
    
#     # Filtrar solo nuestras empresas de interés
#     df_comp = df[df['nif'].isin(nifs_interes)].copy()
    
#     if df_comp.empty:
#         print("No se encontraron registros para los NIFs seleccionados.")
#         return

#     print("--- 📊 INFORME DE POSICIONAMIENTO ESTRATÉGICO ---")
    
#     # --- KPI 1: Cuota de Mercado en el Set de Datos ---
#     total_mercado_iva = df['importe_con_iva'].sum()
#     total_grupo_iva = df_comp['importe_con_iva'].sum()
#     market_share = (total_grupo_iva / total_mercado_iva) * 100
    
#     print(f"\n✅ Volumen Total del Grupo: {total_grupo_iva:,.2f} €")
#     print(f"✅ Cuota de Captación: {market_share:.2f}% del total analizado")

#     # --- KPI 2: Análisis por Empresa (Licitaciones y Valor) ---
#     resumen = df_comp.groupby('nombre').agg({
#         'uuid': 'count',
#         'importe_con_iva': 'sum',
#         'cpvs': lambda x: "; ".join(set(x))
#     }).rename(columns={'uuid': 'Licitaciones_Ganadas', 'importe_con_iva': 'Total_€'}).sort_values('Total_€', ascending=False)
    
#     print("\n--- Ranking del Grupo de Interés ---")
#     print(resumen[['Licitaciones_Ganadas', 'Total_€']])

#     # --- KPI 3: Especialización por CPV ---
#     # Separamos los CPVs ya que pueden venir varios en una celda
#     cpvs_series = df_comp['cpvs'].str.split('; ').explode()
#     top_cpvs = cpvs_series.value_counts().head(5)
    
#     print("\n--- Sectores Dominantes (Top 5 CPVs) ---")
#     print(top_cpvs)

#     # --- Visualización ---
#     plt.figure(figsize=(12, 6))
#     sns.barplot(data=resumen.reset_index(), x='Total_€', y='nombre', palette='viridis')
#     plt.title('Capacidad de Captación por Empresa (Euros Adjudicados)')
#     plt.tight_layout()
#     plt.show()

# # Ejecutar el análisis
# # generar_informe_competencia('analisis_adjudicaciones.xlsx - Detalle Adjudicaciones.csv', 'analisis_adjudicaciones.xlsx - Estadísticas.csv')
# generar_informe_competencia('analisis_adjudicaciones.xlsx')

# import pandas as pd
# from reportlab.lib.pagesizes import A4
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
# from reportlab.lib.units import cm

# # --- CONFIGURACIÓN ---
# ARCHIVO_EXCEL = 'analisis_adjudicaciones.xlsx'
# ARCHIVO_PARQUET = r'src\data\Pliegos_general_aux.parquet'
# ARCHIVO_SALIDA_PDF = 'Informe_Licitaciones_Empresas.pdf'

# # NIFs de interés (Tu lista)
# NIFS_GRUPO = [
#     'B98513260', 'A97929566', 'B96273032', 
#     'B46992731', 'B19925676', 'A91834036',
#     'B19959329', 'A80929490',
#     "B61172219", 'A33845009', '47232180R', 
#     'B96377882', 'B96949425'
# ]

# # --- Añadir esto a tu sección de CONFIGURACIÓN ---
# CPVS_ENETIC_RAW = [
#     "30000000-9 - Máquinas, equipo y artículos de oficina...",
#     "30100000-0 - Máquinas, equipo y artículos de oficina...",
#     "30200000-1 - Equipo y material informático",
#     "30210000-4 - Máquinas procesadoras de datos (hardware)",
#     "30230000-0 - Equipo relacionado con la informática",
#     "32000000-3 - Equipos de radio, televisión...",
#     "32400000-7 - Redes",
#     "32500000-8 - Equipo y material para telecomunicaciones",
#     "48510000-6 - Paquetes de software de comunicación",
#     "48600000-4 - Paquetes de software de bases de datos...",
#     "48620000-0 - Sistemas operativos",
#     "48710000-8 - Paquetes de software de copia de seguridad...",
#     "48730000-4 - Paquetes de software de seguridad",
#     "48760000-3 - Paquetes de software de protección antivirus",
#     "48780000-9 - Paquetes de software de gestión de sistemas...",
#     "48800000-6 - Sistemas y servidores de información",
#     "50300000-8 - Servicios de reparación, mantenimiento...",
#     "51300000-5 - Servicios de instalación de equipos...",
#     "51600000-8 - Servicios de instalación de ordenadores...",
#     "48820000-2 - Servidores",
#     "48000000-8 Paquetes de software y sistemas de información",
#     "72000000-5 Servicios TI: consultoría, desarrollo de software, Internet y apoyo",
# ]

# # Extraemos solo el código numérico para comparar fácilmente (ej: '30200000')
# CPVS_ENETIC_CODES = [c.split(' - ')[0].split('-')[0].strip() for c in CPVS_ENETIC_RAW]

# def cargar_y_fusionar_datos():
#     print("🚀 Iniciando carga y limpieza de datos...")
    
#     # 1. Cargar fuentes
#     df_detalle = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Detalle Adjudicaciones')
#     df_parquet = pd.read_parquet(ARCHIVO_PARQUET)
    
#     # 2. Definir nombres de columnas (ajusta si en el parquet se llama diferente)
#     col_excel = 'expediente'
#     col_parquet = 'ID' 

#     # 3. NORMALIZACIÓN AGRESIVA
#     # Convertimos a string, quitamos espacios y (opcional) pasamos a mayúsculas
#     df_detalle['key_clean'] = df_detalle[col_excel].astype(str).str.strip().str.upper()
#     df_parquet['key_clean'] = df_parquet[col_parquet].astype(str).str.strip().str.upper()

#     print(f"Muestra de llave Excel: '{df_detalle['key_clean'].iloc[0]}'")
#     print(f"Muestra de llave Parquet: '{df_parquet['key_clean'].iloc[0]}'")

#     # 4. MERGE
#     # Traemos del parquet solo lo que necesitamos: la llave limpia, el nombre y el link
#     # Nota: Asegúrate de que 'NOMBRE_PROYECTO' y 'URL' existan en tu parquet
#     df_final = pd.merge(
#         df_detalle, 
#         df_parquet[['key_clean', 'NOMBRE_PROYECTO', 'URL']], 
#         on='key_clean', 
#         how='left'
#     )

#     # 5. Renombrar para que el generador de PDF encuentre las columnas
#     df_final.rename(columns={
#         'NOMBRE_PROYECTO': 'nombre_licitacion',
#         'URL': 'link_licitacion'
#     }, inplace=True)

#     # Verificación de éxito
#     exitos = df_final['nombre_licitacion'].notna().sum()
#     print(f"✅ Cruce completado: {exitos} licitaciones encontradas en el Parquet de un total de {len(df_final)}.")
    
#     return df_final, df_parquet

# def limpiar_cpvs(cpv_string):
#     """Convierte la cadena de CPVs en una lista limpia y única"""
#     if pd.isna(cpv_string): return "N/A"
#     # Separar por punto y coma, quitar espacios y códigos vacíos
#     lista = [c.strip() for c in str(cpv_string).split(';') if c.strip()]
#     # Eliminar duplicados manteniendo orden
#     return list(dict.fromkeys(lista))

# from collections import Counter

# def obtener_cpvs_mercado(df):
#     contador = Counter()

#     for cpv_str in df['cpvs'].dropna():
#         cpvs = limpiar_cpvs(cpv_str)
#         cpvs = [c.split(" - ")[0] for c in cpvs]
#         contador.update(cpvs)

#     return contador

# def generar_pdf():
#     # 1. Preparación de datos
#     df, df_parquet = cargar_y_fusionar_datos()
    
#     # Intentar enriquecer df con el nombre del parquet (Simulacion de merge)
#     # Si tienes una columna clave común, descomenta esto:
#     # df = pd.merge(df, df_parquet[['URL', 'OBJETO_LICITACION']], on='URL', how='left')
    
#     # Si no logramos cruzar, usaremos un placeholder o el nombre si existe
#     if 'nombre_licitacion' not in df.columns:
#         # Intentamos buscarlo en el parquet usando el expediente como clave
#         # Asegúrate de que los nombres de columnas coincidan con tu realidad
#         if 'expediente' in df.columns and 'ID' in df_parquet.columns:
#              df = pd.merge(df, df_parquet[['ID', 'NOMBRE_PROYECTO', 'URL']], 
#                            left_on='expediente', right_on='ID', how='left')
#              df.rename(columns={'NOMBRE_PROYECTO': 'nombre_licitacion', 'URL': 'link_licitacion'}, inplace=True)
#              print(df)
#         else:
#             df['nombre_licitacion'] = "Nombre no disponible (Revisar cruce)"
#             df['link_licitacion'] = "Enlace no disponible"

#     # Filtrar solo grupo objetivo
#     df_grupo = df[df['nif'].isin(NIFS_GRUPO)].copy()

#     # --- [INICIO DE LA NUEVA LÓGICA DE CRUCE] ---
    
#     # 1. Mapeo de descripción para los CPVs de Enetic (para la tabla)
#     dict_enetic = {c.split(' - ')[0].split('-')[0].strip(): c for c in CPVS_ENETIC_RAW}

#     # 2. Analizar qué empresas del grupo tocan estos CPVs
#     # Estructura: { codigo_cpv: [lista_de_nombres_de_empresas] }
#     coincidencias = {code: [] for code in CPVS_ENETIC_CODES}
    
#     for _, row in df_grupo.iterrows():
#         cpvs_licitacion = limpiar_cpvs(row['cpvs'])
#         for cpv_full in cpvs_licitacion:
#             codigo_limpio = cpv_full.split(' - ')[0].split('-')[0].strip()
#             if codigo_limpio in coincidencias:
#                 if row['nombre'] not in coincidencias[codigo_limpio]:
#                     coincidencias[codigo_limpio].append(row['nombre'])

#     # --- [FIN DE LA LÓGICA DE CRUCE] ---

#     # 2. Configuración PDF
#     doc = SimpleDocTemplate(ARCHIVO_SALIDA_PDF, pagesize=A4,
#                             rightMargin=2*cm, leftMargin=2*cm,
#                             topMargin=2*cm, bottomMargin=2*cm)
    
#     elements = []
#     styles = getSampleStyleSheet()
    
#     # Estilos personalizados
#     estilo_titulo_empresa = ParagraphStyle('EmpresaTitle', parent=styles['Heading2'], textColor=colors.navy, spaceAfter=6)
#     estilo_datos_empresa = ParagraphStyle('EmpresaData', parent=styles['Normal'], fontSize=10, leading=12)
#     estilo_celda = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, leading=10)
#     estilo_link = ParagraphStyle('LinkStyle', parent=styles['Normal'], fontSize=8, textColor=colors.blue)

#     # # 3. GENERAR FICHAS POR EMPRESA
#     # empresas_unicas = df_grupo['nif'].unique()
    
#     # elements.append(Paragraph("ANÁLISIS DE DATOS OBTENIDOS ENTRE DICIEMBRE Y ENERO", styles['Heading1']))
    
#     # for nif in empresas_unicas:
#     #     sub_df = df_grupo[df_grupo['nif'] == nif]
#     #     nombre_empresa = sub_df['nombre'].iloc[0]
#     #     num_licitaciones = len(sub_df)
        
#     #     # --- Cabecera Empresa ---
#     #     elements.append(Paragraph(f"{nombre_empresa}", estilo_titulo_empresa))
#     #     elements.append(Paragraph(f"<b>ID Empresa (NIF):</b> {nif}", estilo_datos_empresa))
#     #     elements.append(Paragraph(f"<b>Licitaciones Ganadas:</b> {num_licitaciones}", estilo_datos_empresa))
#     #     elements.append(Spacer(1, 0.5*cm))
        
#     #     # --- Tabla de Licitaciones ---
#     #     data_tabla = [['ID (UUID)', 'Nombre Licitación', 'Importe (€)', 'Link']] # Header
        
#     #     # Recopilar CPVs de todas las licitaciones de esta empresa
#     #     todos_cpvs_empresa = []

#     #     for _, row in sub_df.iterrows():
#     #         # Procesar texto largo para que ajuste en la celda
#     #         nombre_lic = Paragraph(str(row.get('nombre_licitacion', 'N/A'))[:200], estilo_celda)
#     #         uuid_lic = Paragraph(str(row.get('expediente', 'N/A')), estilo_celda)
            
#     #         # Formatear importe
#     #         imp = f"{row.get('importe_con_iva', 0):,.2f} €"
#     #         importe_lic = Paragraph(imp, estilo_celda)
            
#     #         # Link (hacerlo clickable si es posible, o texto corto)
#     #         link_txt = row.get('link_licitacion', '')
#     #         if pd.isna(link_txt): link_txt = ""
#     #         # Creamos un tag HTML para el link
#     #         link_html = f'<a href="{link_txt}">Ver Licitación</a>' if link_txt else "No Link"
#     #         link_lic = Paragraph(link_html, estilo_link)
            
#     #         data_tabla.append([uuid_lic, nombre_lic, importe_lic, link_lic])
            
#     #         # Acumular CPVs
#     #         todos_cpvs_empresa.extend(limpiar_cpvs(row['cpvs']))

#     # 3. GENERAR FICHAS POR EMPRESA
#     empresas_unicas = df_grupo['nif'].unique()
    
#     elements.append(Paragraph("ANÁLISIS DE DETALLE POR EMPRESA", styles['Heading1']))
#     elements.append(Spacer(1, 0.5*cm))
    
#     for nif in empresas_unicas:
#         sub_df = df_grupo[df_grupo['nif'] == nif]
#         nombre_empresa = sub_df['nombre'].iloc[0]
#         num_licitaciones = len(sub_df)
        
#         # --- Cabecera Empresa ---
#         elements.append(Paragraph(f"{nombre_empresa}", estilo_titulo_empresa))
#         elements.append(Paragraph(f"<b>NIF:</b> {nif} | <b>Licitaciones Ganadas:</b> {num_licitaciones}", estilo_datos_empresa))
#         elements.append(Spacer(1, 0.3*cm))
        
#         # --- Tabla de Licitaciones de esta Empresa ---
#         # Definimos los encabezados
#         data_tabla = [['ID (UUID)', 'Nombre Licitación', 'Importe (€)', 'Link']]
        
#         todos_cpvs_empresa = []

#         for _, row in sub_df.iterrows():
#             # 1. ID / Expediente
#             uuid_lic = Paragraph(str(row.get('expediente', 'N/A')), estilo_celda)
            
#             # 2. Nombre (limitado para no romper la tabla)
#             nombre_txt = str(row.get('nombre_licitacion', 'Nombre no disponible'))
#             nombre_lic = Paragraph(nombre_txt[:150] + ('...' if len(nombre_txt) > 150 else ''), estilo_celda)
            
#             # 3. Importe formateado
#             imp_val = row.get('importe_con_iva', 0)
#             imp_formateado = f"{imp_val:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')
#             importe_lic = Paragraph(imp_formateado, estilo_celda)
            
#             # 4. Link clickable
#             link_url = row.get('link_licitacion', '')
#             if pd.isna(link_url) or link_url == "":
#                 link_p = Paragraph("No disponible", estilo_celda)
#             else:
#                 link_html = f'<a href="{link_url}" color="blue"><u>Ver Enlace</u></a>'
#                 link_p = Paragraph(link_html, estilo_link)
            
#             data_tabla.append([uuid_lic, nombre_lic, importe_lic, link_p])
            
#             # Acumular CPVs para el pie de la empresa
#             todos_cpvs_empresa.extend(limpiar_cpvs(row['cpvs']))

#         # Crear y dar estilo a la tabla de la empresa actual
#         t = Table(data_tabla, colWidths=[3.5*cm, 8.5*cm, 2.5*cm, 2.5*cm])
#         t.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
#             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#             ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
#         ]))
        
#         elements.append(t)
#         elements.append(Spacer(1, 0.4*cm))
        
#         # --- Pie de Empresa: CPVs ---
#         cpvs_unicos = sorted(list(set(todos_cpvs_empresa)))
#         texto_cpvs = ", ".join(cpvs_unicos)
#         elements.append(Paragraph(f"<b>CPVs detectados en estas licitaciones:</b> {texto_cpvs}", estilo_celda))
        
#         # Salto de página para que la siguiente empresa empiece limpia
#         elements.append(PageBreak())

#         # 1. Preparar el conjunto de exclusión (lo que Enetic YA TIENE)
#     # Extraemos solo los primeros 8 dígitos para una comparación limpia
#     enetic_base = {code[:8] for code in CPVS_ENETIC_CODES}
    
#     # 2. Rastrear CPVs de la competencia que NO están en Enetic
#     cpvs_nuevos_contador = Counter()
#     cpv_descripciones = {} # Para guardar la descripción y que no sea solo el número

#     for _, row in df_grupo.iterrows():
#         cpvs_raw = limpiar_cpvs(row['cpvs'])
#         for cpv_full in cpvs_raw:
#             # Separar código de descripción
#             partes = cpv_full.split(" - ")
#             codigo_completo = partes[0].split("-")[0].strip()
#             codigo_8 = codigo_completo[:8]
            
#             if codigo_8 not in enetic_base:
#                 cpvs_nuevos_contador[codigo_completo] += 1
#                 if codigo_completo not in cpv_descripciones:
#                     desc = partes[1] if len(partes) > 1 else "Sin descripción"
#                     cpv_descripciones[codigo_completo] = desc

#     # --- NUEVA SECCIÓN EN EL PDF: OPORTUNIDADES DE EXPANSIÓN ---
#     elements.append(PageBreak())
#     elements.append(Paragraph("OPORTUNIDADES DE EXPANSIÓN (CPVs NO EXPLORADOS)", styles['Heading1']))
#     elements.append(Paragraph(
#         "Los siguientes códigos CPV han sido adjudicados a empresas del grupo, pero <b>no figuran</b> en el radar actual de Enetic. "
#         "Se recomienda evaluar su inclusión para captar nuevas licitaciones.", 
#         styles['Normal']
#     ))
#     elements.append(Spacer(1, 0.5*cm))

#     # Crear tabla de "Gaps"
#     data_gap = [['Código CPV', 'Descripción', 'Frecuencia (Licitaciones)']]
    
#     # Ordenar por los más frecuentes (los que más "duelen" perder)
#     for codigo, cuenta in cpvs_nuevos_contador.most_common(20): # Top 20 nuevos
#         data_gap.append([
#             codigo,
#             Paragraph(cpv_descripciones[codigo], estilo_celda),
#             str(cuenta)
#         ])

#     if len(data_gap) > 1:
#         t_gap = Table(data_gap, colWidths=[3*cm, 11*cm, 3*cm])
#         t_gap.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
#             ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
#             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ('ALIGN', (2, 0), (2, -1), 'CENTER'),
#             ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.navajowhite])
#         ]))
#         elements.append(t_gap)
#     else:
#         elements.append(Paragraph("No se detectaron CPVs fuera del catálogo de Enetic.", estilo_datos_empresa))

#         # Crear Objeto Tabla
#         # Anchos de columnas: UUID, Nombre, Importe, Link
#         t = Table(data_tabla, colWidths=[3.5*cm, 8*cm, 2.5*cm, 2.5*cm])
#         t.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#             ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, 0), 9),
#             ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#             ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
#             ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
#             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#         ]))
#         elements.append(t)
#         elements.append(Spacer(1, 0.5*cm))
        
#         # --- Lista de CPVs ---
#         cpvs_unicos = sorted(list(set(todos_cpvs_empresa)))
#         texto_cpvs = ", ".join(cpvs_unicos)
#         elements.append(Paragraph(f"<b>CPVs detectados:</b> {texto_cpvs}", estilo_datos_empresa))
        
#         # Salto de página entre empresas
#         elements.append(PageBreak())

#     # --- NUEVA SECCIÓN: TABLA DE CRUCE ESTRATÉGICO ---
#     elements.append(PageBreak())
#     elements.append(Paragraph("ANÁLISIS DE COMPETENCIA EN CPVs OBJETIVO (ENETIC)", styles['Heading1']))
#     elements.append(Paragraph("Esta tabla muestra en qué categorías de Enetic están ganando licitaciones las empresas del grupo analizado.", styles['Normal']))
#     elements.append(Spacer(1, 0.5*cm))

#     data_cruce = [['CPV Enetic', 'Empresas Competidoras']]
    
#     for code in CPVS_ENETIC_CODES:
#         desc_completa = dict_enetic[code]
#         competidores = ", ".join(coincidencias[code]) if coincidencias[code] else "-"
        
#         # Formatear para que no rompa la tabla si hay muchos nombres
#         p_desc = Paragraph(desc_completa, estilo_celda)
#         p_comp = Paragraph(competidores, estilo_celda)
        
#         data_cruce.append([p_desc, p_comp])

#     t_cruce = Table(data_cruce, colWidths=[9*cm, 8*cm])
#     t_cruce.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke])
#     ]))
#     elements.append(t_cruce)

#     # 4. INFORME FINAL DE GRUPO (Global)
#     elements.append(Paragraph("INFORME DE ANÁLISIS DE GRUPO", styles['Heading1']))
    
#     total_importe = df_grupo['importe_con_iva'].sum()
#     total_licitaciones = len(df_grupo)
    
#     elements.append(Paragraph(f"<b>Volumen Total Adjudicado al Grupo:</b> {total_importe:,.2f} €", estilo_datos_empresa))
#     elements.append(Paragraph(f"<b>Total Licitaciones Ganadas:</b> {total_licitaciones}", estilo_datos_empresa))
#     elements.append(Spacer(1, 0.5*cm))
    
#     # Ranking Tabla
#     # 1. Agrupamos por NIF
#     # 2. Sumamos el importe y tomamos el 'first' del nombre
#     ranking = df_grupo.groupby('nif').agg({
#         'nombre': 'first', 
#         'importe_con_iva': 'sum'
#     }).sort_values(by='importe_con_iva', ascending=False).reset_index()

#     # El resto de tu código se mantiene igual
#     data_ranking = [['Pos.', 'Empresa', 'Volumen Total (€)']]
#     for idx, row in ranking.iterrows():
#         data_ranking.append([
#             str(idx + 1),
#             Paragraph(row['nombre'], estilo_celda),
#             f"{row['importe_con_iva']:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.') # Formato europeo
#         ])
        
#     t_rank = Table(data_ranking, colWidths=[1.5*cm, 10*cm, 4*cm])
#     t_rank.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#     ]))
#     elements.append(t_rank)

#     # Construir PDF
#     doc.build(elements)
#     print(f"✅ PDF Generado exitosamente: {ARCHIVO_SALIDA_PDF}")

# if __name__ == "__main__":
#     generar_pdf()

## --------------------------------

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import cm
from collections import Counter
from datetime import date

hoy = date.today()

# --- CONFIGURACIÓN ---
# Cambiado: Ahora apuntamos al parquet de adjudicatarios
ARCHIVO_ADJUDICATARIOS = r'/home/enetic/Desktop/Licitaciones/src/data/Adjudicatarios_general.parquet' 
ARCHIVO_PLIEGOS = r'src/data/Pliegos_general.parquet'
ARCHIVO_SALIDA_PDF = f'Informe_Licitaciones_Empresas{hoy}.pdf'

NIFS_GRUPO = [
    'B98513260', 'A97929566', 'B96273032', 'B46992731', 'B19925676', 
    'A91834036', 'B19959329', 'A80929490', 'B61172219', 'A33845009', 
    '47232180R', 'B96377882', 'B96949425'
]

CPVS_ENETIC_RAW = [
    "30000000-9 - Máquinas, equipo y artículos de oficina...",
    "30100000-0 - Máquinas, equipo y artículos de oficina...",
    "30200000-1 - Equipo y material informático",
    "30210000-4 - Máquinas procesadoras de datos (hardware)",
    "30230000-0 - Equipo relacionado con la informática",
    "32400000-7 - Redes",
    "32500000-8 - Equipo y material para telecomunicaciones",
    "48000000-8 Paquetes de software y sistemas de información",
    "72000000-5 Servicios TI: consultoría, desarrollo de software, Internet y apoyo",
]

CPVS_ENETIC_CODES = [c.split(' - ')[0].split('-')[0].strip() for c in CPVS_ENETIC_RAW]

# --- LÓGICA DE DATOS ---

def cargar_y_fusionar_datos():
    print(f"🚀 Cargando datos desde {ARCHIVO_ADJUDICATARIOS}...")
    
    # 1. Cargar fuentes (Ambos ahora son Parquet)
    try:
        df_detalle = pd.read_parquet(ARCHIVO_ADJUDICATARIOS)
        df_parquet_aux = pd.read_parquet(ARCHIVO_PLIEGOS)
    except Exception as e:
        print(f"❌ Error al cargar los archivos: {e}")
        return None, None

    # 2. Normalización de llaves para el cruce
    # Ajustamos nombres de columnas: 'expediente' en adjudicaciones, 'ID' en pliegos
    col_adj = 'expediente'
    col_pliego = 'ID_INTERNO' 
    # print("ADJUDICATARIOS COLUMNAS")
    # print(df_detalle.columns)
    # print("PRINCIPAL COLUMNAS")
    # print(df_parquet_aux.columns)

    if col_adj in df_detalle.columns:
        df_detalle['key_clean'] = df_detalle[col_adj].astype(str).str.strip().str.upper()
    else:
        # Fallback si en el parquet de adjudicatarios la columna se llama 'ID'
        df_detalle['key_clean'] = df_detalle['ID_INTERNO'].astype(str).str.strip().str.upper()

    df_parquet_aux['key_clean'] = df_parquet_aux[col_pliego].astype(str).str.strip().str.upper()

    # 4. MERGE (Cruce para obtener nombres de licitación y URLs)
    df_final = pd.merge(
        df_detalle, 
        df_parquet_aux[['key_clean', 'NOMBRE_PROYECTO', 'URL', 'ID', 'CPV']], 
        on='key_clean', 
        how='left'
    )

    # 5. Renombrar para compatibilidad con el generador de PDF
    df_final.rename(columns={
        'NOMBRE_PROYECTO': 'nombre_licitacion',
        'URL': 'link_licitacion'
    }, inplace=True)
    # print("FINAL COLUMNAS")
    # print(df_final.columns)

    print(f"✅ Cruce completado. {df_final['nombre_licitacion'].notna().sum()} coincidencias encontradas.")
    return df_final, df_parquet_aux

def limpiar_cpvs(cpv_string):
    # if pd.isna(cpv_string): return []
    lista = [c.strip() for c in str(cpv_string).split(';') if c.strip()]
    return list(dict.fromkeys(lista))

# --- GENERACIÓN DE PDF ---

def generar_pdf():
    df, _ = cargar_y_fusionar_datos()
    if df is None: return

    # Filtrar solo empresas del grupo
    df_grupo = df[df['NIF_ADJUDICATARIO'].isin(NIFS_GRUPO)].copy()
    
    # 1. Limpieza y conversión global (Haz esto ANTES de cualquier cálculo)
    df_grupo['IMPORTE_CON_IVA'] = (
        df_grupo['IMPORTE_CON_IVA']
        .astype(str)
        # .str.replace('.', '', regex=False)
        # .str.replace(',', '.', regex=False)
        # .str.replace(r'[^\d.]', '', regex=True)
    )
    # Convertimos la columna permanentemente a números
    df_grupo['IMPORTE_CON_IVA'] = pd.to_numeric(df_grupo['IMPORTE_CON_IVA'], errors='coerce').fillna(0)

    # Mapeo de descripción para los CPVs de Enetic
    dict_enetic = {c.split(' - ')[0].split('-')[0].strip(): c for c in CPVS_ENETIC_RAW}

    # Analizar coincidencias CPV
    coincidencias = {code: [] for code in CPVS_ENETIC_CODES}
    for _, row in df_grupo.iterrows():
        # cpvs_licitacion = limpiar_cpvs(row.get('CPV', ''))
        cpvs_licitacion = row.get('CPV','')
        # print(row.get('CPV',''),cpvs_licitacion)
        for cpv_full in cpvs_licitacion:
            codigo_limpio = cpv_full.split(' - ')[0].split('-')[0].strip()
            # print(codigos_limpio)
            print(codigo_limpio)
            if codigo_limpio in coincidencias:
                print("ENTRA EN COINCIDENCIA")
                if row['NOMBRE_ADJUDICATARIO'] not in coincidencias[codigo_limpio]:
                    coincidencias[codigo_limpio].append(row['NOMBRE_ADJUDICATARIO'])
    print(coincidencias)

    # Configuración de documento
    doc = SimpleDocTemplate(ARCHIVO_SALIDA_PDF, pagesize=A4, margin=(2*cm, 2*cm, 2*cm, 2*cm))
    elements = []
    styles = getSampleStyleSheet()
    
#     # Estilos personalizados
#     estilo_titulo_empresa = ParagraphStyle('EmpresaTitle', parent=styles['Heading2'], textColor=colors.navy, spaceAfter=6)
#     estilo_datos_empresa = ParagraphStyle('EmpresaData', parent=styles['Normal'], fontSize=10, leading=12)
#     estilo_celda = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, leading=10)
#     estilo_link = ParagraphStyle('LinkStyle', parent=styles['Normal'], fontSize=8, textColor=colors.blue)
    
    # Estilos personalizados
    estilo_titulo = styles['Heading1']
    estilo_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
    estilo_celda = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=10)
    estilo_link = ParagraphStyle('Link', parent=styles['Normal'], fontSize=8, textColor=colors.blue)

    # 1. SECCIÓN: DETALLE POR EMPRESA
    elements.append(Paragraph("INFORME DETALLADO POR EMPRESA", estilo_titulo))
    elements.append(Spacer(1, 0.5*cm))

    for nif in df_grupo['NIF_ADJUDICATARIO'].unique():
        sub_df = df_grupo[df_grupo['NIF_ADJUDICATARIO'] == nif]
        nombre_empresa = sub_df['NOMBRE_ADJUDICATARIO'].iloc[0]
        
        elements.append(Paragraph(f"<b>{nombre_empresa}</b>", styles['Heading2']))
        elements.append(Paragraph(f"NIF: {nif} | Adjudicaciones: {len(sub_df)}", estilo_sub))
        elements.append(Spacer(1, 0.3*cm))

        data_tabla = [['Expediente', 'Objeto Licitación', 'Importe (IVA inc.)', 'Link']]
        todos_cpvs = []

        for _, row in sub_df.iterrows():
            # Formateo de importe estilo europeo
            imp = f"{row.get('IMPORTE_CON_IVA', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " €"
            # imp = row.get('IMPORTE_CON_IVA',0)
            
            link_url = row.get('link_licitacion', '')
            link_p = Paragraph(f'<a href="{link_url}" color="blue"><u>Ver</u></a>', estilo_link) if link_url else "N/A"
            
            data_tabla.append([
                Paragraph(str(row.get('ID', 'N/A')), estilo_celda),
                Paragraph(str(row.get('nombre_licitacion', 'Sin nombre'))[:120], estilo_celda),
                Paragraph(imp, estilo_celda),
                link_p
            ])
            # todos_cpvs.extend(limpiar_cpvs(row.get('CPV', '')))
            todos_cpvs.extend(row.get('CPV', ''))

        t = Table(data_tabla, colWidths=[3.5*cm, 8.5*cm, 2.5*cm, 2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t)
        
        cpvs_txt = ", ".join(sorted(list(set(todos_cpvs))))
        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph(f"<b>CPVs:</b> {cpvs_txt}", estilo_celda))
        elements.append(PageBreak())
        
    # 1. Preparar el conjunto de exclusión (lo que Enetic YA TIENE)
    # Extraemos solo los primeros 8 dígitos para una comparación limpia
    enetic_base = {code[:8] for code in CPVS_ENETIC_CODES}
    
    # 2. Rastrear CPVs de la competencia que NO están en Enetic
    cpvs_nuevos_contador = Counter()
    cpv_descripciones = {} # Para guardar la descripción y que no sea solo el número

    for _, row in df_grupo.iterrows():
        cpvs_raw = row['CPV']
        for cpv_full in cpvs_raw:
            # Separar código de descripción
            partes = cpv_full.split(" - ")
            codigo_completo = partes[0].split("-")[0].strip()
            codigo_8 = codigo_completo[:8]
            
            if codigo_8 not in enetic_base:
                cpvs_nuevos_contador[codigo_completo] += 1
                if codigo_completo not in cpv_descripciones:
                    desc = partes[1] if len(partes) > 1 else "Sin descripción"
                    cpv_descripciones[codigo_completo] = desc
    
    # --- CARGA DEL MAESTRO DE CPVs ---
    # header=5 indica que la fila 6 (índice 5) contiene los nombres de las columnas
    df_maestro_cpv = pd.read_excel('/home/enetic/Desktop/Licitaciones/src/data/listado-cpv.xlsx', header=5)

    # Limpiamos el código del Excel para que sea solo el número (ej: '03000000')
    # Esto asegura que el cruce sea exacto
    df_maestro_cpv['codigo_limpio'] = (
        df_maestro_cpv['Código']
        .astype(str)
        .str.split('-')
        .str[0]
        .str.strip()
    )

    # Creamos un diccionario rápido de búsqueda: { '03000000': 'Productos de la agricultura...' }
    dict_nombres_cpv = dict(zip(df_maestro_cpv['codigo_limpio'], df_maestro_cpv['Epígrafe']))
    print(dict_nombres_cpv)
        
    # --- NUEVA SECCIÓN EN EL PDF: OPORTUNIDADES DE EXPANSIÓN ---
    # elements.append(PageBreak())
    elements.append(Paragraph("OPORTUNIDADES DE EXPANSIÓN (CPVs NO EXPLORADOS)", styles['Heading1']))
    elements.append(Paragraph(
        "Los siguientes códigos CPV han sido adjudicados a empresas del grupo, pero <b>no figuran</b> en el radar actual de Enetic. "
        "Se recomienda evaluar su inclusión para captar nuevas licitaciones.", 
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))

    # Crear tabla de "Gaps"
    data_gap = [['Código CPV', 'Descripción', 'Frecuencia (Licitaciones)']]
    
    # Ordenar por los más frecuentes (los que más "duelen" perder)
    for codigo, cuenta in cpvs_nuevos_contador.most_common(20): # Top 20 nuevos
        data_gap.append([
            codigo,
            Paragraph(dict_nombres_cpv[codigo], estilo_celda),
            str(cuenta)
        ])

    if len(data_gap) > 1:
        t_gap = Table(data_gap, colWidths=[3*cm, 11*cm, 3*cm])
        t_gap.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.navajowhite])
        ]))
        elements.append(t_gap)
    else:
        elements.append(Paragraph("No se detectaron CPVs fuera del catálogo de Enetic.", estilo_sub))

        # Crear Objeto Tabla
        # Anchos de columnas: UUID, Nombre, Importe, Link
        t = Table(data_tabla, colWidths=[3.5*cm, 8*cm, 2.5*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.5*cm))
        
        # --- Lista de CPVs ---
        cpvs_unicos = sorted(list(set(todos_cpvs)))
        texto_cpvs = ", ".join(cpvs_unicos)
        elements.append(Paragraph(f"<b>CPVs detectados:</b> {texto_cpvs}", estilo_sub))
        
    # Salto de página entre empresas
    elements.append(PageBreak())

    # 2. SECCIÓN: CRUCE ESTRATÉGICO ENETIC
    elements.append(Paragraph("ANÁLISIS DE COMPETENCIA EN CPVs ENETIC", estilo_titulo))
    data_cruce = [['CPV Objetivo', 'Empresas del Grupo Presentes']]
    for code, empresas in coincidencias.items():
        if code in dict_enetic:
            data_cruce.append([Paragraph(dict_enetic[code], estilo_celda), Paragraph(", ".join(empresas) if empresas else "-", estilo_celda)])

    t_cruce = Table(data_cruce, colWidths=[9*cm, 8*cm])
    t_cruce.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(t_cruce)
    elements.append(PageBreak())
    
    # 4. INFORME FINAL DE GRUPO (Global)
    elements.append(Paragraph("INFORME DE ANÁLISIS DE GRUPO", styles['Heading1']))
    
    # total_importe = df_grupo['IMPORTE_CON_IVA'].sum()
    total_importe = df_grupo['IMPORTE_CON_IVA'].sum()
    total_licitaciones = len(df_grupo)
    
    print(f"Total calculado: {total_importe}") # Verás que ahora es un float
    
    elements.append(Paragraph(f"<b>Volumen Total Adjudicado al Grupo:</b> {total_importe:,.2f} €", estilo_sub))
    elements.append(Paragraph(f"<b>Total Licitaciones Ganadas:</b> {total_licitaciones}", estilo_sub))
    elements.append(Spacer(1, 0.5*cm))
    
    # Ranking Tabla
    # 1. Agrupamos por NIF
    # 2. Sumamos el importe y tomamos el 'first' del nombre
    ranking = df_grupo.groupby('NIF_ADJUDICATARIO').agg({
        'NOMBRE_ADJUDICATARIO': 'first', 
        'IMPORTE_CON_IVA': 'sum'
    }).sort_values(by='IMPORTE_CON_IVA', ascending=False).reset_index()

    # El resto de tu código se mantiene igual
    data_ranking = [['Pos.', 'Empresa', 'Volumen Total (€)']]
    for idx, row in ranking.iterrows():
        print(row['IMPORTE_CON_IVA'])
        data_ranking.append([
            str(idx + 1),
            Paragraph(row['NOMBRE_ADJUDICATARIO'], estilo_celda),
            f"{row['IMPORTE_CON_IVA']:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.') # Formato europeo
        ])
        
    t_rank = Table(data_ranking, colWidths=[1.5*cm, 10*cm, 4*cm])
    t_rank.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(t_rank)

    # Construcción final
    doc.build(elements)
    print(f"✅ PDF '{ARCHIVO_SALIDA_PDF}' generado con éxito.")

if __name__ == "__main__":
    generar_pdf()
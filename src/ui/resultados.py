# import flet as ft
# import pandas as pd
# import json
# import os
# import shutil
# from datetime import datetime
# from pathlib import Path
# try:
#     from chatbot_licitacion import BotonChatbotFlotante 
#     from gestor_CPVS import CPVFilterManager
# except:
#     from .chatbot_licitacion import BotonChatbotFlotante 
#     from .gestor_CPVS import CPVFilterManager     

# from utils.load_data import load_dataset

# #Librerias utilitarias para el tema de la generacion de documentos sobre  la pantalla de resultados.
# import xml.etree.ElementTree as ET
# from xml.dom import minidom
# from reportlab.lib.pagesizes import letter, landscape
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet

# class GestorFavoritos:
#     """Clase para manejar el almacenamiento de favoritos de forma persistente"""
    
#     def __init__(self, page: ft.Page, usuario_actual:str):

#         # Crear carpeta de exportaciones si no existe
#         if not os.path.exists("assets/exports"):
#             os.makedirs("assets/exports", exist_ok= True)
#         # self.page = page
#         self.usuario_actual = usuario_actual
#         # self.archivo_favoritos = self._get_archivo_path()
#         self.archivo_favoritos = "usuarios.json"
#         self.favoritos = self._cargar_favoritos()
    
#     def _get_archivo_path(self):
#         """Obtiene la ruta del archivo de favoritos"""
#         config_dir = Path.home() / ".licitaciones_app"
#         config_dir.mkdir(exist_ok=True)
#         return config_dir / "favoritos.json"
    
#     def _cargar_favoritos(self):
#         """Carga los favoritos desde archivo JSON"""
#         try:
#             if os.path.exists(self.archivo_favoritos):
#                 # print("ENCONTRADO!")
#                 with open(self.archivo_favoritos, 'r', encoding='utf-8') as f:
#                     data = json.load(f)
#                     data = data[self.usuario_actual]
#                     # print(data)
#                     favoritos_set = set(data.get("favoritos", []))
#                     # print(f"✓ Favoritos cargados desde archivo: {favoritos_set}")
#                     return favoritos_set
#             else:
#                 print("ℹ️ No se encontró archivo de favoritos, iniciando vacío")
#                 return set()
#         except Exception as e:
#             print(f"⚠️ Error al cargar favoritos: {e}")
#             return set()
            
    
#     def _guardar_favoritos(self):
#         """Guarda los favoritos en archivo JSON de forma persistente"""
#         try:
#             with open(self.archivo_favoritos, 'r', encoding='utf-8') as f:
#                 data = json.load(f)
#                 # data = data[self.usuario_actual]

#             data[self.usuario_actual]["favoritos"]= list(self.favoritos)
#             # data = {
#             #     "favoritos": list(self.favoritos),
#             #     "fecha_actualizacion": datetime.now().isoformat()
#             # }
#             with open(self.archivo_favoritos, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, indent=2, ensure_ascii=False)
#             print(f"✓ Favoritos guardados en: {self.archivo_favoritos}")
#             print(f"  Total: {len(self.favoritos)} favoritos")
#         except Exception as e:
#             print(f"❌ Error al guardar favoritos: {e}")
    
#     def agregar(self, id_licitacion):
#         """Agrega una licitación a favoritos"""
#         self.favoritos.add(str(id_licitacion))
#         self._guardar_favoritos()
    
#     def quitar(self, id_licitacion):
#         """Quita una licitación de favoritos"""
#         self.favoritos.discard(str(id_licitacion))
#         self._guardar_favoritos()
    
#     def es_favorito(self, id_licitacion):
#         """Verifica si una licitación está en favoritos"""
#         return str(id_licitacion) in self.favoritos
    
#     def toggle(self, id_licitacion):
#         """Alterna el estado de favorito"""
#         if self.es_favorito(id_licitacion):
#             self.quitar(id_licitacion)
#             return False
#         else:
#             self.agregar(id_licitacion)
#             return True
    
#     def obtener_todos(self):
#         """Retorna la lista de todos los IDs favoritos"""
#         return list(self.favoritos)


# class PaginaResultados(ft.Container):
#     def __init__(self, page: ft.Page, df_general: pd.DataFrame, df_requisitos: pd.DataFrame, 
#                  df_criterios: pd.DataFrame, df_docs: pd.DataFrame, df_cpv:pd.DataFrame, usuario_actual:str,
#                  on_detalles, filtros_aplicados=None, on_aplicar_filtros=None, df_completo=None):
#         super().__init__()
#         # self.page = page
#         self.df_general = df_general
#         self.df_general_completo = df_completo if df_completo is not None else df_general
#         self.df_requisitos = df_requisitos
#         self.df_criterios = df_criterios
#         self.df_docs = df_docs
#         self.df_cpv = df_cpv
#         self.usuario_actual = usuario_actual
#         self.on_detalles = on_detalles
#         self.on_aplicar_filtros = on_aplicar_filtros

#         # NUEVO: Cargar datos de adjudicatarios
#         self.df_adjudicatarios = self._cargar_adjudicatarios()
        
#         # Guardar filtros aplicados
#         self.filtros_aplicados = filtros_aplicados or {}
        
#         # Controles de filtros editables
#         self.filtro_controls = {}

#         # Gestor de favoritos
#         self.gestor_favoritos = GestorFavoritos(page, self.usuario_actual)
        
#         # Estado de filtro
#         self.mostrar_solo_favoritos = False
        
#         # Estado de la barra lateral
#         self.sidebar_visible = True

#         # NUEVO: Variables de paginación
#         self.pagina_actual = 1
#         self.elementos_por_pagina = 100
#         self.total_paginas = 1

#         # Crear botón flotante
#         self.btn_chatbot_flotante = BotonChatbotFlotante(page)

#         # Agregarlo a la página
#         if self.btn_chatbot_flotante not in page.overlay:
#             page.overlay.append(self.btn_chatbot_flotante)

#         self.selected_row = None

#         self._build_ui()

#     def _cargar_adjudicatarios(self):
#         """Carga el DataFrame de adjudicatarios"""
#         try:
#             # df_adj = load_dataset(r"src\data", "Adjudicatarios_general.parquet")
#             df_adj = load_dataset(r"src/data", "Adjudicatarios_general.parquet")
#             # Convertir pliego_id a string para el merge
#             df_adj["pliego_id"] = df_adj["pliego_id"].astype(str)
#             return df_adj
#         except Exception as e:
#             print(f"⚠️ Error al cargar adjudicatarios: {e}")
#             # Retornar DataFrame vacío con las columnas esperadas
#             return pd.DataFrame(columns=["pliego_id", "nombre", "importe"])

#     def _obtener_cpvs_disponibles(self):
#         """Obtiene la lista de CPVs únicos del dataset"""
#         # print("CPVS TODOS",self.df_cpv)
#         try:
#             if 'codigo' in self.df_cpv.columns:
#                 cpvs = self.df_cpv['codigo'].dropna().unique().tolist()
#                 # print(cpvs)
#                 return sorted([str(cpv) for cpv in cpvs])
#             return []
#         except Exception as e:
#             print(f"Error obteniendo CPVs: {e}")
#             return []

#     def _on_cpvs_changed(self, cpvs):
#         """Actualiza los filtros cuando cambian los CPVs"""
#         if cpvs:
#             self.filtros_aplicados['cpv'] = cpvs
#         else:
#             self.filtros_aplicados.pop('cpv', None)

#     def _render_cpvs(self):
#         cpvs = self.filtros_aplicados.get("cpv") or []

#         self.cpv_container.controls.clear()

#         for cpv in cpvs:
#             self.cpv_container.controls.append(
#                 ft.Chip(
#                     label=ft.Text(cpv),
#                     on_delete=lambda e, cpv=cpv: self._remove_cpv(cpv),
#                 )
#             )

#         self.page.update()

#     def _remove_cpv(self, cpv):
#         cpvs = self.filtros_aplicados.get("cpv") or []

#         if cpv in cpvs:
#             cpvs.remove(cpv)

#         if cpvs:
#             self.filtros_aplicados["cpv"] = cpvs
#         else:
#             self.filtros_aplicados.pop("cpv", None)

#         self._render_cpvs()

#     def _crear_sidebar(self):
#         """Crea la barra lateral con filtros y favoritos"""
        
#         # Sección de filtros EDITABLES
#         filtros_widgets = [
#             ft.Text("🔍 Filtros de Búsqueda", 
#                    size=16, 
#                    weight=ft.FontWeight.BOLD,
#                    color=ft.Colors.BLUE_700)
#         ]
        
#         # Crear controles editables para cada tipo de filtro común
#         self.filtro_controls = {}
   
        
#         # Filtro de presupuesto
#         self.filtro_controls['presupuesto_min'] = ft.TextField(
#             label="Presupuesto mínimo",
#             value=self.filtros_aplicados.get('importe_min', ''),
#             hint_text="Ej: 50000",
#             border_color=ft.Colors.BLUE_300,
#             dense=True,
#             keyboard_type=ft.KeyboardType.NUMBER,
#         )
        
#         self.filtro_controls['presupuesto_max'] = ft.TextField(
#             label="Presupuesto máximo",
#             value=self.filtros_aplicados.get('importe_max', ''),
#             hint_text="Ej: 500000",
#             border_color=ft.Colors.BLUE_300,
#             dense=True,
#             keyboard_type=ft.KeyboardType.NUMBER,
#         )
        

#         #Modificacion Filtro Fechas
#         self.fecha_desde_input = ft.TextField(
#             label="Fecha desde",
#             value=(
#                 self.filtros_aplicados.get('fecha_desde').strftime("%Y-%m-%d")
#                 if isinstance(self.filtros_aplicados.get('fecha_desde'), datetime)
#                 else (self.filtros_aplicados.get('fecha_desde') or "").partition("T")[0]
#             ),
#             hint_text="YYYY-MM-DD",
#             border_color=ft.Colors.BLUE_300,
#             dense=True,
#             expand=True,
#         )

#         self.fecha_hasta_input = ft.TextField(
#             label="Fecha hasta",
#             value=(
#                 self.filtros_aplicados.get('fecha_hasta').strftime("%Y-%m-%d")
#                 if isinstance(self.filtros_aplicados.get('fecha_hasta'), datetime)
#                 else (self.filtros_aplicados.get('fecha_hasta') or "").partition("T")[0]
#             ),
#             hint_text="YYYY-MM-DD",
#             border_color=ft.Colors.BLUE_300,
#             dense=True,
#             expand=True,
#         )
#         self.filtro_controls['fechas'] = ft.Column(
#             controls=[
#                 ft.Text(
#                     "Fecha limite de presentación",
#                     size=13,
#                     weight=ft.FontWeight.BOLD,
#                     color=ft.Colors.BLUE_700,
#                 ),
#                 ft.Row(
#                     controls=[
#                         self.fecha_desde_input,
#                         self.fecha_hasta_input,
#                     ],
#                     spacing=8,
#                 ),
#             ],
#             spacing=4,
#         )

#         ## Fechas de Publicacion
#         self.fecha_desde_publicado_input = ft.TextField(
#             label="Fecha desde",
#             value=(
#                 self.filtros_aplicados.get('fecha_desde_publicado').strftime("%Y-%m-%d")
#                 if isinstance(self.filtros_aplicados.get('fecha_desde_publicado'), datetime)
#                 else (self.filtros_aplicados.get('fecha_desde_publicado') or "").partition("T")[0]
#             ),
#             hint_text="YYYY-MM-DD",
#             border_color=ft.Colors.BLUE_300,
#             dense=True,
#             expand=True,
#         )

#         self.fecha_hasta_publicado_input = ft.TextField(
#             label="Fecha hasta",
#             value=(
#                 self.filtros_aplicados.get('fecha_hasta_publicado').strftime("%Y-%m-%d")
#                 if isinstance(self.filtros_aplicados.get('fecha_hasta_publicado'), datetime)
#                 else (self.filtros_aplicados.get('fecha_publicado') or "").partition("T")[0]
#             ),
#             hint_text="YYYY-MM-DD",
#             border_color=ft.Colors.BLUE_300,
#             dense=True,
#             expand=True,
#         )

#         self.filtro_controls['fechas_publicado'] = ft.Column(
#             controls=[
#                 ft.Text(
#                     "Fecha de publicación",
#                     size=13,
#                     weight=ft.FontWeight.BOLD,
#                     color=ft.Colors.BLUE_700,
#                 ),
#                 ft.Row(
#                     controls=[
#                         self.fecha_desde_publicado_input,
#                         self.fecha_hasta_publicado_input,
#                     ],
#                     spacing=8,
#                 ),
#             ],
#             spacing=4,
#         )

#         # Estados de licitación
#         self.estados = {
#             "PUB": "Publicado",
#             "EV": "Evaluado", 
#             "ADJ": "Adjudicado",
#             "RES": "Resuelto",
#             "PRE": "Anuncio Previo"
#         }
        
#         self.filtro_controls["Estados"] = ft.Column(
#             controls=[
#                 ft.Text(
#                     "Estado de la publicación",
#                     size=13,
#                     weight=ft.FontWeight.BOLD,
#                     color=ft.Colors.BLUE_700,
#                 ),
#                 ft.Column(
#                     controls=[
#                         ft.Checkbox(label=nombre, value=False)
#                         for codigo, nombre in self.estados.items()
#                     ]
#                 )
#             ]
#         )
        
#         # self.filtro_controls['CPVs'] = self.cpv_manager.get_control()        
        
#         # Añadir todos los controles a la lista
#         for control in self.filtro_controls.values():
#             filtros_widgets.append(control)
        
#         # Botones de acción para filtros
#         btn_aplicar_filtros = ft.Button(
#             "Aplicar filtros",
#             icon=ft.Icons.SEARCH,
#             on_click=self._aplicar_filtros_editados,
#             style=ft.ButtonStyle(
#                 bgcolor=ft.Colors.BLUE_600,
#                 color=ft.Colors.WHITE,
#             ),
#         )
        
#         btn_limpiar_filtros = ft.OutlinedButton(
#             "Limpiar todo",
#             icon=ft.Icons.CLEAR,
#             on_click=self._limpiar_filtros,
#             style=ft.ButtonStyle(
#                 color=ft.Colors.RED_600,
#             ),
#         )
        
#         filtros_widgets.append(
#             ft.Row([btn_aplicar_filtros, btn_limpiar_filtros], spacing=5)
#         )
        
#         # Sección de favoritos
#         self.contador_favoritos_sidebar = ft.Text(
#             f"⭐ {len(self.gestor_favoritos.favoritos)} favoritos",
#             size=14,
#             weight=ft.FontWeight.BOLD,
#             color=ft.Colors.AMBER_700,
#         )
        
#         self.switch_filtro_sidebar = ft.Switch(
#             label="Solo favoritos",
#             value=False,
#             on_change=self._toggle_filtro_favoritos,
#         )
        
#         self.btn_exportar_sidebar = ft.Button(
#             "Exportar favoritos",
#             icon=ft.Icons.DOWNLOAD,
#             on_click=self._exportar_favoritos,
#             style=ft.ButtonStyle(
#                 bgcolor=ft.Colors.GREEN_600,
#                 color=ft.Colors.WHITE,
#             ),
#             disabled=len(self.gestor_favoritos.favoritos) == 0,
#         )

#         self.btn_exportar_excel = ft.Button(
#             "Exportar tabla (Excel)",
#             icon=ft.Icons.CODE,
#             on_click=self._exportar_excel,
#             style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE),
#         )

#         self.btn_exportar_pdf = ft.Button(
#             "Exportar informe de resultados (PDF)",
#             icon=ft.Icons.PICTURE_AS_PDF,
#             on_click=self._ver_reporte_pdf,
#             style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
#         )

#         self.btn_exportar_pdf_tabla = ft.Button(
#             "Exportar tabla resultados (PDF)",
#             icon=ft.Icons.PICTURE_AS_PDF,
#             on_click=self._ver_reporte_pdf_tabla,
#             style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
#         )
        
#         # Botón para agregar/quitar favorito
#         self.btn_favorito_sidebar = ft.Button(
#             "Marcar como favorito",
#             icon=ft.Icons.STAR_BORDER,
#             icon_color=ft.Colors.AMBER,
#             on_click=self._toggle_favorito,
#             disabled=True,
#             style=ft.ButtonStyle(
#                 bgcolor=ft.Colors.BLUE_50,
#             ),
#         )
        
#         # Construir la sidebar
#         sidebar = ft.Container(
#             content=ft.Column([
#                 # ft.Text("⚙️ Panel de Control", 
#                 #        size=18, 
#                 #        weight=ft.FontWeight.BOLD,
#                 #        color=ft.Colors.BLUE_900),
#                 # ft.Divider(height=20, color=ft.Colors.BLUE_200),
                
#                 # Filtros editables
#                 # ft.Container(
#                 #     content=ft.Column(
#                 #         filtros_widgets,
#                 #         spacing=8,
#                 #         scroll=ft.ScrollMode.AUTO,
#                 #     ),
#                 #     height=500,
#                 # ),
                
#                 # ft.Divider(height=20, color=ft.Colors.BLUE_200),
                
#                 # Favoritos
#                 ft.Text("⭐ Gestión de Favoritos", 
#                        size=16, 
#                        weight=ft.FontWeight.BOLD,
#                        color=ft.Colors.AMBER_700),
#                 self.contador_favoritos_sidebar,
#                 self.btn_favorito_sidebar,
#                 self.switch_filtro_sidebar,
#                 self.btn_exportar_sidebar,
#                 # self.btn_exportar_xml, # Nuevo
#                 self.btn_exportar_pdf, # Nuevo
#                 self.btn_exportar_pdf_tabla, # Nuevo
#                 # self.btn_exportar_excel, #Nuevo
                
#             ], spacing=10, scroll=ft.ScrollMode.AUTO),
#             width=300,
#             padding=15,
#             bgcolor=ft.Colors.GREY_50,
#             border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.GREY_300)),
#         )

#         # if 'cpv' in self.filtros_aplicados:
#         #     self.cpv_manager.set_cpvs(self.filtros_aplicados['cpv'])
                
#         return sidebar

#     def _crear_controles_paginacion(self):
#         """Crea los controles de paginación"""
#         self.txt_info_pagina = ft.Text(
#             f"Página {self.pagina_actual} de {self.total_paginas} ({len(self.df_general)} resultados)",
#             size=14,
#             color=ft.Colors.BLUE_700,
#             weight=ft.FontWeight.BOLD,
#         )
        
#         self.btn_primera_pagina = ft.IconButton(
#             icon=ft.Icons.FIRST_PAGE,
#             tooltip="Primera página",
#             on_click=lambda e: self._ir_a_pagina(1),
#             disabled=self.pagina_actual == 1,
#         )
        
#         self.btn_pagina_anterior = ft.IconButton(
#             icon=ft.Icons.CHEVRON_LEFT,
#             tooltip="Página anterior",
#             on_click=lambda e: self._ir_a_pagina(self.pagina_actual - 1),
#             disabled=self.pagina_actual == 1,
#         )
        
#         self.btn_pagina_siguiente = ft.IconButton(
#             icon=ft.Icons.CHEVRON_RIGHT,
#             tooltip="Página siguiente",
#             on_click=lambda e: self._ir_a_pagina(self.pagina_actual + 1),
#             disabled=self.pagina_actual >= self.total_paginas,
#         )
        
#         self.btn_ultima_pagina = ft.IconButton(
#             icon=ft.Icons.LAST_PAGE,
#             tooltip="Última página",
#             on_click=lambda e: self._ir_a_pagina(self.total_paginas),
#             disabled=self.pagina_actual >= self.total_paginas,
#         )
        
#         # Selector de elementos por página
#         self.dropdown_elementos = ft.Dropdown(
#             label="Elementos por página",
#             value="100",
#             options=[
#                 ft.dropdown.Option("50"),
#                 ft.dropdown.Option("100"),
#                 ft.dropdown.Option("200"),
#                 ft.dropdown.Option("500"),
#             ],
#             width=180,
#             # on_change=self._cambiar_elementos_por_pagina,
#         )
#         self.dropdown_elementos.on_change = self._cambiar_elementos_por_pagina # Así es más seguro
        
#         return ft.Row(
#             [
#                 self.btn_primera_pagina,
#                 self.btn_pagina_anterior,
#                 self.txt_info_pagina,
#                 self.btn_pagina_siguiente,
#                 self.btn_ultima_pagina,
#                 ft.VerticalDivider(),
#                 self.dropdown_elementos,
#             ],
#             alignment=ft.MainAxisAlignment.CENTER,
#             vertical_alignment=ft.CrossAxisAlignment.CENTER,
#         )

#     def _ir_a_pagina(self, numero_pagina):
#         """Navega a una página específica"""
#         if 1 <= numero_pagina <= self.total_paginas:
#             self.pagina_actual = numero_pagina
#             self._refrescar_tabla()

#     def _cambiar_elementos_por_pagina(self, e):
#         """Cambia la cantidad de elementos por página"""
#         self.elementos_por_pagina = int(e.control.value)
#         self.pagina_actual = 1  # Resetear a la primera página
#         self._refrescar_tabla()

#     def _actualizar_controles_paginacion(self):
#         """Actualiza el estado de los controles de paginación"""
#         self.txt_info_pagina.value = f"Página {self.pagina_actual} de {self.total_paginas} ({len(self.df_general)} resultados)"
        
#         self.btn_primera_pagina.disabled = self.pagina_actual == 1
#         self.btn_pagina_anterior.disabled = self.pagina_actual == 1
#         self.btn_pagina_siguiente.disabled = self.pagina_actual >= self.total_paginas
#         self.btn_ultima_pagina.disabled = self.pagina_actual >= self.total_paginas

#     def _build_ui(self):
#         # Botón para toggle de sidebar
#         self.btn_toggle_sidebar = ft.IconButton(
#             icon=ft.Icons.MENU,
#             icon_color=ft.Colors.BLUE_700,
#             tooltip="Mostrar/Ocultar panel lateral",
#             on_click=self._toggle_sidebar,
#         )
        
#         # Crear sidebar
#         self.sidebar = self._crear_sidebar()
#         # self._render_cpvs()
        
#         # Crear controles de paginación
#         self.controles_paginacion = self._crear_controles_paginacion()
        
#         # -------- TABLA PRINCIPAL (GENERAL) --------
#         self.cont_general = ft.Container(
#             content=ft.Column(
#                 [self._crear_tabla_general()], 
#                 # scroll=ft.ScrollMode.ALWAYS, 
#                 # expand=True
#             ),
#             # height=self.page.height * 0.6,
#             expand = 60,
#             # border=ft.border.all(1, ft.Colors.GREY_400),
#             border = ft.Border.all(1, ft.Colors.GREY_400),
#             border_radius=10,
#             padding=10,
#         )

#         # -------- TABLAS RELACIONADAS --------
#         tabla_requisitos = self._make_table(
#             self.df_requisitos.head(50),
#             ["pliego_id", "TIPO", "DESCRIPCION"]
#         )

#         tabla_criterios = self._make_table(
#             self.df_criterios.head(50),
#             ["pliego_id", "TIPO", "DESCRIPCION", "PESO"]
#         )

#         cont_requisitos = ft.Container(
#             content=ft.Column([tabla_requisitos], scroll=ft.ScrollMode.ALWAYS),#, expand=True),
#             # height=self.page.height * 0.22,
#             expand= 22,
#             # border=ft.border.all(1, ft.Colors.GREY_400),
#             border = ft.Border.all(),
#             border_radius=10,
#             padding=10,
#             # expand=True,
#         )

#         cont_criterios = ft.Container(
#             content=ft.Column([tabla_criterios], scroll=ft.ScrollMode.ALWAYS),#, expand=True),
#             # height=self.page.height * 0.25,
#             expand=25,
#             # border=ft.border.all(1, ft.Colors.GREY_400),
#             border = ft.Border.all(),
#             border_radius=10,
#             padding=10,
#             # expand=True,
#         )

#         # -------- BOTÓN DE NAVEGACIÓN --------
#         self.boton_detalles = ft.Button(
#             "Ver más detalles",
#             icon=ft.Icons.ARROW_FORWARD,
#             on_click=self._go_to_details,
#             style=ft.ButtonStyle(
#                 bgcolor=ft.Colors.BLUE_500,
#                 color=ft.Colors.WHITE,
#                 padding=15,
#             ),
#         )

#         # -------- CONTENIDO PRINCIPAL --------
#         contenido_principal = ft.Column(
#             [
#                 ft.Row([
#                     self.btn_toggle_sidebar,
#                     ft.Text("📄 Resultados de Búsqueda", size=22, weight=ft.FontWeight.BOLD),
#                 ], spacing=10),
#                 self.controles_paginacion,  # NUEVO: Controles de paginación arriba
#                 self.cont_general,
#                 self.controles_paginacion,  # NUEVO: Controles de paginación abajo también
#                 # ft.Row([cont_requisitos, cont_criterios], expand=True),
#                 ft.Row([self.boton_detalles], alignment=ft.MainAxisAlignment.END),
#             ],
#             spacing=15,
#             scroll=ft.ScrollMode.AUTO,
#             expand=True,
#         )

#         # -------- ESTRUCTURA FINAL CON SIDEBAR --------
#         self.content = ft.Row(
#             [
#                 self.sidebar,
#                 ft.Container(
#                     content=contenido_principal,
#                     expand=True,
#                     padding=10,
#                 )
#             ],
#             spacing=0,
#             expand=True,
#         )

#     def _toggle_sidebar(self, e):
#         """Muestra u oculta la barra lateral"""
#         self.sidebar_visible = not self.sidebar_visible
#         self.sidebar.visible = self.sidebar_visible
#         self.btn_toggle_sidebar.icon = ft.Icons.MENU_OPEN if self.sidebar_visible else ft.Icons.MENU
#         self.page.update()

#     def _obtener_datos_paginados(self, df_trabajo):
#         """Obtiene los datos correspondientes a la página actual"""
#         # Calcular el total de páginas
#         self.total_paginas = max(1, (len(df_trabajo) + self.elementos_por_pagina - 1) // self.elementos_por_pagina)
        
#         # Asegurar que la página actual esté en rango válido
#         if self.pagina_actual > self.total_paginas:
#             self.pagina_actual = self.total_paginas
        
#         # Calcular índices de inicio y fin
#         inicio = (self.pagina_actual - 1) * self.elementos_por_pagina
#         fin = inicio + self.elementos_por_pagina
        
#         # Retornar slice del dataframe
#         return df_trabajo.iloc[inicio:fin]

#     def _crear_celda_expandible(self, contenido, flex_factor):
#         """Crea un contenedor que ocupa una proporción del ancho total"""
#         return ft.Container(
#             content=contenido,
#             expand=flex_factor, # Esto reemplaza al cálculo de self.page.width
#             padding=5,
#             alignment=ft.Alignment(-1.0, 0.0),
#         )

#     def _crear_tabla_general(self):
#         """Crea la tabla general con indicadores de favoritos y datos de adjudicación"""

#         # Cargar datos de análisis y textos
#         df_analisis = load_dataset(r"src/data", "analisis_resultados.parquet") ## Versión Linux
#         # df_analisis = load_dataset(r"src/data", "analisis_resultados.parquet")
#         df_textos = load_dataset(r"src/data", "Textos_Extraidos_viejo.parquet")
#         # df_textos = load_dataset(r"src", "Textos_Extraidos_viejo.parquet")        dddd

#         # ===== CORRECCIÓN 1: Hacer el merge solo una vez y evitar duplicados =====
#         # Asegurar que los IDs sean string para el merge
#         df_analisis["pliego_id"] = df_analisis["pliego_id"].astype(str)
        
#         # Crear una copia del dataframe general para no modificar el original
#         df_trabajo = self.df_general.copy()
#         df_trabajo["ID"] = df_trabajo["ID"].astype(str)
        
#         # ===== CORRECCIÓN 2: Verificar si ya tiene la columna PRIORIDAD =====
#         if "PRIORIDAD" not in df_trabajo.columns:
#             # Hacer merge solo si no existe la columna
#             df_trabajo = df_trabajo.merge(
#                 df_analisis[["pliego_id", "PRIORIDAD"]],
#                 left_on="ID",
#                 right_on="pliego_id",
#                 how="left"
#             )
#             # Eliminar columna duplicada del merge
#             if "pliego_id" in df_trabajo.columns:
#                 df_trabajo = df_trabajo.drop(columns=["pliego_id"])
        
#         # ===== NUEVO: Merge con adjudicatarios =====
#         if not self.df_adjudicatarios.empty:
#             # Agrupar adjudicatarios por pliego_id y tomar el primero (evitar duplicados)
#             df_adj_primero = self.df_adjudicatarios.groupby("pliego_id").first().reset_index()
            
#             # Hacer merge con los datos de adjudicación
#             df_trabajo = df_trabajo.merge(
#                 df_adj_primero[["pliego_id", "NOMBRE_ADJUDICATARIO", "IMPORTE_CON_IVA"]],
#                 left_on="ID",
#                 right_on="pliego_id",
#                 how="left",
#                 suffixes=('', '_adj')
#             )
            
#             # Renombrar columnas de adjudicación
#             df_trabajo = df_trabajo.rename(columns={
#                 "NOMBRE_ADJUDICATARIO": "ADJUDICATARIO",
#                 "IMPORTE_CON_IVA": "IMPORTE_ADJUDICACION"
#             })
            
#             # Eliminar columna duplicada del merge
#             if "pliego_id" in df_trabajo.columns:
#                 df_trabajo = df_trabajo.drop(columns=["pliego_id"])
            
#             # Rellenar valores nulos con "No aplica"
#             df_trabajo["ADJUDICATARIO"] = df_trabajo["ADJUDICATARIO"].fillna("No aplica")
#             df_trabajo["IMPORTE_ADJUDICACION"] = df_trabajo["IMPORTE_ADJUDICACION"].fillna("No aplica")
#         else:
#             # Si no hay datos de adjudicatarios, crear columnas con "No aplica"
#             df_trabajo["ADJUDICATARIO"] = "No aplica"
#             df_trabajo["IMPORTE_ADJUDICACION"] = "No aplica"
        
#         # Convertir PRIORIDAD a string y rellenar vacíos
#         df_trabajo["PRIORIDAD"] = df_trabajo["PRIORIDAD"].astype(str)
#         df_trabajo['PRIORIDAD'] = df_trabajo['PRIORIDAD'].fillna("No estudiado")
#         df_trabajo['PRIORIDAD'] = df_trabajo['PRIORIDAD'].replace('nan', 'No estudiado')
#         df_trabajo['PRIORIDAD'] = df_trabajo['PRIORIDAD'].replace('<NA>', 'No estudiado')

#         # Definir orden de prioridad
#         orden_prioridad = {
#             "ALTA": 4,
#             "MEDIA": 3,
#             "BAJA": 2,
#             "No estudiado": 1
#         }

#         # Crear columna auxiliar para ordenar
#         df_trabajo["orden_prioridad"] = df_trabajo["PRIORIDAD"].map(
#             lambda x: orden_prioridad.get(x, 5)
#         )

#         # ===== CORRECCIÓN 3: Eliminar duplicados ANTES de ordenar =====
#         # Esto evita problemas con favoritos de filas duplicadas
#         df_trabajo = df_trabajo.drop_duplicates(
#             subset=["ID"],
#             keep="first"
#         )

#         # Ordenar por prioridad
#         df_trabajo = df_trabajo.sort_values(
#             by=["orden_prioridad"],
#             ascending=False
#         )

#         # Eliminar duplicados por proyecto manteniendo el de mayor prioridad
#         df_trabajo = df_trabajo.drop_duplicates(
#             subset=["NOMBRE_PROYECTO"],
#             keep="first"
#         )

#         # Limpieza fuerte de valores
#         df_trabajo["PRIORIDAD"] = (
#             df_trabajo["PRIORIDAD"]
#                 .astype(str)
#                 .str.strip()         # Quita espacios
#                 .str.upper()         # Convierte a mayúsculas
#                 .replace(["NAN", "<NA>", "NONE"], "NO ESTUDIADO")
#         )

#         # Eliminar la columna auxiliar
#         df_trabajo = df_trabajo.drop(columns=["orden_prioridad"])

#         # Iconos para cada prioridad
#         iconos_prioridad = {
#             "ALTA": "🟢 ALTA",
#             "MEDIA": "🟡 MEDIA",
#             "BAJA": "🔴 BAJA",
#             "Descartado": "⬛ Descartado",
#             "No estudiado": "▫️ No estudiado"
#         }

#         # Aplicar icono
#         df_trabajo["PRIORIDAD"] = df_trabajo["PRIORIDAD"].map(
#             lambda x: iconos_prioridad.get(x, "▫️ No estudiado")
#         )

#         # ===== CORRECCIÓN 4: Aplicar filtro de favoritos sobre df_trabajo =====
#         if self.mostrar_solo_favoritos:
#             df_filtrado = df_trabajo[
#                 df_trabajo["ID"].astype(str).isin(self.gestor_favoritos.favoritos)
#             ]
#             if df_filtrado.empty:
#                 return ft.Text(
#                     "⭐ No tienes licitaciones favoritas aún",
#                     size=16,
#                     color=ft.Colors.GREY_600,
#                     text_align=ft.TextAlign.CENTER,
#                 )
#         else:
#             df_filtrado = df_trabajo

#         # NUEVO: Aplicar paginación
#         df_paginado = self._obtener_datos_paginados(df_filtrado)
        
#         # Actualizar controles de paginación
#         self._actualizar_controles_paginacion()

#         #----------------------------------------------- Modificacion

#         # 2. Definición de la CABECERA (Header)
#         # MODIFICADO: Añadir columnas de adjudicatario e importe adjudicación
#         header = ft.Container(
#             bgcolor=ft.Colors.BLUE_GREY_50,
#             border=ft.Border.only(bottom=ft.border.BorderSide(2, ft.Colors.BLUE_700)),
#             content=ft.Row([
#                 self._crear_celda_expandible(ft.Text("⭐", weight="bold"), 1),
#                 self._crear_celda_expandible(ft.Text("NOMBRE PROYECTO", weight="bold"), 6),
#                 self._crear_celda_expandible(ft.Text("ENTIDAD", weight="bold"), 4),
#                 self._crear_celda_expandible(ft.Text("IMPORTE", weight="bold"), 2),
#                 self._crear_celda_expandible(ft.Text("LÍMITE", weight="bold"), 2),
#                 self._crear_celda_expandible(ft.Text("PRIORIDAD", weight="bold"), 2),
#                 self._crear_celda_expandible(ft.Text("ADJUDICATARIO", weight="bold"), 4),
#                 self._crear_celda_expandible(ft.Text("IMP. ADJ.", weight="bold"), 2),
#             ])
#         )

#         # 3. Creación de las FILAS (Data Rows)
#         # MODIFICADO: Añadir celdas para adjudicatario e importe adjudicación
#         filas_controles = []
#         for _, row in df_paginado.iterrows():
#             es_fav = self.gestor_favoritos.es_favorito(row["ID"])
            
#             # Formatear importe de adjudicación
#             imp_adj = row.get("IMPORTE_ADJUDICACION", "No aplica")
#             if imp_adj != "No aplica":
#                 try:
#                     imp_adj = f"{float(imp_adj):,.2f} €"
#                 except:
#                     imp_adj = str(imp_adj)
            
#             nueva_fila = ft.Container(
#                 padding=ft.Padding.symmetric(vertical=5),
#                 border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
#                 on_click=lambda e, r=row: self._on_row_click(r),
#                 content=ft.Row([
#                     # Columna Favorito
#                     self._crear_celda_expandible(
#                         ft.Icon(
#                             ft.Icons.STAR if es_fav else ft.Icons.STAR_BORDER,
#                             color=ft.Colors.AMBER if es_fav else ft.Colors.GREY_400,
#                             size=20
#                         ), 1
#                     ),
#                     # Columna Proyecto (con link)
#                     self._crear_celda_expandible(
#                         ft.TextButton(
#                             content=ft.Text(
#                                 str(row["NOMBRE_PROYECTO"]),
#                                 color=ft.Colors.BLUE,
#                                 size=12,
#                             ),
#                             # on_click=lambda e, r=row: self._abrir_detalle(r),
#                             url=row.get('URL', "https://www.hacienda.gob.es"),
#                             style=ft.ButtonStyle(padding=0),
#                         ), 6
#                     ),
#                     # Columna Entidad
#                     self._crear_celda_expandible(ft.Text(str(row["ENTIDAD"]), size=12), 4),
#                     # Columna Importe
#                     self._crear_celda_expandible(ft.Text(str(row["IMPORTE"]), size=12), 2),
#                     # Columna Fecha
#                     self._crear_celda_expandible(ft.Text(str(row["FECHA_LIMITE"]), size=12), 2),
#                     # Columna Prioridad
#                     self._crear_celda_expandible(ft.Text(str(row["PRIORIDAD"]), size=12), 2),
#                     # NUEVO: Columna Adjudicatario
#                     self._crear_celda_expandible(
#                         ft.Text(
#                             str(row.get("ADJUDICATARIO", "No aplica")), 
#                             size=11,
#                             color=ft.Colors.GREEN_700 if row.get("ADJUDICATARIO", "No aplica") != "No aplica" else ft.Colors.GREY_500
#                         ), 4
#                     ),
#                     # NUEVO: Columna Importe Adjudicación
#                     self._crear_celda_expandible(
#                         ft.Text(
#                             str(imp_adj), 
#                             size=11,
#                             weight=ft.FontWeight.BOLD if imp_adj != "No aplica" else ft.FontWeight.NORMAL,
#                             color=ft.Colors.GREEN_700 if imp_adj != "No aplica" else ft.Colors.GREY_500
#                         ), 2
#                     ),
#                 ])
#             )
#             filas_controles.append(nueva_fila)

#         # 4. Ensamblaje final
#         return ft.Column([
#             header,
#             ft.Column(
#                 controls=filas_controles,
#                 scroll=ft.ScrollMode.ADAPTIVE,
#                 expand=True
#             )
#         ], expand=True)
    
    

#     def _make_table(self, df, columnas):
#         columnas_lista = list(columnas)
#         return ft.DataTable(
#             columns=[ft.DataColumn(ft.Text(col)) for col in columnas_lista],
#             rows=[
#                 ft.DataRow(
#                     cells=[ft.DataCell(ft.Text(str(row[col]))) for col in columnas_lista]
#                 )
#                 for _, row in df.iterrows()
#             ],
#         )
    
#     # def _abrir_detalle(self,row):
#     #     try:
#     #         url=row['URL']
#     #     except:
#     #         url="https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
#     #     self.page.run_task(self._handle_abrir_url, url)
#     #     # self._handle_abrir_url(url)

#     # # 1. Define una función asíncrona dedicada para abrir la URL
#     async def _handle_abrir_url(self,url):
#         # url = self.url_actual  # O de donde obtengas la URL
#         print(f"Abriendo navegador para: {url}")
#         # Usamos await para que la corrutina se ejecute realmente
#         await self.page.launch_url(url) 

#     async def _abrir_detalle(self, row):
#         try:
#             url = row['URL']
#         except:
#             url = "https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
        
#         print(f"Abriendo: {url}")
#         # Llamada directa sin run_task, mucho más rápido
#         await self.page.launch_url(url)

#     def _on_row_click(self, row_data):
#         """Guarda la fila seleccionada y actualiza el botón de favorito"""
#         self.selected_row = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data

#         # Actualizar botón de favorito en sidebar
#         es_favorito = self.gestor_favoritos.es_favorito(self.selected_row["ID"])
#         self.btn_favorito_sidebar.text = "Quitar de favoritos" if es_favorito else "Marcar como favorito"
#         self.btn_favorito_sidebar.icon = ft.Icons.STAR if es_favorito else ft.Icons.STAR_BORDER
#         self.btn_favorito_sidebar.disabled = False

#         # Activar botón de chatbot con los docs de esta licitación
#         docs_licitacion = self.df_docs[self.df_docs["pliego_id"] == self.selected_row["ID"]]
#         self.btn_chatbot_flotante.activar(
#             df_docs=docs_licitacion,
#             nombre_licitacion=self.selected_row["NOMBRE_PROYECTO"]
#         )

#         self.page.snack_bar = ft.SnackBar(
#             content=ft.Text(f"✔️ Fila seleccionada: ID {self.selected_row['ID']}"),
#             bgcolor=ft.Colors.BLUE_100,
#         )
#         self.page.snack_bar.open = True
#         self.page.update()

#     def _toggle_favorito(self, e):
#         """Agrega o quita de favoritos la fila seleccionada"""
#         if self.selected_row is None:
#             return

#         id_licitacion = self.selected_row["ID"]
#         es_favorito = self.gestor_favoritos.toggle(id_licitacion)

#         # Actualizar botón en sidebar
#         self.btn_favorito_sidebar.text = "Quitar de favoritos" if es_favorito else "Marcar como favorito"
#         self.btn_favorito_sidebar.icon = ft.Icons.STAR if es_favorito else ft.Icons.STAR_BORDER

#         # Actualizar contador
#         self.contador_favoritos_sidebar.value = f"⭐ {len(self.gestor_favoritos.favoritos)} favoritos"
        
#         # Actualizar botón de exportar
#         self.btn_exportar_sidebar.disabled = len(self.gestor_favoritos.favoritos) == 0

#         # Actualizar tabla si estamos en modo favoritos
#         if self.mostrar_solo_favoritos:
#             self._refrescar_tabla()

#         # Mostrar notificación
#         mensaje = "✨ Añadido a favoritos" if es_favorito else "🗑️ Quitado de favoritos"
#         self.page.snack_bar = ft.SnackBar(
#             content=ft.Text(mensaje),
#             bgcolor=ft.Colors.GREEN_100 if es_favorito else ft.Colors.GREY_300,
#         )
#         self.page.snack_bar.open = True
#         self.page.update()

#     def _toggle_filtro_favoritos(self, e):
#         """Activa/desactiva el filtro de favoritos"""
#         self.mostrar_solo_favoritos = e.control.value
#         self.pagina_actual = 1  # NUEVO: Resetear a primera página al cambiar filtro
#         self._refrescar_tabla()

#     def _refrescar_tabla(self):
#         """Refresca la tabla general"""
#         self.cont_general.content.controls[0] = self._crear_tabla_general()
#         self.page.update()
    
#     def _exportar_favoritos(self, e):
#         """Exporta las licitaciones favoritas a un archivo Excel"""
#         try:
#             ids_favoritos = self.gestor_favoritos.obtener_todos()
            
#             if not ids_favoritos:
#                 self.page.snack_bar = ft.SnackBar(
#                     content=ft.Text("⚠️ No hay favoritos para exportar"),
#                     bgcolor=ft.Colors.AMBER_300,
#                 )
#                 self.page.snack_bar.open = True
#                 self.page.update()
#                 return
            
#             df_general_fav = self.df_general[
#                 self.df_general["ID"].astype(str).isin(ids_favoritos)
#             ].copy()
            
#             with pd.ExcelWriter('Licitaciones_Favoritas.xlsx', engine='openpyxl') as writer:
#                 df_general_fav.to_excel(writer, sheet_name='General', index=False)
                
#                 df_req_fav = self.df_requisitos[
#                     self.df_requisitos["pliego_id"].astype(str).isin(ids_favoritos)
#                 ]
#                 if not df_req_fav.empty:
#                     df_req_fav.to_excel(writer, sheet_name='Requisitos', index=False)
                
#                 df_crit_fav = self.df_criterios[
#                     self.df_criterios["pliego_id"].astype(str).isin(ids_favoritos)
#                 ]
#                 if not df_crit_fav.empty:
#                     df_crit_fav.to_excel(writer, sheet_name='Criterios', index=False)
                
#                 df_docs_fav = self.df_docs[
#                     self.df_docs["pliego_id"].astype(str).isin(ids_favoritos)
#                 ]
#                 if not df_docs_fav.empty:
#                     df_docs_fav.to_excel(writer, sheet_name='Documentos', index=False)
            
#             timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
#             self.page.snack_bar = ft.SnackBar(
#                 content=ft.Text(
#                     f"✅ Archivo exportado: Licitaciones_Favoritas.xlsx\n"
#                     f"📊 {len(df_general_fav)} licitaciones exportadas"
#                 ),
#                 bgcolor=ft.Colors.GREEN_100,
#                 duration=5000,
#             )
#             self.page.snack_bar.open = True
#             self.page.update()
            
#         except Exception as ex:
#             self.page.snack_bar = ft.SnackBar(
#                 content=ft.Text(f"❌ Error al exportar: {str(ex)}"),
#                 bgcolor=ft.Colors.RED_100,
#             )
#             self.page.snack_bar.open = True
#             self.page.update()

#     def _go_to_details(self, e):
#         """Abre la página de detalles pasando la fila seleccionada"""
#         if self.selected_row is not None:
#             _selected_row_aux = self.selected_row.to_dict() if hasattr(self.selected_row, 'to_dict') else self.selected_row
#             self.on_detalles(_selected_row_aux)
#         else:
#             self.page.snack_bar = ft.SnackBar(
#                 content=ft.Text("⚠️ Selecciona una fila antes de continuar."),
#                 bgcolor=ft.Colors.AMBER_300,
#             )
#             self.page.snack_bar.open = True
#             self.page.update()

#     def _aplicar_filtros_editados(self, e):
#         """Aplica los filtros editados en la barra lateral"""
#         # Recoger valores de los controles
#         nuevos_filtros = {}
        
#         ## Filtros de Importe
#         if self.filtro_controls['presupuesto_min'].value!='':
#             nuevos_filtros['importe_min'] = float(self.filtro_controls['presupuesto_min'].value) 
#         else:
#             nuevos_filtros['importe_min']=0
#         if self.filtro_controls['presupuesto_max'].value!='':
#             nuevos_filtros['importe_max'] = float(self.filtro_controls['presupuesto_max'].value)
#         else:
#             nuevos_filtros["importe_max"] = 0

       
#         nuevos_filtros['fecha_desde'] = self.fecha_desde_input.value
#         nuevos_filtros['fecha_hasta'] = self.fecha_hasta_input.value

#         nuevos_filtros['fecha_desde_publicado'] = self.fecha_desde_publicado_input.value
#         nuevos_filtros['fecha_hasta_publicado'] = self.fecha_hasta_publicado_input.value

#         # print(self.cpv_container)
#         # nuevos_filtros['cpv'] = self.cpv_manager.get_cpvs()

        
#         # Actualizar filtros aplicados
#         self.filtros_aplicados = nuevos_filtros
        
#         # NUEVO: Resetear a primera página al aplicar filtros
#         self.pagina_actual = 1
        
#         # Si hay un callback para aplicar filtros (para refiltrar desde la fuente original)
#         if self.on_aplicar_filtros:
#             try:
#                 # Llamar al callback que debería devolver nuevos dataframes filtrados
#                 nuevos_dfs = self.on_aplicar_filtros(nuevos_filtros)
#                 if nuevos_dfs:
#                     self.df_general = nuevos_dfs.get('df_general', self.df_general)
#                     self.df_requisitos = nuevos_dfs.get('df_requisitos', self.df_requisitos)
#                     self.df_criterios = nuevos_dfs.get('df_criterios', self.df_criterios)
#                     self.df_docs = nuevos_dfs.get('df_docs', self.df_docs)
#             except Exception as ex:
#                 print(f"Error al aplicar filtros: {ex}")
#         else:
#             # Aplicar filtros localmente al dataframe completo
#             self._aplicar_filtros_locales(nuevos_filtros)
        
#         # Refrescar la vista
#         self._refrescar_tabla()
        
#         # Notificar al usuario
#         self.page.snack_bar = ft.SnackBar(
#             content=ft.Text(f"✅ Filtros aplicados ({len(nuevos_filtros)} activos)"),
#             bgcolor=ft.Colors.GREEN_100,
#         )
#         self.page.snack_bar.open = True
#         self.page.update()
    
#     def _aplicar_filtros_locales(self, filtros):
#         """Aplica filtros localmente al dataframe"""
#         df_filtrado = self.df_general_completo.copy()
        
#         # Filtrar por nombre de proyecto
#         if 'nombre_proyecto' in filtros and filtros['nombre_proyecto']:
#             df_filtrado = df_filtrado[
#                 df_filtrado['NOMBRE_PROYECTO'].str.contains(
#                     filtros['nombre_proyecto'], 
#                     case=False, 
#                     na=False
#                 )
#             ]
        
#         # Filtrar por presupuesto mínimo
#         if 'presupuesto_min' in filtros and filtros['presupuesto_min']:
#             try:
#                 min_val = float(filtros['presupuesto_min'])
#                 if 'PRESUPUESTO' in df_filtrado.columns:
#                     df_filtrado = df_filtrado[df_filtrado['PRESUPUESTO'] >= min_val]
#             except ValueError:
#                 pass
        
#         # Filtrar por presupuesto máximo
#         if 'presupuesto_max' in filtros and filtros['presupuesto_max']:
#             try:
#                 max_val = float(filtros['presupuesto_max'])
#                 if 'PRESUPUESTO' in df_filtrado.columns:
#                     df_filtrado = df_filtrado[df_filtrado['PRESUPUESTO'] <= max_val]
#             except ValueError:
#                 pass
        
#         # Filtrar por fecha desde
#         if 'fecha_desde' in filtros and filtros['fecha_desde']:
#             try:
#                 if 'FECHA_LIMITE' in df_filtrado.columns:
#                     df_filtrado['FECHA_LIMITE'] = pd.to_datetime(df_filtrado['FECHA_LIMITE'], errors='coerce')
#                     fecha_desde = pd.to_datetime(filtros['fecha_desde'])
#                     df_filtrado = df_filtrado[df_filtrado['FECHA_LIMITE'] >= fecha_desde]
#             except:
#                 pass
        
#         # Filtrar por fecha hasta
#         if 'fecha_hasta' in filtros and filtros['fecha_hasta']:
#             try:
#                 if 'FECHA_LIMITE' in df_filtrado.columns:
#                     df_filtrado['FECHA_LIMITE'] = pd.to_datetime(df_filtrado['FECHA_LIMITE'], errors='coerce')
#                     fecha_hasta = pd.to_datetime(filtros['fecha_hasta'])
#                     df_filtrado = df_filtrado[df_filtrado['FECHA_LIMITE'] <= fecha_hasta]
#             except:
#                 pass
        
#         # Filtrar por categoría
#         if 'categoria' in filtros and filtros['categoria']:
#             if 'CATEGORIA' in df_filtrado.columns:
#                 df_filtrado = df_filtrado[
#                     df_filtrado['CATEGORIA'].str.contains(
#                         filtros['categoria'], 
#                         case=False, 
#                         na=False
#                     )
#                 ]
        
#         self.df_general = df_filtrado
    
#     def _limpiar_filtros(self, e):
#         """Limpia todos los filtros y restaura los datos originales"""
#         # Limpiar controles
#         for control in self.filtro_controls.values():
#             control.value = ""
        
#         # Limpiar filtros aplicados
#         self.filtros_aplicados = {}

#         #Limpiar los CPVs
#         # self.cpv_manager.set_cpvs([])
        
#         # NUEVO: Resetear a primera página al limpiar filtros
#         self.pagina_actual = 1
        
#         # Restaurar dataframe original
#         self.df_general = self.df_general_completo.copy()
#         self.page.update()
        
#         # Refrescar vista
#         self._refrescar_tabla()
        
#         # Notificar
#         self.page.snack_bar = ft.SnackBar(
#             content=ft.Text("🧹 Filtros limpiados - Mostrando todos los resultados"),
#             bgcolor=ft.Colors.BLUE_100,
#         )
#         self.page.snack_bar.open = True
#         self.page.update()

#     def _exportar_excel(self, e):
#         """Genera un archivo Excel (.xlsx) con los resultados filtrados y el link de la licitación"""
#         try:
#             # 1. Obtener los datos que están actualmente pasando los filtros
#             # Usamos una copia para no afectar la visualización de la app
#             df_export = self.df_general.copy()

#             # 2. Asegurar que la columna de URL exista (basado en tu lógica de _abrir_detalle)
#             # Si por alguna razón la fila no tiene URL, ponemos el link por defecto de Hacienda
#             if 'URL' not in df_export.columns:
#                 df_export['URL'] = "https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
#             else:
#                 df_export['URL'] = df_export['URL'].fillna("https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx")

#             # 3. Formatear el archivo Excel
#             nombre_archivo = "Resultados_Licitaciones.xlsx"
            
#             with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
#                 # Hoja de Resultados
#                 df_export.to_excel(writer, sheet_name='Tabla de Resultados', index=False)
                
#                 # Crear una hoja pequeña para los filtros aplicados (solicitado en el encabezado)
#                 df_filtros = pd.DataFrame([
#                     {"Filtro": k, "Valor": v} for k, v in self.filtros_aplicados.items()
#                 ])
#                 if not df_filtros.empty:
#                     df_filtros.to_excel(writer, sheet_name='Filtros Utilizados', index=False)

#             self.page.snack_bar = ft.SnackBar(
#                 content=ft.Text(f"✅ Excel generado: {nombre_archivo}"),
#                 bgcolor=ft.Colors.GREEN_400,
#             )
#             self.page.snack_bar.open = True
#             self.page.update()

#         except Exception as ex:
#             self.page.snack_bar = ft.SnackBar(
#                 content=ft.Text(f"❌ Error al exportar Excel: {str(ex)}"),
#                 bgcolor=ft.Colors.RED_400,
#             )
#             self.page.snack_bar.open = True
#             self.page.update()

#     def _exportar_xml(self, e):
#         """Genera un archivo XML con los resultados actuales y filtros"""
#         try:
#             root = ET.Element("ExportacionLicitaciones")
            
#             # Nodo de Filtros
#             filtros_node = ET.SubElement(root, "FiltrosAplicados")
#             for key, val in self.filtros_aplicados.items():
#                 f_node = ET.SubElement(filtros_node, "Filtro")
#                 f_node.set("campo", str(key))
#                 f_node.text = str(val)

#             # Nodo de Resultados
#             resultados_node = ET.SubElement(root, "Resultados")
#             # Usamos el DF que se muestra actualmente en la tabla
#             for _, row in self.df_general.iterrows():
#                 item = ET.SubElement(resultados_node, "Licitacion")
#                 for col in self.df_general.columns:
#                     child = ET.SubElement(item, col.replace(" ", "_"))
#                     child.text = str(row[col])

#             # Guardar archivo
#             xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
#             with open("resultados_exportados.xml", "w", encoding="utf-8") as f:
#                 f.write(xml_str)

#             self._mostrar_snackbar("✅ XML generado: resultados_exportados.xml")
#         except Exception as ex:
#             self._mostrar_snackbar(f"❌ Error XML: {str(ex)}", True)


#     async def _ver_reporte_pdf_tabla(self, e):
#         try:
#             user_name = getattr(self, "usuario_actual", "usuario")
#             fecha_hoy = datetime.now().strftime("%d/%m/%Y")
#             nombre_archivo = f"reporte_{user_name.replace(' ', '_')}.pdf"
#             ruta_fisica = os.path.join("assets", "exports", nombre_archivo)

#             from reportlab.lib.pagesizes import A4, landscape
#             from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
#             from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
#             from reportlab.lib import colors

#             # Usamos Landscape (horizontal) para tener más espacio para las columnas
#             doc = SimpleDocTemplate(ruta_fisica, pagesize=landscape(A4), 
#                                     leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
#             styles = getSampleStyleSheet()
            
#             # Estilo para el texto dentro de las celdas que requiere ajuste de línea
#             style_cell = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=8, leading=10)
#             style_header = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontSize=9, 
#                                         textColor=colors.whitesmoke, fontName='Helvetica-Bold')

#             elementos = []

#             # Título del reporte
#             elementos.append(Paragraph(f"<b>Resumen resultados - {fecha_hoy} - Usuario: {user_name}</b>", styles['Title']))
            
#             # Filtros (Solo los activos)
#             filtros_txt = ", ".join([f"{k}: {v}" for k, v in self.filtros_aplicados.items() if v and v != []])
#             elementos.append(Paragraph(f"<b>Filtros aplicados:</b> {filtros_txt if filtros_txt else 'Ninguno'}", styles['Normal']))
#             elementos.append(Spacer(1, 15))

#             # --- CONFIGURACIÓN DE LA TABLA ---
#             # MODIFICADO: Añadir columnas de adjudicatario e importe adjudicación
#             headers = ["ID", "NOMBRE DE LA LICITACIÓN", "ENTIDAD", "IMPORTE", "ESTADO", "LIMITE", "ADJUDICATARIO", "IMP. ADJ.", "LINK"]
#             data = [headers]

#             for i, row in self.df_general.iterrows():
#                 # Procesar Prioridad
#                 prioridad = str(row.get('PRIORIDAD_IA', 'No estudiado'))
#                 prioridad_txt = "No estudiado (en desarrollo)" if prioridad == "No estudiado" else prioridad
                
#                 # Procesar Fecha
#                 f_limite = row.get('FECHA_LIMITE')
#                 fecha_txt = str(f_limite) if pd.notnull(f_limite) and f_limite != "" else "No aplica"

#                 # Procesar datos de adjudicación
#                 adjudicatario = str(row.get('ADJUDICATARIO', 'No aplica'))
#                 imp_adj = row.get('IMPORTE_ADJUDICACION', 'No aplica')
#                 if imp_adj != 'No aplica':
#                     try:
#                         imp_adj = f"{float(imp_adj):,.2f} €"
#                     except:
#                         imp_adj = str(imp_adj)

#                 # Creamos la fila
#                 fila = [
#                     Paragraph(str(row.get("ID", "")), style_cell),
#                     Paragraph(str(row.get("NOMBRE_PROYECTO", "")).upper(), style_cell),
#                     Paragraph(str(row.get("ENTIDAD", "")), style_cell),
#                     str(row.get("IMPORTE", "")),
#                     str(row.get("ESTADO", "Ver portal")),
#                     fecha_txt,
#                     Paragraph(adjudicatario, style_cell),
#                     str(imp_adj),
#                 ]
                
#                 url = row.get('URL', None)
#                 if url:
#                     fila.append(Paragraph(f'<a href="{url}" color="blue"><u>Ver licitación</u></a>', style_cell))
#                 else:
#                     fila.append("No disponible")
                    
#                 data.append(fila)

#             # MODIFICADO: Ajustar anchos de columna para incluir las nuevas columnas
#             col_widths = [35, 200, 100, 60, 60, 60, 100, 70, 65] 

#             tabla = Table(data, colWidths=col_widths, repeatRows=1)
            
#             tabla.setStyle(TableStyle([
#                 ('BACKGROUND', (0, 0), (-1, 0), colors.blueviolet),
#                 ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#                 ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
#                 ('FONTSIZE', (0, 0), (-1, -1), 8),
#                 ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
#                 ('TOPPADDING', (0, 0), (-1, -1), 4),
#             ]))

#             elementos.append(tabla)
#             doc.build(elementos)

#             # Lanzar URL con tu función personalizada
#             url_publica = f"/exports/{nombre_archivo}"
#             self.page.run_task(self._handle_abrir_url, url_publica)

#         except Exception as ex:
#             print(f"Error PDF: {ex}")

#     async def _ver_reporte_pdf(self, e):
#         print("Iniciando generación de PDF...")
#         try:
#             user_name = getattr(self, "usuario_actual", "usuario").replace(" ", "_")
#             nombre_archivo = f"reporte_{user_name}.pdf"
            
#             # Asegúrate de que la ruta sea relativa a donde ejecutas el script
#             ruta_fisica = os.path.join("assets", "exports", nombre_archivo)
            
#             # --- (Aquí va tu código de generación de PDF con Reportlab igual que antes) ---
#             # ... (Generación del PDF) ...
#             # ------------------------------------------------------------------------------

#             print(f"PDF creado en: {ruta_fisica}")

#             # 3. LANZAR URL CORREGIDO
#             url_publica = f"/exports/{nombre_archivo}"
#             print(f"Lanzando URL: {url_publica}")
            
#             # CORRECCIÓN AQUÍ: Usar await y la nueva sintaxis
#             await self.page.launch_url(url_publica)
            
#         except Exception as ex:
#             print(f"ERROR: {ex}")
#             self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="red")
#             self.page.snack_bar.open = True
        
#         await self.page.update_async() # También usa update_async si tu app es async

#     async def _ver_reporte_pdf(self, e):
#         try:
#             user_name = getattr(self, "usuario_actual", "usuario")
#             fecha_hoy = datetime.now().strftime("%d/%m/%Y")
#             nombre_archivo = f"reporte_{user_name.replace(' ', '_')}.pdf"
#             ruta_fisica = os.path.join("assets", "exports", nombre_archivo)

#             from reportlab.lib.pagesizes import A4
#             from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
#             from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
#             from reportlab.lib.enums import TA_CENTER

#             doc = SimpleDocTemplate(ruta_fisica, pagesize=A4)
#             styles = getSampleStyleSheet()
            
#             # Estilos personalizados
#             estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=20)
#             estilo_subtitulo = ParagraphStyle('Subtitulo', parent=styles['Heading3'], textColor="#2E5077", spaceBefore=15)
#             estilo_cuerpo = styles['Normal']
            
#             elementos = []

#             # 1. TÍTULO
#             elementos.append(Paragraph(f"Resumen resultados, {fecha_hoy}, {user_name}", estilo_titulo))
#             elementos.append(Spacer(1, 10))

#             # 2. FILTROS (Solo los que tienen valor)
#             elementos.append(Paragraph("<b>Los resultados mostrados a continuación respetan los siguientes filtros:</b>", estilo_cuerpo))
#             filtros_activos = [f"• {k}: {v}" for k, v in self.filtros_aplicados.items() if v and v != []]
            
#             if filtros_activos:
#                 for f in filtros_activos:
#                     elementos.append(Paragraph(f, estilo_cuerpo))
#             else:
#                 elementos.append(Paragraph("• Ningún filtro aplicado.", estilo_cuerpo))
            
#             elementos.append(Spacer(1, 20))
#             elementos.append(HRFlowable(width="100%", thickness=1, color="black"))

#             # 3. CONTENIDO (Fichas por licitación)
#             for i, row in self.df_general.iterrows():
#                 # Procesar datos con lógica de seguridad
#                 nombre = str(row.get('NOMBRE_PROYECTO', 'Sin nombre')).upper()
#                 entidad = str(row.get('ENTIDAD', 'No especificada'))
#                 importe = str(row.get('IMPORTE', 'N/A'))
                
#                 # Estado (Si no está en el DF de resultados, puedes buscarlo en el DF completo o poner 'Ver detalle')
#                 estado = str(row.get('ESTADO', 'Ver en portal')) 
                
#                 # Fecha Límite
#                 fecha_limite = row.get('FECHA_LIMITE')
#                 fecha_txt = str(fecha_limite) if pd.notnull(fecha_limite) and fecha_limite != "" else "No aplica"
                
#                 # Prioridad IA
#                 prioridad = str(row.get('PRIORIDAD_IA', 'No estudiado'))
#                 if prioridad == "No estudiado":
#                     prioridad_txt = "No estudiado, en desarrollo aun agradecemos su comprensión."
#                 else:
#                     prioridad_txt = prioridad

#                 # NUEVO: Datos de adjudicación
#                 adjudicatario = str(row.get('ADJUDICATARIO', 'No aplica'))
#                 imp_adj = row.get('IMPORTE_ADJUDICACION', 'No aplica')
#                 if imp_adj != 'No aplica':
#                     try:
#                         imp_adj_txt = f"{float(imp_adj):,.2f} €"
#                     except:
#                         imp_adj_txt = str(imp_adj)
#                 else:
#                     imp_adj_txt = "No aplica"

#                 # Construir la ficha en el PDF
#                 elementos.append(Paragraph(f"Resultado #{i+1}: <i>{nombre}</i>", estilo_subtitulo))
#                 elementos.append(Paragraph(f"<b>Entidad adjudicadora:</b> {entidad}", estilo_cuerpo))
#                 elementos.append(Paragraph(f"<b>Importe:</b> {importe}", estilo_cuerpo))
#                 elementos.append(Paragraph(f"<b>Estado:</b> {estado}", estilo_cuerpo))
#                 elementos.append(Paragraph(f"<b>Fecha límite de presentación:</b> {fecha_txt}", estilo_cuerpo))
#                 elementos.append(Paragraph(f"<b>Prioridad:</b> {prioridad_txt}", estilo_cuerpo))
                
#                 # NUEVO: Información de adjudicación
#                 elementos.append(Paragraph(f"<b>Adjudicatario:</b> {adjudicatario}", estilo_cuerpo))
#                 elementos.append(Paragraph(f"<b>Importe de adjudicación:</b> {imp_adj_txt}", estilo_cuerpo))
                
#                 # Añadir un link directo si existe
#                 url = row.get('URL', None)
#                 if url:
#                     elementos.append(Paragraph(f'<a href="{url}" color="blue"><u>Ver licitación en el portal</u></a>', estilo_cuerpo))
                
#                 elementos.append(Spacer(1, 10))
#                 elementos.append(HRFlowable(width="30%", thickness=0.5, color="grey", hAlign="LEFT"))

#             # Generar PDF
#             doc.build(elementos)

#             # Lanzar URL usando tu nueva lógica
#             url_publica = f"/exports/{nombre_archivo}"
#             self.page.run_task(self._handle_abrir_url, url_publica)

#         except Exception as ex:
#             print(f"Error al generar reporte: {ex}")
#             self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
#             self.page.snack_bar.open = True
#             self.page.update()

#     def _mostrar_snackbar(self, mensaje, error=False):
#         self.page.snack_bar = ft.SnackBar(
#             content=ft.Text(mensaje),
#             bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400,
#         )
#         self.page.snack_bar.open = True
#         self.page.update()

## --------------------------------------
## CORRIGIENDO TEMAS DE PLIEGO ID
## ---------------------------------------

import flet as ft
import pandas as pd
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
try:
    from chatbot_licitacion import BotonChatbotFlotante 
    from gestor_CPVS import CPVFilterManager
except:
    from .chatbot_licitacion import BotonChatbotFlotante 
    from .gestor_CPVS import CPVFilterManager     

from utils.load_data import load_dataset

#Librerias utilitarias para el tema de la generacion de documentos sobre  la pantalla de resultados.
import xml.etree.ElementTree as ET
from xml.dom import minidom
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

class GestorFavoritos:
    """Clase para manejar el almacenamiento de favoritos de forma persistente"""
    
    def __init__(self, page: ft.Page, usuario_actual:str):

        # Crear carpeta de exportaciones si no existe
        if not os.path.exists("assets/exports"):
            os.makedirs("assets/exports", exist_ok= True)
        # self.page = page
        self.usuario_actual = usuario_actual
        # self.archivo_favoritos = self._get_archivo_path()
        self.archivo_favoritos = "usuarios.json"# Cargamos ambos estados al iniciar
        # self.favoritos = self._cargar_dato_usuario("favoritos")
        # self.descartados = self._cargar_dato_usuario("licitaciones_descartadas")
        self.favoritos = self._cargar_favoritos()
        self.descartados = self._cargar_descartados()
        self.descartados = list(self.descartados)
    
    # def _get_archivo_path(self):
    #     """Obtiene la ruta del archivo de favoritos"""
    #     config_dir = Path.home() / ".licitaciones_app"
    #     config_dir.mkdir(exist_ok=True)
    #     return config_dir / "favoritos.json"
    
    def _cargar_dato_usuario(self, clave):
        """Carga una lista específica (favoritos o descartados) del JSON"""
        try:
            if os.path.exists(self.archivo_favoritos):
                with open(self.archivo_favoritos, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if self.usuario_actual in data:
                        return data[self.usuario_actual].get(clave, [])
        except Exception as e:
            print(f"Error cargando {clave}: {e}")
        return []

    def _guardar_datos(self):
        """Guarda el estado actual de favoritos y descartados en el JSON"""
        try:
            with open(self.archivo_favoritos, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if self.usuario_actual in data:
                data[self.usuario_actual]["favoritos"] = self.favoritos
                data[self.usuario_actual]["licitaciones_descartadas"] = self.descartados
                
                with open(self.archivo_favoritos, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando datos: {e}")

    def toggle_descarte(self, id_licitacion):
        """Añade o quita de la lista de descartados"""
        id_licitacion = str(id_licitacion)
        if id_licitacion in self.descartados:
            self.descartados.remove(id_licitacion)
        else:
            self.descartados.append(id_licitacion)
        self._guardar_datos()

    def es_descartado(self, id_licitacion):
        return str(id_licitacion) in self.descartados
    
    def _cargar_favoritos(self):
        """Carga los favoritos desde archivo JSON"""
        try:
            if os.path.exists(self.archivo_favoritos):
                # print("ENCONTRADO!")
                with open(self.archivo_favoritos, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data = data[self.usuario_actual]
                    # print(data)
                    favoritos_set = set(data.get("favoritos", []))
                    # print(f"✓ Favoritos cargados desde archivo: {favoritos_set}")
                    return favoritos_set
            else:
                print("ℹ️ No se encontró archivo de favoritos, iniciando vacío")
                return set()
        except Exception as e:
            print(f"⚠️ Error al cargar favoritos: {e}")
            return set()
        
    def _cargar_descartados(self):
        """Carga los favoritos desde archivo JSON"""
        try:
            if os.path.exists(self.archivo_favoritos):
                # print("ENCONTRADO!")
                with open(self.archivo_favoritos, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data = data[self.usuario_actual]
                    # print(data)
                    descartadas_set = set(data.get("licitaciones_descartadas", []))
                    # print(f"✓ Favoritos cargados desde archivo: {favoritos_set}")
                    return descartadas_set
            else:
                print("ℹ️ No se encontró archivo de favoritos, iniciando vacío")
                return set()
        except Exception as e:
            print(f"⚠️ Error al cargar favoritos: {e}")
            return set()
        
    def _guardar_descartados(self):
        """Guarda los favoritos en archivo JSON de forma persistente"""
        try:
            with open(self.archivo_favoritos, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # data = data[self.usuario_actual]

            data[self.usuario_actual]["licitaciones_descartadas"]= list(self.descartados)
            # data = {
            #     "favoritos": list(self.favoritos),
            #     "fecha_actualizacion": datetime.now().isoformat()
            # }
            with open(self.archivo_favoritos, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Favoritos guardados en: {self.archivo_favoritos}")
            print(f"  Total: {len(self.favoritos)} favoritos")
        except Exception as e:
            print(f"❌ Error al guardar favoritos: {e}")
            
    def _guardar_favoritos(self):
        """Guarda los favoritos en archivo JSON de forma persistente"""
        try:
            with open(self.archivo_favoritos, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # data = data[self.usuario_actual]

            data[self.usuario_actual]["favoritos"]= list(self.favoritos)
            # data = {
            #     "favoritos": list(self.favoritos),
            #     "fecha_actualizacion": datetime.now().isoformat()
            # }
            with open(self.archivo_favoritos, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Favoritos guardados en: {self.archivo_favoritos}")
            print(f"  Total: {len(self.favoritos)} favoritos")
        except Exception as e:
            print(f"❌ Error al guardar favoritos: {e}")
    
    def agregar(self, id_licitacion):
        """Agrega una licitación a favoritos"""
        self.favoritos.add(str(id_licitacion))
        self._guardar_favoritos()
    
    def quitar(self, id_licitacion):
        """Quita una licitación de favoritos"""
        self.favoritos.discard(str(id_licitacion))
        self._guardar_favoritos()
    
    def es_favorito(self, id_licitacion):
        """Verifica si una licitación está en favoritos"""
        return str(id_licitacion) in self.favoritos
    
    def toggle(self, id_licitacion):
        """Alterna el estado de favorito"""
        if self.es_favorito(id_licitacion):
            self.quitar(id_licitacion)
            return False
        else:
            self.agregar(id_licitacion)
            return True
    
    def obtener_todos(self):
        """Retorna la lista de todos los IDs favoritos"""
        return list(self.favoritos)


class PaginaResultados(ft.Container):
    def __init__(self, page: ft.Page, df_general: pd.DataFrame, df_requisitos: pd.DataFrame, 
                 df_criterios: pd.DataFrame, df_docs: pd.DataFrame, df_cpv:pd.DataFrame, usuario_actual:str,
                 on_detalles, filtros_aplicados=None, on_aplicar_filtros=None, df_completo=None):
        super().__init__()
        # self.page = page
        self.df_general = df_general
        self.df_general_completo = df_completo if df_completo is not None else df_general
        self.df_requisitos = df_requisitos
        self.df_criterios = df_criterios
        self.df_docs = df_docs
        self.df_cpv = df_cpv
        self.usuario_actual = usuario_actual
        self.on_detalles = on_detalles
        self.on_aplicar_filtros = on_aplicar_filtros

        # NUEVO: Cargar datos de adjudicatarios
        self.df_adjudicatarios = self._cargar_adjudicatarios()
        
        # Guardar filtros aplicados
        self.filtros_aplicados = filtros_aplicados or {}
        print(self.filtros_aplicados)
        
        # Controles de filtros editables
        self.filtro_controls = {}

        # Gestor de favoritos
        self.gestor_favoritos = GestorFavoritos(page, self.usuario_actual)
        
        # Estado de filtro
        self.mostrar_solo_favoritos = False
        
        # Estado de la barra lateral
        self.sidebar_visible = True

        # NUEVO: Variables de paginación
        self.pagina_actual = 1
        self.elementos_por_pagina = 100
        self.total_paginas = 1

        # Crear botón flotante
        self.btn_chatbot_flotante = BotonChatbotFlotante(page)

        # Agregarlo a la página
        if self.btn_chatbot_flotante not in page.overlay:
            page.overlay.append(self.btn_chatbot_flotante)

        self.selected_container = None  # Esto evita el AttributeError
        self.selected_row = None        # Para guardar los datos de la fila

        self._build_ui()

    def _cargar_adjudicatarios(self):
        """Carga el DataFrame de adjudicatarios"""
        try:
            # df_adj = load_dataset(r"src\data", "Adjudicatarios_general.parquet")
            df_adj = load_dataset(r"src/data", "Adjudicatarios_general.parquet")
            # Convertir pliego_id a string para el merge
            df_adj["ID_INTERNO"] = df_adj["ID_INTERNO"].astype(str)
            return df_adj
        except Exception as e:
            print(f"⚠️ Error al cargar adjudicatarios: {e}")
            # Retornar DataFrame vacío con las columnas esperadas
            return pd.DataFrame(columns=["ID_INTERNO", "nombre", "importe"])

    def _obtener_cpvs_disponibles(self):
        """Obtiene la lista de CPVs únicos del dataset"""
        # print("CPVS TODOS",self.df_cpv)
        try:
            if 'codigo' in self.df_cpv.columns:
                cpvs = self.df_cpv['codigo'].dropna().unique().tolist()
                # print(cpvs)
                return sorted([str(cpv) for cpv in cpvs])
            return []
        except Exception as e:
            print(f"Error obteniendo CPVs: {e}")
            return []

    def _on_cpvs_changed(self, cpvs):
        """Actualiza los filtros cuando cambian los CPVs"""
        if cpvs:
            self.filtros_aplicados['cpv'] = cpvs
        else:
            self.filtros_aplicados.pop('cpv', None)

    def _render_cpvs(self):
        cpvs = self.filtros_aplicados.get("cpv") or []

        self.cpv_container.controls.clear()

        for cpv in cpvs:
            self.cpv_container.controls.append(
                ft.Chip(
                    label=ft.Text(cpv),
                    on_delete=lambda e, cpv=cpv: self._remove_cpv(cpv),
                )
            )

        self.page.update()

    def _remove_cpv(self, cpv):
        cpvs = self.filtros_aplicados.get("cpv") or []

        if cpv in cpvs:
            cpvs.remove(cpv)

        if cpvs:
            self.filtros_aplicados["cpv"] = cpvs
        else:
            self.filtros_aplicados.pop("cpv", None)

        self._render_cpvs()

    def _crear_sidebar(self):
        """Crea la barra lateral con filtros y favoritos"""
        
        # Sección de filtros EDITABLES
        filtros_widgets = [
            ft.Text("🔍 Filtros de Búsqueda", 
                   size=16, 
                   weight=ft.FontWeight.BOLD,
                   color=ft.Colors.BLUE_700)
        ]
        
        # Crear controles editables para cada tipo de filtro común
        self.filtro_controls = {}
   
        
        # Filtro de presupuesto
        self.filtro_controls['presupuesto_min'] = ft.TextField(
            label="Presupuesto mínimo",
            value=self.filtros_aplicados.get('importe_min', ''),
            hint_text="Ej: 50000",
            border_color=ft.Colors.BLUE_300,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        self.filtro_controls['presupuesto_max'] = ft.TextField(
            label="Presupuesto máximo",
            value=self.filtros_aplicados.get('importe_max', ''),
            hint_text="Ej: 500000",
            border_color=ft.Colors.BLUE_300,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        

        #Modificacion Filtro Fechas
        self.fecha_desde_input = ft.TextField(
            label="Fecha desde",
            value=(
                self.filtros_aplicados.get('fecha_desde').strftime("%Y-%m-%d")
                if isinstance(self.filtros_aplicados.get('fecha_desde'), datetime)
                else (self.filtros_aplicados.get('fecha_desde') or "").partition("T")[0]
            ),
            hint_text="YYYY-MM-DD",
            border_color=ft.Colors.BLUE_300,
            dense=True,
            expand=True,
        )

        self.fecha_hasta_input = ft.TextField(
            label="Fecha hasta",
            value=(
                self.filtros_aplicados.get('fecha_hasta').strftime("%Y-%m-%d")
                if isinstance(self.filtros_aplicados.get('fecha_hasta'), datetime)
                else (self.filtros_aplicados.get('fecha_hasta') or "").partition("T")[0]
            ),
            hint_text="YYYY-MM-DD",
            border_color=ft.Colors.BLUE_300,
            dense=True,
            expand=True,
        )
        self.filtro_controls['fechas'] = ft.Column(
            controls=[
                ft.Text(
                    "Fecha limite de presentación",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700,
                ),
                ft.Row(
                    controls=[
                        self.fecha_desde_input,
                        self.fecha_hasta_input,
                    ],
                    spacing=8,
                ),
            ],
            spacing=4,
        )

        ## Fechas de Publicacion
        self.fecha_desde_publicado_input = ft.TextField(
            label="Fecha desde",
            value=(
                self.filtros_aplicados.get('fecha_desde_publicado').strftime("%Y-%m-%d")
                if isinstance(self.filtros_aplicados.get('fecha_desde_publicado'), datetime)
                else (self.filtros_aplicados.get('fecha_desde_publicado') or "").partition("T")[0]
            ),
            hint_text="YYYY-MM-DD",
            border_color=ft.Colors.BLUE_300,
            dense=True,
            expand=True,
        )

        self.fecha_hasta_publicado_input = ft.TextField(
            label="Fecha hasta",
            value=(
                self.filtros_aplicados.get('fecha_hasta_publicado').strftime("%Y-%m-%d")
                if isinstance(self.filtros_aplicados.get('fecha_hasta_publicado'), datetime)
                else (self.filtros_aplicados.get('fecha_publicado') or "").partition("T")[0]
            ),
            hint_text="YYYY-MM-DD",
            border_color=ft.Colors.BLUE_300,
            dense=True,
            expand=True,
        )

        self.filtro_controls['fechas_publicado'] = ft.Column(
            controls=[
                ft.Text(
                    "Fecha de publicación",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700,
                ),
                ft.Row(
                    controls=[
                        self.fecha_desde_publicado_input,
                        self.fecha_hasta_publicado_input,
                    ],
                    spacing=8,
                ),
            ],
            spacing=4,
        )

        # Estados de licitación
        self.estados = {
            "PUB": "Publicado",
            "EV": "Evaluado", 
            "ADJ": "Adjudicado",
            "RES": "Resuelto",
            "PRE": "Anuncio Previo"
        }
        
        self.filtro_controls["Estados"] = ft.Column(
            controls=[
                ft.Text(
                    "Estado de la publicación",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700,
                ),
                ft.Column(
                    controls=[
                        ft.Checkbox(label=nombre, value=False)
                        for codigo, nombre in self.estados.items()
                    ]
                )
            ]
        )
        
        # self.filtro_controls['CPVs'] = self.cpv_manager.get_control()        
        
        # Añadir todos los controles a la lista
        for control in self.filtro_controls.values():
            filtros_widgets.append(control)
        
        # Botones de acción para filtros
        btn_aplicar_filtros = ft.Button(
            "Aplicar filtros",
            icon=ft.Icons.SEARCH,
            on_click=self._aplicar_filtros_editados,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
            ),
        )
        
        btn_limpiar_filtros = ft.OutlinedButton(
            "Limpiar todo",
            icon=ft.Icons.CLEAR,
            on_click=self._limpiar_filtros,
            style=ft.ButtonStyle(
                color=ft.Colors.RED_600,
            ),
        )
        
        filtros_widgets.append(
            ft.Row([btn_aplicar_filtros, btn_limpiar_filtros], spacing=5)
        )
        
        # Sección de favoritos
        self.contador_favoritos_sidebar = ft.Text(
            f"⭐ {len(self.gestor_favoritos.favoritos)} favoritos",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_700,
        )
        
        self.switch_filtro_sidebar = ft.Switch(
            label="Solo favoritos",
            value=False,
            on_change=self._toggle_filtro_favoritos,
        )
        
        self.btn_exportar_sidebar = ft.Button(
            "Exportar favoritos",
            icon=ft.Icons.DOWNLOAD,
            on_click=self._exportar_favoritos,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE,
            ),
            disabled=len(self.gestor_favoritos.favoritos) == 0,
        )

        self.btn_exportar_excel = ft.Button(
            "Exportar tabla (Excel)",
            icon=ft.Icons.CODE,
            on_click=self._exportar_excel,
            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE),
        )

        self.btn_exportar_pdf = ft.Button(
            "Exportar informe de resultados (PDF)",
            icon=ft.Icons.PICTURE_AS_PDF,
            on_click=self._ver_reporte_pdf,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
        )

        self.btn_exportar_pdf_tabla = ft.Button(
            "Exportar tabla resultados (PDF)",
            icon=ft.Icons.PICTURE_AS_PDF,
            on_click=self._ver_reporte_pdf_tabla,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
        )
        
        # Botón para agregar/quitar favorito
        self.btn_favorito_sidebar = ft.Button(
            "Marcar como favorito",
            icon=ft.Icons.STAR_BORDER,
            icon_color=ft.Colors.AMBER,
            on_click=self._toggle_favorito,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_50,
            ),
        )
        
        self.btn_descartar_sidebar = ft.Button(
            "Descartar licitación",
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=ft.Colors.RED,
            on_click=self._descartar_licitacion,
            disabled=True, # Se activa al seleccionar una fila
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_50),
        )
        
        # Construir la sidebar
        sidebar = ft.Container(
            content=ft.Column([
                # ft.Text("⚙️ Panel de Control", 
                #        size=18, 
                #        weight=ft.FontWeight.BOLD,
                #        color=ft.Colors.BLUE_900),
                # ft.Divider(height=20, color=ft.Colors.BLUE_200),
                
                # Filtros editables
                # ft.Container(
                #     content=ft.Column(
                #         filtros_widgets,
                #         spacing=8,
                #         scroll=ft.ScrollMode.AUTO,
                #     ),
                #     height=500,
                # ),
                
                # ft.Divider(height=20, color=ft.Colors.BLUE_200),
                
                # Favoritos
                ft.Text("⭐ Gestión de Favoritos", 
                       size=16, 
                       weight=ft.FontWeight.BOLD,
                       color=ft.Colors.AMBER_700),
                self.contador_favoritos_sidebar,
                self.btn_favorito_sidebar,
                self.switch_filtro_sidebar,
                self.btn_exportar_sidebar,
                self.btn_exportar_pdf, # Nuevo
                self.btn_exportar_pdf_tabla, # Nuevo
                # self.btn_descartar_sidebar MOMENTANEAMENTE COMENTADO MIENTRAS SE AJUSTA EL AGREGAR LOS DESCARTADOS AL JSON
                
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            width=300,
            padding=15,
            bgcolor=ft.Colors.GREY_50,
            border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.GREY_300)),
        )

        # if 'cpv' in self.filtros_aplicados:
        #     self.cpv_manager.set_cpvs(self.filtros_aplicados['cpv'])
                
        return sidebar

    def _crear_controles_paginacion(self):
        """Crea los controles de paginación"""
        self.txt_info_pagina = ft.Text(
            f"Página {self.pagina_actual} de {self.total_paginas} ({len(self.df_general)} resultados)",
            size=14,
            color=ft.Colors.BLUE_700,
            weight=ft.FontWeight.BOLD,
        )
        
        self.btn_primera_pagina = ft.IconButton(
            icon=ft.Icons.FIRST_PAGE,
            tooltip="Primera página",
            on_click=lambda e: self._ir_a_pagina(1),
            disabled=self.pagina_actual == 1,
        )
        
        self.btn_pagina_anterior = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            tooltip="Página anterior",
            on_click=lambda e: self._ir_a_pagina(self.pagina_actual - 1),
            disabled=self.pagina_actual == 1,
        )
        
        self.btn_pagina_siguiente = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            tooltip="Página siguiente",
            on_click=lambda e: self._ir_a_pagina(self.pagina_actual + 1),
            disabled=self.pagina_actual >= self.total_paginas,
        )
        
        self.btn_ultima_pagina = ft.IconButton(
            icon=ft.Icons.LAST_PAGE,
            tooltip="Última página",
            on_click=lambda e: self._ir_a_pagina(self.total_paginas),
            disabled=self.pagina_actual >= self.total_paginas,
        )
        
        # Selector de elementos por página
        self.dropdown_elementos = ft.Dropdown(
            label="Elementos por página",
            value="100",
            options=[
                ft.dropdown.Option("50"),
                ft.dropdown.Option("100"),
                ft.dropdown.Option("200"),
                ft.dropdown.Option("500"),
            ],
            width=180,
            # on_change=self._cambiar_elementos_por_pagina,
        )
        self.dropdown_elementos.on_change = self._cambiar_elementos_por_pagina # Así es más seguro
        
        return ft.Row(
            [
                self.btn_primera_pagina,
                self.btn_pagina_anterior,
                self.txt_info_pagina,
                self.btn_pagina_siguiente,
                self.btn_ultima_pagina,
                ft.VerticalDivider(),
                self.dropdown_elementos,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _ir_a_pagina(self, numero_pagina):
        """Navega a una página específica"""
        if 1 <= numero_pagina <= self.total_paginas:
            self.pagina_actual = numero_pagina
            self._refrescar_tabla()

    def _cambiar_elementos_por_pagina(self, e):
        """Cambia la cantidad de elementos por página"""
        self.elementos_por_pagina = int(e.control.value)
        self.pagina_actual = 1  # Resetear a la primera página
        self._refrescar_tabla()

    def _actualizar_controles_paginacion(self):
        """Actualiza el estado de los controles de paginación"""
        self.txt_info_pagina.value = f"Página {self.pagina_actual} de {self.total_paginas} ({len(self.df_general)} resultados)"
        
        self.btn_primera_pagina.disabled = self.pagina_actual == 1
        self.btn_pagina_anterior.disabled = self.pagina_actual == 1
        self.btn_pagina_siguiente.disabled = self.pagina_actual >= self.total_paginas
        self.btn_ultima_pagina.disabled = self.pagina_actual >= self.total_paginas

    def _build_ui(self):
        # Botón para toggle de sidebar
        self.btn_toggle_sidebar = ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color=ft.Colors.BLUE_700,
            tooltip="Mostrar/Ocultar panel lateral",
            on_click=self._toggle_sidebar,
        )
        
        # Crear sidebar
        self.sidebar = self._crear_sidebar()
        # self._render_cpvs()
        
        # Crear controles de paginación
        self.controles_paginacion = self._crear_controles_paginacion()
        
        # -------- TABLA PRINCIPAL (GENERAL) --------
        self.cont_general = ft.Container(
            content=ft.Column(
                [self._crear_tabla_general()], 
                # scroll=ft.ScrollMode.ALWAYS, 
                # expand=True
            ),
            # height=self.page.height * 0.6,
            expand = 60,
            # border=ft.border.all(1, ft.Colors.GREY_400),
            border = ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            padding=10,
        )

        # -------- TABLAS RELACIONADAS --------
        tabla_requisitos = self._make_table(
            self.df_requisitos.head(50),
            ["ID_INTERNO", "TIPO", "DESCRIPCION"]
        )

        tabla_criterios = self._make_table(
            self.df_criterios.head(50),
            ["ID_INTERNO", "TIPO", "DESCRIPCION", "PESO"]
        )

        cont_requisitos = ft.Container(
            content=ft.Column([tabla_requisitos], scroll=ft.ScrollMode.ALWAYS),#, expand=True),
            # height=self.page.height * 0.22,
            expand= 22,
            # border=ft.border.all(1, ft.Colors.GREY_400),
            border = ft.Border.all(),
            border_radius=10,
            padding=10,
            # expand=True,
        )

        cont_criterios = ft.Container(
            content=ft.Column([tabla_criterios], scroll=ft.ScrollMode.ALWAYS),#, expand=True),
            # height=self.page.height * 0.25,
            expand=25,
            # border=ft.border.all(1, ft.Colors.GREY_400),
            border = ft.Border.all(),
            border_radius=10,
            padding=10,
            # expand=True,
        )

        # -------- BOTÓN DE NAVEGACIÓN --------
        self.boton_detalles = ft.Button(
            "Ver más detalles",
            icon=ft.Icons.ARROW_FORWARD,
            on_click=self._go_to_details,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE,
                padding=15,
            ),
        )

        # -------- CONTENIDO PRINCIPAL --------
        contenido_principal = ft.Column(
            [
                ft.Row([
                    self.btn_toggle_sidebar,
                    ft.Text("📄 Resultados de Búsqueda", size=22, weight=ft.FontWeight.BOLD),
                ], spacing=10),
                self.controles_paginacion,  # NUEVO: Controles de paginación arriba
                self.cont_general,
                self.controles_paginacion,  # NUEVO: Controles de paginación abajo también
                # ft.Row([cont_requisitos, cont_criterios], expand=True),
                ft.Row([self.boton_detalles], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # -------- ESTRUCTURA FINAL CON SIDEBAR --------
        self.content = ft.Row(
            [
                self.sidebar,
                ft.Container(
                    content=contenido_principal,
                    expand=True,
                    padding=10,
                )
            ],
            spacing=0,
            expand=True,
        )

    def _toggle_sidebar(self, e):
        """Muestra u oculta la barra lateral"""
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.visible = self.sidebar_visible
        self.btn_toggle_sidebar.icon = ft.Icons.MENU_OPEN if self.sidebar_visible else ft.Icons.MENU
        self.page.update()

    def _obtener_datos_paginados(self, df_trabajo):
        """Obtiene los datos correspondientes a la página actual"""
        # Calcular el total de páginas
        self.total_paginas = max(1, (len(df_trabajo) + self.elementos_por_pagina - 1) // self.elementos_por_pagina)
        
        # Asegurar que la página actual esté en rango válido
        if self.pagina_actual > self.total_paginas:
            self.pagina_actual = self.total_paginas
        
        # Calcular índices de inicio y fin
        inicio = (self.pagina_actual - 1) * self.elementos_por_pagina
        fin = inicio + self.elementos_por_pagina
        
        # Retornar slice del dataframe
        return df_trabajo.iloc[inicio:fin]

    def _crear_celda_expandible(self, contenido, flex_factor):
        """Crea un contenedor que ocupa una proporción del ancho total"""
        return ft.Container(
            content=contenido,
            expand=flex_factor, # Esto reemplaza al cálculo de self.page.width
            padding=5,
            alignment=ft.Alignment(-1.0, 0.0),
        )

    def _crear_tabla_general(self):
        """Crea la tabla general con indicadores de favoritos y datos de adjudicación"""

        # Cargar datos de análisis y textos
        df_analisis = load_dataset(r"src/data", "analisis_resultados.parquet") ## Versión Linux
        # df_analisis = load_dataset(r"src/data", "analisis_resultados.parquet")
        df_textos = load_dataset(r"src/data", "Textos_Extraidos_viejo.parquet")
        # df_textos = load_dataset(r"src", "Textos_Extraidos_viejo.parquet")

        # ===== CORRECCIÓN 1: Hacer el merge solo una vez y evitar duplicados =====
        # Asegurar que los IDs sean string para el merge
        df_analisis["ID_INTERNO"] = df_analisis["pliego_id"].astype(str)
        
        # Crear una copia del dataframe general para no modificar el original
        df_trabajo = self.df_general.copy()
        df_trabajo["ID_INTERNO"] = df_trabajo["ID_INTERNO"].astype(str)
        print(self.df_general)
        print("DF TRABAJO")
        print(df_trabajo)
    
        # ===== CORRECCIÓN 2: Verificar si ya tiene la columna PRIORIDAD =====
        if "PRIORIDAD" not in df_trabajo.columns:
            # Hacer merge solo si no existe la columna
            df_trabajo = df_trabajo.merge(
                df_analisis[["ID_INTERNO", "PRIORIDAD"]],
                on = "ID_INTERNO",
                how="left"
            )
            # # Eliminar columna duplicada del merge
            # if "ID_INTERNO" in df_trabajo.columns:
            #     df_trabajo = df_trabajo.drop(columns=["ID_INTERNO"])
        
        # ===== NUEVO: Merge con adjudicatarios =====
        if not self.df_adjudicatarios.empty:
            # Agrupar adjudicatarios por ID_INTERNO y tomar el primero (evitar duplicados)
            df_adj_primero = self.df_adjudicatarios.groupby("ID_INTERNO").first().reset_index()
            print("ADJ PRIMERO")
            print(df_adj_primero)
            
            # Hacer merge con los datos de adjudicación
            df_trabajo = df_trabajo.merge(
                df_adj_primero[["ID_INTERNO", "NOMBRE_ADJUDICATARIO", "IMPORTE_CON_IVA"]],
                on="ID_INTERNO",
                how="left",
                suffixes=('', '_adj')
            )
            
            # Renombrar columnas de adjudicación
            df_trabajo = df_trabajo.rename(columns={
                "NOMBRE_ADJUDICATARIO": "ADJUDICATARIO",
                "IMPORTE_CON_IVA": "IMPORTE_ADJUDICACION"
            })
            
            # Eliminar columna duplicada del merge
            # if "ID_INTERNO" in df_trabajo.columns:
            #     df_trabajo = df_trabajo.drop(columns=["ID_INTERNO"])
            
            # Rellenar valores nulos con "No aplica"
            df_trabajo["ADJUDICATARIO"] = df_trabajo["ADJUDICATARIO"].fillna("No aplica")
            df_trabajo["IMPORTE_ADJUDICACION"] = df_trabajo["IMPORTE_ADJUDICACION"].fillna("No aplica")
        else:
            # Si no hay datos de adjudicatarios, crear columnas con "No aplica"
            df_trabajo["ADJUDICATARIO"] = "No aplica"
            df_trabajo["IMPORTE_ADJUDICACION"] = "No aplica"
        
        # Convertir PRIORIDAD a string y rellenar vacíos
        df_trabajo["PRIORIDAD"] = df_trabajo["PRIORIDAD"].astype(str)
        df_trabajo['PRIORIDAD'] = df_trabajo['PRIORIDAD'].fillna("No estudiado")
        df_trabajo['PRIORIDAD'] = df_trabajo['PRIORIDAD'].replace('nan', 'No estudiado')
        df_trabajo['PRIORIDAD'] = df_trabajo['PRIORIDAD'].replace('<NA>', 'No estudiado')

        # Definir orden de prioridad
        orden_prioridad = {
            "ALTA": 4,
            "MEDIA": 3,
            "BAJA": 2,
            "No estudiado": 1
        }

        # Crear columna auxiliar para ordenar
        df_trabajo["orden_prioridad"] = df_trabajo["PRIORIDAD"].map(
            lambda x: orden_prioridad.get(x, 5)
        )

        # ===== CORRECCIÓN 3: Eliminar duplicados ANTES de ordenar =====
        # Esto evita problemas con favoritos de filas duplicadas
        df_trabajo = df_trabajo.drop_duplicates(
            subset=["ID_INTERNO"],
            keep="first"
        )

        # Ordenar por prioridad
        df_trabajo = df_trabajo.sort_values(
            by=["orden_prioridad"],
            ascending=False
        )

        # Eliminar duplicados por proyecto manteniendo el de mayor prioridad
        df_trabajo = df_trabajo.drop_duplicates(
            subset=["NOMBRE_PROYECTO"],
            keep="first"
        )

        # Limpieza fuerte de valores
        df_trabajo["PRIORIDAD"] = (
            df_trabajo["PRIORIDAD"]
                .astype(str)
                .str.strip()         # Quita espacios
                .str.upper()         # Convierte a mayúsculas
                .replace(["NAN", "<NA>", "NONE"], "NO ESTUDIADO")
        )

        # Eliminar la columna auxiliar
        df_trabajo = df_trabajo.drop(columns=["orden_prioridad"])

        # Iconos para cada prioridad
        iconos_prioridad = {
            "ALTA": "🟢 ALTA",
            "MEDIA": "🟡 MEDIA",
            "BAJA": "🔴 BAJA",
            "Descartado": "⬛ Descartado",
            "No estudiado": "▫️ No estudiado"
        }

        # Aplicar icono
        df_trabajo["PRIORIDAD"] = df_trabajo["PRIORIDAD"].map(
            lambda x: iconos_prioridad.get(x, "▫️ No estudiado")
        )

        # ===== CORRECCIÓN 4: Aplicar filtro de favoritos sobre df_trabajo =====
        if self.mostrar_solo_favoritos:
            df_filtrado = df_trabajo[
                df_trabajo["ID_INTERNO"].astype(str).isin(self.gestor_favoritos.favoritos)
            ]
            if df_filtrado.empty:
                return ft.Text(
                    "⭐ No tienes licitaciones favoritas aún",
                    size=16,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                )
        else:
            df_filtrado = df_trabajo

        # NUEVO: Aplicar paginación
        df_paginado = self._obtener_datos_paginados(df_filtrado)
        
        # Actualizar controles de paginación
        self._actualizar_controles_paginacion()

        #----------------------------------------------- Modificacion

        # 2. Definición de la CABECERA (Header)
        # MODIFICADO: Añadir columnas de adjudicatario e importe adjudicación
        header = ft.Container(
            bgcolor=ft.Colors.BLUE_GREY_50,
            border=ft.Border.only(bottom=ft.border.BorderSide(2, ft.Colors.BLUE_700)),
            content=ft.Row([
                self._crear_celda_expandible(ft.Text("⭐", weight="bold"), 1),
                self._crear_celda_expandible(ft.Text("ID", weight="bold"), 6),
                self._crear_celda_expandible(ft.Text("NOMBRE PROYECTO", weight="bold"), 6),
                self._crear_celda_expandible(ft.Text("ENTIDAD", weight="bold"), 4),
                self._crear_celda_expandible(ft.Text("IMPORTE", weight="bold"), 2),
                self._crear_celda_expandible(ft.Text("LÍMITE", weight="bold"), 2),
                self._crear_celda_expandible(ft.Text("PRIORIDAD", weight="bold"), 2),
                self._crear_celda_expandible(ft.Text("ADJUDICATARIO", weight="bold"), 4),
                self._crear_celda_expandible(ft.Text("IMP. ADJ.", weight="bold"), 2),
            ])
        )

        # 3. Creación de las FILAS (Data Rows)
        # MODIFICADO: Añadir celdas para adjudicatario e importe adjudicación
        filas_controles = []
        for _, row in df_paginado.iterrows():
            es_fav = self.gestor_favoritos.es_favorito(row["ID_INTERNO"])
            
            # Formatear importe de adjudicación
            imp_adj = row.get("IMPORTE_ADJUDICACION", "No aplica")
            if imp_adj != "No aplica":
                try:
                    imp_adj = f"{float(imp_adj):,.2f} €"
                except:
                    imp_adj = str(imp_adj)
            
            nueva_fila = ft.Container(
                padding=ft.Padding.symmetric(vertical=5),
                border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
                on_click=lambda e, r=row: self._on_row_click(e, r),
                content=ft.Row([
                    # Columna Favorito
                    self._crear_celda_expandible(
                        ft.Icon(
                            ft.Icons.STAR if es_fav else ft.Icons.STAR_BORDER,
                            color=ft.Colors.AMBER if es_fav else ft.Colors.GREY_400,
                            size=20
                        ), 1
                    ),
                    # Columna Proyecto (con link)
                    self._crear_celda_expandible(ft.Text(str(row["ID"]),size=12, selectable=True), 4),
                    self._crear_celda_expandible(
                        ft.TextButton(
                            content=ft.Text(
                                str(row["NOMBRE_PROYECTO"]),
                                color=ft.Colors.BLUE,
                                size=12,
                            ),
                            # on_click=lambda e, r=row: self._abrir_detalle(r),
                            url=row.get('URL', "https://www.hacienda.gob.es"),
                            style=ft.ButtonStyle(padding=0),
                        ), 6
                    ),
                    # Columna Entidad
                    self._crear_celda_expandible(ft.Text(str(row["ENTIDAD"]), size=12), 4),
                    # Columna Importe
                    self._crear_celda_expandible(ft.Text(str(row["IMPORTE"]), size=12), 2),
                    # Columna Fecha
                    self._crear_celda_expandible(ft.Text(str(row["FECHA_LIMITE"]), size=12), 2),
                    # Columna Prioridad
                    self._crear_celda_expandible(ft.Text(str(row["PRIORIDAD"]), size=12), 2),
                    # NUEVO: Columna Adjudicatario
                    self._crear_celda_expandible(
                        ft.Text(
                            str(row.get("ADJUDICATARIO", "No aplica")), 
                            size=11,
                            color=ft.Colors.GREEN_700 if row.get("ADJUDICATARIO", "No aplica") != "No aplica" else ft.Colors.GREY_500
                        ), 4
                    ),
                    # NUEVO: Columna Importe Adjudicación
                    self._crear_celda_expandible(
                        ft.Text(
                            str(imp_adj), 
                            size=11,
                            weight=ft.FontWeight.BOLD if imp_adj != "No aplica" else ft.FontWeight.NORMAL,
                            color=ft.Colors.GREEN_700 if imp_adj != "No aplica" else ft.Colors.GREY_500
                        ), 2
                    ),
                ])
            )
            filas_controles.append(nueva_fila)

        # 4. Ensamblaje final
        return ft.Column([
            header,
            ft.Column(
                controls=filas_controles,
                scroll=ft.ScrollMode.ADAPTIVE,
                expand=True
            )
        ], expand=True)
    
    

    def _make_table(self, df, columnas):
        columnas_lista = list(columnas)
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col)) for col in columnas_lista],
            rows=[
                ft.DataRow(
                    cells=[ft.DataCell(ft.Text(str(row[col]))) for col in columnas_lista]
                )
                for _, row in df.iterrows()
            ],
        )
    
    # def _abrir_detalle(self,row):
    #     try:
    #         url=row['URL']
    #     except:
    #         url="https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
    #     self.page.run_task(self._handle_abrir_url, url)
    #     # self._handle_abrir_url(url)

    # # 1. Define una función asíncrona dedicada para abrir la URL
    async def _handle_abrir_url(self,url):
        # url = self.url_actual  # O de donde obtengas la URL
        print(f"Abriendo navegador para: {url}")
        # Usamos await para que la corrutina se ejecute realmente
        await self.page.launch_url(url) 

    async def _abrir_detalle(self, row):
        try:
            url = row['URL']
        except:
            url = "https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
        
        print(f"Abriendo: {url}")
        # Llamada directa sin run_task, mucho más rápido
        await self.page.launch_url(url)

    # def _on_row_click(self, row_data):
    #     """Guarda la fila seleccionada y actualiza el botón de favorito"""
    #     self.selected_row = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data

    #     # Actualizar botón de favorito en sidebar
    #     es_favorito = self.gestor_favoritos.es_favorito(self.selected_row["ID_INTERNO"])
    #     self.btn_favorito_sidebar.text = "Quitar de favoritos" if es_favorito else "Marcar como favorito"
    #     self.btn_favorito_sidebar.icon = ft.Icons.STAR if es_favorito else ft.Icons.STAR_BORDER
    #     self.btn_favorito_sidebar.disabled = False

    #     # Activar botón de chatbot con los docs de esta licitación
    #     docs_licitacion = self.df_docs[self.df_docs["ID_INTERNO"] == self.selected_row["ID_INTERNO"]]
    #     self.btn_chatbot_flotante.activar(
    #         df_docs=docs_licitacion,
    #         nombre_licitacion=self.selected_row["NOMBRE_PROYECTO"]
    #     )

    #     self.page.snack_bar = ft.SnackBar(
    #         content=ft.Text(f"✔️ Fila seleccionada: ID_INTERNO {self.selected_row['ID_INTERNO']}"),
    #         bgcolor=ft.Colors.BLUE_100,
    #     )
    #     self.page.snack_bar.open = True
    #     self.page.update()
    
    def _on_row_click(self, e, row_data):
        
        # 1. Quitar el resaltado de la fila anterior si existe
        if self.selected_container:
            self.selected_container.bgcolor = None
            
        # 2. Resaltar la nueva fila (e.control es el Container que disparó el click)
        self.selected_container = e.control
        self.selected_container.bgcolor = ft.Colors.BLUE_50 # Color suave de selección
        
        """Guarda la fila seleccionada y actualiza el botón de favorito"""
        self.selected_row = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data

        # Actualizar botón de favorito en sidebar
        es_favorito = self.gestor_favoritos.es_favorito(self.selected_row["ID_INTERNO"])
        self.btn_favorito_sidebar.text = "Quitar de favoritos" if es_favorito else "Marcar como favorito"
        self.btn_favorito_sidebar.icon = ft.Icons.STAR if es_favorito else ft.Icons.STAR_BORDER
        self.btn_favorito_sidebar.disabled = False

        # Activar botón de chatbot con los docs de esta licitación
        docs_licitacion = self.df_docs[self.df_docs["ID_INTERNO"] == self.selected_row["ID_INTERNO"]]
        self.btn_chatbot_flotante.activar(
            df_docs=docs_licitacion,
            nombre_licitacion=self.selected_row["NOMBRE_PROYECTO"]
        )

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"✔️ Fila seleccionada: ID_INTERNO {self.selected_row['ID_INTERNO']}"),
            bgcolor=ft.Colors.BLUE_100,
        )
        self.page.snack_bar.open = True
        self.btn_descartar_sidebar.disabled = False # Habilitar el nuevo botón
        self.page.update()

    def _toggle_favorito(self, e):
        """Agrega o quita de favoritos la fila seleccionada"""
        if self.selected_row is None:
            return

        id_licitacion = self.selected_row["ID_INTERNO"]
        es_favorito = self.gestor_favoritos.toggle(id_licitacion)

        # Actualizar botón en sidebar
        self.btn_favorito_sidebar.text = "Quitar de favoritos" if es_favorito else "Marcar como favorito"
        self.btn_favorito_sidebar.icon = ft.Icons.STAR if es_favorito else ft.Icons.STAR_BORDER

        # Actualizar contador
        self.contador_favoritos_sidebar.value = f"⭐ {len(self.gestor_favoritos.favoritos)} favoritos"
        
        # Actualizar botón de exportar
        self.btn_exportar_sidebar.disabled = len(self.gestor_favoritos.favoritos) == 0

        # Actualizar tabla si estamos en modo favoritos
        if self.mostrar_solo_favoritos:
            self._refrescar_tabla()

        # Mostrar notificación
        mensaje = "✨ Añadido a favoritos" if es_favorito else "🗑️ Quitado de favoritos"
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=ft.Colors.GREEN_100 if es_favorito else ft.Colors.GREY_300,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _toggle_filtro_favoritos(self, e):
        """Activa/desactiva el filtro de favoritos"""
        self.mostrar_solo_favoritos = e.control.value
        self.pagina_actual = 1  # NUEVO: Resetear a primera página al cambiar filtro
        self._refrescar_tabla()

    def _refrescar_tabla(self):
        """Refresca la tabla general"""
        self.cont_general.content.controls[0] = self._crear_tabla_general()
        self.page.update()
    
    def _exportar_favoritos(self, e):
        """Exporta las licitaciones favoritas a un archivo Excel"""
        try:
            ids_favoritos = self.gestor_favoritos.obtener_todos()
            
            if not ids_favoritos:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("⚠️ No hay favoritos para exportar"),
                    bgcolor=ft.Colors.AMBER_300,
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            df_general_fav = self.df_general[
                self.df_general["ID_INTERNO"].astype(str).isin(ids_favoritos)
            ].copy()
            
            with pd.ExcelWriter('Licitaciones_Favoritas.xlsx', engine='openpyxl') as writer:
                df_general_fav.to_excel(writer, sheet_name='General', index=False)
                
                df_req_fav = self.df_requisitos[
                    self.df_requisitos["ID_INTERNO"].astype(str).isin(ids_favoritos)
                ]
                if not df_req_fav.empty:
                    df_req_fav.to_excel(writer, sheet_name='Requisitos', index=False)
                
                df_crit_fav = self.df_criterios[
                    self.df_criterios["ID_INTERNO"].astype(str).isin(ids_favoritos)
                ]
                if not df_crit_fav.empty:
                    df_crit_fav.to_excel(writer, sheet_name='Criterios', index=False)
                
                df_docs_fav = self.df_docs[
                    self.df_docs["ID_INTERNO"].astype(str).isin(ids_favoritos)
                ]
                if not df_docs_fav.empty:
                    df_docs_fav.to_excel(writer, sheet_name='Documentos', index=False)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    f"✅ Archivo exportado: Licitaciones_Favoritas.xlsx\n"
                    f"📊 {len(df_general_fav)} licitaciones exportadas"
                ),
                bgcolor=ft.Colors.GREEN_100,
                duration=5000,
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error al exportar: {str(ex)}"),
                bgcolor=ft.Colors.RED_100,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _go_to_details(self, e):
        """Abre la página de detalles pasando la fila seleccionada"""
        if self.selected_row is not None:
            _selected_row_aux = self.selected_row.to_dict() if hasattr(self.selected_row, 'to_dict') else self.selected_row
            self.on_detalles(_selected_row_aux)
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("⚠️ Selecciona una fila antes de continuar."),
                bgcolor=ft.Colors.AMBER_300,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _aplicar_filtros_editados(self, e):
        """Aplica los filtros editados en la barra lateral"""
        # Recoger valores de los controles
        nuevos_filtros = {}
        
        ## Filtros de Importe
        if self.filtro_controls['presupuesto_min'].value!='':
            nuevos_filtros['importe_min'] = float(self.filtro_controls['presupuesto_min'].value) 
        else:
            nuevos_filtros['importe_min']=0
        if self.filtro_controls['presupuesto_max'].value!='':
            nuevos_filtros['importe_max'] = float(self.filtro_controls['presupuesto_max'].value)
        else:
            nuevos_filtros["importe_max"] = 0

       
        nuevos_filtros['fecha_desde'] = self.fecha_desde_input.value
        nuevos_filtros['fecha_hasta'] = self.fecha_hasta_input.value

        nuevos_filtros['fecha_desde_publicado'] = self.fecha_desde_publicado_input.value
        nuevos_filtros['fecha_hasta_publicado'] = self.fecha_hasta_publicado_input.value

        # print(self.cpv_container)
        # nuevos_filtros['cpv'] = self.cpv_manager.get_cpvs()

        
        # Actualizar filtros aplicados
        self.filtros_aplicados = nuevos_filtros
        
        # NUEVO: Resetear a primera página al aplicar filtros
        self.pagina_actual = 1
        
        # Si hay un callback para aplicar filtros (para refiltrar desde la fuente original)
        if self.on_aplicar_filtros:
            try:
                # Llamar al callback que debería devolver nuevos dataframes filtrados
                nuevos_dfs = self.on_aplicar_filtros(nuevos_filtros)
                if nuevos_dfs:
                    self.df_general = nuevos_dfs.get('df_general', self.df_general)
                    self.df_requisitos = nuevos_dfs.get('df_requisitos', self.df_requisitos)
                    self.df_criterios = nuevos_dfs.get('df_criterios', self.df_criterios)
                    self.df_docs = nuevos_dfs.get('df_docs', self.df_docs)
            except Exception as ex:
                print(f"Error al aplicar filtros: {ex}")
        else:
            # Aplicar filtros localmente al dataframe completo
            self._aplicar_filtros_locales(nuevos_filtros)
        
        # Refrescar la vista
        self._refrescar_tabla()
        
        # Notificar al usuario
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"✅ Filtros aplicados ({len(nuevos_filtros)} activos)"),
            bgcolor=ft.Colors.GREEN_100,
        )
        self.page.snack_bar.open = True
        self.page.update()
        
    ## NUEVO METODO PARA DESCARTAR LICITACIONES
    def _descartar_licitacion(self, e):
        if self.selected_row is None:
            return
        
        id_licitacion = self.selected_row["ID_INTERNO"]
        
        # 1. Guardar en el JSON de forma persistente
        self.gestor_favoritos.toggle_descarte(id_licitacion)
        
        # Aquí puedes guardar el ID en una lista de 'descartados' persistente
        # Por ahora, simplemente lo marcamos visualmente
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"🚫 Licitación {id_licitacion} descartada"),
            bgcolor=ft.Colors.RED_400
        )
        self.page.snack_bar.open = True
        
        # Opcional: Refrescar la tabla para ocultarla si tienes un filtro
        # o simplemente cambiarle el color permanentemente a gris oscuro
        if self.selected_container:
            self.selected_container.disabled = True
            self.selected_container.opacity = 0.5
            
        self.page.update()
    
    def _aplicar_filtros_locales(self, filtros):
        """Aplica filtros localmente al dataframe"""
        df_filtrado = self.df_general_completo.copy()
        
        # Filtrar por nombre de proyecto
        if 'nombre_proyecto' in filtros and filtros['nombre_proyecto']:
            df_filtrado = df_filtrado[
                df_filtrado['NOMBRE_PROYECTO'].str.contains(
                    filtros['nombre_proyecto'], 
                    case=False, 
                    na=False
                )
            ]
        
        # Filtrar por presupuesto mínimo
        if 'presupuesto_min' in filtros and filtros['presupuesto_min']:
            try:
                min_val = float(filtros['presupuesto_min'])
                if 'PRESUPUESTO' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['PRESUPUESTO'] >= min_val]
            except ValueError:
                pass
        
        # Filtrar por presupuesto máximo
        if 'presupuesto_max' in filtros and filtros['presupuesto_max']:
            try:
                max_val = float(filtros['presupuesto_max'])
                if 'PRESUPUESTO' in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado['PRESUPUESTO'] <= max_val]
            except ValueError:
                pass
        
        # Filtrar por fecha desde
        if 'fecha_desde' in filtros and filtros['fecha_desde']:
            try:
                if 'FECHA_LIMITE' in df_filtrado.columns:
                    df_filtrado['FECHA_LIMITE'] = pd.to_datetime(df_filtrado['FECHA_LIMITE'], errors='coerce')
                    fecha_desde = pd.to_datetime(filtros['fecha_desde'])
                    df_filtrado = df_filtrado[df_filtrado['FECHA_LIMITE'] >= fecha_desde]
            except:
                pass
        
        # Filtrar por fecha hasta
        if 'fecha_hasta' in filtros and filtros['fecha_hasta']:
            try:
                if 'FECHA_LIMITE' in df_filtrado.columns:
                    df_filtrado['FECHA_LIMITE'] = pd.to_datetime(df_filtrado['FECHA_LIMITE'], errors='coerce')
                    fecha_hasta = pd.to_datetime(filtros['fecha_hasta'])
                    df_filtrado = df_filtrado[df_filtrado['FECHA_LIMITE'] <= fecha_hasta]
            except:
                pass
        
        # Filtrar por categoría
        if 'categoria' in filtros and filtros['categoria']:
            if 'CATEGORIA' in df_filtrado.columns:
                df_filtrado = df_filtrado[
                    df_filtrado['CATEGORIA'].str.contains(
                        filtros['categoria'], 
                        case=False, 
                        na=False
                    )
                ]
        
        self.df_general = df_filtrado
    
    def _limpiar_filtros(self, e):
        """Limpia todos los filtros y restaura los datos originales"""
        # Limpiar controles
        for control in self.filtro_controls.values():
            control.value = ""
        
        # Limpiar filtros aplicados
        self.filtros_aplicados = {}

        #Limpiar los CPVs
        # self.cpv_manager.set_cpvs([])
        
        # NUEVO: Resetear a primera página al limpiar filtros
        self.pagina_actual = 1
        
        # Restaurar dataframe original
        self.df_general = self.df_general_completo.copy()
        self.page.update()
        
        # Refrescar vista
        self._refrescar_tabla()
        
        # Notificar
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("🧹 Filtros limpiados - Mostrando todos los resultados"),
            bgcolor=ft.Colors.BLUE_100,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _exportar_excel(self, e):
        """Genera un archivo Excel (.xlsx) con los resultados filtrados y el link de la licitación"""
        try:
            # 1. Obtener los datos que están actualmente pasando los filtros
            # Usamos una copia para no afectar la visualización de la app
            df_export = self.df_general.copy()

            # 2. Asegurar que la columna de URL exista (basado en tu lógica de _abrir_detalle)
            # Si por alguna razón la fila no tiene URL, ponemos el link por defecto de Hacienda
            if 'URL' not in df_export.columns:
                df_export['URL'] = "https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx"
            else:
                df_export['URL'] = df_export['URL'].fillna("https://www.hacienda.gob.es/es-ES/Paginas/Home.aspx")

            # 3. Formatear el archivo Excel
            nombre_archivo = "Resultados_Licitaciones.xlsx"
            
            with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
                # Hoja de Resultados
                df_export.to_excel(writer, sheet_name='Tabla de Resultados', index=False)
                
                # Crear una hoja pequeña para los filtros aplicados (solicitado en el encabezado)
                df_filtros = pd.DataFrame([
                    {"Filtro": k, "Valor": v} for k, v in self.filtros_aplicados.items()
                ])
                if not df_filtros.empty:
                    df_filtros.to_excel(writer, sheet_name='Filtros Utilizados', index=False)

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Excel generado: {nombre_archivo}"),
                bgcolor=ft.Colors.GREEN_400,
            )
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error al exportar Excel: {str(ex)}"),
                bgcolor=ft.Colors.RED_400,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _exportar_xml(self, e):
        """Genera un archivo XML con los resultados actuales y filtros"""
        try:
            root = ET.Element("ExportacionLicitaciones")
            
            # Nodo de Filtros
            filtros_node = ET.SubElement(root, "FiltrosAplicados")
            for key, val in self.filtros_aplicados.items():
                f_node = ET.SubElement(filtros_node, "Filtro")
                f_node.set("campo", str(key))
                f_node.text = str(val)

            # Nodo de Resultados
            resultados_node = ET.SubElement(root, "Resultados")
            # Usamos el DF que se muestra actualmente en la tabla
            for _, row in self.df_general.iterrows():
                item = ET.SubElement(resultados_node, "Licitacion")
                for col in self.df_general.columns:
                    child = ET.SubElement(item, col.replace(" ", "_"))
                    child.text = str(row[col])

            # Guardar archivo
            xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
            with open("resultados_exportados.xml", "w", encoding="utf-8") as f:
                f.write(xml_str)

            self._mostrar_snackbar("✅ XML generado: resultados_exportados.xml")
        except Exception as ex:
            self._mostrar_snackbar(f"❌ Error XML: {str(ex)}", True)


    async def _ver_reporte_pdf_tabla(self, e):
        try:
            user_name = getattr(self, "usuario_actual", "usuario")
            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
            nombre_archivo = f"reporte_{user_name.replace(' ', '_')}.pdf"
            ruta_fisica = os.path.join("assets", "exports", nombre_archivo)

            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            # Usamos Landscape (horizontal) para tener más espacio para las columnas
            doc = SimpleDocTemplate(ruta_fisica, pagesize=landscape(A4), 
                                    leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
            styles = getSampleStyleSheet()
            
            # Estilo para el texto dentro de las celdas que requiere ajuste de línea
            style_cell = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=8, leading=10)
            style_header = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontSize=9, 
                                        textColor=colors.whitesmoke, fontName='Helvetica-Bold')

            elementos = []

            # Título del reporte
            elementos.append(Paragraph(f"<b>Resumen resultados - {fecha_hoy} - Usuario: {user_name}</b>", styles['Title']))
            
            # Filtros (Solo los activos)
            filtros_txt = ", ".join([f"{k}: {v}" for k, v in self.filtros_aplicados.items() if v and v != []])
            elementos.append(Paragraph(f"<b>Filtros aplicados:</b> {filtros_txt if filtros_txt else 'Ninguno'}", styles['Normal']))
            elementos.append(Spacer(1, 15))

            # --- CONFIGURACIÓN DE LA TABLA ---
            # MODIFICADO: Añadir columnas de adjudicatario e importe adjudicación
            headers = ["ID", "NOMBRE DE LA LICITACIÓN", "ENTIDAD", "IMPORTE", "ESTADO", "LIMITE", "ADJUDICATARIO", "IMP. ADJ.", "LINK"]
            data = [headers]

            for i, row in self.df_general.iterrows():
                # Procesar Prioridad
                prioridad = str(row.get('PRIORIDAD_IA', 'No estudiado'))
                prioridad_txt = "No estudiado (en desarrollo)" if prioridad == "No estudiado" else prioridad
                
                # Procesar Fecha
                f_limite = row.get('FECHA_LIMITE')
                fecha_txt = str(f_limite) if pd.notnull(f_limite) and f_limite != "" else "No aplica"

                # Procesar datos de adjudicación
                adjudicatario = str(row.get('ADJUDICATARIO', 'No aplica'))
                imp_adj = row.get('IMPORTE_ADJUDICACION', 'No aplica')
                if imp_adj != 'No aplica':
                    try:
                        imp_adj = f"{float(imp_adj):,.2f} €"
                    except:
                        imp_adj = str(imp_adj)

                # Creamos la fila
                fila = [
                    Paragraph(str(row.get("ID", "")), style_cell),
                    Paragraph(str(row.get("NOMBRE_PROYECTO", "")).upper(), style_cell),
                    Paragraph(str(row.get("ENTIDAD", "")), style_cell),
                    str(row.get("IMPORTE", "")),
                    str(row.get("ESTADO", "Ver portal")),
                    fecha_txt,
                    Paragraph(adjudicatario, style_cell),
                    str(imp_adj),
                ]
                
                url = row.get('URL', None)
                if url:
                    fila.append(Paragraph(f'<a href="{url}" color="blue"><u>Ver licitación</u></a>', style_cell))
                else:
                    fila.append("No disponible")
                    
                data.append(fila)

            # MODIFICADO: Ajustar anchos de columna para incluir las nuevas columnas
            col_widths = [35, 200, 100, 60, 60, 60, 100, 70, 65] 

            tabla = Table(data, colWidths=col_widths, repeatRows=1)
            
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blueviolet),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))

            elementos.append(tabla)
            doc.build(elementos)

            # Lanzar URL con tu función personalizada
            url_publica = f"/exports/{nombre_archivo}"
            self.page.run_task(self._handle_abrir_url, url_publica)

        except Exception as ex:
            print(f"Error PDF: {ex}")

    async def _ver_reporte_pdf(self, e):
        print("Iniciando generación de PDF...")
        try:
            user_name = getattr(self, "usuario_actual", "usuario").replace(" ", "_")
            nombre_archivo = f"reporte_{user_name}.pdf"
            
            # Asegúrate de que la ruta sea relativa a donde ejecutas el script
            ruta_fisica = os.path.join("assets", "exports", nombre_archivo)
            
            # --- (Aquí va tu código de generación de PDF con Reportlab igual que antes) ---
            # ... (Generación del PDF) ...
            # ------------------------------------------------------------------------------

            print(f"PDF creado en: {ruta_fisica}")

            # 3. LANZAR URL CORREGIDO
            url_publica = f"/exports/{nombre_archivo}"
            print(f"Lanzando URL: {url_publica}")
            
            # CORRECCIÓN AQUÍ: Usar await y la nueva sintaxis
            await self.page.launch_url(url_publica)
            
        except Exception as ex:
            print(f"ERROR: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="red")
            self.page.snack_bar.open = True
        
        await self.page.update_async() # También usa update_async si tu app es async

    async def _ver_reporte_pdf(self, e):
        try:
            user_name = getattr(self, "usuario_actual", "usuario")
            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
            nombre_archivo = f"reporte_{user_name.replace(' ', '_')}.pdf"
            ruta_fisica = os.path.join("assets", "exports", nombre_archivo)

            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER

            doc = SimpleDocTemplate(ruta_fisica, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Estilos personalizados
            estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=20)
            estilo_subtitulo = ParagraphStyle('Subtitulo', parent=styles['Heading3'], textColor="#2E5077", spaceBefore=15)
            estilo_cuerpo = styles['Normal']
            
            elementos = []

            # 1. TÍTULO
            elementos.append(Paragraph(f"Resumen resultados, {fecha_hoy}, {user_name}", estilo_titulo))
            elementos.append(Spacer(1, 10))

            # 2. FILTROS (Solo los que tienen valor)
            elementos.append(Paragraph("<b>Los resultados mostrados a continuación respetan los siguientes filtros:</b>", estilo_cuerpo))
            filtros_activos = [f"• {k}: {v}" for k, v in self.filtros_aplicados.items() if v and v != []]
            
            if filtros_activos:
                for f in filtros_activos:
                    elementos.append(Paragraph(f, estilo_cuerpo))
            else:
                elementos.append(Paragraph("• Ningún filtro aplicado.", estilo_cuerpo))
            
            elementos.append(Spacer(1, 20))
            elementos.append(HRFlowable(width="100%", thickness=1, color="black"))

            # 3. CONTENIDO (Fichas por licitación)
            for i, row in self.df_general.iterrows():
                # Procesar datos con lógica de seguridad
                nombre = str(row.get('NOMBRE_PROYECTO', 'Sin nombre')).upper()
                entidad = str(row.get('ENTIDAD', 'No especificada'))
                importe = str(row.get('IMPORTE', 'N/A'))
                
                # Estado (Si no está en el DF de resultados, puedes buscarlo en el DF completo o poner 'Ver detalle')
                estado = str(row.get('ESTADO', 'Ver en portal')) 
                
                # Fecha Límite
                fecha_limite = row.get('FECHA_LIMITE')
                fecha_txt = str(fecha_limite) if pd.notnull(fecha_limite) and fecha_limite != "" else "No aplica"
                
                # Prioridad IA
                prioridad = str(row.get('PRIORIDAD_IA', 'No estudiado'))
                if prioridad == "No estudiado":
                    prioridad_txt = "No estudiado, en desarrollo aun agradecemos su comprensión."
                else:
                    prioridad_txt = prioridad

                # NUEVO: Datos de adjudicación
                adjudicatario = str(row.get('ADJUDICATARIO', 'No aplica'))
                imp_adj = row.get('IMPORTE_ADJUDICACION', 'No aplica')
                if imp_adj != 'No aplica':
                    try:
                        imp_adj_txt = f"{float(imp_adj):,.2f} €"
                    except:
                        imp_adj_txt = str(imp_adj)
                else:
                    imp_adj_txt = "No aplica"

                # Construir la ficha en el PDF
                elementos.append(Paragraph(f"Resultado #{i+1}: <i>{nombre}</i>", estilo_subtitulo))
                elementos.append(Paragraph(f"<b>Entidad adjudicadora:</b> {entidad}", estilo_cuerpo))
                elementos.append(Paragraph(f"<b>Importe:</b> {importe}", estilo_cuerpo))
                elementos.append(Paragraph(f"<b>Estado:</b> {estado}", estilo_cuerpo))
                elementos.append(Paragraph(f"<b>Fecha límite de presentación:</b> {fecha_txt}", estilo_cuerpo))
                elementos.append(Paragraph(f"<b>Prioridad:</b> {prioridad_txt}", estilo_cuerpo))
                
                # NUEVO: Información de adjudicación
                elementos.append(Paragraph(f"<b>Adjudicatario:</b> {adjudicatario}", estilo_cuerpo))
                elementos.append(Paragraph(f"<b>Importe de adjudicación:</b> {imp_adj_txt}", estilo_cuerpo))
                
                # Añadir un link directo si existe
                url = row.get('URL', None)
                if url:
                    elementos.append(Paragraph(f'<a href="{url}" color="blue"><u>Ver licitación en el portal</u></a>', estilo_cuerpo))
                
                elementos.append(Spacer(1, 10))
                elementos.append(HRFlowable(width="30%", thickness=0.5, color="grey", hAlign="LEFT"))

            # Generar PDF
            doc.build(elementos)

            # Lanzar URL usando tu nueva lógica
            url_publica = f"/exports/{nombre_archivo}"
            self.page.run_task(self._handle_abrir_url, url_publica)

        except Exception as ex:
            print(f"Error al generar reporte: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

    def _mostrar_snackbar(self, mensaje, error=False):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
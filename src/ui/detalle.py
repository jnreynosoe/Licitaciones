# import flet as ft
# import pandas as pd
# import os
# import sys
# import threading

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from models.resumidor_IA import analizar_pliego
# from chatbot_licitacion import abrir_chatbot_licitacion  # Importar la función del chatbot

# class PaginaDetalle(ft.Container):
#     def __init__(self, row, docs, page=ft.Page):
#     # def __init__(self, page: ft.Page, df_general: pd.DataFrame, df_requisitos: pd.DataFrame, df_criterios: pd.DataFrame, on_detalles):#, df_docs: pd.DataFrame):
#         super().__init__()
#         self.page = page
#         self.row = row
#         self.docs = docs
#         # print("DOCUMENTACION", docs)
#         # self.resumen_ia = 
#         self.item = self.row#.iloc[0].to_dict()
#         # self.df_general = df_general
#         # self.df_requisitos = df_requisitos
#         # self.df_criterios = df_criterios
#         # self.on_detalles = on_detalles
#         # self.df_docs = df_docs

#         self.selected_id = None

#         self._build_ui()

#     # --------------------------------------------------------
#     # Construcción de la interfaz
#     # --------------------------------------------------------
#     def _build_ui(self):
#         # # -------- TABLA PRINCIPAL (GENERAL) --------
#         # tabla_general = ft.DataTable(
#         #     columns=[
#         #         ft.DataColumn(ft.Text("ID")),
#         #         ft.DataColumn(ft.Text("NOMBRE_PROYECTO")),
#         #         ft.DataColumn(ft.Text("FECHA_LIMITE")),
#         #     ],
#         #     rows=[
#         #         ft.DataRow(
#         #             cells=[
#         #                 ft.DataCell(ft.Text(str(row["ID"]))),
#         #                 ft.DataCell(ft.Text(str(row["NOMBRE_PROYECTO"]))),
#         #                 ft.DataCell(ft.Text(str(row["FECHA_LIMITE"]))),
#         #             ],
#         #             data=row,
#         #             on_select_changed=self._on_row_click,
#         #         )
#         #         for _, row in self.df_general.iterrows()
#         #     ],
#         # )

#         # -------- FORMULARIO EN GRILLA --------
#         grid = ft.ResponsiveRow(
#             controls=[
#                 ft.TextField(label="ID", value=str(self.item["ID"]), col={"sm": 2}),
#                 ft.TextField(label="NOMBRE_PROYECTO", value=self.item.get("NOMBRE_PROYECTO", ""), col={"sm": 5}),
#                 ft.TextField(label="carpeta_origen", value=self.item.get("carpeta_origen", ""), col={"sm": 3}),
#                 ft.TextField(label="FECHA_ACTUALIZACION", value=str(self.item.get("FECHA_ACTUALIZACION", "")), col={"sm": 3}),
#                 ft.TextField(label="FECHA_LIMITE", value=str(self.item.get("FECHA_LIMITE", "")), col={"sm": 3}),
#             ]
#         )

#         # -------- TABLA DE DOCUMENTACIÓN --------
#         tabla_docs = ft.DataTable(
#             columns=[
#                 ft.DataColumn(ft.Text("pliego_id")),
#                 ft.DataColumn(ft.Text("tipo")),
#                 ft.DataColumn(ft.Text("descripcion")),
#                 ft.DataColumn(ft.Text("URI")),
#             ],
#             rows=[
#                 ft.DataRow(
#                     cells=[
#                         ft.DataCell(ft.Text(str(d["pliego_id"]))),
#                         ft.DataCell(ft.Text(str(d["tipo"]))),
#                         ft.DataCell(ft.Text(str(d["descripcion"]))),
#                         # ft.DataCell(ft.Text(str(d["ubicacion"]))),
#                         ft.DataCell(ft.Text(str(d["URI"]))),
#                     ]
#                 )
#                 for _, d in self.docs.iterrows()  # 👈 aquí está la clave
#             ],
#         )

#         # -------- VISUALIZADOR DE PDF --------
#         # resumen_ia_view = ResumenIA(self.resumen_ia)
#         visor_pdf = VisorPDF(self.docs[self.docs["pliego_id"] == self.item["ID"]])

#         tabla_docs_contenedor = ft.Container(
#             content=ft.Column([tabla_docs], scroll=ft.ScrollMode.ALWAYS, expand=True),
#             height=self.page.height * 0.3,
#             border=ft.border.all(1, ft.Colors.GREY_400),
#             padding=10,
#         )

#         self.content = ft.Column(
#             [
#                 ft.Text("📄 Detalles de la licitación", size=22, weight="bold"),
#                 grid,
#                 ft.Divider(),
#                 ft.Text("📚 Documentos relacionados", size=18, weight="bold"),
#                 tabla_docs_contenedor,
#                 ft.Divider(),
#                 visor_pdf,
#                 ft.Button("⬅️ Volver", on_click=lambda e: self.page.go("/")),
#             ],
#             spacing=15,
#             scroll=ft.ScrollMode.AUTO,
#         )

# import flet as ft
# import os

# class VisorPDF(ft.Container):
#     """
#     Componente para visualizar PDFs desde URLs o rutas locales.
#     """
#     def __init__(self, df_docs: pd.DataFrame):
#         super().__init__()
#         self.df_docs = df_docs
#         self.selected_doc = None
#         self.viewer = ft.Container()  # Contendrá el visor actual
#         self.resumen_container = ft.Container(
#             content=ft.Text("Selecciona un documento para generar el resumen IA."),
#             expand=True,
#             border=ft.border.all(1, ft.Colors.GREY_300),
#             padding=10,
#         )

#         self._build_ui()

#     def _build_ui(self):
#         # Dropdown con los documentos disponibles
#         self.dropdown = ft.Dropdown(
#             label="Selecciona un documento para previsualizar",
#             options=[ft.dropdown.Option(d["descripcion"]) for _, d in self.df_docs.iterrows()],
#             width=500,
#             on_change=self._on_select_doc,
#         )

#         # Layout del visor
#         self.viewer = ft.Container(
#             content=ft.Text("Selecciona un documento para previsualizar."),
#             expand=True,
#             border=ft.border.all(1, ft.Colors.GREY_400),
#             border_radius=8,
#             padding=10,
#         )

#         # Estructura final
#         # self.content = ft.Column(
#         #     [
#         #         self.dropdown,
#         #         self.viewer
#         #     ],
#         #     spacing=10,
#         #     expand=True,
#         # )
#         self.content = ft.Row(
#             [
#                 ft.Container(
#                     ft.Column([self.dropdown, self.viewer]),
#                     expand=True,
#                     col={"md": 6}
#                 ),
#                 ft.Container(
#                     self.resumen_container,
#                     expand=True,
#                     col={"md": 6}
#                 ),
#             ],
#             expand=True,
#             alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#         )

#     # def _on_select_doc(self, e):
#     #     """Actualiza el visor según el documento seleccionado."""
#     #     descripcion = e.control.value
#     #     fila = self.df_docs[self.df_docs["descripcion"] == descripcion].iloc[0]
#     #     print(fila)

#     #     # Determinar la fuente (URI o ruta local)
#     #     pdf_src = fila.get("URI") or fila.get("ubicacion")

#     #     if pdf_src.startswith("http"):
#     #         # Es un enlace web
#     #         self._mostrar_pdf_url(pdf_src)
#     #     else:
#     #         # Es una ruta local → verificamos que exista
#     #         if os.path.exists(pdf_src):
#     #             self._mostrar_pdf_local(pdf_src)
#     #         else:
#     #             self.viewer.content = ft.Text(
#     #                 f"⚠️ No se encontró el archivo en la ruta:\n{pdf_src}",
#     #                 color=ft.Colors.RED
#     #             )
#     #             self.update()
#     def _on_select_doc(self, e):
#         descripcion = e.control.value
#         fila = self.df_docs[self.df_docs["descripcion"] == descripcion].iloc[0]
#         pdf_src = fila.get("URI") or fila.get("ubicacion")

#         if pdf_src.startswith("http"):
#             self._mostrar_pdf_url(pdf_src)
#             threading.Thread(target=self._analizar_pdf, args=(pdf_src,)).start()
#         else:
#             if os.path.exists(pdf_src):
#                 self._mostrar_pdf_local(pdf_src)
#                 threading.Thread(target=self._analizar_pdf, args=(pdf_src,)).start()
#             else:
#                 self.viewer.content = ft.Text(f"⚠️ No se encontró el archivo:\n{pdf_src}", color=ft.Colors.RED)
#                 self.update()

#     def _analizar_pdf(self, pdf_src):
#         """Ejecuta el análisis IA en segundo plano."""
#         self.resumen_container.content = ft.Text("🧠 Analizando el documento, por favor espera...")
#         self.update()

#         try:
#             resumen_data = analizar_pliego(pdf_src)
#             resumen_vista = ResumenIA(resumen_data)
#             self.resumen_container.content = resumen_vista
#         except Exception as e:
#             self.resumen_container.content = ft.Text(f"❌ Error analizando el PDF:\n{e}", color=ft.Colors.RED)

#         self.update()

#     def _mostrar_pdf_url(self, url):
#         """Muestra PDF desde una URL."""
#         self.viewer.content = ft.WebView(
#             url=url,
#             width=800,
#             height=600
#         )
#         self.update()


#     def _mostrar_pdf_local(self, path):
#         """Muestra PDF desde una ruta relativa o absoluta del proyecto."""
#         # Convertir ruta relativa a absoluta
#         base_dir = os.getcwd()  # o define tu carpeta base explícitamente
#         abs_path = os.path.abspath(os.path.join(base_dir, path))
        
#         if not os.path.exists(abs_path):
#             self.viewer.content = ft.Text(
#                 f"⚠️ No se encontró el archivo:\n{abs_path}",
#                 color=ft.Colors.RED
#             )
#             self.update()
#             return

#         # Convertir a formato URL válido para el navegador
#         file_url = f"file:///{abs_path.replace(os.sep, '/')}"
        
#         self.viewer.content = ft.Iframe(
#             src=file_url,
#             width=800,
#             height=600,
#             border_radius=8,
#         )
#         self.update()


# ##Componente grafico para el resumidor IA
# class ResumenIA(ft.Container):
#     def __init__(self, resumen_ia: dict):
#         super().__init__()
#         self.resumen_ia = resumen_ia
#         self.content = self._build_ui()

#     def _build_ui(self):
#         contrato = self.resumen_ia.get("contrato", {})
#         criterios = self.resumen_ia.get("criterios", {})
#         requisitos = self.resumen_ia.get("requisitos", {})

#         return ft.Column(
#             [
#                 ft.Text("🧠 Resumen IA del Pliego", size=18, weight="bold"),
#                 ft.Divider(),
#                 ft.Text(f"📄 Objeto: {contrato.get('objeto', '')}"),
#                 ft.Text(f"Duración: {contrato.get('duracion', '')}"),
#                 ft.Text(f"Presupuesto: {contrato.get('presupuesto_estimado', '')}"),
#                 ft.Divider(),
#                 ft.Text("⚙️ Criterios", size=16, weight="bold"),
#                 ft.Text(criterios.get("criterios_adjudicacion", "")),
#                 ft.Text(criterios.get("criterios_valoracion", "")),
#                 ft.Divider(),
#                 ft.Text("🧾 Requisitos", size=16, weight="bold"),
#                 ft.Text(requisitos.get("requisitos_licitador", "")),
#                 ft.Text("📜 Certificaciones:", weight="bold"),
#                 ft.Column(
#                     [ft.Text(f"- {c}") for c in requisitos.get("certificaciones_detectadas", [])],
#                     spacing=5,
#                 ),
#             ],
#             spacing=5,
#             scroll="auto",
#         )

# import flet as ft
# import pandas as pd
# import os
# import sys
# import threading

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from models.resumidor_IA import analizar_pliego
# try:
#     from chatbot_licitacion import abrir_chatbot_licitacion  # Importar la función del chatbot
# except:
#     from .chatbot_licitacion import abrir_chatbot_licitacion  # Importar la función del chatbot

# class PaginaDetalle(ft.Container):
#     def __init__(self, row, docs, page=ft.Page):
#         super().__init__()
#         self.page = page
#         self.row = row
#         self.docs = docs
#         self.item = self.row
#         self.selected_id = None

#         self._build_ui()

#     def _build_ui(self):
#         # -------- FORMULARIO EN GRILLA --------
#         grid = ft.ResponsiveRow(
#             controls=[
#                 ft.TextField(label="ID", value=str(self.item["ID"]), col={"sm": 2}),
#                 ft.TextField(label="NOMBRE_PROYECTO", value=self.item.get("NOMBRE_PROYECTO", ""), col={"sm": 5}),
#                 ft.TextField(label="carpeta_origen", value=self.item.get("carpeta_origen", ""), col={"sm": 3}),
#                 ft.TextField(label="FECHA_ACTUALIZACION", value=str(self.item.get("FECHA_ACTUALIZACION", "")), col={"sm": 3}),
#                 ft.TextField(label="FECHA_LIMITE", value=str(self.item.get("FECHA_LIMITE", "")), col={"sm": 3}),
#             ]
#         )

#         # -------- BOTÓN DE CHATBOT --------
#         btn_chatbot = ft.Button(
#             "💬 Consultar con IA",
#             icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
#             on_click=self._abrir_chatbot,
#             style=ft.ButtonStyle(
#                 bgcolor=ft.Colors.PURPLE_500,
#                 color=ft.Colors.WHITE,
#                 padding=15,
#             ),
#             tooltip="Abre un asistente IA para hacer preguntas sobre esta licitación"
#         )

#         # -------- TABLA DE DOCUMENTACIÓN --------
#         tabla_docs = ft.DataTable(
#             columns=[
#                 ft.DataColumn(ft.Text("pliego_id")),
#                 ft.DataColumn(ft.Text("tipo")),
#                 ft.DataColumn(ft.Text("descripcion")),
#                 ft.DataColumn(ft.Text("URI")),
#             ],
#             rows=[
#                 ft.DataRow(
#                     cells=[
#                         ft.DataCell(ft.Text(str(d["pliego_id"]))),
#                         ft.DataCell(ft.Text(str(d["TIPO"]))),
#                         ft.DataCell(ft.Text(str(d["DESCRIPCION"]))),
#                         ft.DataCell(ft.Text(str(d["URI"]))),
#                     ]
#                 )
#                 for _, d in self.docs.iterrows()
#             ],
#         )

#         # -------- VISUALIZADOR DE PDF --------
#         visor_pdf = VisorPDF(self.docs[self.docs["pliego_id"] == self.item["ID"]])

#         tabla_docs_contenedor = ft.Container(
#             content=ft.Column([tabla_docs], scroll=ft.ScrollMode.ALWAYS, expand=True),
#             height=self.page.height * 0.3,
#             border=ft.border.all(1, ft.Colors.GREY_400),
#             padding=10,
#         )

#         # -------- ESTRUCTURA PRINCIPAL CON BOTÓN CHATBOT --------
#         self.content = ft.Column(
#             [
#                 ft.Row(
#                     [
#                         ft.Text("📄 Detalles de la licitación", size=22, weight="bold", expand=True),
#                         btn_chatbot,  # Botón del chatbot en la parte superior
#                     ],
#                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#                 ),
#                 grid,
#                 ft.Divider(),
#                 ft.Text("📚 Documentos relacionados", size=18, weight="bold"),
#                 tabla_docs_contenedor,
#                 ft.Divider(),
#                 visor_pdf,
#                 # ft.Button("⬅️ Volver", on_click=lambda e: self.page.go("/")),
#             ],
#             spacing=15,
#             scroll=ft.ScrollMode.AUTO,
#         )
    
#     def _abrir_chatbot(self, e):
#         """Abre el chatbot con los documentos de esta licitación"""
#         abrir_chatbot_licitacion(
#             page=self.page,
#             df_docs=self.docs,
#             nombre_licitacion=self.item.get("NOMBRE_PROYECTO", "Licitación")
#         )


# # ===============================================================
# # COMPONENTE: Visor de PDFs (sin cambios)
# # ===============================================================
# class VisorPDF(ft.Container):
#     """
#     Componente para visualizar PDFs desde URLs o rutas locales.
#     """
#     def __init__(self, df_docs: pd.DataFrame):
#         super().__init__()
#         self.df_docs = df_docs
#         self.selected_doc = None
#         self.viewer = ft.Container()
#         self.resumen_container = ft.Container(
#             content=ft.Text("Selecciona un documento para generar el resumen IA."),
#             expand=True,
#             border=ft.border.all(1, ft.Colors.GREY_300),
#             padding=10,
#         )

#         self._build_ui()

#     def _build_ui(self):
#         self.dropdown = ft.Dropdown(
#             label="Selecciona un documento para previsualizar",
#             options=[ft.dropdown.Option(d["DESCRIPCION"]) for _, d in self.df_docs.iterrows()],
#             width=500,
#             on_change=self._on_select_doc,
#         )

#         self.viewer = ft.Container(
#             content=ft.Text("Selecciona un documento para previsualizar."),
#             expand=True,
#             border=ft.border.all(1, ft.Colors.GREY_400),
#             border_radius=8,
#             padding=10,
#         )

#         self.content = ft.Row(
#             [
#                 ft.Container(
#                     ft.Column([self.dropdown, self.viewer]),
#                     expand=True,
#                     col={"md": 6}
#                 ),
#                 ft.Container(
#                     self.resumen_container,
#                     expand=True,
#                     col={"md": 6}
#                 ),
#             ],
#             expand=True,
#             alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#         )

#     def _on_select_doc(self, e):
#         descripcion = e.control.value
#         fila = self.df_docs[self.df_docs["DESCRIPCION"] == descripcion].iloc[0]
#         pdf_src = fila.get("URI") or fila.get("ubicacion")

#         if pdf_src.startswith("http"):
#             self._mostrar_pdf_url(pdf_src)
#             threading.Thread(target=self._analizar_pdf, args=(pdf_src,)).start()
#         else:
#             if os.path.exists(pdf_src):
#                 self._mostrar_pdf_local(pdf_src)
#                 threading.Thread(target=self._analizar_pdf, args=(pdf_src,)).start()
#             else:
#                 self.viewer.content = ft.Text(f"⚠️ No se encontró el archivo:\n{pdf_src}", color=ft.Colors.RED)
#                 self.update()

#     def _analizar_pdf(self, pdf_src):
#         """Ejecuta el análisis IA en segundo plano."""
#         self.resumen_container.content = ft.Text("🧠 Analizando el documento, por favor espera...")
#         self.update()

#         try:
#             resumen_data = analizar_pliego(pdf_src)
#             resumen_vista = ResumenIA(resumen_data)
#             self.resumen_container.content = resumen_vista
#         except Exception as e:
#             self.resumen_container.content = ft.Text(f"❌ Error analizando el PDF:\n{e}", color=ft.Colors.RED)

#         self.update()

#     def _mostrar_pdf_url(self, url):
#         """Muestra PDF desde una URL."""
#         self.viewer.content = ft.WebView(
#             url=url,
#             width=800,
#             height=600
#         )
#         self.update()

#     def _mostrar_pdf_local(self, path):
#         """Muestra PDF desde una ruta relativa o absoluta del proyecto."""
#         base_dir = os.getcwd()
#         abs_path = os.path.abspath(os.path.join(base_dir, path))
        
#         if not os.path.exists(abs_path):
#             self.viewer.content = ft.Text(
#                 f"⚠️ No se encontró el archivo:\n{abs_path}",
#                 color=ft.Colors.RED
#             )
#             self.update()
#             return

#         file_url = f"file:///{abs_path.replace(os.sep, '/')}"
        
#         self.viewer.content = ft.Iframe(
#             src=file_url,
#             width=800,
#             height=600,
#             border_radius=8,
#         )
#         self.update()


# # ===============================================================
# # COMPONENTE: Resumen IA (sin cambios)
# # ===============================================================
# class ResumenIA(ft.Container):
#     def __init__(self, resumen_ia: dict):
#         super().__init__()
#         self.resumen_ia = resumen_ia
#         self.content = self._build_ui()

#     def _build_ui(self):
#         contrato = self.resumen_ia.get("contrato", {})
#         criterios = self.resumen_ia.get("criterios", {})
#         requisitos = self.resumen_ia.get("requisitos", {})

#         return ft.Column(
#             [
#                 ft.Text("🧠 Resumen IA del Pliego", size=18, weight="bold"),
#                 ft.Divider(),
#                 ft.Text(f"📄 Objeto: {contrato.get('objeto', '')}"),
#                 ft.Text(f"Duración: {contrato.get('duracion', '')}"),
#                 ft.Text(f"Presupuesto: {contrato.get('presupuesto_estimado', '')}"),
#                 ft.Divider(),
#                 ft.Text("⚙️ Criterios", size=16, weight="bold"),
#                 ft.Text(criterios.get("criterios_adjudicacion", "")),
#                 ft.Text(criterios.get("criterios_valoracion", "")),
#                 ft.Divider(),
#                 ft.Text("🧾 Requisitos", size=16, weight="bold"),
#                 ft.Text(requisitos.get("requisitos_licitador", "")),
#                 ft.Text("📜 Certificaciones:", weight="bold"),
#                 ft.Column(
#                     [ft.Text(f"- {c}") for c in requisitos.get("certificaciones_detectadas", [])],
#                     spacing=5,
#                 ),
#             ],
#             spacing=5,
#             scroll="auto",
#         )

#-------------------------------------------
import flet as ft
import flet_webview as ftwv
import pandas as pd
import os
import sys
import threading
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.resumidor_IA import analizar_pliego
try:
    from chatbot_licitacion import ChatBotLicitacion
except:
    from .chatbot_licitacion import ChatBotLicitacion

class PaginaDetalle(ft.Container):
    def __init__(self, row, docs, analisis_data=None, page=ft.Page):
        super().__init__()
        # self.page = page
        self.row = row
        self.docs = docs
        self.item = self.row
        self.analisis_data = analisis_data  # Datos del análisis
        self.selected_id = None
        self.chatbot_widget = None
        self.chatbot_visible = False

        self._build_ui()

    def _build_ui(self):
        # -------- FORMULARIO EN GRILLA --------
        grid = ft.ResponsiveRow(
            controls=[
                ft.TextField(label="ID", value=str(self.item["ID"]), col={"sm": 2}, read_only=True),
                ft.TextField(label="NOMBRE_PROYECTO", value=self.item.get("NOMBRE_PROYECTO", ""), col={"sm": 5}, read_only=True),
                ft.TextField(label="Estado", value=self.item.get("ESTADO", ""), col={"sm": 3}, read_only=True),
                ft.TextField(label="FECHA_ACTUALIZACION", value=str(self.item.get("FECHA_ACTUALIZACION", "")), col={"sm": 3}, read_only=True),
                ft.TextField(label="FECHA_LIMITE", value=str(self.item.get("FECHA_LIMITE", "")), col={"sm": 3}, read_only=True),
            ]
        )

        # -------- BOTÓN DE CHATBOT --------
        btn_chatbot = ft.Button(
            "💬 Consultar con IA",
            icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
            on_click=self._toggle_chatbot,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PURPLE_500,
                color=ft.Colors.WHITE,
                padding=15,
            ),
            tooltip="Abre un asistente IA para hacer preguntas sobre esta licitación"
        )

        # -------- SECCIÓN DE ANÁLISIS (NUEVA) --------
        seccion_analisis = self._build_seccion_analisis()

        # -------- TABLA DE DOCUMENTACIÓN --------
        tabla_docs = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("pliego_id")),
                ft.DataColumn(ft.Text("tipo")),
                ft.DataColumn(ft.Text("descripcion")),
                ft.DataColumn(ft.Text("URI")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(d["pliego_id"]))),
                        ft.DataCell(ft.Text(str(d["TIPO"]))),
                        ft.DataCell(ft.Text(str(d["DESCRIPCION"]))),
                        ft.DataCell(ft.Text(str(d["URI"]))),
                    ]
                )
                for _, d in self.docs.iterrows()
            ],
        )

        # -------- VISUALIZADOR DE PDF --------
        visor_pdf = VisorPDF(self.docs[self.docs["pliego_id"] == self.item["ID"]])

        tabla_docs_contenedor = ft.Container(
            content=ft.Column([tabla_docs], scroll=ft.ScrollMode.ALWAYS, expand=True),
            # height=self.page.height * 0.3,
            expand = 30,
            # border=ft.border.all(1, ft.Colors.GREY_400),
            border=ft.Border.all(),
            padding=10,
        )

        # -------- ESTRUCTURA PRINCIPAL CON BOTÓN CHATBOT --------
        self.content = ft.Stack(
            [
                # Contenido principal
                ft.Column(
                    [
                       
                        grid,
                        ft.Divider(),
                        # Nueva sección de análisis
                        seccion_analisis,
                        ft.Divider(),
                        ft.Text("📚 Documentos relacionados", size=18, weight="bold"),
                        tabla_docs_contenedor,
                        ft.Divider(),
                        visor_pdf,
                    ],
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ],
            expand=True,
        )
    
    def _build_seccion_analisis(self):
        """Construye la sección de análisis con matches, penalizaciones, etc."""
        # Validar si hay datos de análisis
        if self.analisis_data is None or (isinstance(self.analisis_data, pd.DataFrame) and self.analisis_data.empty):
            return ft.Container(
                content=ft.Text("ℹ️ No hay datos de análisis disponibles", color=ft.Colors.GREY_600),
                padding=10,
            )

        # Convertir DataFrame a dict si es necesario
        if isinstance(self.analisis_data, pd.DataFrame):
            # Tomar la primera fila si es un DataFrame
            analisis_dict = self.analisis_data.iloc[0].to_dict()
        else:
            analisis_dict = self.analisis_data

        # Parsear datos si vienen como strings
        matches = analisis_dict.get("matches", {})
        if isinstance(matches, str):
            try:
                matches = json.loads(matches)
            except:
                matches = {}

        penalizaciones = analisis_dict.get("penalizaciones", [])
        if isinstance(penalizaciones, str):
            try:
                penalizaciones = json.loads(penalizaciones)
            except:
                penalizaciones = []

        warnings = analisis_dict.get("warnings", [])
        if isinstance(warnings, str):
            try:
                warnings = json.loads(warnings)
            except:
                warnings = []

        score = analisis_dict.get("score", 0)
        prioridad = analisis_dict.get("PRIORIDAD", "Descartar")
        presupuesto = analisis_dict.get("presupuesto", {})

        # Card de Score y Prioridad
        card_score = self._build_score_card(score, prioridad)

        # Card de Matches
        card_matches = self._build_matches_card(matches)

        # Card de Penalizaciones
        card_penalizaciones = self._build_penalizaciones_card(penalizaciones)

        # Card de Warnings
        card_warnings = self._build_warnings_card(warnings)

        # Card de Presupuesto
        card_presupuesto = self._build_presupuesto_card(presupuesto)

        return ft.Column([
            ft.Text("🎯 Análisis de Viabilidad", size=20, weight="bold"),
            ft.ResponsiveRow(
                [
                    card_score,
                    card_presupuesto,
                ],
                spacing=10,
            ),
            ft.ResponsiveRow(
                [
                    card_matches,
                    card_penalizaciones,
                    card_warnings,
                ],
                spacing=10,
            ),
        ], spacing=15)

    def _build_score_card(self, score, prioridad):
        """Construye la tarjeta de score y prioridad"""
        # Color según prioridad
        color_map = {
            "Alta": ft.Colors.GREEN_500,
            "Media": ft.Colors.ORANGE_500,
            "Baja": ft.Colors.YELLOW_700,
            "Descartar": ft.Colors.RED_500,
        }
        color = color_map.get(prioridad, ft.Colors.GREY_500)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.STAR, color=color, size=30),
                    ft.Text("Score y Prioridad", size=16, weight="bold"),
                ]),
                ft.Divider(),
                ft.Text(f"Score: {score}", size=24, weight="bold", color=color),
                ft.Container(
                    content=ft.Text(prioridad, size=16, weight="bold", color=ft.Colors.WHITE),
                    bgcolor=color,
                    padding=8,
                    border_radius=5,
                    # alignment=ft.MainAxisAlignment.CENTER,
                    alignment=ft.Alignment(0.0, 0.0),
                ),
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            # border=ft.border.all(2, color),
            border= ft.Border.all(),
            border_radius=10,
            padding=15,
            col={"sm": 12, "md": 6},
        )

    def _build_presupuesto_card(self, presupuesto):
        """Construye la tarjeta de presupuesto"""
        if isinstance(presupuesto, str):
            try:
                presupuesto = json.loads(presupuesto)
            except:
                presupuesto = {}

        valor = presupuesto.get("valor", "No disponible")
        viable = presupuesto.get("viable", True)
        motivo = presupuesto.get("motivo", "")

        color = ft.Colors.GREEN_500 if viable else ft.Colors.RED_500
        icon = ft.Icons.CHECK_CIRCLE if viable else ft.Icons.CANCEL

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EURO, color=ft.Colors.BLUE_500, size=30),
                    ft.Text("Presupuesto", size=16, weight="bold"),
                ]),
                ft.Divider(),
                ft.Text(f"Valor: {valor}", size=14),
                ft.Row([
                    ft.Icon(icon, color=color, size=20),
                    ft.Text("Viable" if viable else "No viable", color=color, weight="bold"),
                ]),
                ft.Text(motivo, size=12, color=ft.Colors.GREY_700, italic=True) if motivo else ft.Container(),
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            # border=ft.border.all(1, ft.Colors.BLUE_300),
            border = ft.Border.all(),
            border_radius=10,
            padding=15,
            col={"sm": 12, "md": 6},
        )

    def _build_matches_card(self, matches):
        """Construye la tarjeta de matches"""
        if all(v=="null" for v in matches.values()):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.HIGHLIGHT_OFF, color=ft.Colors.GREY_500, size=30),
                        ft.Text("Matches", size=16, weight="bold"),
                    ]),
                    ft.Divider(),
                    ft.Text("No se encontraron coincidencias", color=ft.Colors.GREY_600, italic=True),
                ], spacing=10),
                bgcolor=ft.Colors.WHITE,
                # border=ft.border.all(1, ft.Colors.GREY_300),
                border = ft.Border.all(),
                border_radius=10,
                padding=15,
                col={"sm": 12, "md": 4},
            )

        items = []
        for key, value in matches.items():
            if value is not "null":  # Solo mostrar si tiene valor
                icon_map = {
                    "certificaciones": ft.Icons.VERIFIED_USER,
                    "cpv": ft.Icons.CATEGORY,
                    "criterios_favorables": ft.Icons.THUMB_UP,
                    "partners": ft.Icons.HANDSHAKE,
                    "sectores": ft.Icons.BUSINESS,
                    "ubicacion": ft.Icons.LOCATION_ON,
                }
                
                icon = icon_map.get(key, ft.Icons.CHECK_CIRCLE)
                
                # Formatear el valor
                if isinstance(value, list):
                    valor_texto = ", ".join(str(v) for v in value)
                else:
                    valor_texto = str(value)

                items.append(
                    ft.Row([
                        ft.Icon(icon, color=ft.Colors.GREEN_500, size=20),
                        ft.Column([
                            ft.Text(key.replace("_", " ").title(), weight="bold", size=12),
                            ft.Text(valor_texto, size=11, color=ft.Colors.GREY_700),
                        ], spacing=2),
                    ], spacing=10)
                )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_500, size=30),
                    ft.Text("✅ Matches", size=16, weight="bold"),
                ]),
                ft.Divider(),
                ft.Column(items, spacing=10, scroll=ft.ScrollMode.AUTO),
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            # border=ft.border.all(2, ft.Colors.GREEN_300),
            border = ft.Border.all(),
            border_radius=10,
            padding=15,
            col={"sm": 12, "md": 4},
        )

    def _build_penalizaciones_card(self, penalizaciones):
        """Construye la tarjeta de penalizaciones"""
        if len(penalizaciones) == 0:
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK, color=ft.Colors.GREEN_500, size=30),
                        ft.Text("Penalizaciones", size=16, weight="bold"),
                    ]),
                    ft.Divider(),
                    ft.Text("Sin penalizaciones", color=ft.Colors.GREEN_600, weight="bold"),
                ], spacing=10),
                bgcolor=ft.Colors.WHITE,
                # border=ft.border.all(1, ft.Colors.GREEN_300),
                border = ft.Border.all(),
                border_radius=10,
                padding=15,
                col={"sm": 12, "md": 4},
            )

        items = [
            ft.Row([
                ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED_500, size=16),
                ft.Text(pen, size=12, color=ft.Colors.RED_700),
            ], spacing=5)
            for pen in penalizaciones
        ]

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CANCEL, color=ft.Colors.RED_500, size=30),
                    ft.Text("❌ Penalizaciones", size=16, weight="bold"),
                ]),
                ft.Divider(),
                ft.Column(items, spacing=8, scroll=ft.ScrollMode.AUTO),
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            # border=ft.border.all(2, ft.Colors.RED_300),
            border = ft.Border.all(),
            border_radius=10,
            padding=15,
            col={"sm": 12, "md": 4},
        )

    def _build_warnings_card(self, warnings):
        """Construye la tarjeta de warnings"""
        if len(warnings) == 0:
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK, color=ft.Colors.GREEN_500, size=30),
                        ft.Text("Advertencias", size=16, weight="bold"),
                    ]),
                    ft.Divider(),
                    ft.Text("Sin advertencias", color=ft.Colors.GREEN_600, weight="bold"),
                ], spacing=10),
                bgcolor=ft.Colors.WHITE,
                # border=ft.border.all(1, ft.Colors.GREEN_300),
                border = ft.Border.all(),
                border_radius=10,
                padding=15,
                col={"sm": 12, "md": 4},
            )

        items = [
            ft.Row([
                ft.Icon(ft.Icons.INFO, color=ft.Colors.ORANGE_500, size=16),
                ft.Text(warn, size=12, color=ft.Colors.ORANGE_700),
            ], spacing=5)
            for warn in warnings
        ]

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_500, size=30),
                    ft.Text("⚠️ Advertencias", size=16, weight="bold"),
                ]),
                ft.Divider(),
                ft.Column(items, spacing=8, scroll=ft.ScrollMode.AUTO),
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            # border=ft.border.all(2, ft.Colors.ORANGE_300),
            border = ft.Border.all(),
            border_radius=10,
            padding=15,
            col={"sm": 12, "md": 4},
        )
    
    def _toggle_chatbot(self, e):
        """Muestra u oculta el chatbot en la esquina inferior derecha"""
        if self.chatbot_visible:
            self._cerrar_chatbot()
        else:
            self._abrir_chatbot()

    def _abrir_chatbot(self):
        """Abre el chatbot como miniventana en la esquina inferior derecha"""
        if self.chatbot_widget is None:
            self.chatbot_widget = MiniChatbot(
                page=self.page,
                df_docs=self.docs,
                nombre_licitacion=self.item.get("NOMBRE_PROYECTO", "Licitación"),
                on_close=self._cerrar_chatbot
            )
            
            self.content.controls.append(self.chatbot_widget)
        
        self.chatbot_visible = True
        self.update()

    def _cerrar_chatbot(self):
        """Cierra el chatbot"""
        if self.chatbot_widget and self.chatbot_widget in self.content.controls:
            self.content.controls.remove(self.chatbot_widget)
            self.chatbot_widget = None
        
        self.chatbot_visible = False
        self.update()


# ===============================================================
# COMPONENTE: Mini Chatbot (Ventana flotante)
# ===============================================================
class MiniChatbot(ft.Container):
    def __init__(self, page, df_docs, nombre_licitacion, on_close):
        super().__init__()
        # self.page = page
        self.df_docs = df_docs
        self.nombre_licitacion = nombre_licitacion
        self.on_close = on_close
        
        self.mensajes = []
        
        self._build_ui()

    def _build_ui(self):
        self.chat_view = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=True,
            expand=True,
        )

        self.input_field = ft.TextField(
            hint_text="Escribe tu pregunta...",
            expand=True,
            multiline=False,
            on_submit=self._enviar_mensaje,
        )

        btn_enviar = ft.IconButton(
            icon=ft.Icons.SEND,
            on_click=self._enviar_mensaje,
            tooltip="Enviar mensaje",
        )

        btn_cerrar = ft.IconButton(
            icon=ft.Icons.CLOSE,
            on_click=lambda e: self.on_close(),
            tooltip="Cerrar chatbot",
        )

        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.CHAT_BUBBLE, color=ft.Colors.WHITE),
                                ft.Text(
                                    f"💬 {self.nombre_licitacion[:30]}...",
                                    size=14,
                                    weight="bold",
                                    color=ft.Colors.WHITE,
                                    expand=True,
                                ),
                                btn_cerrar,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        bgcolor=ft.Colors.PURPLE_500,
                        padding=10,
                    ),
                    ft.Container(
                        content=self.chat_view,
                        expand=True,
                        bgcolor=ft.Colors.GREY_100,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [self.input_field, btn_enviar],
                            spacing=5,
                        ),
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                    ),
                ],
                spacing=0,
            ),
            width=400,
            height=500,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLACK26,
            ),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
        )

        self.right = 20
        self.bottom = 20

        self._agregar_mensaje_sistema("¡Hola! Soy tu asistente IA. Pregúntame lo que quieras sobre esta licitación.")

    def _agregar_mensaje_sistema(self, texto):
        mensaje = ft.Container(
            content=ft.Text(texto, size=12, color=ft.Colors.GREY_700),
            bgcolor=ft.Colors.BLUE_50,
            padding=10,
            border_radius=8,
        )
        self.chat_view.controls.append(mensaje)
        self.update()

    def _agregar_mensaje_usuario(self, texto):
        mensaje = ft.Container(
            content=ft.Text(texto, size=12, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.PURPLE_500,
            padding=10,
            border_radius=8,
            # alignment=ft.alignment.center_right,
            alignment=ft.Alignment(1.0, 0.0),
        )
        self.chat_view.controls.append(
            ft.Row([ft.Container(expand=True), mensaje], alignment=ft.MainAxisAlignment.END)
        )
        self.update()

    def _agregar_mensaje_ia(self, texto):
        mensaje = ft.Container(
            content=ft.Text(texto, size=12),
            bgcolor=ft.Colors.GREY_200,
            padding=10,
            border_radius=8,
        )
        self.chat_view.controls.append(mensaje)
        self.update()

    def _enviar_mensaje(self, e):
        texto = self.input_field.value.strip()
        if not texto:
            return

        self._agregar_mensaje_usuario(texto)
        
        self.input_field.value = ""
        self.update()

        threading.Thread(target=self._procesar_respuesta_ia, args=(texto,)).start()

    def _procesar_respuesta_ia(self, pregunta):
        typing_indicator = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=16, height=16, stroke_width=2),
                ft.Text("Pensando...", size=12, color=ft.Colors.GREY_600),
            ]),
            padding=10,
        )
        self.chat_view.controls.append(typing_indicator)
        self.update()

        import time
        time.sleep(2)

        self.chat_view.controls.remove(typing_indicator)
        
        respuesta = f"Esta es una respuesta simulada a tu pregunta: '{pregunta}'. Aquí deberías integrar tu lógica de ChatbotLicitacion."
        self._agregar_mensaje_ia(respuesta)


# ===============================================================
# COMPONENTE: Visor de PDFs
# ===============================================================
class VisorPDF(ft.Container):
    def __init__(self, df_docs: pd.DataFrame):
        super().__init__()
        self.df_docs = df_docs
        self.selected_doc = None
        self.viewer = ft.Container()
        self.resumen_container = ft.Container(
            content=ft.Text("Selecciona un documento para generar el resumen IA."),
            expand=True,
            # border=ft.border.all(1, ft.Colors.GREY_300),
            border = ft.Border.all(),
            padding=10,
        )

        self._build_ui()

    def _build_ui(self):
        self.dropdown = ft.DropdownM2(
            label="Selecciona un documento para previsualizar",
            # options=[ft.dropdown.Option(d["DESCRIPCION"]) for _, d in self.df_docs.iterrows()],
            # options=[
            #     ft.dropdown.Option(
            #         text=d["DESCRIPCION"],
            #         value=d["DESCRIPCION"]
            #     )
            #     for _, d in self.df_docs.iterrows()
            # ],
            width=500,
            # on_change=self._on_select_doc,
        )
        self.dropdown.on_change = self._on_select_doc # Así es más seguro
        self.dropdown.options=[ft.dropdown.Option(d["DESCRIPCION"]) for _, d in self.df_docs.iterrows()]

        self.viewer = ft.Container(
            content=ft.Text("Selecciona un documento para previsualizar."),
            expand=True,
            # border=ft.border.all(1, ft.Colors.GREY_400),
            border = ft.Border.all(),
            border_radius=8,
            padding=10,
        )

        self.content = ft.Row(
            [
                ft.Container(
                    ft.Column([self.dropdown, self.viewer]),
                    expand=True,
                    col={"md": 6}
                ),
                ft.Container(
                    self.resumen_container,
                    expand=True,
                    col={"md": 6}
                ),
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _on_select_doc(self, e):
        print("SE HA SELECCIONADO UN DOCUMENTO",self.dropdown.value)
        descripcion = e.control.value
        fila = self.df_docs[self.df_docs["DESCRIPCION"] == descripcion].iloc[0]
        pdf_src = fila.get("URI") or fila.get("ubicacion")

        if pdf_src.startswith("http"):
            self._mostrar_pdf_url(pdf_src)
            threading.Thread(target=self._analizar_pdf, args=(pdf_src,)).start()
        else:
            if os.path.exists(pdf_src):
                self._mostrar_pdf_local(pdf_src)
                threading.Thread(target=self._analizar_pdf, args=(pdf_src,)).start()
            else:
                self.viewer.content = ft.Text(f"⚠️ No se encontró el archivo:\n{pdf_src}", color=ft.Colors.RED)
        self.update()

    def _analizar_pdf(self, pdf_src):
        self.resumen_container.content = ft.Text("🧠 Analizando el documento, por favor espera...")
        self.update()

        try:
            resumen_data = analizar_pliego(pdf_src)
            resumen_vista = ResumenIA(resumen_data)
            self.resumen_container.content = resumen_vista
        except Exception as e:
            self.resumen_container.content = ft.Text(f"❌ Error analizando el PDF:\n{e}", color=ft.Colors.RED)

        self.update()

    # def _mostrar_pdf_url(self, url):
    #     self.viewer.content = ft.WebView(
    #         url=url,
    #         width=800,
    #         height=600
    #     )
    #     self.update()

    # def _mostrar_pdf_url(self, url):
    # # En Flet Web, esto renderiza el visor nativo del navegador (Chrome/Edge)
    #     self.viewer.content = ft.Html(
    #         content=f'<embed src="{url}#toolbar=0&navpanes=0" type="application/pdf" width="100%" height="600px" />',
    #     )
    #     self.viewer.update()

    ## Mostrar el PDF en una pagina secundaria.
    # def _mostrar_pdf_url(self, url):
    #     self.viewer.content = ft.Column([
    #         ft.Icon(ft.Icons.PICTURE_AS_PDF, size=50, color="red"),
    #         ft.Text("Documento listo para previsualizar"),
    #         ft.ElevatedButton(
    #             "Abrir PDF en pantalla completa", 
    #             icon=ft.Icons.OPEN_IN_NEW,
    #             # on_click=lambda _: self.page.UrlLauncher().launch_url(url)
    #             on_click=lambda _: self.page.launch_url(url)
                
    #         )
    #     ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    #     self.viewer.update()

    ## Mostrar el PDF en una pagina secundaria. Segunda Verison.

    def _mostrar_pdf_url(self, url):
        self.url_actual=url
        self.viewer.content = ft.Column([
            ft.Icon(ft.Icons.PICTURE_AS_PDF, size=50, color="red"),
            ft.Text("Documento listo para previsualizar"),
            # 2. En tu botón o componente, asígnalo sin lambda
            ft.ElevatedButton(
                "Abrir en el navegador",
                icon=ft.Icons.OPEN_IN_NEW,
                on_click=self._handle_abrir_url # <-- Sin lambda, Flet lo gestionará como async
                
            )
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.viewer.update()

    # 1. Define una función asíncrona dedicada para abrir la URL
    async def _handle_abrir_url(self, e):
        url = self.url_actual  # O de donde obtengas la URL
        print(f"Abriendo navegador para: {url}")
        # Usamos await para que la corrutina se ejecute realmente
        await self.page.launch_url(url) 

    

    ## Usando Libreria Externa
    # def _mostrar_pdf_url(self, url):
    #     print(f"Intentando cargar PDF con flet_webview: {url}")
        
    #     # Reemplazamos el contenido del viewer con el componente de la librería
    #     self.viewer.content = ftwv.WebView(
    #         url=url,
    #         expand=True,
    #         on_page_started=lambda _: print("Iniciando carga de PDF..."),
    #         on_page_ended=lambda _: print("Carga finalizada"),
    #         on_web_resource_error=lambda e: print(f"Error en visor: {e.data}"),
    #     )
        
    #     self.viewer.update()
        

    def _mostrar_pdf_local(self, path):
        base_dir = os.getcwd()
        abs_path = os.path.abspath(os.path.join(base_dir, path))
        
        if not os.path.exists(abs_path):
            self.viewer.content = ft.Text(
                f"⚠️ No se encontró el archivo:\n{abs_path}",
                color=ft.Colors.RED
            )
            self.update()
            return

        file_url = f"file:///{abs_path.replace(os.sep, '/')}"
        
        self.viewer.content = ft.Iframe(
            src=file_url,
            width=800,
            height=600,
            border_radius=8,
        )
        self.update()


# ===============================================================
# COMPONENTE: Resumen IA
# ===============================================================
class ResumenIA(ft.Container):
    def __init__(self, resumen_ia: dict):
        super().__init__()
        self.resumen_ia = resumen_ia
        self.content = self._build_ui()

    def _build_ui(self):
        contrato = self.resumen_ia.get("contrato", {})
        criterios = self.resumen_ia.get("criterios", {})
        requisitos = self.resumen_ia.get("requisitos", {})

        return ft.Column(
            [
                ft.Text("🧠 Resumen IA del Pliego", size=18, weight="bold"),
                ft.Divider(),
                ft.Text(f"📄 Objeto: {contrato.get('objeto', '')}"),
                ft.Text(f"Duración: {contrato.get('duracion', '')}"),
                ft.Text(f"Presupuesto: {contrato.get('presupuesto_estimado', '')}"),
                ft.Divider(),
                ft.Text("⚙️ Criterios", size=16, weight="bold"),
                ft.Text(criterios.get("criterios_adjudicacion", "")),
                ft.Text(criterios.get("criterios_valoracion", "")),
                ft.Divider(),
                ft.Text("🧾 Requisitos", size=16, weight="bold"),
                ft.Text(requisitos.get("requisitos_licitador", "")),
                ft.Text("📜 Certificaciones:", weight="bold"),
                ft.Column(
                    [ft.Text(f"- {c}") for c in requisitos.get("certificaciones_detectadas", [])],
                    spacing=5,
                ),
            ],
            spacing=5,
            scroll="auto",
        )

#--------------------------------------------

# import flet as ft
# import pandas as pd
# import os
# import sys
# import threading

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from models.resumidor_IA import analizar_pliego
# try:
#     from chatbot_licitacion import ChatBotLicitacion, BotonChatbotFlotante  # Importar la clase del chatbot
# except:
#     from .chatbot_licitacion import ChatBotLicitacion, BotonChatbotFlotante  # Importar la clase del chatbot

# class PaginaDetalle(ft.Container):
#     def __init__(self, row, docs, page=ft.Page):
#         super().__init__()
#         self.page = page
#         self.row = row
#         self.docs = docs
#         self.item = self.row
#         self.selected_id = None
#         self.chatbot_widget = None
#         self.chatbot_visible = False

#         self._build_ui()

#     def _build_ui(self):
#         # -------- FORMULARIO EN GRILLA --------
#         grid = ft.ResponsiveRow(
#             controls=[
#                 ft.TextField(label="ID", value=str(self.item["ID"]), col={"sm": 2}),
#                 ft.TextField(label="NOMBRE_PROYECTO", value=self.item.get("NOMBRE_PROYECTO", ""), col={"sm": 5}),
#                 ft.TextField(label="carpeta_origen", value=self.item.get("carpeta_origen", ""), col={"sm": 3}),
#                 ft.TextField(label="FECHA_ACTUALIZACION", value=str(self.item.get("FECHA_ACTUALIZACION", "")), col={"sm": 3}),
#                 ft.TextField(label="FECHA_LIMITE", value=str(self.item.get("FECHA_LIMITE", "")), col={"sm": 3}),
#             ]
#         )

#         # -------- BOTÓN DE CHATBOT --------
#         btn_chatbot = ft.Button(
#             "💬 Consultar con IA",
#             icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
#             on_click=self._toggle_chatbot,
#             style=ft.ButtonStyle(
#                 bgcolor=ft.Colors.PURPLE_500,
#                 color=ft.Colors.WHITE,
#                 padding=15,
#             ),
#             tooltip="Abre un asistente IA para hacer preguntas sobre esta licitación"
#         )

#         # -------- TABLA DE DOCUMENTACIÓN --------
#         tabla_docs = ft.DataTable(
#             columns=[
#                 ft.DataColumn(ft.Text("pliego_id")),
#                 ft.DataColumn(ft.Text("tipo")),
#                 ft.DataColumn(ft.Text("descripcion")),
#                 ft.DataColumn(ft.Text("URI")),
#             ],
#             rows=[
#                 ft.DataRow(
#                     cells=[
#                         ft.DataCell(ft.Text(str(d["pliego_id"]))),
#                         ft.DataCell(ft.Text(str(d["TIPO"]))),
#                         ft.DataCell(ft.Text(str(d["DESCRIPCION"]))),
#                         ft.DataCell(ft.Text(str(d["URI"]))),
#                     ]
#                 )
#                 for _, d in self.docs.iterrows()
#             ],
#         )

#         # -------- VISUALIZADOR DE PDF --------
#         visor_pdf = VisorPDF(self.docs[self.docs["pliego_id"] == self.item["ID"]])

#         tabla_docs_contenedor = ft.Container(
#             content=ft.Column([tabla_docs], scroll=ft.ScrollMode.ALWAYS, expand=True),
#             height=self.page.height * 0.3,
#             border=ft.border.all(1, ft.Colors.GREY_400),
#             padding=10,
#         )

#         # -------- ESTRUCTURA PRINCIPAL CON BOTÓN CHATBOT --------
#         self.content = ft.Stack(
#             [
#                 # Contenido principal
#                 ft.Column(
#                     [
#                         ft.Row(
#                             [
#                                 ft.Text("📄 Detalles de la licitación", size=22, weight="bold", expand=True),
#                                 btn_chatbot,
#                             ],
#                             alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#                         ),
#                         grid,
#                         ft.Divider(),
#                         ft.Text("📚 Documentos relacionados", size=18, weight="bold"),
#                         tabla_docs_contenedor,
#                         ft.Divider(),
#                         visor_pdf,
#                     ],
#                     spacing=15,
#                     scroll=ft.ScrollMode.AUTO,
#                 ),
#             ],
#             expand=True,
#         )
    
#     def _toggle_chatbot(self, e):
#         """Muestra u oculta el chatbot en la esquina inferior derecha"""
#         if self.chatbot_visible:
#             # Cerrar el chatbot
#             self._cerrar_chatbot()
#         else:
#             # Abrir el chatbot
#             self._abrir_chatbot()

#     def _abrir_chatbot(self):
#         """Abre el chatbot como miniventana en la esquina inferior derecha"""
#         if self.chatbot_widget is None:
#             # Crear el widget del chatbot
#             self.chatbot_widget = MiniChatbot(
#                 page=self.page,
#                 df_docs=self.docs,
#                 nombre_licitacion=self.item.get("NOMBRE_PROYECTO", "Licitación"),
#                 on_close=self._cerrar_chatbot
#             )
            
#             # Agregar al Stack
#             self.content.controls.append(self.chatbot_widget)
        
#         self.chatbot_visible = True
#         self.update()

#     def _cerrar_chatbot(self):
#         """Cierra el chatbot"""
#         if self.chatbot_widget and self.chatbot_widget in self.content.controls:
#             self.content.controls.remove(self.chatbot_widget)
#             self.chatbot_widget = None
        
#         self.chatbot_visible = False
#         self.update()


# # ===============================================================
# # COMPONENTE: Mini Chatbot (Ventana flotante)
# # ===============================================================
# class MiniChatbot(ft.Container):
#     def __init__(self, page, df_docs, nombre_licitacion, on_close):
#         super().__init__()
#         self.page = page
#         self.df_docs = df_docs
#         self.nombre_licitacion = nombre_licitacion
#         self.on_close = on_close
        
#         # Historial de mensajes
#         self.mensajes = []
        
#         self._build_ui()

#     def _build_ui(self):
#         # Área de mensajes
#         self.chat_view = ft.ListView(
#             spacing=10,
#             padding=10,
#             auto_scroll=True,
#             expand=True,
#         )

#         # Campo de entrada
#         self.input_field = ft.TextField(
#             hint_text="Escribe tu pregunta...",
#             expand=True,
#             multiline=False,
#             on_submit=self._enviar_mensaje,
#         )

#         # Botón enviar
#         btn_enviar = ft.IconButton(
#             icon=ft.Icons.SEND,
#             on_click=self._enviar_mensaje,
#             tooltip="Enviar mensaje",
#         )

#         # Botón cerrar
#         btn_cerrar = ft.IconButton(
#             icon=ft.Icons.CLOSE,
#             on_click=lambda e: self.on_close(),
#             tooltip="Cerrar chatbot",
#         )

#         # Estructura del chatbot
#         self.content = ft.Container(
#             content=ft.Column(
#                 [
#                     # Cabecera
#                     ft.Container(
#                         content=ft.Row(
#                             [
#                                 ft.Icon(ft.Icons.CHAT_BUBBLE, color=ft.Colors.WHITE),
#                                 ft.Text(
#                                     f"💬 {self.nombre_licitacion}",
#                                     size=14,
#                                     weight="bold",
#                                     color=ft.Colors.WHITE,
#                                     expand=True,
#                                 ),
#                                 btn_cerrar,
#                             ],
#                             alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#                         ),
#                         bgcolor=ft.Colors.PURPLE_500,
#                         padding=10,
#                     ),
#                     # Área de chat
#                     ft.Container(
#                         content=self.chat_view,
#                         expand=True,
#                         bgcolor=ft.Colors.GREY_100,
#                     ),
#                     # Barra de entrada
#                     ft.Container(
#                         content=ft.Row(
#                             [self.input_field, btn_enviar],
#                             spacing=5,
#                         ),
#                         padding=10,
#                         bgcolor=ft.Colors.WHITE,
#                     ),
#                 ],
#                 spacing=0,
#             ),
#             width=400,
#             height=500,
#             shadow=ft.BoxShadow(
#                 spread_radius=1,
#                 blur_radius=15,
#                 color=ft.Colors.BLACK26,
#             ),
#             border_radius=10,
#             bgcolor=ft.Colors.WHITE,
#         )

#         # Posicionar en la esquina inferior derecha
#         self.right = 20
#         self.bottom = 20

#         # Mensaje de bienvenida
#         self._agregar_mensaje_sistema("¡Hola! Soy tu asistente IA. Pregúntame lo que quieras sobre esta licitación.")

#     def _agregar_mensaje_sistema(self, texto):
#         """Agrega un mensaje del sistema"""
#         mensaje = ft.Container(
#             content=ft.Text(texto, size=12, color=ft.Colors.GREY_700),
#             bgcolor=ft.Colors.BLUE_50,
#             padding=10,
#             border_radius=8,
#         )
#         self.chat_view.controls.append(mensaje)
#         self.update()

#     def _agregar_mensaje_usuario(self, texto):
#         """Agrega un mensaje del usuario"""
#         mensaje = ft.Container(
#             content=ft.Text(texto, size=12, color=ft.Colors.WHITE),
#             bgcolor=ft.Colors.PURPLE_500,
#             padding=10,
#             border_radius=8,
#             alignment=ft.alignment.center_right,
#         )
#         self.chat_view.controls.append(
#             ft.Row([ft.Container(expand=True), mensaje], alignment=ft.MainAxisAlignment.END)
#         )
#         self.update()

#     def _agregar_mensaje_ia(self, texto):
#         """Agrega un mensaje de la IA"""
#         mensaje = ft.Container(
#             content=ft.Text(texto, size=12),
#             bgcolor=ft.Colors.GREY_200,
#             padding=10,
#             border_radius=8,
#         )
#         self.chat_view.controls.append(mensaje)
#         self.update()

#     def _enviar_mensaje(self, e):
#         """Envía un mensaje al chatbot"""
#         texto = self.input_field.value.strip()
#         if not texto:
#             return

#         # Mostrar mensaje del usuario
#         self._agregar_mensaje_usuario(texto)
        
#         # Limpiar el campo de entrada
#         self.input_field.value = ""
#         self.update()

#         # Simular respuesta de IA (aquí deberías integrar tu lógica de chatbot real)
#         threading.Thread(target=self._procesar_respuesta_ia, args=(texto,)).start()

#     def _procesar_respuesta_ia(self, pregunta):
#         """Procesa la pregunta y genera una respuesta (placeholder)"""
#         # Agregar indicador de escritura
#         typing_indicator = ft.Container(
#             content=ft.Row([
#                 ft.ProgressRing(width=16, height=16, stroke_width=2),
#                 ft.Text("Pensando...", size=12, color=ft.Colors.GREY_600),
#             ]),
#             padding=10,
#         )
#         self.chat_view.controls.append(typing_indicator)
#         self.update()

#         # Simular procesamiento (aquí iría tu lógica real de ChatbotLicitacion)
#         import time
#         time.sleep(2)

#         # Eliminar indicador
#         self.chat_view.controls.remove(typing_indicator)
        
#         # Agregar respuesta (placeholder)
#         respuesta = f"Esta es una respuesta simulada a tu pregunta: '{pregunta}'. Aquí deberías integrar tu lógica de ChatbotLicitacion."
#         self._agregar_mensaje_ia(respuesta)


# # ===============================================================
# # COMPONENTE: Visor de PDFs (sin cambios)
# # ===============================================================
# class VisorPDF(ft.Container):
#     """
#     Componente para visualizar PDFs desde URLs o rutas locales.
#     """
#     def __init__(self, df_docs: pd.DataFrame):
#         super().__init__()
#         self.df_docs = df_docs
#         self.selected_doc = None
#         self.viewer = ft.Container()
#         self.resumen_container = ft.Container(
#             content=ft.Text("Selecciona un documento para generar el resumen IA."),
#             expand=True,
#             border=ft.border.all(1, ft.Colors.GREY_300),
#             padding=10,
#         )

#         self._build_ui()

#     def _build_ui(self):
#         self.dropdown = ft.Dropdown(
#             label="Selecciona un documento para previsualizar",
#             options=[ft.dropdown.Option(d["DESCRIPCION"]) for _, d in self.df_docs.iterrows()],
#             width=500,
#             on_change=self._on_select_doc,
#         )

#         self.viewer = ft.Container(
#             content=ft.Text("Selecciona un documento para previsualizar."),
#             expand=True,
#             border=ft.border.all(1, ft.Colors.GREY_400),
#             border_radius=8,
#             padding=10,
#         )

#         self.content = ft.Row(
#             [
#                 ft.Container(
#                     ft.Column([self.dropdown, self.viewer]),
#                     expand=True,
#                     col={"md": 6}
#                 ),
#                 ft.Container(
#                     self.resumen_container,
#                     expand=True,
#                     col={"md": 6}
#                 ),
#             ],
#             expand=True,
#             alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#         )

#     def _on_select_doc(self, e):
#         descripcion = e.control.value
#         fila = self.df_docs[self.df_docs["DESCRIPCION"] == descripcion].iloc[0]
#         pdf_src = fila.get("URI") or fila.get("ubicacion")

#         if pdf_src.startswith("http"):
#             self._mostrar_pdf_url(pdf_src)
#             threading.Thread(target=self._analizar_pdf, args=(pdf_src,)).start()
#         else:
#             if os.path.exists(pdf_src):
#                 self._mostrar_pdf_local(pdf_src)
#                 threading.Thread(target=self._analizar_pdf, args=(pdf_src,)).start()
#             else:
#                 self.viewer.content = ft.Text(f"⚠️ No se encontró el archivo:\n{pdf_src}", color=ft.Colors.RED)
#                 self.update()

#     def _analizar_pdf(self, pdf_src):
#         """Ejecuta el análisis IA en segundo plano."""
#         self.resumen_container.content = ft.Text("🧠 Analizando el documento, por favor espera...")
#         self.update()

#         try:
#             resumen_data = analizar_pliego(pdf_src)
#             resumen_vista = ResumenIA(resumen_data)
#             self.resumen_container.content = resumen_vista
#         except Exception as e:
#             self.resumen_container.content = ft.Text(f"❌ Error analizando el PDF:\n{e}", color=ft.Colors.RED)

#         self.update()

#     def _mostrar_pdf_url(self, url):
#         """Muestra PDF desde una URL."""
#         self.viewer.content = ft.WebView(
#             url=url,
#             width=800,
#             height=600
#         )
#         self.update()

#     def _mostrar_pdf_local(self, path):
#         """Muestra PDF desde una ruta relativa o absoluta del proyecto."""
#         base_dir = os.getcwd()
#         abs_path = os.path.abspath(os.path.join(base_dir, path))
        
#         if not os.path.exists(abs_path):
#             self.viewer.content = ft.Text(
#                 f"⚠️ No se encontró el archivo:\n{abs_path}",
#                 color=ft.Colors.RED
#             )
#             self.update()
#             return

#         file_url = f"file:///{abs_path.replace(os.sep, '/')}"
        
#         self.viewer.content = ft.Iframe(
#             src=file_url,
#             width=800,
#             height=600,
#             border_radius=8,
#         )
#         self.update()


# # ===============================================================
# # COMPONENTE: Resumen IA (sin cambios)
# # ===============================================================
# class ResumenIA(ft.Container):
#     def __init__(self, resumen_ia: dict):
#         super().__init__()
#         self.resumen_ia = resumen_ia
#         self.content = self._build_ui()

#     def _build_ui(self):
#         contrato = self.resumen_ia.get("contrato", {})
#         criterios = self.resumen_ia.get("criterios", {})
#         requisitos = self.resumen_ia.get("requisitos", {})

#         return ft.Column(
#             [
#                 ft.Text("🧠 Resumen IA del Pliego", size=18, weight="bold"),
#                 ft.Divider(),
#                 ft.Text(f"📄 Objeto: {contrato.get('objeto', '')}"),
#                 ft.Text(f"Duración: {contrato.get('duracion', '')}"),
#                 ft.Text(f"Presupuesto: {contrato.get('presupuesto_estimado', '')}"),
#                 ft.Divider(),
#                 ft.Text("⚙️ Criterios", size=16, weight="bold"),
#                 ft.Text(criterios.get("criterios_adjudicacion", "")),
#                 ft.Text(criterios.get("criterios_valoracion", "")),
#                 ft.Divider(),
#                 ft.Text("🧾 Requisitos", size=16, weight="bold"),
#                 ft.Text(requisitos.get("requisitos_licitador", "")),
#                 ft.Text("📜 Certificaciones:", weight="bold"),
#                 ft.Column(
#                     [ft.Text(f"- {c}") for c in requisitos.get("certificaciones_detectadas", [])],
#                     spacing=5,
#                 ),
#             ],
#             spacing=5,
#             scroll="auto",
#         )
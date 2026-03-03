# import flet as ft
# import pandas as pd
# import threading
# import sys
# import os

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from models.resumidor_IA import analizar_pliego  # Tu función existente
    

# # ===============================================================
# # COMPONENTE: ChatBot para consultas sobre PDFs
# # ===============================================================
# class ChatBotLicitacion(ft.AlertDialog):
#     def __init__(self, page: ft.Page, df_docs: pd.DataFrame, nombre_licitacion: str):
#         super().__init__()
#         # self.page = page
#         self.df_docs = df_docs
#         self.nombre_licitacion = nombre_licitacion
#         self.historial_mensajes = []
#         self.documentos_analizados = False
#         self.contexto_documentos = ""
        
#         self._build_ui()
#         self._iniciar_analisis()
    
#     def _build_ui(self):
#         # Título del diálogo
#         self.modal = True
#         self.title = ft.Row(
#             [
#                 ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, color=ft.Colors.BLUE_500),
#                 ft.Text(
#                     "💬 Asistente de Licitación",
#                     size=18,
#                     weight="bold",
#                     expand=True,
#                 ),
#                 ft.IconButton(
#                     icon=ft.Icons.CLOSE,
#                     on_click=self._cerrar_dialogo,
#                     tooltip="Cerrar",
#                 ),
#             ],
#             alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#         )
        
#         # Área de mensajes (historial del chat)
#         self.lista_mensajes = ft.ListView(
#             spacing=10,
#             padding=10,
#             auto_scroll=True,
#             expand=True,
#         )
        
#         # Mensaje inicial (crear el control pero no actualizar aún)
#         mensaje_inicial = self._crear_mensaje_sistema(
#             f"🔄 Analizando documentos de: {self.nombre_licitacion}\n\n" +
#             f"📄 Documentos encontrados: {len(self.df_docs)}\n" +
#             "Por favor espera mientras proceso la información..."
#         )
#         self.lista_mensajes.controls.append(mensaje_inicial)
        
#         # Campo de entrada de texto
#         self.txt_pregunta = ft.TextField(
#             hint_text="Escribe tu pregunta aquí...",
#             multiline=True,
#             min_lines=1,
#             max_lines=3,
#             expand=True,
#             disabled=True,  # Deshabilitado hasta que termine el análisis
#             on_submit=self._enviar_pregunta,
#         )
        
#         # Botón de enviar
#         self.btn_enviar = ft.IconButton(
#             icon=ft.Icons.SEND,
#             tooltip="Enviar pregunta",
#             disabled=True,
#             on_click=self._enviar_pregunta,
#             style=ft.ButtonStyle(
#                 bgcolor=ft.Colors.BLUE_500,
#                 color=ft.Colors.WHITE,
#             ),
#         )
        
#         # Indicador de escritura
#         self.indicador_escritura = ft.Container(
#             content=ft.Row(
#                 [
#                     ft.ProgressRing(width=16, height=16, stroke_width=2),
#                     ft.Text("Escribiendo...", size=12, italic=True),
#                 ],
#                 spacing=5,
#             ),
#             visible=False,
#             padding=5,
#         )
        
#         # Contenedor de entrada
#         contenedor_entrada = ft.Row(
#             [
#                 self.txt_pregunta,
#                 self.btn_enviar,
#             ],
#             spacing=10,
#         )
        
#         # Estructura del contenido
#         self.content = ft.Container(
#             content=ft.Column(
#                 [
#                     ft.Container(
#                         content=self.lista_mensajes,
#                         border=ft.border.all(1, ft.Colors.GREY_300),
#                         border_radius=8,
#                         padding=5,
#                         expand=True,
#                     ),
#                     self.indicador_escritura,
#                     contenedor_entrada,
#                 ],
#                 spacing=10,
#             ),
#             width=700,
#             height=600,
#         )
        
#         # Botones de acción
#         self.actions = [
#             ft.TextButton(
#                 "Limpiar chat",
#                 icon=ft.Icons.DELETE_SWEEP,
#                 on_click=self._limpiar_chat,
#             ),
#             ft.TextButton(
#                 "Cerrar",
#                 on_click=self._cerrar_dialogo,
#             ),
#         ]
    
#     def _iniciar_analisis(self):
#         """Analiza los PDFs"""
#         threading.Thread(target=self._analizar_documentos, daemon=True).start()
    
#     def _analizar_documentos(self):
#         """Procesa todos los PDFs y extrae su contenido"""
#         try:
#             contextos = []
            
#             for _, doc in self.df_docs.iterrows():
#                 pdf_src = doc.get("URI") or doc.get("ubicacion")
#                 tipo_doc = doc.get("tipo", "Documento")
                
#                 # Aquí usarías tu función de análisis existente
#                 # o una nueva función específica para extraer texto
#                 try:
#                     resumen = analizar_pliego(pdf_src)
#                     contextos.append(
#                         f"\n--- {tipo_doc}: {doc.get('descripcion', '')} ---\n" +
#                         self._formatear_resumen(resumen)
#                     )
#                 except Exception as e:
#                     contextos.append(f"\n--- Error en {tipo_doc}: {str(e)} ---\n")
            
#             self.contexto_documentos = "\n\n".join(contextos)
#             self.documentos_analizados = True
            
#             # Actualizar UI usando update() directamente
#             self._finalizar_analisis()
            
#         except Exception as e:
#             self._agregar_mensaje_sistema(
#                 f"❌ Error al analizar documentos: {str(e)}",
#                 color=ft.Colors.RED_400
#             )
    
#     def _formatear_resumen(self, resumen_data):
#         """Convierte el diccionario de resumen en texto legible"""
#         texto = []
        
#         if "contrato" in resumen_data:
#             contrato = resumen_data["contrato"]
#             texto.append(f"Objeto: {contrato.get('objeto', '')}")
#             texto.append(f"Duración: {contrato.get('duracion', '')}")
#             texto.append(f"Presupuesto: {contrato.get('presupuesto_estimado', '')}")
        
#         if "criterios" in resumen_data:
#             criterios = resumen_data["criterios"]
#             texto.append(f"\nCriterios de adjudicación: {criterios.get('criterios_adjudicacion', '')}")
        
#         if "requisitos" in resumen_data:
#             requisitos = resumen_data["requisitos"]
#             texto.append(f"\nRequisitos: {requisitos.get('requisitos_licitador', '')}")
            
#             if "certificaciones_detectadas" in requisitos:
#                 certs = requisitos["certificaciones_detectadas"]
#                 if certs:
#                     texto.append("Certificaciones requeridas:")
#                     for cert in certs:
#                         texto.append(f"  - {cert}")
        
#         return "\n".join(texto)
    
#     def _finalizar_analisis(self):
#         """Actualiza la UI cuando termina el análisis"""
#         self._agregar_mensaje_sistema(
#             "✅ Análisis completado!\n\n" +
#             "Ahora puedes hacerme preguntas sobre:\n" +
#             "• Requisitos y documentación necesaria\n" +
#             "• Criterios de valoración\n" +
#             "• Plazos y fechas importantes\n" +
#             "• Presupuesto y condiciones económicas\n" +
#             "• Cualquier otro aspecto de la licitación",
#             color=ft.Colors.GREEN_600
#         )
        
#         # Habilitar la entrada
#         self.txt_pregunta.disabled = False
#         self.btn_enviar.disabled = False
#         if self.txt_pregunta.page:
#             self.txt_pregunta.focus()
#             self.update()
    
#     def _crear_mensaje_sistema(self, texto, color=ft.Colors.BLUE_700):
#         """Crea un mensaje del sistema sin agregarlo al chat"""
#         return ft.Container(
#             content=ft.Row(
#                 [
#                     ft.Icon(ft.Icons.INFO_OUTLINE, size=20, color=color),
#                     ft.Text(
#                         texto,
#                         size=13,
#                         color=color,
#                         expand=True,
#                     ),
#                 ],
#                 spacing=10,
#             ),
#             bgcolor=ft.Colors.BLUE_50,
#             padding=10,
#             border_radius=8,
#         )
    
#     def _agregar_mensaje_sistema(self, texto, color=ft.Colors.BLUE_700):
#         """Agrega un mensaje del sistema al chat"""
#         mensaje = self._crear_mensaje_sistema(texto, color)
#         self.lista_mensajes.controls.append(mensaje)
#         if self.lista_mensajes.page:
#             self.lista_mensajes.update()
    
#     def _agregar_mensaje_usuario(self, texto):
#         """Agrega un mensaje del usuario al chat"""
#         mensaje = ft.Container(
#             content=ft.Column(
#                 [
#                     ft.Text("Tú", size=12, weight="bold", color=ft.Colors.GREY_700),
#                     ft.Text(texto, size=14),
#                 ],
#                 spacing=5,
#             ),
#             bgcolor=ft.Colors.BLUE_100,
#             padding=10,
#             border_radius=8,
#             alignment=ft.Alignment(1,0),
#         )
        
#         self.lista_mensajes.controls.append(mensaje)
#         self.historial_mensajes.append({"role": "user", "content": texto})
#         if self.lista_mensajes.page:
#             self.lista_mensajes.update()
    
#     def _agregar_mensaje_asistente(self, texto):
#         """Agrega un mensaje del asistente al chat"""
#         mensaje = ft.Container(
#             content=ft.Column(
#                 [
#                     ft.Row(
#                         [
#                             ft.Icon(ft.Icons.SMART_TOY, size=18, color=ft.Colors.BLUE_500),
#                             ft.Text("Asistente", size=12, weight="bold", color=ft.Colors.BLUE_700),
#                         ],
#                         spacing=5,
#                     ),
#                     ft.Text(texto, size=14, selectable=True),
#                 ],
#                 spacing=5,
#             ),
#             bgcolor=ft.Colors.GREY_100,
#             padding=10,
#             border_radius=8,
#         )
        
#         self.lista_mensajes.controls.append(mensaje)
#         self.historial_mensajes.append({"role": "assistant", "content": texto})
#         if self.lista_mensajes.page:
#             self.lista_mensajes.update()
    
#     def _enviar_pregunta(self, e):
#         """Envía la pregunta al modelo de IA"""
#         pregunta = self.txt_pregunta.value.strip()
        
#         if not pregunta:
#             return
        
#         if not self.documentos_analizados:
#             self._agregar_mensaje_sistema(
#                 "⚠️ Por favor espera a que termine el análisis de documentos.",
#                 color=ft.Colors.ORANGE_600
#             )
#             return
        
#         # Agregar mensaje del usuario
#         self._agregar_mensaje_usuario(pregunta)
        
#         # Limpiar campo de entrada
#         self.txt_pregunta.value = ""
#         self.txt_pregunta.update()
        
#         # Mostrar indicador de escritura
#         self.indicador_escritura.visible = True
#         self.indicador_escritura.update()
        
#         # Deshabilitar entrada mientras procesa
#         self.txt_pregunta.disabled = True
#         self.btn_enviar.disabled = True
#         self.update()
        
#         # Procesar pregunta en hilo separado
#         threading.Thread(
#             target=self._procesar_pregunta,
#             args=(pregunta,),
#             daemon=True
#         ).start()
    
#     def _procesar_pregunta(self, pregunta):
#         # """Procesa la pregunta usando la API de Anthropic"""
#         try:
#             # Construir el prompt con contexto
#             prompt_sistema = f"""Eres un asistente experto en licitaciones públicas españolas. 
#             Tu tarea es ayudar al usuario a entender los detalles de una licitación específica.

#             CONTEXTO DE LOS DOCUMENTOS:
#             {self.contexto_documentos}

#             INSTRUCCIONES:
#             - Responde SOLO basándote en la información proporcionada en los documentos
#             - Si no tienes información para responder, indícalo claramente
#             - Sé conciso pero completo en tus respuestas
#             - Usa un lenguaje claro y profesional
#             - Si detectas información importante, destácala
#             - Estructura tus respuestas con viñetas cuando sea apropiado"""

#             # Construir historial de mensajes para el contexto
#             mensajes = [{"role": "user", "content": prompt_sistema}]
#             mensajes.extend(self.historial_mensajes[-10:])
#             mensajes.append({"role": "user", "content": pregunta})
            
#             # Llamar a la API de Anthropic
#             import requests
            
#             response = requests.post(
#                 "https://api.anthropic.com/v1/messages",
#                 headers={
#                     "Content-Type": "application/json",
#                     "anthropic-version": "2023-06-01",
#                 },
#                 json={
#                     "model": "claude-sonnet-4-20250514",
#                     "max_tokens": 2000,
#                     "messages": mensajes,
#                 }
#             )
            
#             if response.status_code == 200:
#                 data = response.json()
#                 respuesta = data["content"][0]["text"]
#                 self._mostrar_respuesta(respuesta)
#             else:
#                 error_msg = f"Error en la API: {response.status_code}"
#                 self._mostrar_error(error_msg)
            
#         except Exception as e:
#             self._mostrar_error(str(e))
        
#     def _mostrar_respuesta(self, respuesta):
#         """Muestra la respuesta del asistente"""
#         self.indicador_escritura.visible = False
#         if self.indicador_escritura.page:
#             self.indicador_escritura.update()
        
#         self._agregar_mensaje_asistente(respuesta)
        
#         # Rehabilitar entrada
#         self.txt_pregunta.disabled = False
#         self.btn_enviar.disabled = False
#         if self.txt_pregunta.page:
#             self.txt_pregunta.focus()
#             self.update()
    
#     def _mostrar_error(self, error):
#         """Muestra un mensaje de error"""
#         self.indicador_escritura.visible = False
#         if self.indicador_escritura.page:
#             self.indicador_escritura.update()
        
#         self._agregar_mensaje_sistema(
#             f"❌ Error al procesar la pregunta: {error}",
#             color=ft.Colors.RED_600
#         )
        
#         # Rehabilitar entrada
#         self.txt_pregunta.disabled = False
#         self.btn_enviar.disabled = False
#         if self.page:
#             self.update()
    
#     def _limpiar_chat(self, e):
#         """Limpia el historial del chat"""
#         self.lista_mensajes.controls.clear()
#         self.historial_mensajes.clear()
        
#         self._agregar_mensaje_sistema(
#             "🧹 Chat limpiado. Puedes seguir haciendo preguntas sobre la licitación."
#         )
    
#     def _cerrar_dialogo(self, e):
#         """Cierra el diálogo"""
#         self.open = False
#         self.update()


# # ===============================================================
# # FUNCIÓN HELPER: Abrir ChatBot desde cualquier parte de la app
# # ===============================================================
# def abrir_chatbot_licitacion(page: ft.Page, df_docs: pd.DataFrame, nombre_licitacion: str):
#     """
#     Función auxiliar para abrir el chatbot desde cualquier componente
    
#     Args:
#         page: Página de Flet
#         df_docs: DataFrame con los documentos de la licitación
#         nombre_licitacion: Nombre de la licitación para mostrar en el título
#     """
#     chatbot = ChatBotLicitacion(
#         page=page,
#         df_docs=df_docs,
#         nombre_licitacion=nombre_licitacion
#     )
    
#     page.overlay.append(chatbot)
#     chatbot.open = True
#     page.update()

# # ===============================================================
# # COMPONENTE: Botón flotante para abrir el chatbot
# # ===============================================================
# class BotonChatbotFlotante(ft.Container):
#     """
#     Botón flotante que se puede usar en cualquier página para acceder
#     rápidamente al chatbot cuando hay una licitación seleccionada
#     """
#     def __init__(self, page: ft.Page):
#         super().__init__()
#         # self.page = page
#         # self.docs_actuales = None
#         self._docs_actuales = None
#         self.nombre_licitacion = None
#         self.visible = False
        
#         self._build_ui()
    
#     def _build_ui(self):
#         self.btn_flotante = ft.FloatingActionButton(
#             icon=ft.Icons.CHAT,
#             bgcolor=ft.Colors.PURPLE_500,
#             on_click=self._abrir_chat,
#             tooltip="Consultar con IA sobre la licitación",
#         )
        
#         self.content = self.btn_flotante
#         self.visible = False
#         self.right = 20
#         self.bottom = 20
    
#     def activar(self, df_docs, nombre_licitacion):
#         """
#         Activa el botón con los documentos de una licitación específica
        
#         Args:
#             df_docs: DataFrame con los documentos
#             nombre_licitacion: Nombre de la licitación
#         """
#         # self.docs_actuales = df_docs
#         self._docs_actuales = df_docs
#         self.nombre_licitacion = nombre_licitacion
#         self.visible = True
#         self.update()
    
#     def desactivar(self):
#         """Desactiva y oculta el botón"""
#         self.visible = False
#         # self.docs_actuales = None
#         self._docs_actuales = None
#         self.nombre_licitacion = None
#         self.update()
    
#     def _abrir_chat(self, e):
#         # if self.docs_actuales is not None:
#         if self._docs_actuales is not None:
#             abrir_chatbot_licitacion(
#                 page=self.page,
#                 # df_docs=self.docs_actuales,
#                 df_docs=self._docs_actuales,
#                 nombre_licitacion=self.nombre_licitacion
#             )


## ----------------------

import flet as ft
import pandas as pd
import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.resumidor_IA import analizar_pliego  # Tu función existente


# ===============================================================
# COMPONENTE: ChatBot para consultas sobre PDFs (Navigation Drawer)
# ===============================================================
class ChatBotLicitacionDrawer(ft.NavigationDrawer):
    def __init__(self, page: ft.Page, df_docs: pd.DataFrame, nombre_licitacion: str, on_close_callback=None):
        super().__init__()
        self.page = page
        self.df_docs = df_docs
        self.nombre_licitacion = nombre_licitacion
        self.on_close_callback = on_close_callback
        self.historial_mensajes = []
        self.documentos_analizados = False
        self.contexto_documentos = ""
        
        self._build_ui()
        self._iniciar_analisis()
    
    def _build_ui(self):
        # Configuración del drawer
        self.bgcolor = ft.Colors.WHITE
        self.elevation = 16
        self.position = ft.NavigationDrawerPosition.END  # Posición derecha
        
        # Encabezado con título y botón de cerrar
        encabezado = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, color=ft.Colors.BLUE_500, size=24),
                    ft.Text(
                        "Asistente de Licitación",
                        size=18,
                        weight="bold",
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        on_click=self._cerrar_drawer,
                        tooltip="Cerrar",
                        icon_size=20,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(left=15, right=5, top=10, bottom=10),
            bgcolor=ft.Colors.BLUE_50,
        )
        
        # Información de la licitación
        info_licitacion = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        self.nombre_licitacion,
                        size=13,
                        weight="w500",
                        color=ft.Colors.GREY_800,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"📄 {len(self.df_docs)} documentos",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
        )
        
        # Área de mensajes (historial del chat)
        self.lista_mensajes = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=True,
            expand=True,
        )
        
        # Mensaje inicial
        mensaje_inicial = self._crear_mensaje_sistema(
            f"🔄 Analizando documentos...\n\n" +
            "Por favor espera mientras proceso la información de los documentos."
        )
        self.lista_mensajes.controls.append(mensaje_inicial)
        
        # Indicador de escritura
        self.indicador_escritura = ft.Container(
            content=ft.Row(
                [
                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                    ft.Text("Escribiendo...", size=12, italic=True, color=ft.Colors.GREY_600),
                ],
                spacing=5,
            ),
            visible=False,
            padding=ft.padding.only(left=10, bottom=5),
        )
        
        # Campo de entrada de texto
        self.txt_pregunta = ft.TextField(
            hint_text="Escribe tu pregunta...",
            multiline=True,
            min_lines=1,
            max_lines=3,
            expand=True,
            disabled=True,
            on_submit=self._enviar_pregunta,
            border_color=ft.Colors.BLUE_200,
            focused_border_color=ft.Colors.BLUE_500,
            text_size=14,
        )
        
        # Botón de enviar
        self.btn_enviar = ft.IconButton(
            icon=ft.Icons.SEND,
            tooltip="Enviar pregunta",
            disabled=True,
            on_click=self._enviar_pregunta,
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_500,
            disabled_color=ft.Colors.GREY_400,
        )
        
        # Contenedor de entrada con borde superior
        contenedor_entrada = ft.Container(
            content=ft.Row(
                [
                    self.txt_pregunta,
                    self.btn_enviar,
                ],
                spacing=10,
            ),
            padding=10,
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300)),
            bgcolor=ft.Colors.GREY_50,
        )
        
        # Botón de limpiar chat (opcional, en la parte inferior)
        btn_limpiar = ft.TextButton(
            "🧹 Limpiar chat",
            icon=ft.Icons.DELETE_SWEEP,
            on_click=self._limpiar_chat,
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_600,
            ),
        )
        
        footer = ft.Container(
            content=ft.Row(
                [btn_limpiar],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=5,
        )
        
        # Estructura principal del drawer
        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        encabezado,
                        info_licitacion,
                        ft.Container(
                            content=self.lista_mensajes,
                            expand=True,
                            bgcolor=ft.Colors.WHITE,
                        ),
                        self.indicador_escritura,
                        footer,
                        contenedor_entrada,
                    ],
                    spacing=0,
                    expand=True,
                ),
                width=450,  # Ancho del drawer
                expand=True,
            )
        ]
    
    def _iniciar_analisis(self):
        """Analiza los PDFs"""
        threading.Thread(target=self._analizar_documentos, daemon=True).start()
    
    def _analizar_documentos(self):
        """Procesa todos los PDFs y extrae su contenido"""
        try:
            contextos = []
            
            for _, doc in self.df_docs.iterrows():
                pdf_src = doc.get("URI") or doc.get("ubicacion")
                tipo_doc = doc.get("tipo", "Documento")
                
                try:
                    resumen = analizar_pliego(pdf_src)
                    contextos.append(
                        f"\n--- {tipo_doc}: {doc.get('descripcion', '')} ---\n" +
                        self._formatear_resumen(resumen)
                    )
                except Exception as e:
                    contextos.append(f"\n--- Error en {tipo_doc}: {str(e)} ---\n")
            
            self.contexto_documentos = "\n\n".join(contextos)
            self.documentos_analizados = True
            
            self._finalizar_analisis()
            
        except Exception as e:
            self._agregar_mensaje_sistema(
                f"❌ Error al analizar documentos: {str(e)}",
                color=ft.Colors.RED_400
            )
    
    def _formatear_resumen(self, resumen_data):
        """Convierte el diccionario de resumen en texto legible"""
        texto = []
        
        if "contrato" in resumen_data:
            contrato = resumen_data["contrato"]
            texto.append(f"Objeto: {contrato.get('objeto', '')}")
            texto.append(f"Duración: {contrato.get('duracion', '')}")
            texto.append(f"Presupuesto: {contrato.get('presupuesto_estimado', '')}")
        
        if "criterios" in resumen_data:
            criterios = resumen_data["criterios"]
            texto.append(f"\nCriterios de adjudicación: {criterios.get('criterios_adjudicacion', '')}")
        
        if "requisitos" in resumen_data:
            requisitos = resumen_data["requisitos"]
            texto.append(f"\nRequisitos: {requisitos.get('requisitos_licitador', '')}")
            
            if "certificaciones_detectadas" in requisitos:
                certs = requisitos["certificaciones_detectadas"]
                if certs:
                    texto.append("Certificaciones requeridas:")
                    for cert in certs:
                        texto.append(f"  - {cert}")
        
        return "\n".join(texto)
    
    def _finalizar_analisis(self):
        """Actualiza la UI cuando termina el análisis"""
        self._agregar_mensaje_sistema(
            "✅ Análisis completado!\n\n" +
            "Ahora puedes hacerme preguntas sobre:\n" +
            "• Requisitos y documentación necesaria\n" +
            "• Criterios de valoración\n" +
            "• Plazos y fechas importantes\n" +
            "• Presupuesto y condiciones económicas\n" +
            "• Cualquier otro aspecto de la licitación",
            color=ft.Colors.GREEN_600
        )
        
        # Habilitar la entrada
        self.txt_pregunta.disabled = False
        self.btn_enviar.disabled = False
        if self.page:
            self.txt_pregunta.focus()
            self.page.update()
    
    def _crear_mensaje_sistema(self, texto, color=ft.Colors.BLUE_700):
        """Crea un mensaje del sistema"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=color),
                    ft.Text(
                        texto,
                        size=12,
                        color=color,
                        expand=True,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.BLUE_50,
            padding=8,
            border_radius=8,
        )
    
    def _agregar_mensaje_sistema(self, texto, color=ft.Colors.BLUE_700):
        """Agrega un mensaje del sistema al chat"""
        mensaje = self._crear_mensaje_sistema(texto, color)
        self.lista_mensajes.controls.append(mensaje)
        if self.page:
            self.page.update()
    
    def _agregar_mensaje_usuario(self, texto):
        """Agrega un mensaje del usuario al chat"""
        mensaje = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Tú", size=11, weight="bold", color=ft.Colors.GREY_700),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Text(texto, size=13),
                ],
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.END,
            ),
            bgcolor=ft.Colors.BLUE_100,
            padding=10,
            border_radius=ft.border_radius.only(
                top_left=12,
                top_right=12,
                bottom_left=12,
                bottom_right=2,
            ),
            alignment=ft.alignment.center_right,
        )
        
        self.lista_mensajes.controls.append(
            ft.Container(
                content=mensaje,
                alignment=ft.alignment.center_right,
                padding=ft.padding.only(left=50),
            )
        )
        self.historial_mensajes.append({"role": "user", "content": texto})
        if self.page:
            self.page.update()
    
    def _agregar_mensaje_asistente(self, texto):
        """Agrega un mensaje del asistente al chat"""
        mensaje = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.SMART_TOY, size=16, color=ft.Colors.BLUE_500),
                            ft.Text("Asistente", size=11, weight="bold", color=ft.Colors.BLUE_700),
                        ],
                        spacing=5,
                    ),
                    ft.Text(texto, size=13, selectable=True),
                ],
                spacing=3,
            ),
            bgcolor=ft.Colors.GREY_100,
            padding=10,
            border_radius=ft.border_radius.only(
                top_left=12,
                top_right=12,
                bottom_left=2,
                bottom_right=12,
            ),
        )
        
        self.lista_mensajes.controls.append(
            ft.Container(
                content=mensaje,
                alignment=ft.alignment.center_left,
                padding=ft.padding.only(right=50),
            )
        )
        self.historial_mensajes.append({"role": "assistant", "content": texto})
        if self.page:
            self.page.update()
    
    def _enviar_pregunta(self, e):
        """Envía la pregunta al modelo de IA"""
        pregunta = self.txt_pregunta.value.strip()
        
        if not pregunta:
            return
        
        if not self.documentos_analizados:
            self._agregar_mensaje_sistema(
                "⚠️ Por favor espera a que termine el análisis de documentos.",
                color=ft.Colors.ORANGE_600
            )
            return
        
        # Agregar mensaje del usuario
        self._agregar_mensaje_usuario(pregunta)
        
        # Limpiar campo de entrada
        self.txt_pregunta.value = ""
        if self.page:
            self.page.update()
        
        # Mostrar indicador de escritura
        self.indicador_escritura.visible = True
        if self.page:
            self.page.update()
        
        # Deshabilitar entrada mientras procesa
        self.txt_pregunta.disabled = True
        self.btn_enviar.disabled = True
        if self.page:
            self.page.update()
        
        # Procesar pregunta en hilo separado
        threading.Thread(
            target=self._procesar_pregunta,
            args=(pregunta,),
            daemon=True
        ).start()
    
    def _procesar_pregunta(self, pregunta):
        """Procesa la pregunta usando la API de Anthropic"""
        try:
            # Construir el prompt con contexto
            prompt_sistema = f"""Eres un asistente experto en licitaciones públicas españolas. 
            Tu tarea es ayudar al usuario a entender los detalles de una licitación específica.

            CONTEXTO DE LOS DOCUMENTOS:
            {self.contexto_documentos}

            INSTRUCCIONES:
            - Responde SOLO basándote en la información proporcionada en los documentos
            - Si no tienes información para responder, indícalo claramente
            - Sé conciso pero completo en tus respuestas
            - Usa un lenguaje claro y profesional
            - Si detectas información importante, destácala
            - Estructura tus respuestas con viñetas cuando sea apropiado"""

            # Construir historial de mensajes para el contexto
            mensajes = [{"role": "user", "content": prompt_sistema}]
            mensajes.extend(self.historial_mensajes[-10:])
            mensajes.append({"role": "user", "content": pregunta})
            
            # Llamar a la API de Anthropic
            import requests
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": mensajes,
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                respuesta = data["content"][0]["text"]
                self._mostrar_respuesta(respuesta)
            else:
                error_msg = f"Error en la API: {response.status_code}"
                self._mostrar_error(error_msg)
            
        except Exception as e:
            self._mostrar_error(str(e))
    
    def _mostrar_respuesta(self, respuesta):
        """Muestra la respuesta del asistente"""
        self.indicador_escritura.visible = False
        if self.page:
            self.page.update()
        
        self._agregar_mensaje_asistente(respuesta)
        
        # Rehabilitar entrada
        self.txt_pregunta.disabled = False
        self.btn_enviar.disabled = False
        if self.page:
            self.txt_pregunta.focus()
            self.page.update()
    
    def _mostrar_error(self, error):
        """Muestra un mensaje de error"""
        self.indicador_escritura.visible = False
        if self.page:
            self.page.update()
        
        self._agregar_mensaje_sistema(
            f"❌ Error al procesar la pregunta: {error}",
            color=ft.Colors.RED_600
        )
        
        # Rehabilitar entrada
        self.txt_pregunta.disabled = False
        self.btn_enviar.disabled = False
        if self.page:
            self.page.update()
    
    def _limpiar_chat(self, e):
        """Limpia el historial del chat"""
        self.lista_mensajes.controls.clear()
        self.historial_mensajes.clear()
        
        self._agregar_mensaje_sistema(
            "🧹 Chat limpiado. Puedes seguir haciendo preguntas sobre la licitación."
        )
    
    def _cerrar_drawer(self, e):
        """Cierra el drawer"""
        self.page.close(self)
        if self.on_close_callback:
            self.on_close_callback()


# ===============================================================
# FUNCIÓN HELPER: Abrir ChatBot desde cualquier parte de la app
# ===============================================================
def abrir_chatbot_licitacion(page: ft.Page, df_docs: pd.DataFrame, nombre_licitacion: str):
    """
    Función auxiliar para abrir el chatbot desde cualquier componente
    
    Args:
        page: Página de Flet
        df_docs: DataFrame con los documentos de la licitación
        nombre_licitacion: Nombre de la licitación para mostrar en el título
    """
    chatbot = ChatBotLicitacionDrawer(
        page=page,
        df_docs=df_docs,
        nombre_licitacion=nombre_licitacion
    )
    
    page.open(chatbot)
    page.update()


# ===============================================================
# COMPONENTE: Botón flotante para abrir el chatbot
# ===============================================================
class BotonChatbotFlotante(ft.Container):
    """
    Botón flotante que se puede usar en cualquier página para acceder
    rápidamente al chatbot cuando hay una licitación seleccionada
    """
    def __init__(self, page: ft.Page):
        super().__init__()
        # self.page = page
        self._docs_actuales = None
        self.nombre_licitacion = None
        self.drawer_abierto = False
        self.drawer_actual = None
        
        self._build_ui()
    
    def _build_ui(self):
        self.btn_flotante = ft.FloatingActionButton(
            icon=ft.Icons.CHAT,
            bgcolor=ft.Colors.BLUE_600,
            on_click=self._toggle_chat,
            tooltip="Consultar con IA sobre la licitación",
            mini=False,
        )
        
        self.content = self.btn_flotante
        self.visible = False
        self.right = 20
        self.bottom = 20
    
    def activar(self, df_docs, nombre_licitacion):
        """
        Activa el botón con los documentos de una licitación específica
        
        Args:
            df_docs: DataFrame con los documentos
            nombre_licitacion: Nombre de la licitación
        """
        self._docs_actuales = df_docs
        self.nombre_licitacion = nombre_licitacion
        self.visible = True
        if self.page:
            self.page.update()
    
    def desactivar(self):
        """Desactiva y oculta el botón"""
        if self.drawer_abierto and self.drawer_actual:
            self.page.close(self.drawer_actual)
        
        self.visible = False
        self._docs_actuales = None
        self.nombre_licitacion = None
        self.drawer_abierto = False
        self.drawer_actual = None
        if self.page:
            self.page.update()
    
    def _toggle_chat(self, e):
        """Abre o cierra el drawer según su estado actual"""
        if self.drawer_abierto and self.drawer_actual:
            # Cerrar drawer
            self.page.close(self.drawer_actual)
            self.drawer_abierto = False
            self.drawer_actual = None
            self.btn_flotante.bgcolor = ft.Colors.BLUE_600
        else:
            # Abrir drawer
            if self._docs_actuales is not None:
                self._abrir_chat()
        
        if self.page:
            self.page.update()
    
    def _abrir_chat(self):
        """Abre el chatbot drawer"""
        self.drawer_actual = ChatBotLicitacionDrawer(
            page=self.page,
            df_docs=self._docs_actuales,
            nombre_licitacion=self.nombre_licitacion,
            on_close_callback=self._on_drawer_closed
        )
        
        self.page.open(self.drawer_actual)
        self.drawer_abierto = True
        self.btn_flotante.bgcolor = ft.Colors.PURPLE_600
        if self.page:
            self.page.update()
    
    def _on_drawer_closed(self):
        """Callback cuando el drawer se cierra"""
        self.drawer_abierto = False
        self.drawer_actual = None
        self.btn_flotante.bgcolor = ft.Colors.BLUE_600
        if self.page:
            self.page.update()
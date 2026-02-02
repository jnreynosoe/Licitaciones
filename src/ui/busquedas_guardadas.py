# import flet as ft
# import json
# import os
# from datetime import datetime

# # ===============================================================
# # COMPONENTE: Diálogo para guardar una búsqueda
# # ===============================================================
# class DialogoGuardarBusqueda(ft.AlertDialog):
#     def __init__(self, filtros, on_guardar):
#         super().__init__()
#         self.filtros = filtros
#         self.on_guardar = on_guardar
#         self._build_ui()

#     def _build_ui(self):
#         self.txt_nombre = ft.TextField(
#             label="Nombre de la búsqueda",
#             hint_text="Ej. Licitaciones de tecnología Madrid",
#             width=400,
#             autofocus=True
#         )

#         self.txt_descripcion = ft.TextField(
#             label="Descripción (opcional)",
#             multiline=True,
#             min_lines=2,
#             width=400
#         )

#         self.txt_categoria = ft.TextField(
#             label="Categoría (opcional)",
#             hint_text="Ej. Tecnología, Construcción, Servicios...",
#             width=400
#         )

#         self.title = ft.Text("💾 Guardar búsqueda actual", size=18, weight="bold")

#         self.content = ft.Container(
#             ft.Column(
#                 [
#                     self.txt_nombre,
#                     self.txt_categoria,
#                     self.txt_descripcion,
#                 ],
#                 spacing=10
#             ),
#             width=420
#         )

#         self.actions = [
#             ft.TextButton("Cancelar", on_click=self._cancelar),
#             ft.ElevatedButton(
#                 "Guardar",
#                 icon=ft.Icons.SAVE,
#                 on_click=self._guardar,
#                 style=ft.ButtonStyle(
#                     bgcolor=ft.Colors.BLUE_500,
#                     color=ft.Colors.WHITE
#                 )
#             )
#         ]

#     def _guardar(self, e):
#         nombre = self.txt_nombre.value.strip()
#         if not nombre:
#             self.txt_nombre.error_text = "El nombre es obligatorio"
#             self.txt_nombre.update()
#             return

#         busqueda = {
#             "nombre": nombre,
#             "descripcion": self.txt_descripcion.value.strip(),
#             "categoria": self.txt_categoria.value.strip(),
#             "filtros": self.filtros,
#             "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
#         }

#         self.on_guardar(busqueda)
#         self.open = False
#         self.update()

#     def _cancelar(self, e):
#         self.open = False
#         self.update()


# # ===============================================================
# # COMPONENTE: Gestor de búsquedas guardadas
# # ===============================================================
# class GestorBusquedas:
#     def __init__(self, archivo="busquedas_guardadas.json"):
#         self.archivo = archivo
#         self.busquedas = self._cargar()

#     def _cargar(self):
#         if os.path.exists(self.archivo):
#             with open(self.archivo, "r", encoding="utf-8") as f:
#                 return json.load(f)
#         return []

#     def guardar_busqueda(self, busqueda):
#         # Evitar duplicados por nombre
#         for i, b in enumerate(self.busquedas):
#             if b["nombre"].lower() == busqueda["nombre"].lower():
#                 self.busquedas[i] = busqueda
#                 break
#         else:
#             self.busquedas.append(busqueda)
#         self._guardar_archivo()

#     def eliminar_busqueda(self, nombre):
#         self.busquedas = [b for b in self.busquedas if b["nombre"] != nombre]
#         self._guardar_archivo()

#     def _guardar_archivo(self):
#         with open(self.archivo, "w", encoding="utf-8") as f:
#             json.dump(self.busquedas, f, ensure_ascii=False, indent=2)

#     def obtener_busquedas(self):
#         return self.busquedas


# # ===============================================================
# # COMPONENTE: Panel de búsquedas guardadas
# # ===============================================================
# class PanelBusquedasGuardadas(ft.Container):
#     def __init__(self, gestor: GestorBusquedas, on_aplicar, on_eliminar):
#         super().__init__()
#         self.gestor = gestor
#         self.on_aplicar = on_aplicar
#         self.on_eliminar = on_eliminar
#         self._build_ui()

#     def _build_ui(self):
#         self.lista = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
#         self.actualizar_lista()

#         self.content = ft.Column(
#             [
#                 ft.Text("🔖 Búsquedas guardadas", size=16, weight="bold"),
#                 self.lista
#             ],
#             spacing=10
#         )

#     def actualizar_lista(self):
#         self.lista.controls.clear()
#         busquedas = self.gestor.obtener_busquedas()

#         if not busquedas:
#             self.lista.controls.append(
#                 ft.Text("No hay búsquedas guardadas", color=ft.Colors.GREY_600)
#             )
#         else:
#             for busq in busquedas:
#                 self.lista.controls.append(
#                     self._crear_tarjeta(busq)
#                 )
#         self.update()

#     def _crear_tarjeta(self, busqueda):
#         return ft.Container(
#             content=ft.Row(
#                 [
#                     ft.Column(
#                         [
#                             ft.Text(busqueda["nombre"], weight="bold"),
#                             ft.Text(
#                                 f"{busqueda.get('categoria', '')} — {busqueda['fecha']}",
#                                 size=12,
#                                 color=ft.Colors.GREY_600
#                             ),
#                         ],
#                         expand=True
#                     ),
#                     ft.IconButton(
#                         icon=ft.Icons.PLAY_ARROW,
#                         tooltip="Aplicar búsqueda",
#                         on_click=lambda e, b=busqueda: self.on_aplicar(b)
#                     ),
#                     ft.IconButton(
#                         icon=ft.Icons.DELETE,
#                         tooltip="Eliminar",
#                         icon_color=ft.Colors.RED_400,
#                         on_click=lambda e, b=busqueda: self._confirmar_eliminar(b)
#                     ),
#                 ],
#                 alignment=ft.MainAxisAlignment.SPACE_BETWEEN
#             ),
#             border=ft.Border.all(1, ft.Colors.GREY_300),
#             border_radius=8,
#             padding=10
#         )

#     def _confirmar_eliminar(self, busqueda):
#         self.on_eliminar(busqueda)
#         self.actualizar_lista()

# import flet as ft
# import json
# import os
# from datetime import datetime

# # ===============================================================
# # COMPONENTE: Diálogo mejorado para guardar una búsqueda
# # ===============================================================
# class DialogoGuardarBusqueda(ft.AlertDialog):
#     def __init__(self, filtros, on_guardar):
#         super().__init__()
#         self.filtros = filtros
#         self.on_guardar = on_guardar
#         self._build_ui()

#     def _build_ui(self):
#         # Campos de entrada
#         self.txt_nombre = ft.TextField(
#             label="Nombre de la búsqueda",
#             hint_text="Ej. Licitaciones de tecnología Madrid",
#             width=500,
#             autofocus=True
#         )

#         self.txt_descripcion = ft.TextField(
#             label="Descripción (opcional)",
#             multiline=True,
#             min_lines=2,
#             width=500
#         )

#         self.txt_categoria = ft.TextField(
#             label="Categoría (opcional)",
#             hint_text="Ej. Tecnología, Construcción, Servicios...",
#             width=500
#         )

#         # Crear resumen visual de filtros
#         resumen_filtros = self._crear_resumen_filtros()

#         self.title = ft.Text("💾 Guardar búsqueda actual", size=18, weight="bold")

#         self.content = ft.Container(
#             ft.Column(
#                 [
#                     ft.Text("📋 Resumen de filtros a guardar:", 
#                            size=14, weight="bold", 
#                            color=ft.Colors.BLUE_700),
#                     resumen_filtros,
#                     ft.Divider(),
#                     self.txt_nombre,
#                     self.txt_categoria,
#                     self.txt_descripcion,
#                 ],
#                 spacing=10,
#                 scroll=ft.ScrollMode.AUTO,
#             ),
#             width=550,
#             height=500,
#         )

#         self.actions = [
#             ft.TextButton("Cancelar", on_click=self._cancelar),
#             ft.ElevatedButton(
#                 "Guardar",
#                 icon=ft.Icons.SAVE,
#                 on_click=self._guardar,
#                 style=ft.ButtonStyle(
#                     bgcolor=ft.Colors.BLUE_500,
#                     color=ft.Colors.WHITE
#                 )
#             )
#         ]

#     def _crear_resumen_filtros(self):
#         """Crea un resumen visual de los filtros actuales"""
#         items = []

#         # CPVs
#         if self.filtros.get("cpv"):
#             cpv_text = f"📦 CPVs seleccionados: {len(self.filtros['cpv'])}"
#             items.append(ft.Text(cpv_text, size=13, weight="bold"))
#             for cpv in self.filtros["cpv"][:3]:  # Mostrar solo los primeros 3
#                 items.append(ft.Text(f"  • {cpv}", size=12, color=ft.Colors.GREY_700))
#             if len(self.filtros["cpv"]) > 3:
#                 items.append(ft.Text(
#                     f"  ... y {len(self.filtros['cpv']) - 3} más",
#                     size=12,
#                     color=ft.Colors.GREY_600,
#                     italic=True
#                 ))

#         # Lugar
#         if self.filtros.get("lugar"):
#             items.append(ft.Text(
#                 f"📍 Lugar: {self.filtros['lugar']}", 
#                 size=13, 
#                 weight="bold"
#             ))

#         # Entidades
#         if self.filtros.get("entidades"):
#             ent_text = f"🏢 Entidades: {', '.join(self.filtros['entidades'])}"
#             items.append(ft.Text(ent_text, size=13, weight="bold"))

#         # Importe
#         importe_min = self.filtros.get("importe_min", 0)
#         importe_max = self.filtros.get("importe_max", 1_000_000)
#         if importe_min > 0 or importe_max < 1_000_000:
#             items.append(ft.Text(
#                 f"💰 Importe: {importe_min:,.0f} € - {importe_max:,.0f} €",
#                 size=13,
#                 weight="bold"
#             ))

#         if not items:
#             items.append(ft.Text(
#                 "⚠️ No hay filtros aplicados",
#                 color=ft.Colors.ORANGE_600
#             ))

#         return ft.Container(
#             content=ft.Column(items, spacing=5),
#             bgcolor=ft.Colors.GREY_100,
#             padding=15,
#             border_radius=8,
#             border=ft.Border.all(1, ft.Colors.GREY_300),
#         )

#     def _guardar(self, e):
#         nombre = self.txt_nombre.value.strip()
#         if not nombre:
#             self.txt_nombre.error_text = "El nombre es obligatorio"
#             self.txt_nombre.update()
#             return

#         busqueda = {
#             "nombre": nombre,
#             "descripcion": self.txt_descripcion.value.strip(),
#             "categoria": self.txt_categoria.value.strip(),
#             "filtros": self.filtros,
#             "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
#         }

#         self.on_guardar(busqueda)
#         self.open = False
#         self.update()

#     def _cancelar(self, e):
#         self.open = False
#         self.update()


# # ===============================================================
# # COMPONENTE: Gestor de búsquedas guardadas
# # ===============================================================
# class GestorBusquedas:
#     def __init__(self, archivo="busquedas_guardadas.json"):
#         self.archivo = archivo
#         self.busquedas = self._cargar()

#     def _cargar(self):
#         if os.path.exists(self.archivo):
#             try:
#                 with open(self.archivo, "r", encoding="utf-8") as f:
#                     return json.load(f)
#             except json.JSONDecodeError:
#                 return []
#         return []

#     def guardar_busqueda(self, busqueda):
#         # Evitar duplicados por nombre
#         for i, b in enumerate(self.busquedas):
#             if b["nombre"].lower() == busqueda["nombre"].lower():
#                 self.busquedas[i] = busqueda
#                 break
#         else:
#             self.busquedas.append(busqueda)
#         self._guardar_archivo()

#     def eliminar_busqueda(self, nombre):
#         self.busquedas = [b for b in self.busquedas if b["nombre"] != nombre]
#         self._guardar_archivo()

#     def _guardar_archivo(self):
#         with open(self.archivo, "w", encoding="utf-8") as f:
#             json.dump(self.busquedas, f, ensure_ascii=False, indent=2)

#     def obtener_busquedas(self):
#         return self.busquedas


# # ===============================================================
# # COMPONENTE: Panel de búsquedas guardadas
# # ===============================================================
# class PanelBusquedasGuardadas(ft.Container):
#     def __init__(self, gestor: GestorBusquedas, on_aplicar, on_eliminar):
#         super().__init__()
#         self.gestor = gestor
#         self.on_aplicar = on_aplicar
#         self.on_eliminar = on_eliminar
#         self._build_ui()

#     def _build_ui(self):
#         self.lista = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
#         self._cargar_lista_inicial()  # Cargar sin llamar a update()

#         self.content = ft.Column(
#             [
#                 ft.Text("🔖 Búsquedas guardadas", size=16, weight="bold"),
#                 ft.Divider(),
#                 self.lista
#             ],
#             spacing=10
#         )
    
#     def _cargar_lista_inicial(self):
#         """Carga la lista inicial sin llamar a update()"""
#         self.lista.controls.clear()
#         busquedas = self.gestor.obtener_busquedas()

#         if not busquedas:
#             self.lista.controls.append(
#                 ft.Container(
#                     content=ft.Text(
#                         "No hay búsquedas guardadas.\nGuarda tus filtros para acceder rápidamente.",
#                         color=ft.Colors.GREY_600,
#                         text_align=ft.TextAlign.CENTER,
#                         size=12,
#                     ),
#                     alignment=ft.alignment.center,
#                     padding=20,
#                 )
#             )
#         else:
#             for busq in busquedas:
#                 self.lista.controls.append(
#                     self._crear_tarjeta(busq)
#                 )

#     def actualizar_lista(self):
#         """Actualiza la lista después de que el componente esté en la página"""
#         self._cargar_lista_inicial()
#         # Solo llamar a update() si ya está en la página
#         if self.page:
#             self.update()

#     def _crear_tarjeta(self, busqueda):
#         # Crear resumen de filtros
#         filtros = busqueda.get("filtros", {})
#         detalles = []
        
#         if filtros.get("cpv"):
#             detalles.append(f"{len(filtros['cpv'])} CPVs")
#         if filtros.get("lugar"):
#             detalles.append(filtros["lugar"])
#         if filtros.get("entidades"):
#             detalles.append(f"{len(filtros['entidades'])} entidades")
        
#         detalle_text = " • ".join(detalles) if detalles else "Sin filtros específicos"

#         return ft.Container(
#             content=ft.Column(
#                 [
#                     ft.Row(
#                         [
#                             ft.Column(
#                                 [
#                                     ft.Text(
#                                         busqueda["nombre"], 
#                                         weight="bold",
#                                         size=14,
#                                     ),
#                                     ft.Text(
#                                         detalle_text,
#                                         size=11,
#                                         color=ft.Colors.GREY_600,
#                                     ),
#                                 ],
#                                 expand=True,
#                                 spacing=2,
#                             ),
#                             ft.Row(
#                                 [
#                                     ft.IconButton(
#                                         icon=ft.Icons.PLAY_ARROW,
#                                         tooltip="Aplicar búsqueda",
#                                         icon_size=20,
#                                         icon_color=ft.Colors.BLUE_600,
#                                         on_click=lambda e, b=busqueda: self.on_aplicar(b)
#                                     ),
#                                     ft.IconButton(
#                                         icon=ft.Icons.DELETE_OUTLINE,
#                                         tooltip="Eliminar",
#                                         icon_size=20,
#                                         icon_color=ft.Colors.RED_400,
#                                         on_click=lambda e, b=busqueda: self._confirmar_eliminar(b)
#                                     ),
#                                 ],
#                                 spacing=0,
#                             ),
#                         ],
#                         alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#                     ),
#                     # Categoría y fecha
#                     ft.Row(
#                         [
#                             ft.Container(
#                                 content=ft.Text(
#                                     busqueda.get("categoria", "Sin categoría"),
#                                     size=10,
#                                     color=ft.Colors.BLUE_700,
#                                 ),
#                                 bgcolor=ft.Colors.BLUE_50,
#                                 padding=ft.padding.symmetric(horizontal=8, vertical=2),
#                                 border_radius=4,
#                             ) if busqueda.get("categoria") else ft.Container(),
#                             ft.Text(
#                                 busqueda.get("fecha", ""),
#                                 size=10,
#                                 color=ft.Colors.GREY_500,
#                             ),
#                         ],
#                         spacing=5,
#                     ),
#                 ],
#                 spacing=5,
#             ),
#             border=ft.Border.all(1, ft.Colors.GREY_300),
#             border_radius=8,
#             padding=12,
#             bgcolor=ft.Colors.WHITE,
#             ink=True,
#         )

#     def _confirmar_eliminar(self, busqueda):
#         self.on_eliminar(busqueda)
#         self.actualizar_lista()
##---------------------------------------------------------------------------------------------

# import flet as ft
# import json
# import os
# from datetime import datetime

# # ===============================================================
# # COMPONENTE: Diálogo mejorado para guardar una búsqueda
# # ===============================================================
# class DialogoGuardarBusqueda(ft.AlertDialog):
#     def __init__(self, filtros, on_guardar):
#         super().__init__()
#         self.filtros = filtros
#         self.on_guardar = on_guardar
#         self._build_ui()

#     def _build_ui(self):
#         # Campos de entrada
#         self.txt_nombre = ft.TextField(
#             label="Nombre de la búsqueda",
#             hint_text="Ej. Licitaciones de tecnología Madrid",
#             width=500,
#             autofocus=True
#         )

#         self.txt_descripcion = ft.TextField(
#             label="Descripción (opcional)",
#             multiline=True,
#             min_lines=2,
#             width=500
#         )

#         self.txt_categoria = ft.TextField(
#             label="Categoría (opcional)",
#             hint_text="Ej. Tecnología, Construcción, Servicios...",
#             width=500
#         )

#         # Crear resumen visual de filtros
#         resumen_filtros = self._crear_resumen_filtros()

#         self.title = ft.Text("💾 Guardar búsqueda actual", size=18, weight="bold")

#         self.content = ft.Container(
#             ft.Column(
#                 [
#                     ft.Text("📋 Resumen de filtros a guardar:", 
#                            size=14, weight="bold", 
#                            color=ft.Colors.BLUE_700),
#                     resumen_filtros,
#                     ft.Divider(),
#                     self.txt_nombre,
#                     self.txt_categoria,
#                     self.txt_descripcion,
#                 ],
#                 spacing=10,
#                 scroll=ft.ScrollMode.AUTO,
#             ),
#             width=550,
#             height=500,
#         )

#         self.actions = [
#             ft.TextButton("Cancelar", on_click=self._cancelar),
#             ft.ElevatedButton(
#                 "Guardar",
#                 icon=ft.Icons.SAVE,
#                 on_click=self._guardar,
#                 style=ft.ButtonStyle(
#                     bgcolor=ft.Colors.BLUE_500,
#                     color=ft.Colors.WHITE
#                 )
#             )
#         ]

#     def _crear_resumen_filtros(self):
#         """Crea un resumen visual de los filtros actuales"""
#         items = []

#         # CPVs
#         if self.filtros.get("cpv"):
#             cpv_text = f"📦 CPVs seleccionados: {len(self.filtros['cpv'])}"
#             items.append(ft.Text(cpv_text, size=13, weight="bold"))
#             for cpv in self.filtros["cpv"][:3]:  # Mostrar solo los primeros 3
#                 items.append(ft.Text(f"  • {cpv}", size=12, color=ft.Colors.GREY_700))
#             if len(self.filtros["cpv"]) > 3:
#                 items.append(ft.Text(
#                     f"  ... y {len(self.filtros['cpv']) - 3} más",
#                     size=12,
#                     color=ft.Colors.GREY_600,
#                     italic=True
#                 ))

#         # Lugar
#         if self.filtros.get("lugar"):
#             items.append(ft.Text(
#                 f"📍 Lugar: {self.filtros['lugar']}", 
#                 size=13, 
#                 weight="bold"
#             ))

#         # Entidades
#         if self.filtros.get("entidades"):
#             ent_text = f"🏢 Entidades: {', '.join(self.filtros['entidades'])}"
#             items.append(ft.Text(ent_text, size=13, weight="bold"))

#         # Importe
#         importe_min = self.filtros.get("importe_min", 0)
#         importe_max = self.filtros.get("importe_max", 1_000_000)
#         if importe_min > 0 or importe_max < 1_000_000:
#             items.append(ft.Text(
#                 f"💰 Importe: {importe_min:,.0f} € - {importe_max:,.0f} €",
#                 size=13,
#                 weight="bold"
#             ))

#         if not items:
#             items.append(ft.Text(
#                 "⚠️ No hay filtros aplicados",
#                 color=ft.Colors.ORANGE_600
#             ))

#         return ft.Container(
#             content=ft.Column(items, spacing=5),
#             bgcolor=ft.Colors.GREY_100,
#             padding=15,
#             border_radius=8,
#             border=ft.Border.all(1, ft.Colors.GREY_300),
#         )

#     def _guardar(self, e):
#         nombre = self.txt_nombre.value.strip()
#         if not nombre:
#             self.txt_nombre.error_text = "El nombre es obligatorio"
#             self.txt_nombre.update()
#             return

#         busqueda = {
#             "nombre": nombre,
#             "descripcion": self.txt_descripcion.value.strip(),
#             "categoria": self.txt_categoria.value.strip(),
#             "filtros": self.filtros,
#             "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
#         }

#         self.on_guardar(busqueda)
#         self.open = False
#         self.update()

#     def _cancelar(self, e):
#         self.open = False
#         self.update()


# # ===============================================================
# # COMPONENTE: Diálogo para EDITAR una búsqueda guardada
# # ===============================================================
# class DialogoEditarBusqueda(ft.AlertDialog):
#     def __init__(self, busqueda, on_guardar, df_cpv, lugares, entidades):
#         super().__init__()
#         self.busqueda = busqueda
#         self.on_guardar = on_guardar
#         self.df_cpv = df_cpv
#         self.lugares = lugares
#         self.entidades = entidades
#         self.filtros_editados = busqueda["filtros"].copy()
#         self._build_ui()

#     def _build_ui(self):
#         # Campos de metadatos
#         self.txt_nombre = ft.TextField(
#             label="Nombre de la búsqueda",
#             value=self.busqueda["nombre"],
#             width=600,
#         )

#         self.txt_descripcion = ft.TextField(
#             label="Descripción",
#             value=self.busqueda.get("descripcion", ""),
#             multiline=True,
#             min_lines=2,
#             width=600,
#         )

#         self.txt_categoria = ft.TextField(
#             label="Categoría",
#             value=self.busqueda.get("categoria", ""),
#             width=600,
#         )

#         # Sección de edición de filtros
#         self.cpv_seleccionados = self.filtros_editados.get("cpv", []).copy()
#         self.chips_cpv = ft.Row(wrap=True, spacing=5, scroll="auto")
#         self._actualizar_chips_cpv()

#         # Buscador de CPV
#         self.txt_buscar_cpv = ft.TextField(
#             label="Buscar y añadir CPVs",
#             hint_text="Mínimo 4 caracteres",
#             width=600,
#             on_change=self._buscar_cpv,
#         )
#         self.lista_cpv = ft.ListView(height=150, spacing=3)

#         # Dropdown de lugar
#         self.dd_lugar = ft.Dropdown(
#             label="Lugar de ejecución",
#             options=[ft.dropdown.Option(l) for l in self.lugares],
#             value=self.filtros_editados.get("lugar"),
#             width=600,
#         )

#         # Checkboxes de entidades
#         self.checks_entidades = []
#         entidades_seleccionadas = self.filtros_editados.get("entidades", [])
#         for ent in self.entidades:
#             check = ft.Checkbox(
#                 label=ent,
#                 value=ent in entidades_seleccionadas
#             )
#             self.checks_entidades.append(check)

#         # Slider de importe
#         self.slider_importe = ft.RangeSlider(
#             min=0,
#             max=1_000_000,
#             divisions=100,
#             start_value=self.filtros_editados.get("importe_min", 0),
#             end_value=self.filtros_editados.get("importe_max", 1_000_000),
#             label="{value} €",
#             width=600,
#         )

#         self.title = ft.Text("✏️ Editar búsqueda guardada", size=18, weight="bold")

#         self.content = ft.Container(
#             ft.Column(
#                 [
#                     ft.Text("📝 Información general", size=14, weight="bold"),
#                     self.txt_nombre,
#                     self.txt_categoria,
#                     self.txt_descripcion,
                    
#                     ft.Divider(height=20),
                    
#                     ft.Text("🔧 Editar filtros", size=14, weight="bold"),
                    
#                     # CPVs
#                     ft.Text("📦 Códigos CPV", size=13, weight="bold"),
#                     self.chips_cpv,
#                     self.txt_buscar_cpv,
#                     self.lista_cpv,
                    
#                     ft.Divider(),
                    
#                     # Lugar
#                     ft.Text("📍 Lugar de ejecución", size=13, weight="bold"),
#                     self.dd_lugar,
                    
#                     ft.Divider(),
                    
#                     # Entidades
#                     ft.Text("🏢 Entidades", size=13, weight="bold"),
#                     ft.Row(self.checks_entidades, wrap=True),
                    
#                     ft.Divider(),
                    
#                     # Importe
#                     ft.Text("💰 Rango de importe", size=13, weight="bold"),
#                     self.slider_importe,
#                     ft.Row(
#                         [
#                             ft.Text("0 €"),
#                             ft.Text("1.000.000 €"),
#                         ],
#                         alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#                     ),
#                 ],
#                 spacing=10,
#                 scroll=ft.ScrollMode.AUTO,
#             ),
#             width=650,
#             height=600,
#         )

#         self.actions = [
#             ft.TextButton("Cancelar", on_click=self._cancelar),
#             ft.ElevatedButton(
#                 "Guardar cambios",
#                 icon=ft.Icons.SAVE,
#                 on_click=self._guardar,
#                 style=ft.ButtonStyle(
#                     bgcolor=ft.Colors.GREEN_500,
#                     color=ft.Colors.WHITE
#                 )
#             )
#         ]

#     def _actualizar_chips_cpv(self):
#         self.chips_cpv.controls.clear()
#         if not self.cpv_seleccionados:
#             self.chips_cpv.controls.append(
#                 ft.Text("No hay CPVs seleccionados", color=ft.Colors.GREY_600, size=12)
#             )
#         else:
#             for cpv in self.cpv_seleccionados:
#                 self.chips_cpv.controls.append(
#                     ft.Chip(
#                         label=ft.Text(cpv, size=11),
#                         on_delete=lambda e, c=cpv: self._eliminar_cpv(c)
#                     )
#                 )

#     def _eliminar_cpv(self, cpv):
#         if cpv in self.cpv_seleccionados:
#             self.cpv_seleccionados.remove(cpv)
#             self._actualizar_chips_cpv()
#             self.chips_cpv.update()

#     def _buscar_cpv(self, e):
#         texto = e.control.value.lower().strip()
#         self.lista_cpv.controls.clear()

#         if len(texto) < 4:
#             self.lista_cpv.controls.append(
#                 ft.Text("🔎 Escribe al menos 4 caracteres", size=12)
#             )
#         else:
#             opciones = [f"{row.codigo} - {row.descripcion}" for _, row in self.df_cpv.iterrows()]
#             coincidencias = [op for op in opciones if texto in op.lower()]
            
#             if coincidencias:
#                 for op in coincidencias[:30]:
#                     self.lista_cpv.controls.append(
#                         ft.TextButton(
#                             op,
#                             on_click=lambda e, o=op: self._agregar_cpv(o)
#                         )
#                     )
#             else:
#                 self.lista_cpv.controls.append(
#                     ft.Text("⚠️ No hay coincidencias", color=ft.Colors.RED_400)
#                 )
        
#         self.lista_cpv.update()

#     def _agregar_cpv(self, cpv):
#         if cpv not in self.cpv_seleccionados:
#             self.cpv_seleccionados.append(cpv)
#             self._actualizar_chips_cpv()
#             self.chips_cpv.update()

#     def _guardar(self, e):
#         nombre = self.txt_nombre.value.strip()
#         if not nombre:
#             self.txt_nombre.error_text = "El nombre es obligatorio"
#             self.txt_nombre.update()
#             return

#         # Actualizar filtros editados
#         entidades_seleccionadas = [c.label for c in self.checks_entidades if c.value]
        
#         busqueda_actualizada = {
#             "nombre": nombre,
#             "descripcion": self.txt_descripcion.value.strip(),
#             "categoria": self.txt_categoria.value.strip(),
#             "filtros": {
#                 "cpv": self.cpv_seleccionados,
#                 "lugar": self.dd_lugar.value,
#                 "importe_min": self.slider_importe.start_value,
#                 "importe_max": self.slider_importe.end_value,
#                 "entidades": entidades_seleccionadas,
#             },
#             "fecha": self.busqueda.get("fecha"),  # Mantener fecha original
#             "fecha_modificacion": datetime.now().strftime("%Y-%m-%d %H:%M")
#         }

#         self.on_guardar(busqueda_actualizada)
#         self.open = False
#         self.update()

#     def _cancelar(self, e):
#         self.open = False
#         self.update()


# # ===============================================================
# # COMPONENTE: Gestor de búsquedas guardadas
# # ===============================================================
# class GestorBusquedas:
#     def __init__(self, archivo="busquedas_guardadas.json"):
#         self.archivo = archivo
#         self.busquedas = self._cargar()

#     def _cargar(self):
#         if os.path.exists(self.archivo):
#             try:
#                 with open(self.archivo, "r", encoding="utf-8") as f:
#                     return json.load(f)
#             except json.JSONDecodeError:
#                 return []
#         return []

#     def guardar_busqueda(self, busqueda):
#         # Evitar duplicados por nombre
#         for i, b in enumerate(self.busquedas):
#             if b["nombre"].lower() == busqueda["nombre"].lower():
#                 self.busquedas[i] = busqueda
#                 break
#         else:
#             self.busquedas.append(busqueda)
#         self._guardar_archivo()

#     def eliminar_busqueda(self, nombre):
#         self.busquedas = [b for b in self.busquedas if b["nombre"] != nombre]
#         self._guardar_archivo()

#     def _guardar_archivo(self):
#         with open(self.archivo, "w", encoding="utf-8") as f:
#             json.dump(self.busquedas, f, ensure_ascii=False, indent=2)

#     def obtener_busquedas(self):
#         return self.busquedas


# # ===============================================================
# # COMPONENTE: Panel de búsquedas guardadas
# # ===============================================================
# class PanelBusquedasGuardadas(ft.Container):
#     def __init__(self, gestor: GestorBusquedas, on_aplicar, on_eliminar, on_editar=None):
#         super().__init__()
#         self.gestor = gestor
#         self.on_aplicar = on_aplicar
#         self.on_eliminar = on_eliminar
#         self.on_editar = on_editar
#         self._build_ui()

#     def _build_ui(self):
#         self.lista = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
#         self._cargar_lista_inicial()

#         self.content = ft.Column(
#             [
#                 ft.Text("🔖 Búsquedas guardadas", size=16, weight="bold"),
#                 ft.Divider(),
#                 self.lista
#             ],
#             spacing=10
#         )
    
#     def _cargar_lista_inicial(self):
#         """Carga la lista inicial sin llamar a update()"""
#         self.lista.controls.clear()
#         busquedas = self.gestor.obtener_busquedas()

#         if not busquedas:
#             self.lista.controls.append(
#                 ft.Container(
#                     content=ft.Text(
#                         "No hay búsquedas guardadas.\nGuarda tus filtros para acceder rápidamente.",
#                         color=ft.Colors.GREY_600,
#                         text_align=ft.TextAlign.CENTER,
#                         size=12,
#                     ),
#                     alignment=ft.alignment.center,
#                     padding=20,
#                 )
#             )
#         else:
#             for busq in busquedas:
#                 self.lista.controls.append(
#                     self._crear_tarjeta(busq)
#                 )

#     def actualizar_lista(self):
#         """Actualiza la lista después de que el componente esté en la página"""
#         self._cargar_lista_inicial()
#         if self.page:
#             self.update()

#     def _crear_tarjeta(self, busqueda):
#         # Crear resumen de filtros
#         filtros = busqueda.get("filtros", {})
#         detalles = []
        
#         if filtros.get("cpv"):
#             detalles.append(f"{len(filtros['cpv'])} CPVs")
#         if filtros.get("lugar"):
#             detalles.append(filtros["lugar"])
#         if filtros.get("entidades"):
#             detalles.append(f"{len(filtros['entidades'])} entidades")
        
#         detalle_text = " • ".join(detalles) if detalles else "Sin filtros específicos"

#         # Mostrar fecha de modificación si existe
#         fecha_mostrar = busqueda.get("fecha_modificacion", busqueda.get("fecha", ""))
#         fecha_texto = f"Editado: {fecha_mostrar}" if "fecha_modificacion" in busqueda else fecha_mostrar

#         return ft.Container(
#             content=ft.Column(
#                 [
#                     ft.Row(
#                         [
#                             ft.Column(
#                                 [
#                                     ft.Text(
#                                         busqueda["nombre"], 
#                                         weight="bold",
#                                         size=14,
#                                     ),
#                                     ft.Text(
#                                         detalle_text,
#                                         size=11,
#                                         color=ft.Colors.GREY_600,
#                                     ),
#                                 ],
#                                 expand=True,
#                                 spacing=2,
#                             ),
#                             ft.Row(
#                                 [
#                                     ft.IconButton(
#                                         icon=ft.Icons.PLAY_ARROW,
#                                         tooltip="Aplicar búsqueda",
#                                         icon_size=20,
#                                         icon_color=ft.Colors.BLUE_600,
#                                         on_click=lambda e, b=busqueda: self.on_aplicar(b)
#                                     ),
#                                     ft.IconButton(
#                                         icon=ft.Icons.EDIT_OUTLINED,
#                                         tooltip="Editar búsqueda",
#                                         icon_size=20,
#                                         icon_color=ft.Colors.ORANGE_600,
#                                         on_click=lambda e, b=busqueda: self._editar_busqueda(b)
#                                     ) if self.on_editar else ft.Container(),
#                                     ft.IconButton(
#                                         icon=ft.Icons.DELETE_OUTLINE,
#                                         tooltip="Eliminar",
#                                         icon_size=20,
#                                         icon_color=ft.Colors.RED_400,
#                                         on_click=lambda e, b=busqueda: self._confirmar_eliminar(b)
#                                     ),
#                                 ],
#                                 spacing=0,
#                             ),
#                         ],
#                         alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#                     ),
#                     # Categoría y fecha
#                     ft.Row(
#                         [
#                             ft.Container(
#                                 content=ft.Text(
#                                     busqueda.get("categoria", "Sin categoría"),
#                                     size=10,
#                                     color=ft.Colors.BLUE_700,
#                                 ),
#                                 bgcolor=ft.Colors.BLUE_50,
#                                 padding=ft.padding.symmetric(horizontal=8, vertical=2),
#                                 border_radius=4,
#                             ) if busqueda.get("categoria") else ft.Container(),
#                             ft.Text(
#                                 fecha_texto,
#                                 size=10,
#                                 color=ft.Colors.GREY_500,
#                             ),
#                         ],
#                         spacing=5,
#                     ),
#                 ],
#                 spacing=5,
#             ),
#             border=ft.Border.all(1, ft.Colors.GREY_300),
#             border_radius=8,
#             padding=12,
#             bgcolor=ft.Colors.WHITE,
#             ink=True,
#         )

#     def _editar_busqueda(self, busqueda):
#         if self.on_editar:
#             self.on_editar(busqueda)

#     def _confirmar_eliminar(self, busqueda):
#         self.on_eliminar(busqueda)
#         self.actualizar_lista()
##---------------------------------------------------------------------------------------------
import flet as ft
import json
import os
from datetime import datetime

class GestorBusquedas:
    """Gestiona el almacenamiento y recuperación de búsquedas guardadas"""
    
    # def __init__(self,usuario, archivo="busquedas_guardadas.json"):
    ## Cambio de pruebas, para usuarios
    def __init__(self, usuario , archivo="usuarios.json"):
        pass
        self.archivo = archivo
        self.usuario = usuario
        self.busquedas = self._cargar_busquedas()
    
    def _cargar_busquedas(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    dict_us = json.load(f)
                    busquedas_guardadas = dict_us[self.usuario]['busquedas_guardadas']
                    # return json.load(f)
                    return busquedas_guardadas
            except Exception:
                print(Exception)
                return []
        return []
    
    def _guardar_busquedas(self):
        with open(self.archivo, 'r', encoding='utf-8') as f:
            dict_us = json.load(f)
            dict_us[self.usuario]['busquedas_guardadas'] = self.busquedas

        with open(self.archivo, 'w', encoding='utf-8') as f:
            json.dump(dict_us, f, ensure_ascii=False, indent=2)
    
    def guardar_busqueda(self, busqueda):
        # Convertir datetime a string si es necesario
        if "filtros" in busqueda:
            if busqueda["filtros"].get("fecha_desde"):
                if not isinstance(busqueda["filtros"]["fecha_desde"], str):
                    busqueda["filtros"]["fecha_desde"] = busqueda["filtros"]["fecha_desde"].strftime("%d/%m/%Y")
            
            if busqueda["filtros"].get("fecha_hasta"):
                if not isinstance(busqueda["filtros"]["fecha_hasta"], str):
                    busqueda["filtros"]["fecha_hasta"] = busqueda["filtros"]["fecha_hasta"].strftime("%d/%m/%Y")

            if busqueda["filtros"].get("fecha_desde_publicado"):
                if not isinstance(busqueda["filtros"]["fecha_desde_publicado"], str):
                    busqueda["filtros"]["fecha_desde_publicado"] = busqueda["filtros"]["fecha_desde_publicado"].strftime("%d/%m/%Y")
            
            if busqueda["filtros"].get("fecha_hasta_publicado"):
                if not isinstance(busqueda["filtros"]["fecha_hasta_publicado"], str):
                    busqueda["filtros"]["fecha_hasta_publicado"] = busqueda["filtros"]["fecha_hasta_publicado"].strftime("%d/%m/%Y")
        
        # Buscar si ya existe
        existe = False
        for i, b in enumerate(self.busquedas):
            if b["nombre"] == busqueda["nombre"]:
                self.busquedas[i] = busqueda
                existe = True
                break
        
        if not existe:
            self.busquedas.append(busqueda)
        
        self._guardar_busquedas()
    
    def eliminar_busqueda(self, nombre):
        self.busquedas = [b for b in self.busquedas if b["nombre"] != nombre]
        self._guardar_busquedas()
    
    def obtener_busquedas(self):
        return self.busquedas
    
    def duplicar_busqueda(self, busqueda):
        """Crea una copia de una búsqueda con un nuevo nombre"""
        nombre_base = busqueda["nombre"]
        contador = 1
        nuevo_nombre = f"{nombre_base} (Copia)"
        
        # Encontrar un nombre único
        nombres_existentes = [b["nombre"] for b in self.busquedas]
        while nuevo_nombre in nombres_existentes:
            contador += 1
            nuevo_nombre = f"{nombre_base} (Copia {contador})"
        
        busqueda_duplicada = {
            "nombre": nuevo_nombre,
            "descripcion": busqueda.get("descripcion", ""),
            "filtros": busqueda["filtros"].copy(),
            "fecha_creacion": datetime.now().isoformat()
        }
        
        self.guardar_busqueda(busqueda_duplicada)
        return busqueda_duplicada


class DialogoGuardarBusqueda(ft.AlertDialog):
    """Diálogo para guardar una búsqueda con filtros"""
    
    def __init__(self, filtros, on_guardar):
        super().__init__()
        self.filtros = filtros
        self.on_guardar = on_guardar
        
        self.modal = True
        self.title = ft.Text("💾 Guardar búsqueda", size=20, weight="bold")
        
        self.txt_nombre = ft.TextField(
            label="Nombre de la búsqueda",
            hint_text="Ej: Licitaciones de software",
            width=400,
            autofocus=True,
        )
        
        self.txt_descripcion = ft.TextField(
            label="Descripción (opcional)",
            hint_text="Describe los criterios de esta búsqueda",
            width=400,
            multiline=True,
            max_lines=3,
        )
        
        # Resumen de filtros aplicados
        resumen_filtros = self._generar_resumen_filtros()
        
        self.content = ft.Column(
            [
                self.txt_nombre,
                self.txt_descripcion,
                ft.Divider(),
                ft.Text("📋 Resumen de filtros:", size=14, weight="bold"),
                ft.Container(
                    content=ft.Column(
                        resumen_filtros,
                        scroll="auto",
                    ),
                    height=200,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                    padding=10,
                ),
            ],
            width=500,
        )
        
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cerrar),
            ft.Button(
                "Guardar",
                icon=ft.Icons.SAVE,
                on_click=self._guardar,
            ),
        ]
    
    def _generar_resumen_filtros(self):
        """Genera un resumen legible de los filtros aplicados"""
        resumen = []
        
        if self.filtros.get("cpv"):
            resumen.append(ft.Text(f"• CPVs: {len(self.filtros['cpv'])} seleccionados"))
        
        if self.filtros.get("lugar"):
            resumen.append(ft.Text(f"• Lugar: {self.filtros['lugar']}"))
        
        if self.filtros.get("entidades"):
            resumen.append(ft.Text(f"• Entidades: {', '.join(self.filtros['entidades'])}"))
        
        if self.filtros.get("estados"):
            resumen.append(ft.Text(f"• Estados: {', '.join(self.filtros['estados'])}"))
        
        if self.filtros.get("fecha_desde") or self.filtros.get("fecha_hasta"):
            fecha_texto = "• Fechas: "
            if self.filtros.get("fecha_desde"):
                fecha_texto += f"desde {self.filtros['fecha_desde'].strftime('%d/%m/%Y')} "
            if self.filtros.get("fecha_hasta"):
                fecha_texto += f"hasta {self.filtros['fecha_hasta'].strftime('%d/%m/%Y')}"
            resumen.append(ft.Text(fecha_texto))
        
        if self.filtros.get("fecha_desde_publicado") or self.filtros.get("fecha_hasta_publicado"):
            fecha_texto = "• Fechas Publicación: "
            if self.filtros.get("fecha_desde_publicado"):
                fecha_texto += f"desde {self.filtros['fecha_desde_publicado'].strftime('%d/%m/%Y')} "
            if self.filtros.get("fecha_hasta_publicado"):
                fecha_texto += f"hasta {self.filtros['fecha_hasta_publicado'].strftime('%d/%m/%Y')}"
            resumen.append(ft.Text(fecha_texto))

        importe_min = self.filtros.get("importe_min", 0)
        importe_max = self.filtros.get("importe_max", 1_000_000)
        if importe_min > 0 or importe_max < 1_000_000:
            resumen.append(ft.Text(f"• Importe: {importe_min:,.0f} € - {importe_max:,.0f} €"))
        
        if self.filtros.get("palabras_clave"):
            resumen.append(ft.Text(f"• Palabras clave: {', '.join(self.filtros['palabras_clave'])}"))
        
        if self.filtros.get("incluir_pdf"):
            resumen.append(ft.Text("• Incluye búsqueda en PDFs"))
        
        if not resumen:
            resumen.append(ft.Text("Sin filtros específicos", italic=True))
        
        return resumen
    
    def _guardar(self, e):
        nombre = self.txt_nombre.value.strip()
        
        if not nombre:
            self.txt_nombre.error_text = "El nombre es obligatorio"
            self.update()
            return
        
        busqueda = {
            "nombre": nombre,
            "descripcion": self.txt_descripcion.value.strip(),
            "filtros": self.filtros,
            "fecha_creacion": datetime.now().isoformat(),
        }
        
        self.on_guardar(busqueda)
        self._cerrar(e)
    
    def _cerrar(self, e):
        self.open = False
        self.update()


class PanelBusquedasGuardadas(ft.Container):
    """Panel que muestra las búsquedas guardadas"""
    
    def __init__(self, gestor, on_aplicar, on_eliminar, on_editar):
        super().__init__()
        self.gestor = gestor
        self.on_aplicar = on_aplicar
        self.on_eliminar = on_eliminar
        self.on_editar = on_editar
        
        self.lista_busquedas = ft.ListView(
            spacing=5,
            height=600,
        )
        
        self.actualizar_lista()
        
        self.content = ft.Column(
            [
                ft.Text("🔖 Búsquedas guardadas", size=18, weight="bold"),
                self.lista_busquedas,
            ],
            spacing=10,
        )
    
    def actualizar_lista(self):
        self.lista_busquedas.controls.clear()
        busquedas = self.gestor.obtener_busquedas()
        
        if not busquedas:
            self.lista_busquedas.controls.append(
                ft.Text("No hay búsquedas guardadas", italic=True, color=ft.Colors.GREY)
            )
        else:
            for busqueda in busquedas:
                self.lista_busquedas.controls.append(
                    self._crear_tarjeta_busqueda(busqueda)
                )
    
    def _crear_tarjeta_busqueda(self, busqueda):
        # Contar filtros activos
        filtros = busqueda["filtros"]
        num_filtros = sum([
            1 if filtros.get("cpv") else 0,
            1 if filtros.get("lugar") else 0,
            1 if filtros.get("entidades") else 0,
            1 if filtros.get("estados") else 0,
            1 if filtros.get("fecha_desde") or filtros.get("fecha_hasta") else 0,
            1 if filtros.get("palabras_clave") else 0,
        ])
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.BOOKMARK, size=20, color=ft.Colors.BLUE),
                            ft.Text(
                                busqueda["nombre"],
                                size=14,
                                weight="bold",
                                expand=True,
                            ),
                        ],
                    ),
                    ft.Text(
                        busqueda.get("descripcion", "Sin descripción"),
                        size=12,
                        color=ft.Colors.GREY,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"{num_filtros} filtros activos",
                        size=11,
                        color=ft.Colors.BLUE_GREY,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.PLAY_ARROW,
                                tooltip="Aplicar búsqueda",
                                icon_color=ft.Colors.GREEN,
                                on_click=lambda e, b=busqueda: self.on_aplicar(b),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip="Editar búsqueda",
                                icon_color=ft.Colors.BLUE,
                                on_click=lambda e, b=busqueda: self.on_editar(b),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CONTENT_COPY,
                                tooltip="Duplicar búsqueda",
                                icon_color=ft.Colors.ORANGE,
                                on_click=lambda e, b=busqueda: self._duplicar_busqueda(b),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Eliminar búsqueda",
                                icon_color=ft.Colors.RED,
                                on_click=lambda e, b=busqueda: self._confirmar_eliminar(b),
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=5,
        )
    
    def _duplicar_busqueda(self, busqueda):
        """Duplica una búsqueda guardada"""
        busqueda_duplicada = self.gestor.duplicar_busqueda(busqueda)
        self.actualizar_lista()
        self.update()
        
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Búsqueda duplicada como '{busqueda_duplicada['nombre']}'"),
                bgcolor=ft.Colors.ORANGE_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _confirmar_eliminar(self, busqueda):
        if not self.page:
            return
        
        def eliminar(e):
            self.on_eliminar(busqueda)
            dialogo.open = False
            self.page.update()
        
        def cancelar(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            title=ft.Text("⚠️ Confirmar eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar la búsqueda '{busqueda['nombre']}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.TextButton("Eliminar", on_click=eliminar),
            ],
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()


class DialogoEditarBusqueda(ft.AlertDialog):
    """Diálogo para editar una búsqueda guardada"""
    
    def __init__(self, busqueda, on_guardar, df_cpv, lugares, entidades):
        super().__init__()
        self.busqueda_original = busqueda
        self.on_guardar = on_guardar
        self.df_cpv = df_cpv
        self.lugares = lugares
        self.entidades = entidades
        
        self.modal = True
        self.title = ft.Text("✏️ Editar búsqueda", size=20, weight="bold")
        
        # Campos de edición
        self.txt_nombre = ft.TextField(
            label="Nombre de la búsqueda",
            value=busqueda["nombre"],
            width=500,
        )
        
        self.txt_descripcion = ft.TextField(
            label="Descripción",
            value=busqueda.get("descripcion", ""),
            width=500,
            multiline=True,
            max_lines=2,
        )
        
        # Contenedor con scroll para los filtros editables
        self.filtros_editables = self._crear_filtros_editables()
        
        self.content = ft.Column(
            [
                self.txt_nombre,
                self.txt_descripcion,
                ft.Divider(),
                ft.Text("Editar filtros:", size=14, weight="bold"),
                ft.Container(
                    content=self.filtros_editables,
                    height=400,
                    border=ft.Border.all(width=1, color=ft.Colors.GREY_300),
                    border_radius=5,
                    padding=ft.Padding.all(10),
                ),
            ],
            width=600,
        )
        
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cerrar),
            # ft.ElevatedButton(
            ft.Button(
                "Guardar cambios",
                icon=ft.Icons.SAVE,
                on_click=self._guardar,
            ),
        ]
    
    def _crear_filtros_editables(self):
        """Crea controles editables para los filtros"""
        filtros = self.busqueda_original["filtros"]
        
        # CPVs (mostrar resumen, permitir edición completa sería complejo)
        self.filtros_editados = filtros
        cpvs_texto = f"{len(filtros.get('cpv', []))} CPVs seleccionados"
        # self.cpv_seleccionados = self.filtros_editados.get("cpv", []).copy()
        # self.chips_cpv = ft.Row(wrap=True, spacing=5, scroll="auto")
        # self._actualizar_chips_cpv()

        # Buscador de CPV
        # self.txt_buscar_cpv = ft.TextField(
        #     label="Buscar y añadir CPVs",
        #     hint_text="Mínimo 4 caracteres",
        #     width=600,
        #     on_change=self._buscar_cpv,
        # )
        # self.lista_cpv = ft.ListView(height=150, spacing=3)
        
        # Lugar
        self.dd_lugar = ft.Dropdown(
            label="Lugar de ejecución",
            options=[ft.dropdown.Option(l) for l in self.lugares],
            value=filtros.get("lugar"),
            width=400,
        )
        
        # Entidades
        self.chk_entidades = [
            ft.Checkbox(label=e, value=e in filtros.get("entidades", []))
            for e in self.entidades
        ]
        
        # Estados
        estados_disponibles = ["Publicado", "Evaluado", "Adjudicado", "Resuelto", "Anuncio Previo"]
        self.chk_estados = [
            ft.Checkbox(label=e, value=e in filtros.get("estados", []))
            for e in estados_disponibles
        ]
        
        # Fechas
        self.txt_fecha_desde = ft.TextField(
            label="Fecha desde (DD/MM/AAAA)",
            value=filtros.get("fecha_desde", ""),
            width=180,
        )
        
        self.txt_fecha_hasta = ft.TextField(
            label="Fecha hasta (DD/MM/AAAA)",
            value=filtros.get("fecha_hasta", ""),
            width=180,
        )
        
        # Fechas Publicado
        self.txt_fecha_desde_publicado = ft.TextField(
            label="Fecha desde (DD/MM/AAAA)",
            value=filtros.get("fecha_desde_publicado", ""),
            width=180,
        )
        
        self.txt_fecha_hasta_publicado = ft.TextField(
            label="Fecha hasta (DD/MM/AAAA)",
            value=filtros.get("fecha_hasta_publicado", ""),
            width=180,
        )

        # Importe
        self.slider_importe = ft.RangeSlider(
            min=0,
            max=1_000_000,
            divisions=100,
            start_value=filtros.get("importe_min", 0),
            end_value=filtros.get("importe_max", 1_000_000),
            label="{value} €",
        )
        
        # Palabras clave
        palabras = ", ".join(filtros.get("palabras_clave", []))
        self.txt_palabras = ft.TextField(
            label="Palabras clave",
            value=palabras,
            width=400,
        )
        
        self.chk_pdf = ft.Checkbox(
            label="Buscar en PDFs",
            value=filtros.get("incluir_pdf", False),
        )
        
        return ft.Column(
            [
                ft.Text(f"📋 CPVs: {cpvs_texto}", size=12),
                # self.chips
                ft.Divider(),
                self.dd_lugar,
                ft.Text("Entidades:", size=12, weight="bold"),
                ft.Row(self.chk_entidades, wrap=True),
                ft.Text("Estados:", size=12, weight="bold"),
                ft.Row(self.chk_estados, wrap=True),
                ft.Text("Fechas limite:", size=12, weight="bold"),
                ft.Row([self.txt_fecha_desde, self.txt_fecha_hasta]),
                ft.Text("Fechas publicado:", size=12, weight="bold"),
                ft.Row([self.txt_fecha_desde_publicado, self.txt_fecha_hasta_publicado]),
                ft.Text("Importe:", size=12, weight="bold"),
                self.slider_importe,
                self.txt_palabras,
                self.chk_pdf,
            ],
            spacing=10,
            scroll="auto",
        )
    
    
    def _guardar(self, e):
        nombre = self.txt_nombre.value.strip()
        
        if not nombre:
            self.txt_nombre.error_text = "El nombre es obligatorio"
            self.update()
            return
        
        # Reconstruir filtros con valores editados
        filtros_actualizados = self.busqueda_original["filtros"].copy()
        
        filtros_actualizados["lugar"] = self.dd_lugar.value
        filtros_actualizados["entidades"] = [
            chk.label for chk in self.chk_entidades if chk.value
        ]
        filtros_actualizados["estados"] = [
            chk.label for chk in self.chk_estados if chk.value
        ]
        filtros_actualizados["fecha_desde"] = self.txt_fecha_desde.value
        filtros_actualizados["fecha_hasta"] = self.txt_fecha_hasta.value
        filtros_actualizados["fecha_desde_publicado"] = self.txt_fecha_desde_publicado.value
        filtros_actualizados["fecha_hasta_publicado"] = self.txt_fecha_hasta_publicado.value
        filtros_actualizados["importe_min"] = self.slider_importe.start_value
        filtros_actualizados["importe_max"] = self.slider_importe.end_value
        
        palabras_clave = []
        if self.txt_palabras.value:
            palabras_clave = [p.strip() for p in self.txt_palabras.value.split(",") if p.strip()]
        filtros_actualizados["palabras_clave"] = palabras_clave
        filtros_actualizados["incluir_pdf"] = self.chk_pdf.value
        
        busqueda_actualizada = {
            "nombre": nombre,
            "descripcion": self.txt_descripcion.value.strip(),
            "filtros": filtros_actualizados,
            "fecha_creacion": self.busqueda_original.get("fecha_creacion", datetime.now().isoformat()),
        }
        
        self.on_guardar(busqueda_actualizada)
        self._cerrar(e)
    
    def _cerrar(self, e):
        self.open = False
        self.update()
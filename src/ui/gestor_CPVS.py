# import flet as ft
# import pandas as pd

# class CPVFilterManager:
#     """Gestor mejorado de filtros CPV con búsqueda y autocompletado"""
    
#     # def __init__(self, page: ft.Page, cpvs_disponibles=None, on_change=None):
#     def __init__(self, cpvs_disponibles=None, on_change=None):
#         """
#         Args:
#             page: Página de Flet
#             cpvs_disponibles: Lista de CPVs disponibles para autocompletado
#             on_change: Callback cuando cambian los CPVs seleccionados
#         """
#         # self.page = page
#         self.cpvs_seleccionados = []
#         self.on_change = on_change
        
#         # Si no se proporciona lista, usar algunos ejemplos
#         self.cpvs_disponibles = cpvs_disponibles or [
#             "45000000 - Obras de construcción",
#             "45100000 - Preparación de obras",
#             "45200000 - Trabajos de construcción",
#             "71000000 - Servicios de arquitectura e ingeniería",
#             "72000000 - Servicios TI: consultoría, desarrollo",
#             "79000000 - Servicios empresariales",
#             "80000000 - Servicios de educación y formación",
#         ]
        
#         self._build_ui()
    
#     def _build_ui(self):
#         """Construye la interfaz del gestor de CPVs"""
        
#         # Campo de búsqueda
#         self.txt_buscar_cpv = ft.TextField(
#             label="Buscar o agregar CPV",
#             hint_text="Escribe código o descripción...",
#             border_color=ft.Colors.BLUE_300,
#             dense=True,
#             on_submit=self._agregar_cpv_manual,
#             suffix=ft.IconButton(
#                 icon=ft.Icons.ADD_CIRCLE,
#                 icon_color=ft.Colors.GREEN,
#                 tooltip="Agregar CPV",
#                 on_click=self._agregar_cpv_manual,
#             ),
#         )
        
#         # Lista de sugerencias (inicialmente oculta)
#         self.lista_sugerencias = ft.Column(
#             visible=False,
#             spacing=2,
#         )
        
#         # Contenedor para chips de CPVs seleccionados
#         self.cpv_chips_container = ft.Column(
#             spacing=8,
#             scroll=ft.ScrollMode.AUTO,
#             height=150,
#         )
        
#         # Actualizar sugerencias mientras escribe
#         self.txt_buscar_cpv.on_change = self._actualizar_sugerencias
        
#         # Contador de CPVs
#         self.txt_contador = ft.Text(
#             "0 CPVs seleccionados",
#             size=12,
#             color=ft.Colors.GREY_600,
#             weight=ft.FontWeight.BOLD,
#         )
        
#         # Botón para limpiar todos
#         self.btn_limpiar_cpvs = ft.TextButton(
#             "Limpiar todos",
#             icon=ft.Icons.CLEAR_ALL,
#             on_click=self._limpiar_todos_cpvs,
#             style=ft.ButtonStyle(color=ft.Colors.RED_600),
#         )
    
#     def get_control(self):
#         """Retorna el control completo para insertar en el layout"""
#         return ft.Container(
#             content=ft.Column([
#                 ft.Text(
#                     "📋 Códigos CPV",
#                     size=13,
#                     weight=ft.FontWeight.BOLD,
#                     color=ft.Colors.BLUE_700,
#                 ),
#                 self.txt_buscar_cpv,
#                 self.lista_sugerencias,
#                 ft.Row([
#                     self.txt_contador,
#                     self.btn_limpiar_cpvs,
#                 ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
#                 ft.Divider(height=5),
#                 ft.Text("Seleccionados:", size=11, weight=ft.FontWeight.BOLD),
#                 self.cpv_chips_container,
#             ], spacing=8),
#             padding=10,
#             border=ft.border.all(1, ft.Colors.BLUE_200),
#             border_radius=8,
#             bgcolor=ft.Colors.BLUE_50,
#         )
    
#     def _actualizar_sugerencias(self, e):
#         """Actualiza la lista de sugerencias según el texto ingresado"""
#         texto = e.control.value.lower().strip()
        
#         if not texto:
#             self.lista_sugerencias.visible = False
#             self.page.update()
#             return
        
#         # Filtrar CPVs disponibles
#         coincidencias = [
#             cpv for cpv in self.cpvs_disponibles
#             if texto in cpv.lower() and cpv not in self.cpvs_seleccionados
#         ]
        
#         self.lista_sugerencias.controls.clear()
        
#         if coincidencias:
#             # Mostrar hasta 5 sugerencias
#             for cpv in coincidencias[:5]:
#                 self.lista_sugerencias.controls.append(
#                     ft.Container(
#                         content=ft.Text(cpv, size=12),
#                         padding=8,
#                         border_radius=5,
#                         bgcolor=ft.Colors.WHITE,
#                         ink=True,
#                         on_click=lambda e, c=cpv: self._agregar_cpv(c),
#                     )
#                 )
#             self.lista_sugerencias.visible = True
#         else:
#             self.lista_sugerencias.visible = False
        
#         self.page.update()
    
#     def _agregar_cpv_manual(self, e):
#         """Agrega un CPV manualmente desde el campo de texto"""
#         texto = self.txt_buscar_cpv.value.strip()
#         if texto and texto not in self.cpvs_seleccionados:
#             self._agregar_cpv(texto)
    
#     def _agregar_cpv(self, cpv):
#         """Agrega un CPV a la lista de seleccionados"""
#         if cpv not in self.cpvs_seleccionados:
#             self.cpvs_seleccionados.append(cpv)
#             self._actualizar_chips()
#             self.txt_buscar_cpv.value = ""
#             self.lista_sugerencias.visible = False
            
#             # Notificar cambio
#             if self.on_change:
#                 self.on_change(self.cpvs_seleccionados)
            
#             self.page.update()
    
#     def _quitar_cpv(self, cpv):
#         """Quita un CPV de la lista de seleccionados"""
#         if cpv in self.cpvs_seleccionados:
#             self.cpvs_seleccionados.remove(cpv)
#             self._actualizar_chips()
            
#             # Notificar cambio
#             if self.on_change:
#                 self.on_change(self.cpvs_seleccionados)
            
#             self.page.update()
    
#     def _limpiar_todos_cpvs(self, e):
#         """Limpia todos los CPVs seleccionados"""
#         self.cpvs_seleccionados.clear()
#         self._actualizar_chips()
        
#         # Notificar cambio
#         if self.on_change:
#             self.on_change(self.cpvs_seleccionados)
        
#         self.page.update()
    
#     def _actualizar_chips(self):
#         """Actualiza los chips visuales de CPVs seleccionados"""
#         self.cpv_chips_container.controls.clear()
        
#         for cpv in self.cpvs_seleccionados:
#             # Truncar texto si es muy largo
#             texto_mostrar = cpv if len(cpv) <= 50 else cpv[:47] + "..."
            
#             chip = ft.Container(
#                 content=ft.Row([
#                     ft.Icon(ft.Icons.TAG, size=16, color=ft.Colors.BLUE_700),
#                     ft.Text(texto_mostrar, size=12, expand=True),
#                     ft.IconButton(
#                         icon=ft.Icons.CLOSE,
#                         icon_size=16,
#                         icon_color=ft.Colors.RED_600,
#                         tooltip="Quitar",
#                         on_click=lambda e, c=cpv: self._quitar_cpv(c),
#                     ),
#                 ], spacing=5, tight=True),
#                 padding=ft.padding.only(left=10, right=5, top=5, bottom=5),
#                 border_radius=20,
#                 bgcolor=ft.Colors.BLUE_100,
#                 border=ft.border.all(1, ft.Colors.BLUE_300),
#             )
#             self.cpv_chips_container.controls.append(chip)
        
#         # Actualizar contador
#         self.txt_contador.value = f"{len(self.cpvs_seleccionados)} CPV{'s' if len(self.cpvs_seleccionados) != 1 else ''} seleccionado{'s' if len(self.cpvs_seleccionados) != 1 else ''}"
    
#     def set_cpvs(self, cpvs):
#         """Establece los CPVs seleccionados desde el exterior"""
#         self.cpvs_seleccionados = list(cpvs) if cpvs else []
#         self._actualizar_chips()
#         self.page.update()
    
#     def get_cpvs(self):
#         """Obtiene la lista de CPVs seleccionados"""
#         return self.cpvs_seleccionados.copy()

## --------------------------------------

import flet as ft
import pandas as pd

class CPVFilterManager:
    """Gestor mejorado de filtros CPV con búsqueda y autocompletado"""
    
    def __init__(self, cpvs_disponibles=None, on_change=None):
        """
        Args:
            cpvs_disponibles: Lista de CPVs disponibles para autocompletado
            on_change: Callback cuando cambian los CPVs seleccionados
        """
        self.cpvs_seleccionados = []
        self.on_change = on_change
        self._page = None  # 👈 Guardar referencia a page cuando esté disponible
        
        # Si no se proporciona lista, usar algunos ejemplos
        self.cpvs_disponibles = cpvs_disponibles or [
            "45000000 - Obras de construcción",
            "45100000 - Preparación de obras",
            "45200000 - Trabajos de construcción",
            "71000000 - Servicios de arquitectura e ingeniería",
            "72000000 - Servicios TI: consultoría, desarrollo",
            "79000000 - Servicios empresariales",
            "80000000 - Servicios de educación y formación",
        ]
        
        self._build_ui()  # 👈 Construir UI en init
    
    def _build_ui(self):
        """Construye la interfaz del gestor de CPVs"""
        
        # Campo de búsqueda
        self.txt_buscar_cpv = ft.TextField(
            label="Buscar o agregar CPV",
            hint_text="Escribe código o descripción...",
            border_color=ft.Colors.BLUE_300,
            dense=True,
            on_submit=self._agregar_cpv_manual,
            suffix=ft.IconButton(
                icon=ft.Icons.ADD_CIRCLE,
                icon_color=ft.Colors.GREEN,
                tooltip="Agregar CPV",
                on_click=self._agregar_cpv_manual,
            ),
        )
        
        # Lista de sugerencias (inicialmente oculta)
        self.lista_sugerencias = ft.Column(
            visible=False,
            spacing=2,
        )
        
        # Contenedor para chips de CPVs seleccionados
        self.cpv_chips_container = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            height=150,
        )
        
        # Actualizar sugerencias mientras escribe
        self.txt_buscar_cpv.on_change = self._actualizar_sugerencias
        
        # Contador de CPVs
        self.txt_contador = ft.Text(
            "0 CPVs seleccionados",
            size=12,
            color=ft.Colors.GREY_600,
            weight=ft.FontWeight.BOLD,
        )
        
        # Botón para limpiar todos
        self.btn_limpiar_cpvs = ft.TextButton(
            "Limpiar todos",
            icon=ft.Icons.CLEAR_ALL,
            on_click=self._limpiar_todos_cpvs,
            style=ft.ButtonStyle(color=ft.Colors.RED_600),
        )
        
    def get_control(self):
        """Retorna el control completo para insertar en el layout"""
        return self.container  # 👈 Retornar el contenedor principal
    
    @property
    def page(self):
        """Obtiene la página desde cualquier control hijo"""
        if self._page is None and hasattr(self.container, 'page'):
            self._page = self.container.page
        return self._page(
            content=ft.Column([
                ft.Text(
                    "📋 Códigos CPV",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700,
                ),
                self.txt_buscar_cpv,
                self.lista_sugerencias,
                ft.Row([
                    self.txt_contador,
                    self.btn_limpiar_cpvs,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=5),
                ft.Text("Seleccionados:", size=11, weight=ft.FontWeight.BOLD),
                self.cpv_chips_container,
            ], spacing=8),
            padding=10,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
            bgcolor=ft.Colors.BLUE_50,
        )
    
    def _actualizar_sugerencias(self, e):
        """Actualiza la lista de sugerencias según el texto ingresado"""
        texto = e.control.value.lower().strip()
        
        if not texto:
            self.lista_sugerencias.visible = False
            if self.page:
                self.page.update()
            return
        
        # Filtrar CPVs disponibles
        coincidencias = [
            cpv for cpv in self.cpvs_disponibles
            if texto in cpv.lower() and cpv not in self.cpvs_seleccionados
        ]
        
        self.lista_sugerencias.controls.clear()
        
        if coincidencias:
            # Mostrar hasta 5 sugerencias
            for cpv in coincidencias[:5]:
                self.lista_sugerencias.controls.append(
                    ft.Container(
                        content=ft.Text(cpv, size=12),
                        padding=8,
                        border_radius=5,
                        bgcolor=ft.Colors.WHITE,
                        ink=True,
                        on_click=lambda e, c=cpv: self._agregar_cpv(c),
                    )
                )
            self.lista_sugerencias.visible = True
        else:
            self.lista_sugerencias.visible = False
        
        if self.page:
            self.page.update()
    
    def _agregar_cpv_manual(self, e):
        """Agrega un CPV manualmente desde el campo de texto"""
        texto = self.txt_buscar_cpv.value.strip()
        if texto and texto not in self.cpvs_seleccionados:
            self._agregar_cpv(texto)
    
    def _agregar_cpv(self, cpv):
        """Agrega un CPV a la lista de seleccionados"""
        if cpv not in self.cpvs_seleccionados:
            self.cpvs_seleccionados.append(cpv)
            self._actualizar_chips()
            self.txt_buscar_cpv.value = ""
            self.lista_sugerencias.visible = False
            
            # Notificar cambio
            if self.on_change:
                self.on_change(self.cpvs_seleccionados)
            
            if self.page:
                self.page.update()
    
    def _quitar_cpv(self, cpv):
        """Quita un CPV de la lista de seleccionados"""
        if cpv in self.cpvs_seleccionados:
            self.cpvs_seleccionados.remove(cpv)
            self._actualizar_chips()
            
            # Notificar cambio
            if self.on_change:
                self.on_change(self.cpvs_seleccionados)
            
            if self.page:
                self.page.update()
    
    def _limpiar_todos_cpvs(self, e):
        """Limpia todos los CPVs seleccionados"""
        self.cpvs_seleccionados.clear()
        self._actualizar_chips()
        
        # Notificar cambio
        if self.on_change:
            self.on_change(self.cpvs_seleccionados)
        
        if self.page:
            self.page.update()
    
    def _actualizar_chips(self):
        """Actualiza los chips visuales de CPVs seleccionados"""
        self.cpv_chips_container.controls.clear()
        
        for cpv in self.cpvs_seleccionados:
            # Truncar texto si es muy largo
            texto_mostrar = cpv if len(cpv) <= 50 else cpv[:47] + "..."
            
            chip = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.TAG, size=16, color=ft.Colors.BLUE_700),
                    ft.Text(texto_mostrar, size=12, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=16,
                        icon_color=ft.Colors.RED_600,
                        tooltip="Quitar",
                        on_click=lambda e, c=cpv: self._quitar_cpv(c),
                    ),
                ], spacing=5, tight=True),
                padding=ft.Padding.only(left=10, right=5, top=5, bottom=5),
                border_radius=20,
                bgcolor=ft.Colors.BLUE_100,
                border=ft.border.all(1, ft.Colors.BLUE_300),
            )
            self.cpv_chips_container.controls.append(chip)
        
        # Actualizar contador
        self.txt_contador.value = f"{len(self.cpvs_seleccionados)} CPV{'s' if len(self.cpvs_seleccionados) != 1 else ''} seleccionado{'s' if len(self.cpvs_seleccionados) != 1 else ''}"
    
    def set_cpvs(self, cpvs):
        """Establece los CPVs seleccionados desde el exterior"""
        self.cpvs_seleccionados = list(cpvs) if cpvs else []
        self._actualizar_chips()
        if self.page:
            self.page.update()
    
    def get_cpvs(self):
        """Obtiene la lista de CPVs seleccionados"""
        return self.cpvs_seleccionados.copy()

## -------------- VERSION GEMINI ------------------

# import flet as ft

# class CPVFilterManager:
#     def __init__(self, cpvs_disponibles=None, on_change=None):
#         self.cpvs_seleccionados = []
#         self.on_change = on_change
#         self.cpvs_disponibles = cpvs_disponibles or [
#             "45000000 - Obras de construcción",
#             "71000000 - Servicios de arquitectura e ingeniería",
#             "72000000 - Servicios TI: consultoría, desarrollo",
#         ]
        
#         # Construimos los controles primero
#         self._setup_controls()
#         # El contenedor principal que retornaremos
#         self.view = self._build_main_container()

#     def _setup_controls(self):
#         """Inicializa los sub-controles"""
#         self.txt_buscar_cpv = ft.TextField(
#             label="Buscar o agregar CPV",
#             hint_text="Escribe código o descripción...",
#             border_color=ft.Colors.BLUE_300,
#             dense=True,
#             on_change=self._actualizar_sugerencias,
#             on_submit=self._agregar_cpv_manual,
#             suffix=ft.IconButton(
#                 icon=ft.Icons.ADD_CIRCLE,
#                 icon_color=ft.Colors.GREEN,
#                 on_click=self._agregar_cpv_manual,
#             ),
#         )
        
#         self.lista_sugerencias = ft.Column(visible=False, spacing=2)
        
#         self.cpv_chips_container = ft.Column(
#             spacing=8,
#             scroll=ft.ScrollMode.AUTO,
#             height=150,
#         )
        
#         self.txt_contador = ft.Text("0 CPVs seleccionados", size=12, weight=ft.FontWeight.BOLD)
        
#         self.btn_limpiar_cpvs = ft.TextButton(
#             "Limpiar todos",
#             icon=ft.Icons.CLEAR_ALL,
#             on_click=self._limpiar_todos_cpvs,
#             style=ft.ButtonStyle(color=ft.Colors.RED_600),
#         )

#     def _build_main_container(self):
#         """Empaqueta todo en un contenedor principal"""
#         return ft.Container(
#             content=ft.Column([
#                 ft.Text("📋 Códigos CPV", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
#                 self.txt_buscar_cpv,
#                 self.lista_sugerencias,
#                 ft.Row([
#                     self.txt_contador,
#                     self.btn_limpiar_cpvs,
#                 ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
#                 ft.Divider(height=5),
#                 ft.Text("Seleccionados:", size=11, weight=ft.FontWeight.BOLD),
#                 self.cpv_chips_container,
#             ], spacing=8),
#             padding=10,
#             border=ft.border.all(1, ft.Colors.BLUE_200),
#             border_radius=8,
#             bgcolor=ft.Colors.BLUE_50,
#         )

#     def get_control(self):
#         return self.view

#     def _actualizar_sugerencias(self, e):
#         texto = e.control.value.lower().strip()
#         if not texto:
#             self.lista_sugerencias.visible = False
#             self.view.update()
#             return

#         coincidencias = [
#             cpv for cpv in self.cpvs_disponibles 
#             if texto in cpv.lower() and cpv not in self.cpvs_seleccionados
#         ]

#         self.lista_sugerencias.controls.clear()
#         if coincidencias:
#             for cpv in coincidencias[:5]:
#                 self.lista_sugerencias.controls.append(
#                     ft.ListTile(
#                         title=ft.Text(cpv, size=12),
#                         on_click=lambda e, c=cpv: self._agregar_cpv(c),
#                         dense=True,
#                         bgcolor=ft.Colors.WHITE,
#                     )
#                 )
#             self.lista_sugerencias.visible = True
#         else:
#             self.lista_sugerencias.visible = False
#         self.view.update()

#     def _agregar_cpv(self, cpv):
#         if cpv not in self.cpvs_seleccionados:
#             self.cpvs_seleccionados.append(cpv)
#             self._actualizar_chips()
#             self.txt_buscar_cpv.value = ""
#             self.lista_sugerencias.visible = False
#             if self.on_change: self.on_change(self.cpvs_seleccionados)
#             self.view.update()

#     def _agregar_cpv_manual(self, e):
#         self._agregar_cpv(self.txt_buscar_cpv.value.strip())

#     def _quitar_cpv(self, cpv):
#         self.cpvs_seleccionados.remove(cpv)
#         self._actualizar_chips()
#         if self.on_change: self.on_change(self.cpvs_seleccionados)
#         self.view.update()

#     def _limpiar_todos_cpvs(self, e):
#         self.cpvs_seleccionados.clear()
#         self._actualizar_chips()
#         if self.on_change: self.on_change(self.cpvs_seleccionados)
#         self.view.update()

#     def _actualizar_chips(self):
#         self.cpv_chips_container.controls.clear()
#         for cpv in self.cpvs_seleccionados:
#             self.cpv_chips_container.controls.append(
#                 ft.Container(
#                     content=ft.Row([
#                         ft.Icon(ft.Icons.TAG, size=16),
#                         ft.Text(cpv if len(cpv) <= 40 else cpv[:37]+"...", size=12, expand=True),
#                         ft.IconButton(ft.Icons.CLOSE, icon_size=16, on_click=lambda e, c=cpv: self._quitar_cpv(c))
#                     ]),
#                     bgcolor=ft.Colors.BLUE_100,
#                     border_radius=10,
#                     padding=5
#                 )
#             )
#         self.txt_contador.value = f"{len(self.cpvs_seleccionados)} CPVs seleccionados"

# # Ejemplo de uso:
# # def main(page: ft.Page):
# #     cpv_manager = CPVFilterManager()
# #     page.add(cpv_manager.get_control())

# # ft.app(target=main)
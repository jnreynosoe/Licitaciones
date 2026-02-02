import flet as ft 
import pandas as pd
try:
    from grupos_cpv import DialogoGrupoCPV, GestorGruposCPV, PanelGruposGuardados
except:
    from .grupos_cpv import DialogoGrupoCPV, GestorGruposCPV, PanelGruposGuardados

# ===============================================================
# COMPONENTE: Filtro CPV
# ===============================================================
class FiltroCPV(ft.Container):
    def __init__(self, df_cpv: pd.DataFrame, gestor_grupos: GestorGruposCPV):
        super().__init__()
        self.df_cpv = df_cpv
        self.gestor_grupos = gestor_grupos
        self.seleccionados = []
        self.opciones = [f"{row.codigo} - {row.descripcion}" for _, row in df_cpv.iterrows()]
        self.page = None  # Se asignará cuando se agregue a la página

    def build(self):
        self.txt_busqueda = ft.TextField(
            label="Buscar CPV (mínimo 4 caracteres)",
            width=500,
            on_change=self.actualizar_lista,
        )
        self.lista_resultados = ft.ListView(height=200, spacing=3)
        self.chips_container = ft.Row(wrap=True, spacing=5, scroll="auto")
        
        # Botón para crear nuevo grupo
        btn_crear_grupo = ft.ElevatedButton(
            "➕ Crear grupo de CPVs",
            icon=ft.Icons.CREATE_NEW_FOLDER,
            on_click=self._abrir_dialogo_grupo,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE,
            ),
        )
        
        # Panel de grupos guardados
        self.panel_grupos = PanelGruposGuardados(
            gestor=self.gestor_grupos,
            on_aplicar_grupo=self._aplicar_grupo,
            on_editar_grupo=self._editar_grupo,
        )

        self.content = ft.Column(
            [
                ft.Text("Códigos CPV", size=16, weight="bold"),
                btn_crear_grupo,
                ft.Divider(),
                self.panel_grupos,
                ft.Divider(),
                self.txt_busqueda,
                self.lista_resultados,
                ft.Divider(),
                ft.Text("Seleccionados:", size=14),
                self.chips_container,
            ],
            spacing=10,
            scroll="auto",
        )

    def actualizar_lista(self, e):
        texto = e.control.value.lower().strip()
        self.lista_resultados.controls.clear()

        if len(texto) < 4:
            self.lista_resultados.controls.append(
                ft.Text("🔎 Escribe al menos 4 caracteres para buscar.")
            )
        else:
            coincidencias = [op for op in self.opciones if texto in op.lower()]
            if coincidencias:
                for op in coincidencias[:50]:
                    self.lista_resultados.controls.append(
                        ft.TextButton(op, on_click=lambda e, op=op: self.agregar_chip(op))
                    )
            else:
                self.lista_resultados.controls.append(
                    ft.Text("⚠️ No se encontraron coincidencias.", color=ft.Colors.RED_400)
                )
        self.update()

    def agregar_chip(self, op):
        if op not in self.seleccionados:
            self.seleccionados.append(op)
            self.chips_container.controls.append(
                ft.Chip(label=ft.Text(op), on_delete=lambda e, op=op: self.eliminar_chip(op))
            )
        self.update()

    def eliminar_chip(self, op):
        self.seleccionados.remove(op)
        self.chips_container.controls[:] = [c for c in self.chips_container.controls if c.label.value != op]
        self.update()
    
    def _abrir_dialogo_grupo(self, e):
        if not self.page:
            return
        
        def guardar_grupo(grupo):
            self.gestor_grupos.guardar_grupo(grupo)
            self.panel_grupos.actualizar_lista()
            self.panel_grupos.update()
            
            # Mostrar notificación
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Grupo '{grupo['nombre']}' guardado correctamente"),
                bgcolor=ft.Colors.GREEN_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        dialogo = DialogoGrupoCPV(
            df_cpv=self.df_cpv,
            on_guardar=guardar_grupo,
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def _editar_grupo(self, grupo):
        if not self.page:
            return
        
        def guardar_grupo_editado(grupo_actualizado):
            self.gestor_grupos.guardar_grupo(grupo_actualizado)
            self.panel_grupos.actualizar_lista()
            self.panel_grupos.update()
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Grupo '{grupo_actualizado['nombre']}' actualizado"),
                bgcolor=ft.Colors.GREEN_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        dialogo = DialogoGrupoCPV(
            df_cpv=self.df_cpv,
            on_guardar=guardar_grupo_editado,
            grupo_existente=grupo,
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def _aplicar_grupo(self, grupo):
        # Limpiar selección actual
        self.seleccionados.clear()
        self.chips_container.controls.clear()
        
        # Aplicar CPVs del grupo
        for cpv in grupo["cpvs"]:
            self.agregar_chip(cpv)
        
        # Notificación
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Grupo '{grupo['nombre']}' aplicado ({len(grupo['cpvs'])} CPVs)"),
                bgcolor=ft.Colors.BLUE_400,
            )
            self.page.snack_bar.open = True
            self.page.update()


# ===============================================================
# COMPONENTE: Filtros generales
# ===============================================================
class PanelFiltros(ft.Container):
    def __init__(self, df_cpv: pd.DataFrame, on_filtrar):
        super().__init__()
        self.df_cpv = df_cpv
        self.on_filtrar = on_filtrar

        # Inicializar gestor de grupos
        self.gestor_grupos = GestorGruposCPV()

        # Subcomponentes
        self.filtro_cpv = FiltroCPV(self.df_cpv, self.gestor_grupos)

        self.lugares = [
            "Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Cantabria",
            "Castilla y León", "Castilla - La Mancha", "Cataluña", "Ceuta", "Extremadura",
            "Galicia", "La Rioja", "Comunidad de Madrid", "Melilla", "Región de Murcia", "Navarra",
            "País Vasco", "Comunidad Valenciana"
        ]
        self.lugar_dropdown = ft.Dropdown(
            label="Lugar de ejecución",
            options=[ft.dropdown.Option(l) for l in self.lugares],
            width=400,
            autofocus=False,
        )

        self.entidades = [
            "AGE", "CCAA", "Entidades locales (643)", "Otras entidades", "Universidades"
        ]
        self.checkboxes_entidades = [ft.Checkbox(label=e) for e in self.entidades]

        self.slider_importe = ft.RangeSlider(
            min=0,
            max=1_000_000,
            divisions=100,
            start_value=0,
            end_value=500_000,
            expand=True,
            label="{value} €",
        )

        self.slider_valores = ft.Row(
            [
                ft.Text("0 €"),
                ft.Text("1.000.000 €"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.boton_filtrar = ft.ElevatedButton(
            "Ver licitaciones",
            icon=ft.Icons.SEARCH,
            on_click=lambda e: self.on_filtrar(self.get_filtros()),
            style=ft.ButtonStyle(padding=20),
        )

        # Estructura visual principal
        self.content = ft.Row(
            [
                # Columna izquierda — solo CPV
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("🧾 Códigos CPV", size=18, weight="bold"),
                            self.filtro_cpv,
                        ],
                        spacing=10,
                        scroll="auto"
                    ),
                    expand=2,
                    padding=10,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=10,
                ),

                # Columna derecha — resto de filtros
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("🎯 Otros filtros", size=18, weight="bold"),
                            self.lugar_dropdown,
                            self.slider_importe,
                            self.slider_valores,
                            ft.Row(self.checkboxes_entidades, wrap=True),
                            ft.Divider(),
                            ft.Row(
                                [self.boton_filtrar],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        spacing=15,
                        scroll="auto"
                    ),
                    expand=1,
                    padding=10,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=10,
                ),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )

        # Estilo del contenedor principal
        self.padding = 20
        self.border_radius = 15
        self.border = ft.border.all(1, ft.Colors.GREY_400)
        self.bgcolor = ft.Colors.WHITE
        self.expand = True
    
    def did_mount(self):
        # Asignar la página al filtro CPV cuando se monte el componente
        self.filtro_cpv.page = self.page

    def get_filtros(self):
        entidades = [c.label for c in self.checkboxes_entidades if c.value]
        return {
            "cpv": self.filtro_cpv.seleccionados,
            "lugar": self.lugar_dropdown.value,
            "importe_min": self.slider_importe.start_value,
            "importe_max": self.slider_importe.end_value,
            "entidades": entidades,
        }
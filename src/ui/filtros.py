import flet as ft 
import pandas as pd
import datetime
import json
try:
    from grupos_cpv import DialogoGrupoCPV, GestorGruposCPV, PanelGruposGuardados
    from busquedas_guardadas import DialogoGuardarBusqueda, GestorBusquedas, PanelBusquedasGuardadas, DialogoEditarBusqueda
except:
    from .grupos_cpv import DialogoGrupoCPV, GestorGruposCPV, PanelGruposGuardados
    from .busquedas_guardadas import DialogoGuardarBusqueda, GestorBusquedas, PanelBusquedasGuardadas, DialogoEditarBusqueda

class GestorCPVsDescartados:
    """Gestor para manejar la lista de CPVs descartados"""
    def __init__(self):
        self.archivo = "cpvs_descartados.json"
        self.cpvs_descartados = self._cargar_descartados()
    
    def _cargar_descartados(self):
        """Carga los CPVs descartados desde el archivo"""
        try:
            with open(self.archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def guardar_descartados(self, cpvs):
        """Guarda la lista de CPVs descartados"""
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(cpvs, f, ensure_ascii=False, indent=2)
        self.cpvs_descartados = cpvs
    
    def agregar_descartado(self, cpv):
        """Agrega un CPV a la lista de descartados"""
        if cpv not in self.cpvs_descartados:
            self.cpvs_descartados.append(cpv)
            self.guardar_descartados(self.cpvs_descartados)
    
    def eliminar_descartado(self, cpv):
        """Elimina un CPV de la lista de descartados"""
        if cpv in self.cpvs_descartados:
            self.cpvs_descartados.remove(cpv)
            self.guardar_descartados(self.cpvs_descartados)
    
    def obtener_descartados(self):
        """Retorna la lista de CPVs descartados"""
        return self.cpvs_descartados


class DialogoCPVsDescartados(ft.AlertDialog):
    """Diálogo para gestionar CPVs descartados"""
    def __init__(self, df_cpv: pd.DataFrame, gestor_descartados: GestorCPVsDescartados,
                 gestor_grupos: GestorGruposCPV, gestor_busquedas: GestorBusquedas,
                 on_actualizar):
        super().__init__()
        # self.page = None
        self.df_cpv = df_cpv
        self.gestor_descartados = gestor_descartados
        self.gestor_grupos = gestor_grupos
        self.gestor_busquedas = gestor_busquedas
        self.on_actualizar = on_actualizar
        
        self.opciones_disponibles = [
            f"{row.codigo} - {row.descripcion}" 
            for _, row in df_cpv.iterrows()
        ]
        
        self.descartados_actuales = list(gestor_descartados.obtener_descartados())
        
        self.modal = True
        self.title = ft.Text("⚙️ Gestionar CPVs Descartados", size=20, weight="bold")
        
        # Campo de búsqueda
        self.txt_busqueda = ft.TextField(
            label="Buscar CPV para descartar (mínimo 4 caracteres)",
            width=600,
            on_change=self._actualizar_lista_busqueda,
        )
        
        self.lista_busqueda = ft.ListView(height=200, spacing=3)
        
        # Lista de CPVs descartados actuales
        self.lista_descartados = ft.ListView(height=250, spacing=5)
        self._actualizar_lista_descartados()
        
        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Agregar CPVs a la lista de descartados:", size=14, weight="bold"),
                    self.txt_busqueda,
                    self.lista_busqueda,
                    ft.Divider(),
                    ft.Text("CPVs descartados actualmente:", size=14, weight="bold"),
                    ft.Text("Estos CPVs no aparecerán en los filtros de búsqueda", 
                           size=12, italic=True, color=ft.Colors.GREY_700),
                    self.lista_descartados,
                ],
                spacing=10,
                scroll="auto",
            ),
            width=700,
            height=600,
        )
        
        self.actions = [
            ft.TextButton("Cerrar", on_click=self._cerrar),
        ]
    
    def _actualizar_lista_busqueda(self, e):
        """Actualiza la lista de resultados de búsqueda"""
        texto = e.control.value.lower().strip()
        self.lista_busqueda.controls.clear()
        
        if len(texto) < 4:
            self.lista_busqueda.controls.append(
                ft.Text("🔎 Escribe al menos 4 caracteres para buscar.")
            )
        else:
            # Filtrar opciones que no estén ya descartadas
            coincidencias = [
                op for op in self.opciones_disponibles 
                if texto in op.lower() and op not in self.descartados_actuales
            ]
            
            if coincidencias:
                for op in coincidencias[:50]:
                    self.lista_busqueda.controls.append(
                        ft.ListTile(
                            title=ft.Text(op, size=12),
                            trailing=ft.IconButton(
                                icon=ft.Icons.BLOCK,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Descartar este CPV",
                                on_click=lambda e, cpv=op: self._descartar_cpv(cpv),
                            ),
                        )
                    )
            else:
                self.lista_busqueda.controls.append(
                    ft.Text("⚠️ No se encontraron coincidencias.", color=ft.Colors.RED_400)
                )
        
        self.update()
    
    def _descartar_cpv(self, cpv):
        """Descarta un CPV y verifica si está en grupos o búsquedas"""
        # Verificar si el CPV está en algún grupo
        grupos_afectados = []
        for grupo in self.gestor_grupos.grupos:
            if cpv in grupo["cpvs"]:
                grupos_afectados.append(grupo)
        
        # Verificar si el CPV está en alguna búsqueda guardada
        busquedas_afectadas = []
        for busqueda in self.gestor_busquedas.busquedas:
            if cpv in busqueda["filtros"].get("cpv", []):
                busquedas_afectadas.append(busqueda)
        
        # Si hay grupos o búsquedas afectados, mostrar diálogo de confirmación
        if grupos_afectados or busquedas_afectadas:
            self._mostrar_dialogo_confirmacion(cpv, grupos_afectados, busquedas_afectadas)
        else:
            # Si no hay conflictos, descartar directamente
            self._confirmar_descarte(cpv, [], [])
    
    def _mostrar_dialogo_confirmacion(self, cpv, grupos_afectados, busquedas_afectadas):
        """Muestra un diálogo preguntando si eliminar el CPV de grupos y búsquedas"""
        mensaje_partes = [f"El CPV '{cpv}' está presente en:"]
        
        if grupos_afectados:
            mensaje_partes.append(f"\n📁 Grupos ({len(grupos_afectados)}):")
            for grupo in grupos_afectados:
                mensaje_partes.append(f"  • {grupo['nombre']}")
        
        if busquedas_afectadas:
            mensaje_partes.append(f"\n🔍 Búsquedas guardadas ({len(busquedas_afectadas)}):")
            for busqueda in busquedas_afectadas:
                mensaje_partes.append(f"  • {busqueda['nombre']}")
        
        mensaje_partes.append("\n¿Deseas eliminarlo de estos grupos y búsquedas?")
        
        dialogo_confirmacion = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ CPV en uso", weight="bold"),
            content=ft.Text("\n".join(mensaje_partes)),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=lambda e: self._cerrar_dialogo_confirmacion(dialogo_confirmacion),
                ),
                ft.TextButton(
                    "Eliminar de grupos/búsquedas",
                    on_click=lambda e: self._confirmar_descarte_con_eliminacion(
                        cpv, grupos_afectados, busquedas_afectadas, dialogo_confirmacion
                    ),
                ),
            ],
        )
        
        self.page.overlay.append(dialogo_confirmacion)
        dialogo_confirmacion.open = True
        self.page.update()
    
    def _confirmar_descarte_con_eliminacion(self, cpv, grupos_afectados, 
                                           busquedas_afectadas, dialogo_confirmacion):
        """Confirma el descarte y elimina el CPV de grupos y búsquedas"""
        self._cerrar_dialogo_confirmacion(dialogo_confirmacion)
        self._confirmar_descarte(cpv, grupos_afectados, busquedas_afectadas)
    
    def _cerrar_dialogo_confirmacion(self, dialogo):
        """Cierra el diálogo de confirmación"""
        dialogo.open = False
        self.page.update()
        self.page.overlay.remove(dialogo)
    
    def _confirmar_descarte(self, cpv, grupos_afectados, busquedas_afectadas):
        """Confirma el descarte del CPV y actualiza grupos y búsquedas"""
        # Eliminar de grupos
        for grupo in grupos_afectados:
            grupo["cpvs"].remove(cpv)
            self.gestor_grupos.guardar_grupo(grupo)
        
        # Eliminar de búsquedas
        for busqueda in busquedas_afectadas:
            busqueda["filtros"]["cpv"].remove(cpv)
            self.gestor_busquedas.guardar_busqueda(busqueda)
        
        # Agregar a descartados
        self.descartados_actuales.append(cpv)
        self.gestor_descartados.agregar_descartado(cpv)
        
        # Actualizar interfaz
        self._actualizar_lista_descartados()
        self.txt_busqueda.value = ""
        self.lista_busqueda.controls.clear()
        
        # Mostrar notificación
        mensaje = f"✅ CPV descartado correctamente"
        if grupos_afectados or busquedas_afectadas:
            mensaje += f" (eliminado de {len(grupos_afectados)} grupos y {len(busquedas_afectadas)} búsquedas)"
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=ft.Colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.update()
    
    def _actualizar_lista_descartados(self):
        """Actualiza la lista de CPVs descartados"""
        self.lista_descartados.controls.clear()
        
        if not self.descartados_actuales:
            self.lista_descartados.controls.append(
                ft.Text("No hay CPVs descartados", italic=True, color=ft.Colors.GREY_500)
            )
        else:
            for cpv in sorted(self.descartados_actuales):
                self.lista_descartados.controls.append(
                    ft.ListTile(
                        title=ft.Text(cpv, size=12),
                        trailing=ft.IconButton(
                            icon=ft.Icons.RESTORE,
                            icon_color=ft.Colors.GREEN_400,
                            tooltip="Restaurar este CPV",
                            on_click=lambda e, cpv=cpv: self._restaurar_cpv(cpv),
                        ),
                    )
                )
        
        # self.update()
    
    def _restaurar_cpv(self, cpv):
        """Restaura un CPV descartado"""
        self.descartados_actuales.remove(cpv)
        self.gestor_descartados.eliminar_descartado(cpv)
        self._actualizar_lista_descartados()
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"✅ CPV '{cpv}' restaurado correctamente"),
            bgcolor=ft.Colors.BLUE_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _cerrar(self, e):
        """Cierra el diálogo y actualiza el filtro principal"""
        self.open = False
        self.on_actualizar()
        self.page.update()


class FiltroCPV(ft.Container):
    def __init__(self, df_cpv: pd.DataFrame, gestor_grupos: GestorGruposCPV, 
                 gestor_descartados: GestorCPVsDescartados):#, page:ft.Page):
        super().__init__()
        self.df_cpv = df_cpv
        self.gestor_grupos = gestor_grupos
        self.gestor_descartados = gestor_descartados
        self.seleccionados = []
        # self.page = page
        self._actualizar_opciones()

    def _actualizar_opciones(self):
        """Actualiza las opciones disponibles excluyendo los descartados"""
        descartados = set(self.gestor_descartados.obtener_descartados())
        self.opciones = [
            f"{row.codigo} - {row.descripcion}" 
            for _, row in self.df_cpv.iterrows()
            if f"{row.codigo} - {row.descripcion}" not in descartados
        ]

    def build(self):
        self.txt_busqueda = ft.TextField(
            label="Buscar CPV (mínimo 4 caracteres)",
            width=500,
            on_change=self.actualizar_lista,
        )
        self.lista_resultados = ft.ListView(height=200, spacing=3)
        self.chips_container = ft.Column(
            spacing=5,
            scroll="auto",  # Permite scroll interno
            height=120,     # Altura fija para evitar desplazamiento
        )
        
        btn_crear_grupo = ft.Button(
            "Crear grupo de CPVs",
            icon=ft.Icons.CREATE_NEW_FOLDER,
            on_click=self._abrir_dialogo_grupo,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE,
            ),
        )
        
        self.panel_grupos = PanelGruposGuardados(
            gestor=self.gestor_grupos,
            on_aplicar_grupo=self._aplicar_grupo,
            on_editar_grupo=self._editar_grupo,
        )

        self.boton_borrar = ft.Button(
            "Eliminar todos los CPVs",
            icon = ft.Icons.PHONELINK_ERASE,
            on_click = self.eliminar_todos_los_cpvs,
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
                ft.Container(
                    content= self.chips_container,
                    height = 120,
                    border = ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius= 5,
                    padding= 10,
                ),
                self.boton_borrar,
            ],
            spacing=10,
            scroll="auto",
        )
        
    def eliminar_todos_los_cpvs(self,e):
        self.seleccionados.clear()
        self.chips_container.controls.clear()
        self.update()

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
        # dialogo.page = self.page
        dialogo.open = True
        # dialogo._actualizar_lista()
        self.page.update()
    
    def _abrir_configuracion(self, e):
        """Abre el menú de configuración"""
        if not self.page:
            return
        
        def abrir_cpvs_descartados(e):
            menu_config.open = False
            self.page.update()
            self._abrir_dialogo_cpvs_descartados()
        
        menu_config = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚙️ Configuración", size=20, weight="bold"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.BLOCK, color=ft.Colors.RED_400),
                            title=ft.Text("CPVs Descartados"),
                            subtitle=ft.Text("Gestionar CPVs que no quieres ver en los filtros"),
                            on_click=abrir_cpvs_descartados,
                        ),
                    ],
                    spacing=10,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self._cerrar_dialogo(menu_config)),
            ],
        )
        
        self.page.overlay.append(menu_config)
        menu_config.open = True
        self.page.update()
    
    def _abrir_dialogo_cpvs_descartados(self):
        """Abre el diálogo de gestión de CPVs descartados"""
        if not self.page:
            return
        
        def actualizar_filtros():
            # Actualizar las opciones disponibles en el filtro CPV
            self.filtro_cpv._actualizar_opciones()
            
            # Limpiar CPVs seleccionados que ahora estén descartados
            descartados = set(self.gestor_descartados.obtener_descartados())
            self.filtro_cpv.seleccionados = [
                cpv for cpv in self.filtro_cpv.seleccionados 
                if cpv not in descartados
            ]
            
            # Actualizar chips
            self.filtro_cpv.chips_container.controls = [
                c for c in self.filtro_cpv.chips_container.controls 
                if c.label.value not in descartados
            ]
            
            self.filtro_cpv.update()
            self.page.update()
        
        dialogo = DialogoCPVsDescartados(
            df_cpv=self.df_cpv,
            gestor_descartados=self.gestor_descartados,
            gestor_grupos=self.gestor_grupos,
            gestor_busquedas=self.gestor_busquedas,
            on_actualizar=actualizar_filtros,
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def _cerrar_dialogo(self, dialogo):
        """Cierra un diálogo genérico"""
        dialogo.open = False
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
        # self.page.update()
    
    def _aplicar_grupo(self, grupo):
        self.seleccionados.clear()
        self.chips_container.controls.clear()
        
        for cpv in grupo["cpvs"]:
            self.agregar_chip(cpv)
        
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Grupo '{grupo['nombre']}' aplicado ({len(grupo['cpvs'])} CPVs)"),
                bgcolor=ft.Colors.BLUE_400,
            )
            self.page.snack_bar.open = True
            self.page.update()


class PanelFiltros(ft.Container):
    def __init__(self,usuario:str, df_cpv: pd.DataFrame, on_filtrar, page:ft.Page):
        super().__init__()
        self.df_cpv = df_cpv
        self.usuario_actual = usuario
        self.on_filtrar = on_filtrar
        # self.page = page

        # Inicializar gestores
        self.gestor_grupos = GestorGruposCPV(self.usuario_actual)
        self.gestor_busquedas = GestorBusquedas(self.usuario_actual)
        self.gestor_descartados = GestorCPVsDescartados()

        # Subcomponentes
        self.filtro_cpv = FiltroCPV(self.df_cpv, self.gestor_grupos, self.gestor_descartados)#,self.page)

        self.lugares = [
            "Todos","Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Comunidad Autónoma de Cantabria",
            "Castilla y León", "Castilla - La Mancha", "Cataluña", "Ceuta", "Extremadura",
            "Galicia", "La Rioja", "Comunidad de Madrid", "Melilla", "Región de Murcia", "Navarra",
            "País Vasco", "Comunidad Valenciana",
        ]
        self.lugar_dropdown = ft.Dropdown(
            label="Lugar de ejecución",
            options=[ft.dropdown.Option(l) for l in self.lugares],
            width=400,
            autofocus=False,
        )

        self.entidades = [
            "ADMINISTRACIÓN GENERAL DEL ESTADO", "COMUNIDADES Y CIUDADES AUTÓNOMAS", "ENTIDADES LOCALES", "OTRAS ENTIDADES DEL SECTOR PÚBLICO",#, "Universidades"
        ]
        self.checkboxes_entidades = [ft.Checkbox(label=e) for e in self.entidades]

        # Estados de licitación
        self.estados = {
            "PUB": "Publicado",
            "EV": "Evaluado", 
            "ADJ": "Adjudicado",
            "RES": "Resuelto",
            "PRE": "Anuncio Previo"
        }
        self.checkboxes_estados = [
            ft.Checkbox(label=f"{nombre}", value=False) 
            for codigo, nombre in self.estados.items()
        ]

        self.slider_importe = ft.RangeSlider(
            min=0,
            max=10_000_000,
            divisions=100,
            start_value=0,
            end_value=500_000,
            expand=True,
            label="{value} €",
        )

        self.slider_valores = ft.Row(
            [
                ft.Text("0 €"),
                ft.Text("10.000.000 €"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # DatePickers
        self.fecha_desde_picker = ft.DatePicker(
            first_date=datetime.date(2000, 1, 1),
            last_date=datetime.date(2100, 12, 31),
            on_change=self._on_fecha_desde,
        )

        self.fecha_hasta_picker = ft.DatePicker(
            first_date=datetime.date(2000, 1, 1),
            last_date=datetime.date(2100, 12, 31),
            on_change=self._on_fecha_hasta,
        )

        self.fecha_desde = ft.TextField(
            label="Fecha límite desde",
            read_only=False,
            width=180,
            # on_click=lambda e: self.page.open(self.fecha_desde_picker),
            # on_click=lambda e: self.mostrar_picker(self.fecha_desde_picker),
            on_click= self.abrir_calendario_desde
        )

        self.fecha_hasta = ft.TextField(
            label="Fecha límite hasta",
            read_only=False,
            width=180,
            # on_click=lambda e: self.page.open(self.fecha_hasta_picker),
            # on_click=lambda e: self.mostrar_picker(self.fecha_hasta_picker),
            on_click = self.abrir_calendario_hasta
        )

        # DatePickers_Publicacion
        self.fecha_desde_picker_p = ft.DatePicker(
            first_date=datetime.date(2000, 1, 1),
            last_date=datetime.date(2100, 12, 31),
            on_change=self._on_fecha_desde_pub,
        )

        """self.fecha_hasta_picker = ft.DatePicker(
            first_date=datetime.date(2000, 1, 1),
            last_date=datetime.date(2100, 12, 31),
            on_change=self._on_fecha_hasta,
        )"""

        self.fecha_hasta_picker_p = ft.DatePicker(
            first_date=datetime.date(2000, 1, 1),
            last_date=datetime.date(2100, 12, 31),
            on_change=self._on_fecha_hasta_pub,
        )

        self.fecha_desde_publicacion = ft.TextField(
            label="Fecha publicación desde",
            read_only=False,
            width=180,
            # on_click=lambda e: self.page.open(self.fecha_desde_picker_p),
            # on_click=lambda e: self.mostrar_picker(self.fecha_desde_picker_p),
            on_click=self.abrir_calendario_desde_p
        )

        self.fecha_hasta_publicacion = ft.TextField(
            label="Fecha publicación hasta",
            read_only=False,
            width=180,
            # on_click=lambda e: self.page.open(self.fecha_hasta_picker_p),
            # on_click=lambda e: self.mostrar_picker(self.fecha_hasta_picker_p)
            on_click= self.abrir_calendario_hasta_p,
        )
        

        # Panel de búsquedas guardadas
        self.panel_busquedas = PanelBusquedasGuardadas(
            gestor=self.gestor_busquedas,
            on_aplicar=self._aplicar_busqueda_guardada,
            on_eliminar=self._eliminar_busqueda,
            on_editar=self._editar_busqueda_guardada,
        )

        # BUSCADOR RÁPIDO 
        self.txt_palabras_clave = ft.TextField(
            label="🔍 Búsqueda rápida por palabras clave",
            hint_text="Ej: mantenimiento, software, energía",
            expand=True,
        )

        self.chk_incluir_pdf = ft.Checkbox(
            label="Buscar también en los documentos asociados (PDFs)",
            value=False,
        )

        self.boton_guardar_busqueda = ft.Button(
            "Guardar búsqueda",
            icon=ft.Icons.SAVE_AS_OUTLINED,
            on_click=self._abrir_dialogo_guardar_busqueda,
            style=ft.ButtonStyle(
                padding=20,
                bgcolor=ft.Colors.GREEN_500,
                color=ft.Colors.WHITE,
            ),
        )

        self.boton_filtrar = ft.Button(
            "Ver licitaciones",
            icon=ft.Icons.SEARCH,
            on_click=lambda e: self.on_filtrar(self.get_filtros()),
            style=ft.ButtonStyle(
                padding=20,
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE,),
        )

        # Botón de configuración
        self.boton_configuracion = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            tooltip="Configuración",
            on_click=self._abrir_configuracion,
            icon_color=ft.Colors.BLUE_700,
            icon_size=30,
        )

        # BARRA DE BÚSQUEDA RÁPIDA EN LA PARTE SUPERIOR
        barra_busqueda_rapida = ft.Container(
            content=ft.Row(
                [
                    self.txt_palabras_clave,
                    self.chk_incluir_pdf,
                    self.boton_filtrar,
                    self.boton_configuracion,
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=15,
            border=ft.Border.all(2, ft.Colors.BLUE_400),
            border_radius=10,
            bgcolor=ft.Colors.BLUE_50,
        )

        # Estructura visual principal
        self.content = ft.Column(
            [
                # BUSCADOR RÁPIDO SUPERIOR
                barra_busqueda_rapida,
                
                ft.Divider(height=20, thickness=2),
                
                # FILA DE FILTROS DETALLADOS
                ft.Row(
                    [
                        # Columna izquierda — CPV
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
                            border=ft.Border.all(1, ft.Colors.GREY_400),
                            border_radius=10,
                        ),

                        # Columna central — Otros filtros
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("🎯 Otros filtros", size=18, weight="bold"),
                                    self.lugar_dropdown,

                                    # Sección de fechas publicacion
                                    ft.Text("📅 Fecha de publicación", size=16, weight="bold"),
                                    ft.Row([self.fecha_desde_publicacion, self.fecha_hasta_publicacion], spacing=10),
                                    
                                    # Sección de fechas
                                    ft.Text("📅 Fecha límite de presentación", size=16, weight="bold"),
                                    # ft.Row([self.fecha_desde, self.fecha_hasta], spacing=10),
                                    ## Este cambio lo hago por la falta de necesidad de delimitar las fechas limite.
                                    # Pero lo conservo por nostalgia
                                    ft.Row([self.fecha_desde], spacing=10),
                                    
                                    
                                    # Sección de estados
                                    ft.Text("📊 Estado de la licitación", size=16, weight="bold"),
                                    ft.Row(self.checkboxes_estados, wrap=True, spacing=5),
                                    
                                    ft.Divider(),
                                    ft.Text("💲​​ Importe", size=16, weight="bold"),
                                    self.slider_importe,
                                    self.slider_valores,
                                    
                                    ft.Text("🏢 Tipo de entidad", size=16, weight="bold"),
                                    ft.Row(self.checkboxes_entidades, wrap=True),
                                    
                                    
                                ],
                                spacing=15,
                                alignment=ft.MainAxisAlignment.START,
                                scroll="auto"
                            ),
                            expand=1,
                            padding=10,
                            border=ft.Border.all(1, ft.Colors.GREY_400),
                            border_radius=10,
                        ),

                        # Columna derecha — Búsquedas guardadas
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [self.boton_guardar_busqueda],
                                        alignment=ft.MainAxisAlignment.END,
                                    ),
                                    ft.Divider(),
                                    self.panel_busquedas,
                                ],
                                scroll="auto"
                            ),
                            expand=1,
                            padding=10,
                            border=ft.Border.all(1, ft.Colors.GREY_400),
                            border_radius=10,
                        ),
                    ],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.START,  # 👈 fuerza que todo quede arriba
                    expand=True,
                ),
            ],
            spacing=10,
            expand=True,
        )

        # Estilo del contenedor principal
        self.padding = 20
        self.border_radius = 15
        self.border = ft.Border.all(1, ft.Colors.GREY_400)
        self.bgcolor = ft.Colors.WHITE
        self.expand = True
    
    # def did_mount(self):
    #     # Asignar la página al filtro CPV cuando se monte el componente
    #     self.filtro_cpv.page = self.page
    ## Cambio ante actualizacion de Flet

    
    async def mostrar_picker(self, picker):
        picker.open = True
        self.page.update()

    async def abrir_calendario_desde(self, e):
        await self.mostrar_picker(self.fecha_desde_picker)

    async def abrir_calendario_hasta(self, e):
        await self.mostrar_picker(self.fecha_hasta_picker)

    async def abrir_calendario_desde_p(self, e):
        await self.mostrar_picker(self.fecha_desde_picker_p)

    async def abrir_calendario_hasta_p(self, e):
        await self.mostrar_picker(self.fecha_hasta_picker_p)

    # async def mostrar_picker(self, picker):
    #     # 1. Verificar si el picker ya está en la página, si no, añadirlo al overlay
    #     if picker not in self.page.overlay:
    #         self.page.overlay.append(picker)
        
    #     # 2. Abrir el picker (forma moderna)
    #     # self.page.open(picker)
    #     # 3. No olvides el await update
    #     self.page.update()

    def did_mount(self):
        # Ya no es necesario: self.filtro_cpv.page = self.page
        # Simplemente usa el componente:
        # print(f"El filtro CPV ya tiene acceso a: {self.filtro_cpv.page}")
         # Agregar pickers al overlay si no están ya
        if self.fecha_desde_picker not in self.page.overlay:
            self.page.overlay.append(self.fecha_desde_picker)
        if self.fecha_hasta_picker not in self.page.overlay:
            self.page.overlay.append(self.fecha_hasta_picker)
        if self.fecha_desde_picker_p not in self.page.overlay:
            self.page.overlay.append(self.fecha_desde_picker_p)
        if self.fecha_hasta_picker_p not in self.page.overlay:
            self.page.overlay.append(self.fecha_hasta_picker_p)
        self.filtro_cpv.update()

    def will_unmount(self):
        """Se ejecuta cuando el control se desmonta de la página"""
        # Limpiar pickers del overlay
        if self.fecha_desde_picker in self.page.overlay:
            self.page.overlay.remove(self.fecha_desde_picker)
        if self.fecha_hasta_picker in self.page.overlay:
            self.page.overlay.remove(self.fecha_hasta_picker)
        if self.fecha_desde_picker_p in self.page.overlay:
            self.page.overlay.remove(self.fecha_desde_picker_p)
        if self.fecha_hasta_picker_p in self.page.overlay:
            self.page.overlay.remove(self.fecha_hasta_picker_p)

    def get_filtros(self):
        entidades = [c.label for c in self.checkboxes_entidades if c.value]
        
        # Extraer estados seleccionados
        estados_aux = [c.label.split(" - ")[0] for c in self.checkboxes_estados if c.value]
        invertido = {v: k for k, v in self.estados.items()}
        # print("INVERTIOD",invertido, "ESTADO AUX", estados_aux)
        estados = [invertido[es] for es in estados_aux]
        
        palabras_clave = []
        if self.txt_palabras_clave.value:
            palabras_clave = [p.strip().lower() for p in self.txt_palabras_clave.value.split(",") if p.strip()]
        
        # Parsear fechas
        fecha_desde_dt = None
        fecha_hasta_dt = None
        
        if self.fecha_desde.value:
            try:
                fecha_desde_dt = datetime.datetime.strptime(self.fecha_desde.value, "%d/%m/%Y")
            except ValueError:
                pass
        
        if self.fecha_hasta.value:
            try:
                fecha_hasta_dt = datetime.datetime.strptime(self.fecha_hasta.value, "%d/%m/%Y")
            except ValueError:
                pass

        # Parsear fechas publicacion
        fecha_desde_dt_p = None
        fecha_hasta_dt_p = None
        
        if self.fecha_desde.value:
            try:
                fecha_desde_dt_p = datetime.datetime.strptime(self.fecha_desde_publicacion.value, "%d/%m/%Y")
            except ValueError:
                pass
        
        if self.fecha_hasta.value:
            try:
                fecha_hasta_dt_p = datetime.datetime.strptime(self.fecha_hasta_publicacion.value, "%d/%m/%Y")
            except ValueError:
                pass
        
        return {
            "cpv": self.filtro_cpv.seleccionados,
            "lugar": self.lugar_dropdown.value,
            "importe_min": self.slider_importe.start_value,
            "importe_max": self.slider_importe.end_value,
            "entidades": entidades,
            "estados": estados,
            "fecha_desde": fecha_desde_dt,
            "fecha_hasta": fecha_hasta_dt,
            "fecha_desde_publicado": fecha_desde_dt_p,
            "fecha_hasta_publicado": fecha_hasta_dt_p,
            "palabras_clave": palabras_clave,
            "incluir_pdf": self.chk_incluir_pdf.value,
        }
        
    def _abrir_dialogo_guardar_busqueda(self, e):
        """Abre el diálogo para guardar la búsqueda actual"""
        if not self.page:
            return
        
        # Obtener los filtros actuales
        filtros_actuales = self.get_filtros()
        # print("filtros_actuales_previos_guardar", filtros_actuales)
        if filtros_actuales["estados"]:
            filtros_actuales["estados"] = [c.label.split(" - ")[0] for c in self.checkboxes_estados if c.value]
        
        # Verificar si hay filtros aplicados
        if not any([
            filtros_actuales["cpv"],
            filtros_actuales["lugar"],
            filtros_actuales["entidades"],
            filtros_actuales["estados"],
            filtros_actuales["fecha_desde"],
            filtros_actuales["fecha_hasta"],
            filtros_actuales["importe_min"] > 0 or filtros_actuales["importe_max"] < 10_000_000
        ]):
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("⚠️ No hay filtros aplicados para guardar"),
                bgcolor=ft.Colors.ORANGE_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        def guardar_busqueda(busqueda):
            self.gestor_busquedas.guardar_busqueda(busqueda)
            self.panel_busquedas.actualizar_lista()
            self.panel_busquedas.update()
            
            # Mostrar notificación
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Búsqueda '{busqueda['nombre']}' guardada correctamente"),
                bgcolor=ft.Colors.GREEN_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        dialogo = DialogoGuardarBusqueda(
            filtros=filtros_actuales,
            on_guardar=guardar_busqueda,
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()

    def _on_fecha_desde(self, e):
        self.fecha_desde.value = e.control.value.strftime("%d/%m/%Y")
        self.page.update()

    def _on_fecha_hasta(self, e):
        self.fecha_hasta.value = e.control.value.strftime("%d/%m/%Y")
        self.page.update()

    def _on_fecha_desde_pub(self, e):
        self.fecha_desde_publicacion.value = e.control.value.strftime("%d/%m/%Y")
        self.page.update()

    def _on_fecha_hasta_pub(self, e):
        self.fecha_hasta_publicacion.value = e.control.value.strftime("%d/%m/%Y")
        self.page.update()
    
    def _aplicar_busqueda_guardada(self, busqueda):
        """Aplica los filtros de una búsqueda guardada"""
        filtros = busqueda["filtros"]
        # print("FILTROS APLICADOS", filtros)
        
        # Aplicar CPVs
        self.filtro_cpv.seleccionados.clear()
        self.filtro_cpv.chips_container.controls.clear()
        for cpv in filtros.get("cpv", []):
            self.filtro_cpv.agregar_chip(cpv)
        
        # Aplicar lugar
        if filtros.get("lugar"):
            self.lugar_dropdown.value = filtros["lugar"]
        
        # Aplicar entidades
        for checkbox in self.checkboxes_entidades:
            checkbox.value = checkbox.label in filtros.get("entidades", [])
        
        # Aplicar estados
        for checkbox in self.checkboxes_estados:
            estado_codigo = checkbox.label.split(" - ")[0]
            checkbox.value = estado_codigo in filtros.get("estados", [])
        
        # Aplicar rangos de importe
        self.slider_importe.start_value = filtros.get("importe_min", 0)
        self.slider_importe.end_value = filtros.get("importe_max", 10_000_000)
        
        # Aplicar fechas
        fecha_desde = filtros.get("fecha_desde")
        fecha_hasta = filtros.get("fecha_hasta")
        
        if fecha_desde:
            if isinstance(fecha_desde, str):
                self.fecha_desde.value = fecha_desde
            else:
                self.fecha_desde.value = fecha_desde.strftime("%d/%m/%Y")
        else:
            self.fecha_desde.value = ""
            
        if fecha_hasta:
            if isinstance(fecha_hasta, str):
                self.fecha_hasta.value = fecha_hasta
            else:
                self.fecha_hasta.value = fecha_hasta.strftime("%d/%m/%Y")
        else:
            self.fecha_hasta.value = ""

        # Aplicar fechas publicacion
        fecha_desde_pub = filtros.get("fecha_desde_publicado")
        fecha_hasta_pub = filtros.get("fecha_hasta_publicado")
        
        if fecha_desde_pub:
            if isinstance(fecha_desde_pub, str):
                self.fecha_desde_publicacion.value = fecha_desde_pub
            else:
                self.fecha_desde_publicacion.value = fecha_desde_pub.strftime("%d/%m/%Y")
        else:
            self.fecha_desde_publicacion.value = ""
            
        if fecha_hasta_pub:
            if isinstance(fecha_hasta_pub, str):
                self.fecha_hasta_publicacion.value = fecha_hasta_pub
            else:
                self.fecha_hasta_publicacion.value = fecha_hasta_pub.strftime("%d/%m/%Y")
        else:
            self.fecha_hasta_publicacion.value = ""

        # Aplicar palabras clave
        palabras_clave = filtros.get("palabras_clave")
        
        if palabras_clave:
            if isinstance(palabras_clave, str):
                self.txt_palabras_clave.value = palabras_clave
                # self.txt_palabras_clave.
            else:
                self.txt_palabras_clave.value = ",".join(palabras_clave)
        else:
            self.txt_palabras_clave.value = ""
            
        
        # Actualizar la interfaz
        self.update()
        
        # Mostrar notificación
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Búsqueda '{busqueda['nombre']}' aplicada"),
                bgcolor=ft.Colors.BLUE_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _eliminar_busqueda(self, busqueda):
        """Elimina una búsqueda guardada"""
        self.gestor_busquedas.eliminar_busqueda(busqueda["nombre"])
        self.panel_busquedas.actualizar_lista()
        
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"🗑️ Búsqueda '{busqueda['nombre']}' eliminada"),
                bgcolor=ft.Colors.RED_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _abrir_configuracion(self, e):
        """Abre el menú de configuración"""
        if not self.page:
            return
        
        def abrir_cpvs_descartados(e):
            menu_config.open = False
            self.page.update()
            self._abrir_dialogo_cpvs_descartados()
        
        menu_config = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚙️ Configuración", size=20, weight="bold"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.BLOCK, color=ft.Colors.RED_400),
                            title=ft.Text("CPVs Descartados"),
                            subtitle=ft.Text("Gestionar CPVs que no quieres ver en los filtros"),
                            on_click=abrir_cpvs_descartados,
                            # on_click= self._abrir_dialogo_cpvs_descartados,
                        ),
                    ],
                    spacing=10,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self._cerrar_dialogo(menu_config)),
            ],
        )
        
        self.page.overlay.append(menu_config)
        menu_config.open = True
        self.page.update()
    
    def _abrir_dialogo_cpvs_descartados(self):
        """Abre el diálogo de gestión de CPVs descartados"""
        if not self.page:
            return
        
        def actualizar_filtros():
            # Actualizar las opciones disponibles en el filtro CPV
            self.filtro_cpv._actualizar_opciones()
            
            # Limpiar CPVs seleccionados que ahora estén descartados
            descartados = set(self.gestor_descartados.obtener_descartados())
            self.filtro_cpv.seleccionados = [
                cpv for cpv in self.filtro_cpv.seleccionados 
                if cpv not in descartados
            ]
            
            # Actualizar chips
            self.filtro_cpv.chips_container.controls = [
                c for c in self.filtro_cpv.chips_container.controls 
                if c.label.value not in descartados
            ]
            
            self.filtro_cpv.update()
            self.page.update()
        
        dialogo = DialogoCPVsDescartados(
            df_cpv=self.df_cpv,
            gestor_descartados=self.gestor_descartados,
            gestor_grupos=self.gestor_grupos,
            gestor_busquedas=self.gestor_busquedas,
            on_actualizar=actualizar_filtros,
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def _cerrar_dialogo(self, dialogo):
        """Cierra un diálogo genérico"""
        dialogo.open = False
        self.page.update()

    def _editar_busqueda_guardada(self, busqueda):
        """Abre el diálogo para editar una búsqueda guardada"""
        if not self.page:
            return
        
        # from busquedas_guardadas import DialogoEditarBusqueda
        
        def guardar_busqueda_editada(busqueda_actualizada):
            # Eliminar la búsqueda antigua si cambió el nombre
            if busqueda["nombre"] != busqueda_actualizada["nombre"]:
                self.gestor_busquedas.eliminar_busqueda(busqueda["nombre"])
            
            self.gestor_busquedas.guardar_busqueda(busqueda_actualizada)
            self.panel_busquedas.actualizar_lista()
            
            # Mostrar notificación
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Búsqueda '{busqueda_actualizada['nombre']}' actualizada"),
                bgcolor=ft.Colors.GREEN_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        dialogo = DialogoEditarBusqueda(
            busqueda=busqueda,
            on_guardar=guardar_busqueda_editada,
            df_cpv=self.df_cpv,
            lugares=self.lugares,
            entidades=self.entidades,
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
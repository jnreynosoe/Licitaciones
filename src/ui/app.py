# import flet as ft
# import pandas as pd

# try:
#     from filtros import PanelFiltros
#     from resultados import PaginaResultados
#     from detalle import PaginaDetalle
#     from busquedas_guardadas import DialogoGuardarBusqueda, GestorBusquedas, PanelBusquedasGuardadas
#     from auth import GestorUsuarios, PantallaLogin, PanelBusquedasUsuario
#     # from panel_alertas import PanelAlertas
    
# except:
#     from .filtros import PanelFiltros
#     from .resultados import PaginaResultados
#     from .detalle import PaginaDetalle
#     from .busquedas_guardadas import DialogoGuardarBusqueda, GestorBusquedas, PanelBusquedasGuardadas
#     from .auth import GestorUsuarios, PantallaLogin, PanelBusquedasUsuario
#     # from .panel_alertas import PanelAlertas

# try:
#     from data.alertas_data import Gestor_Alertas
# except:
#     from ..data.alertas_data import Gestor_Alertas

# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from utils.filtrador import filtrar_bd
# from utils.load_data import load_datasets, load_dataset

# class AppLicitaciones:
#     def __init__(self, page: ft.Page, df_general, df_requisitos, df_criterios, df_docs, df_cpv):
#         self.page = page
#         self.page.title = "Explorador de Licitaciones"
#         self.page.scroll = "adaptive"
#         self.page.padding = 20
#         self.page.theme_mode = ft.ThemeMode.LIGHT

#         # Sistema de autenticación
#         self.gestor_usuarios = GestorUsuarios()
#         self.usuario_actual = None

#         # NUEVO: Sistema de alertas
#         self.gestor_alertas = Gestor_Alertas(
#             archivo_usuarios="usuarios.json",
#             archivo_alertas="alertas.json"
#         )
#         self.panel_alertas = None
        
#         # # Gestor de búsquedas antiguo (para migración)
#         # self.gestor_busquedas_antiguo = GestorBusquedas()

#         # Estado persistente
#         self.estado = {
#             "filtros": {},
#             "df_filtrado": None,
#         }

#         # Asignar datasets
#         self.df_general = df_general
#         self.df_requisitos = df_requisitos
#         self.df_criterios = df_criterios
#         self.df_docs = df_docs
#         self.df_cpv = df_cpv
#         self.df_analisis = load_dataset(r"src\data", "analisis_resultados.parquet")
#         self.df_textos_extraidos = load_dataset(r"src", "Textos_Extraidos_viejo.parquet")

#         # Crear el panel de filtros una sola vez (se configurará después del login)
#         self.panel_filtros = None

#         # Inicializar usuario Admin con búsquedas antiguas si no existe
#         self._inicializar_admin()

#         # Mostrar pantalla de login primero
#         self.mostrar_login()

#     def _inicializar_admin(self):
#         """Inicializa el usuario Admin y migra búsquedas antiguas si existen"""
#         # Verificar si Admin ya existe
#         if "Admin" not in self.gestor_usuarios.usuarios:
#             # Crear usuario Admin
#             self.gestor_usuarios.registrar_usuario("Admin", "123456", "admin@licitaciones.com")
            
#             # Migrar búsquedas antiguas del sistema anterior
#             busquedas_antiguas = self.gestor_busquedas_antiguo.obtener_busquedas()
#             if busquedas_antiguas:
#                 for busqueda in busquedas_antiguas:
#                     self.gestor_usuarios.guardar_busqueda(
#                         "Admin",
#                         busqueda["nombre"],
#                         busqueda["filtros"]
#                     )
#                 print(f"✅ Migradas {len(busquedas_antiguas)} búsquedas al usuario Admin")

#     # -------------------------
#     # AUTENTICACIÓN
#     # -------------------------
#     def mostrar_login(self):
#         """Muestra la pantalla de login"""
#         self.page.clean()
#         pantalla_login = PantallaLogin(
#             self.page,
#             self.gestor_usuarios,
#             self.on_login_exitoso
#         )
#         self.page.add(
#             ft.Container(
#                 content=pantalla_login.container,
#                 alignment=ft.Alignment(0, 0),
#                 expand=True,
#                 bgcolor=ft.Colors.BLUE_GREY_50,
#             )
#         )
#         self.page.update()

#     def on_login_exitoso(self, usuario):
#         """Callback cuando el login es exitoso"""
#         self.usuario_actual = usuario
        
#         # Gestor de búsquedas antiguo (para migración)
#         self.gestor_busquedas_antiguo = GestorBusquedas(self.usuario_actual)
        
#         # Crear el panel de filtros con el callback de guardar búsqueda del usuario
#         self.panel_filtros = PanelFiltros(
#             self.usuario_actual,
#             self.df_cpv,
#             self.aplicar_filtros,
#             self.page
#         )
        
#         # Configurar el callback para guardar búsquedas desde el panel de filtros
#         # Esto se conecta con el botón existente en PanelFiltros
#         self._configurar_guardar_busqueda_panel()
        
#         self.mostrar_inicio()

#     def _configurar_guardar_busqueda_panel(self):
#         """Configura el callback del botón de guardar búsqueda en el panel de filtros"""
#         # Buscar el botón de guardar búsqueda en el panel de filtros
#         # y reemplazar su callback para usar el sistema de usuarios
#         if hasattr(self.panel_filtros, 'btn_guardar_busqueda'):
#             self.panel_filtros.btn_guardar_busqueda.on_click = lambda e: self.guardar_busqueda_desde_panel()

#     def guardar_busqueda_desde_panel(self):
#         """Guarda la búsqueda usando el sistema de usuarios"""
#         # Obtener filtros actuales del panel
#         filtros = self.panel_filtros.obtener_filtros()
        
#         # Crear diálogo personalizado para el usuario
#         def guardar_con_nombre(nombre):
#             if nombre:
#                 exito = self.gestor_usuarios.guardar_busqueda(
#                     self.usuario_actual,
#                     nombre,
#                     filtros
#                 )
#                 if exito:
#                     # Actualizar panel de búsquedas guardadas
#                     self.mostrar_inicio()
#                     # Mostrar snackbar de confirmación
#                     snack = ft.SnackBar(
#                         content=ft.Text(f"✅ Búsqueda '{nombre}' guardada exitosamente"),
#                         bgcolor=ft.Colors.GREEN,
#                     )
#                     self.page.overlay.append(snack)
#                     snack.open = True
#                     self.page.update()
        
#         # Mostrar el diálogo existente pero conectado al sistema de usuarios
#         dialogo = DialogoGuardarBusqueda(
#             self.page,
#             guardar_con_nombre
#         )
#         dialogo.mostrar()

#     def cerrar_sesion(self):
#         """Cierra la sesión del usuario actual"""
#         self.usuario_actual = None
#         self.estado = {"filtros": {}, "df_filtrado": None}
#         self.panel_filtros = None
#         self.mostrar_login()

#     # -------------------------
#     # PÁGINA DE INICIO (FILTROS)
#     # -------------------------
#     def mostrar_inicio(self):
#         self.page.clean()
        
#         # Si ya existen filtros aplicados, restaurarlos
#         if self.estado.get("filtros"):
#             self._restaurar_filtros(self.estado["filtros"])

#         # Barra superior con información del usuario
#         barra_usuario = ft.Row(
#             [
#                 ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.BLUE_700),
#                 ft.Text(f"Usuario: {self.usuario_actual}", weight="bold", size=16),
#                 ft.VerticalDivider(width=20),
#                 ft.Button(
#                     "Cerrar Sesión",
#                     icon=ft.Icons.LOGOUT,
#                     on_click=lambda e: self.cerrar_sesion(),
#                     style=ft.ButtonStyle(
#                         bgcolor=ft.Colors.RED_400,
#                         color=ft.Colors.WHITE,
#                     )
#                 ),
#             ],
#             alignment=ft.MainAxisAlignment.END,
#         )

#         bienvenida = ft.Column(
#             [
#                 ft.Text("🧾 Bienvenido al Explorador de Licitaciones", size=24, weight="bold"),
#                 ft.Text(
#                     "Filtre las licitaciones por código CPV, entidad, ubicación o importe.",
#                     size=16,
#                     color=ft.Colors.GREY_700,
#                 ),
#             ],
#             spacing=5,
#         )

#         # Panel de búsquedas guardadas del usuario
#         panel_busquedas = PanelBusquedasUsuario(
#             self.gestor_usuarios,
#             self.usuario_actual,
#             self.cargar_busqueda_guardada
#         )

#         layout = ft.Column([
#             barra_usuario,
#             ft.Divider(),
#             bienvenida,
#             # ft.ResponsiveRow(
#                 # [
#             ft.Container(self.panel_filtros, expand=True),
#                     # ft.Container(panel_busquedas.container, col={"xs": 12, "md": 5, "lg": 4}),
#                 # ]
#             # ),
#         ], spacing=20)

#         self.page.add(layout)
#         self.page.update()

#     def cargar_busqueda_guardada(self, filtros):
#         """Carga una búsqueda guardada y aplica los filtros"""
#         self.estado["filtros"] = filtros
#         self._restaurar_filtros(filtros)
#         self.aplicar_filtros(filtros)

#     def _restaurar_filtros(self, filtros):
#         """Restaura los filtros aplicados previamente en la interfaz"""
#         if not self.panel_filtros:
#             return
            
#         # Restaurar CPVs seleccionados
#         if filtros.get("cpv"):
#             self.panel_filtros.filtro_cpv.seleccionados = list(filtros["cpv"])
#             self.panel_filtros.filtro_cpv.chips_container.controls.clear()
#             for cpv in filtros["cpv"]:
#                 self.panel_filtros.filtro_cpv.chips_container.controls.append(
#                     ft.Chip(
#                         label=ft.Text(cpv), 
#                         on_delete=lambda e, op=cpv: self.panel_filtros.filtro_cpv.eliminar_chip(op)
#                     )
#                 )
        
#         # Restaurar lugar
#         if filtros.get("lugar"):
#             self.panel_filtros.lugar_dropdown.value = filtros["lugar"]
        
#         # Restaurar entidades
#         if filtros.get("entidades"):
#             for checkbox in self.panel_filtros.checkboxes_entidades:
#                 checkbox.value = checkbox.label in filtros["entidades"]
        
#         # Restaurar estados
#         if filtros.get("estados"):
#             estados_dict = {v: k for k, v in self.panel_filtros.estados.items()}
#             for checkbox in self.panel_filtros.checkboxes_estados:
#                 estado_nombre = checkbox.label
#                 checkbox.value = estados_dict.get(estado_nombre) in filtros["estados"]
        
#         # Restaurar rangos de importe
#         if "importe_min" in filtros and "importe_max" in filtros:
#             self.panel_filtros.slider_importe.start_value = filtros["importe_min"]
#             self.panel_filtros.slider_importe.end_value = filtros["importe_max"]
        
#         # Restaurar fechas
#         if filtros.get("fecha_desde"):
#             fecha_desde = filtros["fecha_desde"]
#             if hasattr(fecha_desde, 'strftime'):
#                 self.panel_filtros.fecha_desde.value = fecha_desde.strftime("%d/%m/%Y")
#             elif isinstance(fecha_desde, str):
#                 self.panel_filtros.fecha_desde.value = fecha_desde
        
#         if filtros.get("fecha_hasta"):
#             fecha_hasta = filtros["fecha_hasta"]
#             if hasattr(fecha_hasta, 'strftime'):
#                 self.panel_filtros.fecha_hasta.value = fecha_hasta.strftime("%d/%m/%Y")
#             elif isinstance(fecha_hasta, str):
#                 self.panel_filtros.fecha_hasta.value = fecha_hasta
        
#         # Restaurar palabras clave
#         if filtros.get("palabras_clave"):
#             self.panel_filtros.txt_palabras_clave.value = ", ".join(filtros["palabras_clave"])
        
#         # Restaurar opción de incluir PDF
#         if "incluir_pdf" in filtros:
#             self.panel_filtros.chk_incluir_pdf.value = filtros["incluir_pdf"]

#     # -------------------------
#     # FILTRADO Y RESULTADOS
#     # -------------------------
#     def aplicar_filtros(self, filtros):
#         self.estado["filtros"] = filtros

#         df_filtrado = filtrar_bd(
#             self.df_general, 
#             self.df_criterios,
#             self.df_requisitos,
#             self.df_docs,
#             self.estado["filtros"],
#             self.df_textos_extraidos
#         )

#         self.estado["df_filtrado"] = df_filtrado[0]
#         self.df_filtrado = df_filtrado[0]
#         self.df_requisito_fil = df_filtrado[2]
#         self.df_criterios_fil = df_filtrado[1]
#         self.mostrar_resultados()

#     def mostrar_resultados(self):
#         self.page.clean()
#         df = self.estado["df_filtrado"]

#         resumen = ft.Row(
#             [
#                 # ft.Text(
#                 #     f"Resultados filtrados: {len(df)} / {len(self.df_general)} licitaciones",
#                 #     size=18,
#                 #     weight="bold",
#                 # ),
#                 ft.IconButton(
#                     icon=ft.Icons.ARROW_BACK,
#                     tooltip="Volver a filtros",
#                     on_click=lambda e: self.mostrar_inicio(),
#                 ),
#             ],
#             alignment=ft.MainAxisAlignment.END,
#         )

#         resultados = PaginaResultados(
#             page=self.page,
#             df_general=self.df_filtrado,
#             df_requisitos=self.df_requisito_fil,
#             df_criterios=self.df_criterios_fil,
#             df_docs=self.df_docs,
#             df_cpv=self.df_cpv,
#             usuario_actual = self.usuario_actual,
#             on_detalles=self.mostrar_detalle,
#             filtros_aplicados=self.estado["filtros"],
#             on_aplicar_filtros=self.aplicar_filtros,
#             df_completo=self.df_general
#         )
        
#         layout = ft.Column([resumen, resultados], spacing=10, expand=True)

#         self.page.add(layout)
#         self.page.update()

#     # -------------------------
#     # DETALLE DE LICITACIÓN
#     # -------------------------
#     def mostrar_detalle(self, row):
#         self.page.clean()

#         detalle_vista = PaginaDetalle(
#             page=self.page,
#             row=row,
#             docs=self.df_docs[self.df_docs["pliego_id"] == row["ID"]],
#             analisis_data=self.df_analisis.loc[
#                 self.df_analisis["pliego_id"] == row["ID"]
#             ].head(1)
#         )

#         detalle = ft.Column(
#             [
#                 ft.Row([
#                     ft.Text("📄 Detalles de la licitación", size=22, weight="bold", expand=True),
#                     ft.Button(
#                         "⬅️ Volver a resultados",
#                         on_click=lambda e: self.mostrar_resultados(),
#                     ),
#                 ],
#                 alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#                 ),
#                 detalle_vista,
#             ],
#             spacing=10,
#             scroll="auto",
#         )

#         self.page.add(detalle)
#         self.page.update()


# def main(page: ft.Page):    
#     df_general, df_requisitos, df_criterios, df_docs, df_cpv = load_datasets()
#     AppLicitaciones(
#         page=page,
#         df_general=df_general,
#         df_requisitos=df_requisitos,
#         df_criterios=df_criterios,
#         df_docs=df_docs,
#         df_cpv=df_cpv
#     )

# ft.app(target=main, view=ft.AppView.WEB_BROWSER)

## -----------------

import flet as ft
import pandas as pd

try:
    from filtros import PanelFiltros
    from resultados import PaginaResultados
    from detalle import PaginaDetalle
    from busquedas_guardadas import DialogoGuardarBusqueda, GestorBusquedas, PanelBusquedasGuardadas
    from auth import GestorUsuarios, PantallaLogin, PanelBusquedasUsuario, PantallaRegistro
    # from alertas_ui import PanelAlertas  # NUEVO
    from alertas_ui_dialog import PanelAlertas
except:
    # import sys, os
    # sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from .filtros import PanelFiltros
    from .resultados import PaginaResultados
    from .detalle import PaginaDetalle
    from .busquedas_guardadas import DialogoGuardarBusqueda, GestorBusquedas, PanelBusquedasGuardadas
    from .auth import GestorUsuarios, PantallaLogin, PanelBusquedasUsuario, PantallaRegistro
    # from .alertas_ui import PanelAlertas  # NUEVO
    from .alertas_ui_dialog import PanelAlertas

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.filtrador import filtrar_bd
from utils.load_data import load_datasets, load_dataset

# NUEVO: Importar gestor de alertas
try:
    from data.alertas_data import Gestor_Alertas
except:
    from ..data.alertas_data import Gestor_Alertas


class AppLicitaciones:
    def __init__(self, page: ft.Page, df_general, df_requisitos, df_criterios, df_docs, df_cpv):
        self.page = page
        self.page.title = "Explorador de Licitaciones"
        self.page.scroll = "adaptive"
        self.page.padding = 20
        self.page.theme_mode = ft.ThemeMode.LIGHT

        # Sistema de autenticación
        self.gestor_usuarios = GestorUsuarios()
        self.usuario_actual = None
        
        # NUEVO: Sistema de alertas
        self.gestor_alertas = Gestor_Alertas(
            archivo_usuarios="usuarios.json",
            archivo_alertas="alertas.json"
        )
        self.panel_alertas = None

        # Estado persistente
        self.estado = {
            "filtros": {},
            "df_filtrado": None,
        }

        # Asignar datasets
        self.df_general = df_general
        self.df_requisitos = df_requisitos
        self.df_criterios = df_criterios
        self.df_docs = df_docs
        self.df_cpv = df_cpv
        self.df_analisis = load_dataset(r"src\data", "analisis_resultados.parquet")
        self.df_textos_extraidos = load_dataset(r"src", "Textos_Extraidos_viejo.parquet")

        # Crear el panel de filtros una sola vez (se configurará después del login)
        self.panel_filtros = None

    ## Método para solucionar la chapuza de los asyncs.
    async def iniciar(self):
        # Inicializar usuario Admin con búsquedas antiguas si no existe
        self._inicializar_admin()

        # Mostrar pantalla de login primero
        await self.mostrar_login()

    def _inicializar_admin(self):
        """Inicializa el usuario Admin y migra búsquedas antiguas si existen"""
        # Verificar si Admin ya existe
        if "Admin" not in self.gestor_usuarios.usuarios:
            # Crear usuario Admin
            self.gestor_usuarios.registrar_usuario("Admin", "123456", "admin@licitaciones.com")
            
            # Migrar búsquedas antiguas del sistema anterior
            try:
                gestor_busquedas_antiguo = GestorBusquedas("Admin")
                busquedas_antiguas = gestor_busquedas_antiguo.obtener_busquedas()
                if busquedas_antiguas:
                    for busqueda in busquedas_antiguas:
                        self.gestor_usuarios.guardar_busqueda(
                            "Admin",
                            busqueda["nombre"],
                            busqueda["filtros"]
                        )
                    print(f"✅ Migradas {len(busquedas_antiguas)} búsquedas al usuario Admin")
            except Exception as e:
                print(f"⚠️ No se pudieron migrar búsquedas antiguas: {e}")

    # -------------------------
    # AUTENTICACIÓN
    # -------------------------
    async def mostrar_login(self):
        """Muestra la pantalla de login"""
        self.page.clean()
        pantalla_login = PantallaLogin(
            gestor_usuarios=self.gestor_usuarios,
            on_login_exitoso=self.on_login_exitoso,
            on_mostrar_registro=self.mostrar_registro 
        )
        self.page.add(
            ft.Container(
                # content=pantalla_login.container,
                content = pantalla_login,
                # alignment=ft.alignment.center,
                alignment=ft.Alignment(0, 0),
                expand=True,
                bgcolor=ft.Colors.BLUE_GREY_50,
            )
        )
        self.page.update()

    async def mostrar_registro(self, e=None):
        """Muestra la pantalla de registro"""
        self.page.clean()
        
        pantalla_registro = PantallaRegistro(
            gestor_usuarios=self.gestor_usuarios,
            on_volver=self.mostrar_login
        )
        
        self.page.add(
            ft.Container(
                content=pantalla_registro,
                alignment=ft.Alignment(0, 0),
                expand=True,
                bgcolor=ft.Colors.BLUE_GREY_50,
            )
        )
        self.page.update()

    async def on_login_exitoso(self, usuario):
        """Callback cuando el login es exitoso"""
        self.usuario_actual = usuario
        
        # Gestor de búsquedas antiguo (para migración)
        self.gestor_busquedas_antiguo = GestorBusquedas(self.usuario_actual)
        
        # Crear el panel de filtros con el callback de guardar búsqueda del usuario
        self.panel_filtros = PanelFiltros(
            self.usuario_actual,
            self.df_cpv,
            self.aplicar_filtros,
            self.page
        )
        
        # NUEVO: Crear panel de alertas
        self.panel_alertas = PanelAlertas(
            page=self.page,
            usuario=self.usuario_actual,
            gestor_alertas=self.gestor_alertas,
            on_ver_detalle_callback=self.ver_detalle_desde_alerta
        )

         # Mensaje de debug para verificar
        print(f"✅ Panel de alertas creado para usuario: {self.usuario_actual}")
        print(f"   Alertas cargadas: {len(self.panel_alertas.alertas)}")

        
        self.debug_alertas()
        
        # Configurar el callback para guardar búsquedas desde el panel de filtros
        self._configurar_guardar_busqueda_panel()
        
        await self.mostrar_inicio()

    def _configurar_guardar_busqueda_panel(self):
        """Configura el callback del botón de guardar búsqueda en el panel de filtros"""
        if hasattr(self.panel_filtros, 'btn_guardar_busqueda'):
            self.panel_filtros.btn_guardar_busqueda.on_click = lambda e: self.guardar_busqueda_desde_panel()

    def guardar_busqueda_desde_panel(self):
        """Guarda la búsqueda usando el sistema de usuarios"""
        filtros = self.panel_filtros.obtener_filtros()
        
        def guardar_con_nombre(nombre):
            if nombre:
                exito = self.gestor_usuarios.guardar_busqueda(
                    self.usuario_actual,
                    nombre,
                    filtros
                )
                if exito:
                    self.mostrar_inicio()
                    snack = ft.SnackBar(
                        content=ft.Text(f"✅ Búsqueda '{nombre}' guardada exitosamente"),
                        bgcolor=ft.Colors.GREEN,
                    )
                    self.page.overlay.append(snack)
                    snack.open = True
                    self.page.update()
        
        dialogo = DialogoGuardarBusqueda(
            self.page,
            guardar_con_nombre
        )
        dialogo.mostrar()

    async def cerrar_sesion(self):
        """Cierra la sesión del usuario actual"""
        self.usuario_actual = None
        self.estado = {"filtros": {}, "df_filtrado": None}
        self.panel_filtros = None
        self.panel_alertas = None  # NUEVO
        await self.mostrar_login()

    # -------------------------
    # NUEVO: MÉTODOS PARA ALERTAS
    # -------------------------
    def ver_detalle_desde_alerta(self, licitacion_id):
        """Ver detalle de licitación desde una alerta"""
        # Buscar la licitación en el DataFrame
        licitacion = self.df_general[self.df_general["ID"] == licitacion_id]
        if not licitacion.empty:
            row = licitacion.iloc[0].to_dict()
            self.mostrar_detalle(row)
        else:
            # Mostrar snackbar si no se encuentra
            snack = ft.SnackBar(
                content=ft.Text("⚠️ No se encontró la licitación"),
                bgcolor=ft.Colors.ORANGE,
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
    
    def actualizar_alertas(self):
        """Actualiza las alertas cuando se procesan nuevas licitaciones"""
        if self.panel_alertas:
            self.panel_alertas.actualizar()
            self.page.update()

    # -------------------------
    # PÁGINA DE INICIO (FILTROS)
    # -------------------------
    async def mostrar_inicio(self):
        self.page.clean()
        
        # Si ya existen filtros aplicados, restaurarlos
        if self.estado.get("filtros"):
            self._restaurar_filtros(self.estado["filtros"])

        # MODIFICADO: Barra superior con información del usuario Y ALERTAS
        barra_usuario = ft.Row(
            [
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.BLUE_700),
                ft.Text(f"Usuario: {self.usuario_actual}", weight="bold", size=16),
                
                # NUEVO: Botón de alertas
                self.panel_alertas.obtener_boton() if self.panel_alertas else ft.Container(
                    content=ft.Text("⚠️ Sin alertas", size=10, color=ft.Colors.RED)
                ),
                
                ft.VerticalDivider(width=20),
                ft.Button(
                    "Cerrar Sesión",
                    icon=ft.Icons.LOGOUT,
                    on_click=self.cerrar_sesion,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_400,
                        color=ft.Colors.WHITE,
                    )
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
        )

        bienvenida = ft.Column(
            [
                ft.Text("🧾 Bienvenido al Explorador de Licitaciones", size=24, weight="bold"),
                ft.Text(
                    "Filtre las licitaciones por código CPV, entidad, ubicación o importe.",
                    size=16,
                    color=ft.Colors.GREY_700,
                ),
                
            ],
            spacing=5,
        )

        # Panel de búsquedas guardadas del usuario
        panel_busquedas = PanelBusquedasUsuario(
            self.gestor_usuarios,
            self.usuario_actual,
            self.cargar_busqueda_guardada
        )

        layout = ft.Column([
            barra_usuario,
            ft.Divider(),
            bienvenida,
            ft.Container(self.panel_filtros, expand=True),
        ], spacing=20)

        self.page.add(layout)
        # self.page.update()
        self.page.update()

    def cargar_busqueda_guardada(self, filtros):
        """Carga una búsqueda guardada y aplica los filtros"""
        self.estado["filtros"] = filtros
        self._restaurar_filtros(filtros)
        self.aplicar_filtros(filtros)

    def _restaurar_filtros(self, filtros):
        """Restaura los filtros aplicados previamente en la interfaz"""
        if not self.panel_filtros:
            return
            
        # Restaurar CPVs seleccionados
        if filtros.get("cpv"):
            self.panel_filtros.filtro_cpv.seleccionados = list(filtros["cpv"])
            self.panel_filtros.filtro_cpv.chips_container.controls.clear()
            for cpv in filtros["cpv"]:
                self.panel_filtros.filtro_cpv.chips_container.controls.append(
                    ft.Chip(
                        label=ft.Text(cpv), 
                        on_delete=lambda e, op=cpv: self.panel_filtros.filtro_cpv.eliminar_chip(op)
                    )
                )
        
        # Restaurar lugar
        if filtros.get("lugar"):
            self.panel_filtros.lugar_dropdown.value = filtros["lugar"]
        
        # Restaurar entidades
        if filtros.get("entidades"):
            for checkbox in self.panel_filtros.checkboxes_entidades:
                checkbox.value = checkbox.label in filtros["entidades"]
        
        # Restaurar estados
        if filtros.get("estados"):
            estados_dict = {v: k for k, v in self.panel_filtros.estados.items()}
            for checkbox in self.panel_filtros.checkboxes_estados:
                estado_nombre = checkbox.label
                checkbox.value = estados_dict.get(estado_nombre) in filtros["estados"]
        
        # Restaurar rangos de importe
        if "importe_min" in filtros and "importe_max" in filtros:
            self.panel_filtros.slider_importe.start_value = filtros["importe_min"]
            self.panel_filtros.slider_importe.end_value = filtros["importe_max"]
        
        # Restaurar fechas
        if filtros.get("fecha_desde"):
            fecha_desde = filtros["fecha_desde"]
            if hasattr(fecha_desde, 'strftime'):
                self.panel_filtros.fecha_desde.value = fecha_desde.strftime("%d/%m/%Y")
            elif isinstance(fecha_desde, str):
                self.panel_filtros.fecha_desde.value = fecha_desde
        
        if filtros.get("fecha_hasta"):
            fecha_hasta = filtros["fecha_hasta"]
            if hasattr(fecha_hasta, 'strftime'):
                self.panel_filtros.fecha_hasta.value = fecha_hasta.strftime("%d/%m/%Y")
            elif isinstance(fecha_hasta, str):
                self.panel_filtros.fecha_hasta.value = fecha_hasta
        
        # Restaurar palabras clave
        if filtros.get("palabras_clave"):
            self.panel_filtros.txt_palabras_clave.value = ", ".join(filtros["palabras_clave"])
        
        # Restaurar opción de incluir PDF
        if "incluir_pdf" in filtros:
            self.panel_filtros.chk_incluir_pdf.value = filtros["incluir_pdf"]

    # -------------------------
    # FILTRADO Y RESULTADOS
    # -------------------------
    # async def aplicar_filtros(self, filtros):
    def aplicar_filtros(self, filtros):
        # Mostrar indicador de carta
        # self.page.splash = ft.Container(
        #     content=ft.Column(
        #         [
        #             ft.ProgressRing(width=50, height=50, stroke_width=5, color=ft.Colors.BLUE_700),
        #             ft.Text("Filtrando licitaciones...", size=16, weight="bold", color=ft.Colors.BLUE_900),
        #         ],
        #         alignment=ft.MainAxisAlignment.CENTER,
        #         horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        #     ),
        #     alignment=ft.Alignment(0, 0),
        #     bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE), # Fondo semitransparente
        # )
        # await self.page.update_async()

        # 2. Ejecutar la lógica de filtrado (el proceso pesado)
        self.estado["filtros"] = filtros

        df_filtrado = filtrar_bd(
            self.df_general, 
            self.df_criterios,
            self.df_requisitos,
            self.df_docs,
            self.estado["filtros"],
            self.df_textos_extraidos
        )

        self.estado["df_filtrado"] = df_filtrado[0]
        self.df_filtrado = df_filtrado[0]
        self.df_requisito_fil = df_filtrado[2]
        self.df_criterios_fil = df_filtrado[1]

        # 3. Quitar el indicador de carga y mostrar resultados
        self.page.splash = None
        self.mostrar_resultados()
        # await self.page.update_async()

    def mostrar_resultados(self):
        self.page.clean()
        df = self.estado["df_filtrado"]

        # MODIFICADO: Añadir botón de alertas también en resultados
        barra_superior = ft.Row(
            [
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.BLUE_700),
                ft.Text(f"Usuario: {self.usuario_actual}", weight="bold", size=16),
                
                # NUEVO: Botón de alertas
                self.panel_alertas.obtener_boton() if self.panel_alertas else ft.Container(),
                
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Volver a filtros",
                    on_click= self.mostrar_inicio,
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
        )
        ## Momentaneo
        resultados = PaginaResultados(
            page=self.page,
            df_general=self.df_filtrado,
            df_requisitos=self.df_requisito_fil,
            df_criterios=self.df_criterios_fil,
            df_docs=self.df_docs,
            df_cpv=self.df_cpv,
            usuario_actual=self.usuario_actual,
            on_detalles=self.mostrar_detalle,
            filtros_aplicados=self.estado["filtros"],
            on_aplicar_filtros=self.aplicar_filtros,
            df_completo=self.df_general
        )
        
        layout = ft.Column([barra_superior, resultados], spacing=10, expand=True)
        # layout = ft.Column([barra_superior, ft.Text("Test")], expand=True)

        self.page.add(layout)
        self.page.update()
        # await self.page.update_async()

    # -------------------------
    # DETALLE DE LICITACIÓN
    # -------------------------
    def mostrar_detalle(self, row):
        self.page.clean()

        detalle_vista = PaginaDetalle(
            page=self.page,
            row=row,
            docs=self.df_docs[self.df_docs["pliego_id"] == row["ID"]],
            analisis_data=self.df_analisis.loc[
                self.df_analisis["pliego_id"] == row["ID"]
            ].head(1)
        )

        # MODIFICADO: Añadir información de usuario y alertas
        barra_superior = ft.Row(
            [
                ft.Text("📄 Detalles de la licitación", size=22, weight="bold", expand=True),
                
                # NUEVO: Info de usuario y alertas
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.BLUE_700),
                ft.Text(f"{self.usuario_actual}", size=14),
                self.panel_alertas.obtener_boton() if self.panel_alertas else ft.Container(),
                
                ft.Button(
                    "⬅️ Volver a resultados",
                    on_click=lambda e: self.mostrar_resultados(),
                ),
                ft.Button(
                    "⬅️ Volver a Inicio",
                    on_click= self.mostrar_inicio,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        detalle = ft.Column(
            [
                barra_superior,
                detalle_vista,
            ],
            spacing=10,
            scroll="auto",
        )

        self.page.add(detalle)
        self.page.update()

    def debug_alertas(self):
        """Método de debug para verificar el estado de las alertas"""
        print("\n" + "="*80)
        print("🔍 DEBUG - Estado de Alertas")
        print("="*80)
        print(f"Usuario actual: {self.usuario_actual}")
        print(f"Panel de alertas existe: {self.panel_alertas is not None}")
        
        if self.panel_alertas:
            print(f"Total alertas: {len(self.panel_alertas.alertas)}")
            print(f"Alertas no leídas: {self.panel_alertas.alertas_no_leidas}")
            print(f"Botón wrapper existe: {hasattr(self.panel_alertas, 'boton_wrapper')}")
            
            # Listar alertas
            if self.panel_alertas.alertas:
                print("\nAlertas encontradas:")
                for i, alerta in enumerate(self.panel_alertas.alertas, 1):
                    print(f"  {i}. ID: {alerta.get('id_alerta')}, "
                        f"Licitación: {alerta.get('licitacion_id')}, "
                        f"Leída: {alerta.get('leida')}")
            else:
                print("\n⚠️ No hay alertas cargadas")
        else:
            print("❌ Panel de alertas NO está inicializado")
        
        print("="*80 + "\n")


async def main(page: ft.Page):    
    df_general, df_requisitos, df_criterios, df_docs, df_cpv = load_datasets()
    app=AppLicitaciones(
        page=page,
        df_general=df_general,
        df_requisitos=df_requisitos,
        df_criterios=df_criterios,
        df_docs=df_docs,
        df_cpv=df_cpv
    )
    await app.iniciar()

ft.app(target=main, view=ft.AppView.WEB_BROWSER, assets_dir="assets")
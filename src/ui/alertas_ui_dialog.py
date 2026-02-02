import flet as ft
from datetime import datetime, date
import json
import os


class PanelAlertas:
    """
    Panel de alertas usando AlertDialog en lugar de NavigationDrawer
    Esta versión es más compatible y confiable
    """
    
    def __init__(self, page: ft.Page, usuario: str, gestor_alertas, on_ver_detalle_callback):
        self.page = page
        self.usuario = usuario
        self.gestor_alertas = gestor_alertas
        self.on_ver_detalle_callback = on_ver_detalle_callback
        self.alertas = []
        self.alertas_no_leidas = 0
        
        # Cargar alertas
        self._cargar_alertas()
        
        # Crear botón wrapper
        self.boton_stack = ft.Stack(width=35, height=35)
        self.boton_alertas = self._crear_boton()
        self.boton_wrapper = ft.Container(
            content=self.boton_alertas,
            tooltip="Ver alertas",
            on_click=lambda e: self._mostrar_panel_alertas(),
            padding=8,
            border_radius=25,
            ink=True,
            alignment=ft.Alignment(0, 0),
        )
        
        # NUEVO: Dialog para mostrar alertas
        self.dialog_alertas = None
    
    def _cargar_alertas(self):
        """Carga las alertas del usuario desde el gestor"""
        try:
            self.alertas = self.gestor_alertas.obtener_alertas_usuario(
                self.usuario, 
                solo_no_leidas=False
            )
            self.alertas_no_leidas = sum(1 for a in self.alertas if not a['leida'])
        except Exception as e:
            print(f"⚠️ Error cargando alertas: {e}")
            self.alertas = []
            self.alertas_no_leidas = 0
    
    def _calcular_dias_restantes(self, fecha_limite_str):
        """Calcula los días restantes hasta la fecha límite"""
        if not fecha_limite_str or fecha_limite_str == "None" or fecha_limite_str is None:
            return None, "Sin fecha límite", ft.Colors.GREY_500
        
        try:
            if isinstance(fecha_limite_str, str):
                if '-' in fecha_limite_str:
                    fecha_limite = datetime.strptime(fecha_limite_str[:10], "%Y-%m-%d").date()
                elif '/' in fecha_limite_str:
                    fecha_limite = datetime.strptime(fecha_limite_str, "%d/%m/%Y").date()
                else:
                    return None, "Fecha inválida", ft.Colors.GREY_500
            elif isinstance(fecha_limite_str, (datetime, date)):
                fecha_limite = fecha_limite_str if isinstance(fecha_limite_str, date) else fecha_limite_str.date()
            else:
                return None, "Sin fecha límite", ft.Colors.GREY_500
            
            hoy = date.today()
            dias_restantes = (fecha_limite - hoy).days
            
            if dias_restantes < 0:
                return dias_restantes, f"Venció hace {abs(dias_restantes)} días", ft.Colors.RED_700
            elif dias_restantes == 0:
                return 0, "¡Vence HOY!", ft.Colors.ORANGE_700
            elif dias_restantes <= 3:
                return dias_restantes, f"⚠️ {dias_restantes} días", ft.Colors.ORANGE_700
            elif dias_restantes <= 7:
                return dias_restantes, f"{dias_restantes} días", ft.Colors.AMBER_700
            elif dias_restantes <= 15:
                return dias_restantes, f"{dias_restantes} días", ft.Colors.BLUE_700
            else:
                return dias_restantes, f"{dias_restantes} días", ft.Colors.GREEN_700
            
        except Exception as e:
            print(f"⚠️ Error parseando fecha {fecha_limite_str}: {e}")
            return None, "Fecha inválida", ft.Colors.GREY_500
    
    def _obtener_icono_estado(self, estado):
        """Retorna el icono y color según el estado"""
        estado_lower = estado.lower() if estado else ""
        
        if "publicada" in estado_lower or "publicado" in estado_lower:
            return ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN_600
        elif "anuncio previo" in estado_lower or "anuncio" in estado_lower:
            return ft.Icons.NOTIFICATIONS_ACTIVE, ft.Colors.BLUE_600
        elif "adjudicada" in estado_lower:
            return ft.Icons.EMOJI_EVENTS, ft.Colors.AMBER_700
        elif "resuelta" in estado_lower:
            return ft.Icons.DONE_ALL, ft.Colors.PURPLE_600
        elif "cerrado" in estado_lower or "vencido" in estado_lower:
            return ft.Icons.BLOCK, ft.Colors.RED_600
        else:
            return ft.Icons.INFO, ft.Colors.GREY_600
    
    def _crear_badge(self):
        """Crea el badge con el número de alertas no leídas"""
        if self.alertas_no_leidas == 0:
            return None
        
        return ft.Container(
            content=ft.Text(
                str(self.alertas_no_leidas) if self.alertas_no_leidas < 100 else "99+",
                size=11,
                weight="bold",
                color=ft.Colors.WHITE,
            ),
            bgcolor=ft.Colors.RED_600,
            border_radius=10,
            padding=ft.Padding(left=6, right=6, top=2, bottom=2),
            alignment=ft.Alignment(0, 0),
        )
    
    def _crear_boton(self):
        """Crea el contenido del botón de alertas con badge"""
        icono = ft.Icon(
            ft.Icons.NOTIFICATIONS,
            color=ft.Colors.BLUE_700 if self.alertas_no_leidas > 0 else ft.Colors.GREY_600,
            size=28,
        )
        
        badge = self._crear_badge()
        
        if badge:
            self.boton_stack.controls = [
                icono,
                ft.Container(content=badge, right=0, top=0),
            ]
            return self.boton_stack
        else:
            return icono
    
    def _crear_tarjeta_alerta(self, alerta):
        """Crea una tarjeta visual para una alerta individual"""
        metadatos = alerta.get('metadatos', {})
        info_licitacion = metadatos.get('licitacion_info', {})
        
        nombre = info_licitacion.get('nombre', 'Sin nombre')[:80] + "..."
        entidad = info_licitacion.get('entidad', 'Sin entidad')
        importe = info_licitacion.get('importe', 'No especificado')
        estado = info_licitacion.get('estado', 'Sin estado')
        fecha_limite = info_licitacion.get('fecha_limite')
        
        dias_restantes, texto_dias, color_dias = self._calcular_dias_restantes(fecha_limite)
        icono_estado, color_estado = self._obtener_icono_estado(estado)
        
        coincidencias = metadatos.get('coincidencias', [])
        chips_coincidencias = ft.Row(
            [
                ft.Chip(
                    label=ft.Text("CPV" if coin == "cpv" else "Palabra clave", size=11),
                    bgcolor=ft.Colors.BLUE_50 if coin == "cpv" else ft.Colors.GREEN_50,
                    height=25,
                ) for coin in coincidencias
            ],
            spacing=5,
        )
        
        estado_row = ft.Row(
            [
                ft.Icon(icono_estado, color=color_estado, size=18),
                ft.Text(estado, size=13, weight="w500", color=color_estado),
            ],
            spacing=5,
        )

        if fecha_limite and fecha_limite != "None":
            fecha_row = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=color_dias),
                        ft.Text(texto_dias, size=13, weight="bold", color=color_dias),
                    ],
                    spacing=5,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, color_dias),
                border_radius=5,
                padding=5,
            )
        else:
            fecha_row = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ft.Colors.GREY_400),
                        ft.Text("Sin fecha límite", size=13, color=ft.Colors.GREY_600),
                    ],
                    spacing=5,
                ),
                padding=5,
            )

        indicador_leida = ft.Container(
            width=8,
            height=8,
            bgcolor=ft.Colors.BLUE_600 if not alerta['leida'] else ft.Colors.TRANSPARENT,
            border_radius=4,
        )
        
        botones = ft.Row(
            [
                ft.Button(
                    "Ver detalles",
                    icon=ft.Icons.OPEN_IN_NEW,
                    on_click=lambda e, aid=alerta['licitacion_id']: self._ver_detalle_licitacion(aid),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                    height=35,
                ),
                ft.IconButton(
                    icon=ft.Icons.DONE if not alerta['leida'] else ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.GREEN_700 if not alerta['leida'] else ft.Colors.RED_700,
                    tooltip="Marcar como leída" if not alerta['leida'] else "Eliminar",
                    on_click=lambda e, aid=alerta['id_alerta']: self._marcar_leida_o_eliminar(aid, alerta['leida']),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        tarjeta = ft.Container(
            content=ft.Row(
                [
                    indicador_leida,
                    ft.Column(
                        [
                            ft.Text(nombre, size=14, weight="bold", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"📋 {alerta['busqueda']['nombre']}", size=12, color=ft.Colors.GREY_700, italic=True),
                            ft.Divider(height=5),
                            ft.Row([
                                ft.Icon(ft.Icons.BUSINESS, size=14, color=ft.Colors.GREY_600),
                                ft.Text(entidad[:50] + "..." if len(entidad) > 50 else entidad, 
                                       size=12, color=ft.Colors.GREY_700)
                            ], spacing=5),
                            ft.Row([
                                ft.Icon(ft.Icons.EURO, size=14, color=ft.Colors.GREY_600),
                                ft.Text(f"{importe}", size=12, color=ft.Colors.GREY_700)
                            ], spacing=5),
                            ft.Row([estado_row, fecha_row], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            chips_coincidencias,
                            ft.Divider(height=5),
                            botones,
                        ],
                        spacing=8,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            bgcolor=ft.Colors.WHITE if alerta['leida'] else ft.Colors.BLUE_50,
            border=ft.Border.all(1, ft.Colors.BLUE_200 if not alerta['leida'] else ft.Colors.GREY_300),
            border_radius=10,
            padding=15,
            margin=ft.Margin.only(bottom=10),
        )
        
        return tarjeta
    
    def _mostrar_panel_alertas(self):
        """Muestra el panel de alertas usando AlertDialog (más compatible)"""
        print(f"🔔 Mostrando panel de alertas para {self.usuario}")
        
        # Recargar alertas
        self._cargar_alertas()
        print(f"   Total alertas: {len(self.alertas)}, No leídas: {self.alertas_no_leidas}")
        
        # Configuración del contenido
        if not self.alertas:
            contenido_alertas = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=64, color=ft.Colors.GREY_400),
                        ft.Text("No tienes alertas", size=18, color=ft.Colors.GREY_600, 
                               text_align=ft.TextAlign.CENTER),
                        ft.Text("Las alertas aparecerán aquí cuando haya nuevas licitaciones", 
                               size=14, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.Alignment(0, 0),
                height=400,
            )
        else:
            tarjetas = [self._crear_tarjeta_alerta(alerta) for alerta in self.alertas]
            contenido_alertas = ft.Container(
                content=ft.Column(
                    tarjetas,
                    scroll=ft.ScrollMode.AUTO,
                ),
                height=500,  # Altura fija para scroll
            )
        
        # Estadísticas
        total_alertas = len(self.alertas)
        estadisticas = ft.Container(
            content=ft.Row(
                [
                    ft.Column([
                        ft.Text(str(total_alertas), size=24, weight="bold", color=ft.Colors.BLUE_700),
                        ft.Text("Total", size=12, color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(),
                    ft.Column([
                        ft.Text(str(self.alertas_no_leidas), size=24, weight="bold", 
                               color=ft.Colors.ORANGE_700),
                        ft.Text("No leídas", size=12, color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            bgcolor=ft.Colors.GREY_100,
            border_radius=10,
            padding=15,
            margin=ft.Margin.only(bottom=10),
        )
        
        # Botones de gestión
        botones_gestion = ft.Row(
            [
                ft.TextButton(
                    "Marcar todas como leídas",
                    icon=ft.Icons.DONE_ALL,
                    on_click=lambda e: self._marcar_todas_leidas(),
                    disabled=self.alertas_no_leidas == 0,
                ),
                ft.TextButton(
                    "Limpiar leídas",
                    icon=ft.Icons.DELETE_SWEEP,
                    on_click=lambda e: self._limpiar_alertas_leidas(),
                    disabled=len([a for a in self.alertas if a['leida']]) == 0,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        )
        
        # USAR ALERTDIALOG EN LUGAR DE NAVIGATIONDRAWER
        self.dialog_alertas = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.NOTIFICATIONS, color=ft.Colors.BLUE_700),
                ft.Text("Mis Alertas", size=22, weight="bold"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column(
                    [
                        estadisticas,
                        botones_gestion,
                        ft.Divider(),
                        contenido_alertas,
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=600,  # Ancho del diálogo
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self._cerrar_panel()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        # Añadir a overlay y abrir
        self.page.overlay.append(self.dialog_alertas)
        self.dialog_alertas.open = True
        self.page.update()
        
        print("   ✅ Panel mostrado correctamente")
    
    def _cerrar_panel(self):
        """Cierra el panel de alertas"""
        print("🔔 Cerrando panel de alertas")
        
        if self.dialog_alertas:
            self.dialog_alertas.open = False
            self.page.update()
        
        # Actualizar el botón
        self._actualizar_boton()
    
    def _ver_detalle_licitacion(self, licitacion_id):
        """Abre el detalle de una licitación"""
        print(f"🔔 Abriendo detalle de licitación: {licitacion_id}")
        self._cerrar_panel()
        if self.on_ver_detalle_callback:
            self.on_ver_detalle_callback(licitacion_id)
    
    def _marcar_leida_o_eliminar(self, id_alerta, ya_leida):
        """Marca una alerta como leída o la elimina si ya estaba leída"""
        if ya_leida:
            self.gestor_alertas.eliminar_alerta(id_alerta)
            print(f"🔔 Alerta {id_alerta} eliminada")
        else:
            self.gestor_alertas.marcar_alerta_leida(id_alerta)
            print(f"🔔 Alerta {id_alerta} marcada como leída")
        
        # Cerrar y volver a abrir para actualizar
        if self.dialog_alertas:
            self.dialog_alertas.open = False
        self._mostrar_panel_alertas()
    
    def _marcar_todas_leidas(self):
        """Marca todas las alertas como leídas"""
        count = 0
        for alerta in self.alertas:
            if not alerta['leida']:
                self.gestor_alertas.marcar_alerta_leida(alerta['id_alerta'])
                count += 1
        
        print(f"🔔 {count} alertas marcadas como leídas")
        
        # Cerrar y volver a abrir para actualizar
        if self.dialog_alertas:
            self.dialog_alertas.open = False
        self._mostrar_panel_alertas()
    
    def _limpiar_alertas_leidas(self):
        """Elimina todas las alertas leídas"""
        count = 0
        for alerta in self.alertas:
            if alerta['leida']:
                self.gestor_alertas.eliminar_alerta(alerta['id_alerta'])
                count += 1
        
        print(f"🔔 {count} alertas leídas eliminadas")
        
        # Cerrar y volver a abrir para actualizar
        if self.dialog_alertas:
            self.dialog_alertas.open = False
        self._mostrar_panel_alertas()
    
    def _actualizar_boton(self):
        """Actualiza el botón de alertas con el nuevo badge"""
        print("🔔 Actualizando botón de alertas")
        
        self._cargar_alertas()
        nuevo_contenido = self._crear_boton()
        self.boton_wrapper.content = nuevo_contenido
        
        if hasattr(self, 'page') and self.page:
            self.page.update()
        
        print(f"   Alertas no leídas: {self.alertas_no_leidas}")
    
    def obtener_boton(self):
        """Retorna el botón de alertas para añadir a la interfaz"""
        return self.boton_wrapper
    
    def actualizar(self):
        """Actualiza el panel de alertas"""
        print("🔔 Actualizando panel de alertas completo")
        self._cargar_alertas()
        self._actualizar_boton()
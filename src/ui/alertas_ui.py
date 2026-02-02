# import flet as ft
# from datetime import datetime, date
# import json
# import os


# class PanelAlertas:
#     def __init__(self, page: ft.Page, usuario: str, gestor_alertas, on_ver_detalle_callback):
#         """
#         Panel de alertas para mostrar notificaciones de licitaciones.
        
#         Args:
#             page: Página de Flet
#             usuario: Nombre del usuario actual
#             gestor_alertas: Instancia del GestorAlertas
#             on_ver_detalle_callback: Callback para ver detalle de licitación
#         """
#         self.page = page
#         self.usuario = usuario
#         self.gestor_alertas = gestor_alertas
#         self.on_ver_detalle_callback = on_ver_detalle_callback
#         self.alertas = []
#         self.alertas_no_leidas = 0
        
#         # Cargar alertas
#         self._cargar_alertas()
        
#         # Crear badge de notificaciones
#         self.badge = self._crear_badge()
        
#         # Crear botón de alertas
#         self.boton_alertas = self._crear_boton()
    
#     def _cargar_alertas(self):
#         """Carga las alertas del usuario desde el gestor"""
#         try:
#             self.alertas = self.gestor_alertas.obtener_alertas_usuario(
#                 self.usuario, 
#                 solo_no_leidas=False
#             )
#             self.alertas_no_leidas = sum(1 for a in self.alertas if not a['leida'])
#         except Exception as e:
#             print(f"⚠️ Error cargando alertas: {e}")
#             self.alertas = []
#             self.alertas_no_leidas = 0
    
#     def _calcular_dias_restantes(self, fecha_limite_str):
#         """
#         Calcula los días restantes hasta la fecha límite.
        
#         Returns:
#             tuple: (dias_restantes, texto_mostrar, color)
#         """
#         if not fecha_limite_str or fecha_limite_str == "None" or fecha_limite_str is None:
#             return None, "Sin fecha límite", ft.Colors.GREY_500
        
#         try:
#             # Intentar parsear diferentes formatos de fecha
#             if isinstance(fecha_limite_str, str):
#                 # Formato ISO: 2026-02-15
#                 if '-' in fecha_limite_str:
#                     fecha_limite = datetime.strptime(fecha_limite_str[:10], "%Y-%m-%d").date()
#                 # Formato español: 15/02/2026
#                 elif '/' in fecha_limite_str:
#                     fecha_limite = datetime.strptime(fecha_limite_str, "%d/%m/%Y").date()
#                 else:
#                     return None, "Fecha inválida", ft.Colors.GREY_500
#             elif isinstance(fecha_limite_str, (datetime, date)):
#                 fecha_limite = fecha_limite_str if isinstance(fecha_limite_str, date) else fecha_limite_str.date()
#             else:
#                 return None, "Sin fecha límite", ft.Colors.GREY_500
            
#             hoy = date.today()
#             dias_restantes = (fecha_limite - hoy).days
            
#             # Determinar color según urgencia
#             if dias_restantes < 0:
#                 color = ft.Colors.RED_700
#                 texto = f"Venció hace {abs(dias_restantes)} días"
#             elif dias_restantes == 0:
#                 color = ft.Colors.ORANGE_700
#                 texto = "¡Vence HOY!"
#             elif dias_restantes <= 3:
#                 color = ft.Colors.ORANGE_700
#                 texto = f"⚠️ {dias_restantes} días"
#             elif dias_restantes <= 7:
#                 color = ft.Colors.AMBER_700
#                 texto = f"{dias_restantes} días"
#             elif dias_restantes <= 15:
#                 color = ft.Colors.BLUE_700
#                 texto = f"{dias_restantes} días"
#             else:
#                 color = ft.Colors.GREEN_700
#                 texto = f"{dias_restantes} días"
            
#             return dias_restantes, texto, color
            
#         except Exception as e:
#             print(f"⚠️ Error parseando fecha {fecha_limite_str}: {e}")
#             return None, "Fecha inválida", ft.Colors.GREY_500
    
#     def _obtener_icono_estado(self, estado):
#         """Retorna el icono y color según el estado"""
#         estado_lower = estado.lower() if estado else ""
        
#         if "publicada" in estado_lower or "publicado" in estado_lower:
#             return ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN_600
#         elif "anuncio previo" in estado_lower or "anuncio" in estado_lower:
#             return ft.Icons.NOTIFICATIONS_ACTIVE, ft.Colors.BLUE_600
#         elif "adjudicada" in estado_lower:
#             return ft.Icons.EMOJI_EVENTS, ft.Colors.AMBER_700
#         elif "resuelta" in estado_lower:
#             return ft.Icons.DONE_ALL, ft.Colors.PURPLE_600
#         elif "cerrado" in estado_lower or "vencido" in estado_lower:
#             return ft.Icons.BLOCK, ft.Colors.RED_600
#         else:
#             return ft.Icons.INFO, ft.Colors.GREY_600
    
#     def _crear_badge(self):
#         """Crea el badge con el número de alertas no leídas"""
#         if self.alertas_no_leidas == 0:
#             return None
        
#         return ft.Container(
#             content=ft.Text(
#                 str(self.alertas_no_leidas) if self.alertas_no_leidas < 100 else "99+",
#                 size=11,
#                 weight="bold",
#                 color=ft.Colors.WHITE,
#             ),
#             bgcolor=ft.Colors.RED_600,
#             border_radius=10,
#             # padding=ft.padding.only(left=6, right=6, top=2, bottom=2),
#             padding=ft.Padding.only(),
#             # alignment=ft.alignment.center,
#             alignment=ft.Alignment(0, 0),
#         )
    
#     # def _crear_boton(self):
#     #     """Crea el botón de alertas con badge"""
#     #     icono = ft.Icon(
#     #         ft.Icons.NOTIFICATIONS,
#     #         color=ft.Colors.BLUE_700 if self.alertas_no_leidas > 0 else ft.Colors.GREY_600,
#     #         size=28,
#     #     )
        
#     #     if self.badge:
#     #         contenido = ft.Stack(
#     #             [
#     #                 icono,
#     #                 ft.Container(
#     #                     content=self.badge,
#     #                     right=-5,
#     #                     top=-5,
#     #                 ),
#     #             ],
#     #             width=35,
#     #             height=35,
#     #         )
#     #     else:
#     #         contenido = icono
        
#     #     return ft.IconButton(
#     #         content=contenido,
#     #         tooltip="Ver alertas",
#     #         on_click=lambda e: self._mostrar_panel_alertas(),
#     #     )

#     def _crear_boton(self):
#         """Crea el botón de alertas con badge compatible con Flet 0.21+"""
#         icono = ft.Icon(
#             ft.Icons.NOTIFICATIONS,
#             color=ft.Colors.BLUE_700 if self.alertas_no_leidas > 0 else ft.Colors.GREY_600,
#             size=28,
#         )
        
#         if self.badge:
#             contenido = ft.Stack(
#                 [
#                     icono,
#                     ft.Container(
#                         content=self.badge,
#                         right=0, # Ajustado un poco para mejor alineación
#                         top=0,
#                     ),
#                 ],
#                 width=35,
#                 height=35,
#             )
#         else:
#             contenido = icono
        
#         # Reemplazamos IconButton por Container + Ink
#         return ft.Container(
#             content=contenido,
#             tooltip="Ver alertas",
#             on_click=lambda e: self._mostrar_panel_alertas(),
#             padding=8,
#             border_radius=25, # Lo hace circular para el efecto de clic
#             ink=True, # Esto activa el efecto visual de botón (splash)
#             # alignment=ft.alignment.center,
#             alignment=ft.Alignment(0, 0),
#         )
    
#     # def _crear_tarjeta_alerta(self, alerta):
#     #     """Crea una tarjeta visual para una alerta individual"""
#     #     metadatos = alerta.get('metadatos', {})
#     #     info_licitacion = metadatos.get('licitacion_info', {})
        
#     #     # Información de la licitación
#     #     nombre = info_licitacion.get('nombre', 'Sin nombre')[:80] + "..."
#     #     entidad = info_licitacion.get('entidad', 'Sin entidad')
#     #     importe = info_licitacion.get('importe', 'No especificado')
#     #     estado = info_licitacion.get('estado', 'Sin estado')
#     #     fecha_limite = info_licitacion.get('fecha_limite')
#     #     url = info_licitacion.get('url', '')
        
#     #     # Calcular días restantes
#     #     dias_restantes, texto_dias, color_dias = self._calcular_dias_restantes(fecha_limite)
        
#     #     # Icono y color del estado
#     #     icono_estado, color_estado = self._obtener_icono_estado(estado)
        
#     #     # Coincidencias
#     #     coincidencias = metadatos.get('coincidencias', [])
#     #     chips_coincidencias = ft.Row(
#     #         [
#     #             ft.Chip(
#     #                 label=ft.Text(
#     #                     "CPV" if coin == "cpv" else "Palabra clave",
#     #                     size=11,
#     #                 ),
#     #                 bgcolor=ft.Colors.BLUE_50 if coin == "cpv" else ft.Colors.GREEN_50,
#     #                 height=25,
#     #             ) for coin in coincidencias
#     #         ],
#     #         spacing=5,
#     #     )
        
#     #     # Información del estado
#     #     estado_row = ft.Row(
#     #         [
#     #             ft.Icon(icono_estado, color=color_estado, size=18),
#     #             ft.Text(estado, size=13, weight="w500", color=color_estado),
#     #         ],
#     #         spacing=5,
#     #     )
        
#     #     # Información de fecha límite
#     #     if fecha_limite and fecha_limite != "None":
#     #         fecha_row = ft.Container(
#     #             content=ft.Row(
#     #                 [
#     #                     ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=color_dias),
#     #                     ft.Text(texto_dias, size=13, weight="bold", color=color_dias),
#     #                 ],
#     #                 spacing=5,
#     #             ),
#     #             bgcolor=f"{color_dias}15",  # 15 es alpha para transparencia
#     #             border_radius=5,
#     #             padding=5,
#     #         )
#     #     else:
#     #         fecha_row = ft.Container(
#     #             content=ft.Row(
#     #                 [
#     #                     ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ft.Colors.GREY_400),
#     #                     ft.Text("Sin fecha límite", size=13, color=ft.Colors.GREY_600),
#     #                 ],
#     #                 spacing=5,
#     #             ),
#     #             padding=5,
#     #         )
        
#     #     # Indicador de no leída
#     #     indicador_leida = ft.Container(
#     #         width=8,
#     #         height=8,
#     #         bgcolor=ft.Colors.BLUE_600 if not alerta['leida'] else ft.Colors.TRANSPARENT,
#     #         border_radius=4,
#     #     )
        
#     #     # Botones de acción
#     #     botones = ft.Row(
#     #         [
#     #             ft.ElevatedButton(
#     #                 "Ver detalles",
#     #                 icon=ft.Icons.OPEN_IN_NEW,
#     #                 on_click=lambda e, aid=alerta['licitacion_id']: self._ver_detalle_licitacion(aid),
#     #                 style=ft.ButtonStyle(
#     #                     bgcolor=ft.Colors.BLUE_700,
#     #                     color=ft.Colors.WHITE,
#     #                 ),
#     #                 height=35,
#     #             ),
#     #             ft.IconButton(
#     #                 icon=ft.Icons.DONE if not alerta['leida'] else ft.Icons.DELETE_OUTLINE,
#     #                 icon_color=ft.Colors.GREEN_700 if not alerta['leida'] else ft.Colors.RED_700,
#     #                 tooltip="Marcar como leída" if not alerta['leida'] else "Eliminar",
#     #                 on_click=lambda e, aid=alerta['id_alerta']: self._marcar_leida_o_eliminar(aid, alerta['leida']),
#     #             ),
#     #         ],
#     #         alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#     #     )
        
#     #     # Tarjeta completa
#     #     tarjeta = ft.Container(
#     #         content=ft.Row(
#     #             [
#     #                 indicador_leida,
#     #                 ft.Column(
#     #                     [
#     #                         # Título y búsqueda
#     #                         ft.Text(
#     #                             nombre,
#     #                             size=14,
#     #                             weight="bold",
#     #                             max_lines=2,
#     #                             overflow=ft.TextOverflow.ELLIPSIS,
#     #                         ),
#     #                         ft.Text(
#     #                             f"📋 {alerta['busqueda']['nombre']}",
#     #                             size=12,
#     #                             color=ft.Colors.GREY_700,
#     #                             italic=True,
#     #                         ),
#     #                         ft.Divider(height=5),
#     #                         # Información de la entidad
#     #                         ft.Row(
#     #                             [
#     #                                 ft.Icon(ft.Icons.BUSINESS, size=14, color=ft.Colors.GREY_600),
#     #                                 ft.Text(
#     #                                     entidad[:50] + "..." if len(entidad) > 50 else entidad,
#     #                                     size=12,
#     #                                     color=ft.Colors.GREY_700,
#     #                                 ),
#     #                             ],
#     #                             spacing=5,
#     #                         ),
#     #                         # Importe
#     #                         ft.Row(
#     #                             [
#     #                                 ft.Icon(ft.Icons.EURO, size=14, color=ft.Colors.GREY_600),
#     #                                 ft.Text(f"{importe}", size=12, color=ft.Colors.GREY_700),
#     #                             ],
#     #                             spacing=5,
#     #                         ),
#     #                         # Estado y fecha
#     #                         ft.Row(
#     #                             [estado_row, fecha_row],
#     #                             alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#     #                         ),
#     #                         # Coincidencias
#     #                         chips_coincidencias,
#     #                         ft.Divider(height=5),
#     #                         # Botones de acción
#     #                         botones,
#     #                     ],
#     #                     spacing=8,
#     #                     expand=True,
#     #                 ),
#     #             ],
#     #             spacing=10,
#     #         ),
#     #         bgcolor=ft.Colors.WHITE if alerta['leida'] else ft.Colors.BLUE_50,
#     #         border=ft.border.all(
#     #             1,
#     #             ft.Colors.BLUE_200 if not alerta['leida'] else ft.Colors.GREY_300
#     #         ),
#     #         border_radius=10,
#     #         padding=15,
#     #         margin=ft.Margin.only(bottom=10),
#     #     )
        
#     #     return tarjeta
    
#     def _crear_tarjeta_alerta(self, alerta):
#         """Crea una tarjeta visual para una alerta individual"""
#         metadatos = alerta.get('metadatos', {})
#         info_licitacion = metadatos.get('licitacion_info', {})
        
#         # Información de la licitación
#         nombre = info_licitacion.get('nombre', 'Sin nombre')[:80] + "..."
#         entidad = info_licitacion.get('entidad', 'Sin entidad')
#         importe = info_licitacion.get('importe', 'No especificado')
#         estado = info_licitacion.get('estado', 'Sin estado')
#         fecha_limite = info_licitacion.get('fecha_limite')
#         url = info_licitacion.get('url', '')
        
#         # Calcular días restantes
#         dias_restantes, texto_dias, color_dias = self._calcular_dias_restantes(fecha_limite)
        
#         # Icono y color del estado
#         icono_estado, color_estado = self._obtener_icono_estado(estado)
        
#         # Coincidencias
#         coincidencias = metadatos.get('coincidencias', [])
#         chips_coincidencias = ft.Row(
#             [
#                 ft.Chip(
#                     label=ft.Text(
#                         "CPV" if coin == "cpv" else "Palabra clave",
#                         size=11,
#                     ),
#                     bgcolor=ft.Colors.BLUE_50 if coin == "cpv" else ft.Colors.GREEN_50,
#                     height=25,
#                 ) for coin in coincidencias
#             ],
#             spacing=5,
#         )
        
#         # Información del estado
#         estado_row = ft.Row(
#             [
#                 ft.Icon(icono_estado, color=color_estado, size=18),
#                 ft.Text(estado, size=13, weight="w500", color=color_estado),
#             ],
#             spacing=5,
#         )

#         # Información de fecha límite - CORRECCIÓN DE COLOR
#         if fecha_limite and fecha_limite != "None":
#             # Aseguramos que color_dias se maneje como string si vas a concatenar "15"
#             # O mejor aún, usamos with_opacity
#             bg_color = color_dias if isinstance(color_dias, str) else None
            
#             fecha_row = ft.Container(
#                 content=ft.Row(
#                     [
#                         ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=color_dias),
#                         ft.Text(texto_dias, size=13, weight="bold", color=color_dias),
#                     ],
#                     spacing=5,
#                 ),
#                 # bgcolor=f"{color_dias}15", # <--- ESTO PUEDE FALLAR
#                 bgcolor=ft.Colors.with_opacity(0.1, color_dias), # Forma segura
                
#                 border_radius=5,
#                 padding=5,
#             )
#         else:
#             fecha_row = ft.Container(
#                 content=ft.Row(
#                     [
#                         ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ft.Colors.GREY_400),
#                         ft.Text("Sin fecha límite", size=13, color=ft.Colors.GREY_600),
#                     ],
#                     spacing=5,
#                 ),
#                 padding=5,
#             )

#         # Indicador de no leída
#         indicador_leida = ft.Container(
#             width=8,
#             height=8,
#             bgcolor=ft.Colors.BLUE_600 if not alerta['leida'] else ft.Colors.TRANSPARENT,
#             border_radius=4,
#         )
        
#         # Botones de acción
#         botones = ft.Row(
#             [
#                 # ft.ElevatedButton(
#                 ft.Button(
#                     "Ver detalles",
#                     icon=ft.Icons.OPEN_IN_NEW,
#                     on_click=lambda e, aid=alerta['licitacion_id']: self._ver_detalle_licitacion(aid),
#                     style=ft.ButtonStyle(
#                         bgcolor=ft.Colors.BLUE_700,
#                         color=ft.Colors.WHITE,
#                     ),
#                     height=35,
#                 ),
#                 ft.IconButton(
#                     icon=ft.Icons.DONE if not alerta['leida'] else ft.Icons.DELETE_OUTLINE,
#                     icon_color=ft.Colors.GREEN_700 if not alerta['leida'] else ft.Colors.RED_700,
#                     tooltip="Marcar como leída" if not alerta['leida'] else "Eliminar",
#                     on_click=lambda e, aid=alerta['id_alerta']: self._marcar_leida_o_eliminar(aid, alerta['leida']),
#                 ),
#             ],
#             alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#         )

#         # Tarjeta completa
#         tarjeta = ft.Container(
#             content=ft.Row(
#                 [
#                     indicador_leida,
#                     ft.Column(
#                         [
#                             ft.Text(nombre, size=14, weight="bold", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
#                             ft.Text(f"📋 {alerta['busqueda']['nombre']}", size=12, color=ft.Colors.GREY_700, italic=True),
#                             ft.Divider(height=5),
#                             # Entidad
#                             ft.Row([ft.Icon(ft.Icons.BUSINESS, size=14, color=ft.Colors.GREY_600),
#                                     ft.Text(entidad[:50] + "..." if len(entidad) > 50 else entidad, size=12, color=ft.Colors.GREY_700)],
#                                     spacing=5),
#                             # Importe
#                             ft.Row([ft.Icon(ft.Icons.EURO, size=14, color=ft.Colors.GREY_600),
#                                     ft.Text(f"{importe}", size=12, color=ft.Colors.GREY_700)],
#                                     spacing=5),
#                             # Estado y fecha
#                             ft.Row([estado_row, fecha_row], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
#                             chips_coincidencias,
#                             ft.Divider(height=5),
#                             botones,
#                         ],
#                         spacing=8,
#                         expand=True,
#                     ),
#                 ],
#                 spacing=10,
#             ),
#             bgcolor=ft.Colors.WHITE if alerta['leida'] else ft.Colors.BLUE_50,
#             border=ft.Border.all(1, ft.Colors.BLUE_200 if not alerta['leida'] else ft.Colors.GREY_300),
#             border_radius=10,
#             padding=15,
#             margin=ft.Margin.only(bottom=10), # <--- CORREGIDO: 'margin' en minúscula
#         )
        
#         return tarjeta
    
#     def _mostrar_panel_alertas(self):
#         """Muestra el panel lateral con todas las alertas"""
#         # Recargar alertas
#         self._cargar_alertas()
        
#         # --- Configuración del contenido (se mantiene igual) ---
#         if not self.alertas:
#             contenido_alertas = ft.Container(
#                 content=ft.Column(
#                     [
#                         ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=64, color=ft.Colors.GREY_400),
#                         ft.Text("No tienes alertas", size=18, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
#                     ],
#                     horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#                     spacing=20,
#                 ),
#                 alignment=ft.Alignment(0, 0),
#                 expand=True,
#             )
#         else:
#             tarjetas = [self._crear_tarjeta_alerta(alerta) for alerta in self.alertas]
#             contenido_alertas = ft.Column(
#                 tarjetas,
#                 scroll=ft.ScrollMode.AUTO,
#                 expand=True,
#             )
        
#         # Estadísticas y Botones (Se mantiene igual)
#         total_alertas = len(self.alertas)
#         estadisticas = ft.Container(
#             content=ft.Row(
#                 [
#                     ft.Column([ft.Text(str(total_alertas), size=24, weight="bold", color=ft.Colors.BLUE_700), ft.Text("Total", size=12, color=ft.Colors.GREY_600)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
#                     ft.VerticalDivider(),
#                     ft.Column([ft.Text(str(self.alertas_no_leidas), size=24, weight="bold", color=ft.Colors.ORANGE_700), ft.Text("No leídas", size=12, color=ft.Colors.GREY_600)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
#                 ],
#                 alignment=ft.MainAxisAlignment.SPACE_AROUND,
#             ),
#             bgcolor=ft.Colors.GREY_100, border_radius=10, padding=15, margin=ft.Margin.only(bottom=10),
#         )
        
#         botones_gestion = ft.Row(
#             [
#                 ft.TextButton("Marcar todas como leídas", icon=ft.Icons.DONE_ALL, on_click=lambda e: self._marcar_todas_leidas()),
#                 ft.TextButton("Limpiar leídas", icon=ft.Icons.DELETE_SWEEP, on_click=lambda e: self._limpiar_alertas_leidas()),
#             ],
#             alignment=ft.MainAxisAlignment.SPACE_AROUND,
#         )
        
#         # Panel completo
#         panel = ft.Container(
#             content=ft.Column(
#                 [
#                     ft.Row([ft.Text("🔔 Mis Alertas", size=22, weight="bold"), ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda e: self._cerrar_panel())], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
#                     ft.Divider(),
#                     estadisticas,
#                     botones_gestion,
#                     ft.Divider(),
#                     contenido_alertas,
#                 ],
#                 expand=True,
#             ),
#             bgcolor=ft.Colors.WHITE,
#             padding=20,
#             width=400, # Ajustado ligeramente para que no ocupe tanto
#         )
        
#         # --- CAMBIOS CRÍTICOS AQUÍ ---
        
#         # 1. Crear el drawer sin el atributo 'position'
#         self.drawer = ft.NavigationDrawer(
#             controls=[panel],
#         )
        
#         # 2. Asignarlo a 'end_drawer' para que aparezca desde la derecha
#         self.page.end_drawer = self.drawer
        
#         # 3. Abrirlo mediante la propiedad .open
#         self.drawer.open = True
        
#         # 4. Actualizar la página
#         self.page.update()
    
#     # def _mostrar_panel_alertas(self):
#     #     """Muestra el panel lateral con todas las alertas"""
#     #     # Recargar alertas
#     #     self._cargar_alertas()
        
#     #     # Crear lista de tarjetas de alertas
#     #     if not self.alertas:
#     #         contenido_alertas = ft.Container(
#     #             content=ft.Column(
#     #                 [
#     #                     ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=64, color=ft.Colors.GREY_400),
#     #                     ft.Text(
#     #                         "No tienes alertas",
#     #                         size=18,
#     #                         color=ft.Colors.GREY_600,
#     #                         text_align=ft.TextAlign.CENTER,
#     #                     ),
#     #                 ],
#     #                 horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#     #                 spacing=20,
#     #             ),
#     #             # alignment=ft.alignment.center,
#     #             alignment=ft.Alignment(0, 0),
#     #             expand=True,
#     #         )
#     #     else:
#     #         tarjetas = [self._crear_tarjeta_alerta(alerta) for alerta in self.alertas]
#     #         contenido_alertas = ft.Column(
#     #             tarjetas,
#     #             scroll=ft.ScrollMode.AUTO,
#     #             expand=True,
#     #         )
        
#     #     # Estadísticas
#     #     total_alertas = len(self.alertas)
        
#     #     estadisticas = ft.Container(
#     #         content=ft.Row(
#     #             [
#     #                 ft.Column(
#     #                     [
#     #                         ft.Text(str(total_alertas), size=24, weight="bold", color=ft.Colors.BLUE_700),
#     #                         ft.Text("Total", size=12, color=ft.Colors.GREY_600),
#     #                     ],
#     #                     horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#     #                 ),
#     #                 ft.VerticalDivider(),
#     #                 ft.Column(
#     #                     [
#     #                         ft.Text(str(self.alertas_no_leidas), size=24, weight="bold", color=ft.Colors.ORANGE_700),
#     #                         ft.Text("No leídas", size=12, color=ft.Colors.GREY_600),
#     #                     ],
#     #                     horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#     #                 ),
#     #             ],
#     #             alignment=ft.MainAxisAlignment.SPACE_AROUND,
#     #         ),
#     #         bgcolor=ft.Colors.GREY_100,
#     #         border_radius=10,
#     #         padding=15,
#     #         margin=ft.margin.only(bottom=10),
#     #     )
        
#     #     # Botones de gestión
#     #     botones_gestion = ft.Row(
#     #         [
#     #             ft.TextButton(
#     #                 "Marcar todas como leídas",
#     #                 icon=ft.Icons.DONE_ALL,
#     #                 on_click=lambda e: self._marcar_todas_leidas(),
#     #             ),
#     #             ft.TextButton(
#     #                 "Limpiar leídas",
#     #                 icon=ft.Icons.DELETE_SWEEP,
#     #                 on_click=lambda e: self._limpiar_alertas_leidas(),
#     #             ),
#     #         ],
#     #         alignment=ft.MainAxisAlignment.SPACE_AROUND,
#     #     )
        
#     #     # Panel completo
#     #     panel = ft.Container(
#     #         content=ft.Column(
#     #             [
#     #                 # Encabezado
#     #                 ft.Row(
#     #                     [
#     #                         ft.Text("🔔 Mis Alertas", size=22, weight="bold"),
#     #                         ft.IconButton(
#     #                             icon=ft.Icons.CLOSE,
#     #                             on_click=lambda e: self._cerrar_panel(),
#     #                         ),
#     #                     ],
#     #                     alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
#     #                 ),
#     #                 ft.Divider(),
#     #                 # Estadísticas
#     #                 estadisticas,
#     #                 # Botones de gestión
#     #                 botones_gestion,
#     #                 ft.Divider(),
#     #                 # Alertas
#     #                 contenido_alertas,
#     #             ],
#     #             expand=True,
#     #         ),
#     #         bgcolor=ft.Colors.WHITE,
#     #         padding=20,
#     #         width=500,
#     #         height=self.page.height,
#     #     )
        
#     #     # Crear drawer
#     #     self.drawer = ft.NavigationDrawer(
#     #         controls=[panel],
#     #         position=ft.NavigationDrawerPosition.END,
#     #     )
        
#     #     self.page.overlay.append(self.drawer)
#     #     self.drawer.open = True
#     #     self.page.update()
    
#     def _cerrar_panel(self):
#         """Cierra el panel de alertas"""
#         self.drawer.open = False
#         self.page.update()
        
#         # Actualizar el badge
#         self._actualizar_boton()
    
#     def _ver_detalle_licitacion(self, licitacion_id):
#         """Abre el detalle de una licitación"""
#         self._cerrar_panel()
#         if self.on_ver_detalle_callback:
#             self.on_ver_detalle_callback(licitacion_id)
    
#     def _marcar_leida_o_eliminar(self, id_alerta, ya_leida):
#         """Marca una alerta como leída o la elimina si ya estaba leída"""
#         if ya_leida:
#             self.gestor_alertas.eliminar_alerta(id_alerta)
#         else:
#             self.gestor_alertas.marcar_alerta_leida(id_alerta)
        
#         # Actualizar vista
#         self._mostrar_panel_alertas()
    
#     def _marcar_todas_leidas(self):
#         """Marca todas las alertas como leídas"""
#         for alerta in self.alertas:
#             if not alerta['leida']:
#                 self.gestor_alertas.marcar_alerta_leida(alerta['id_alerta'])
        
#         # Actualizar vista
#         self._mostrar_panel_alertas()
    
#     def _limpiar_alertas_leidas(self):
#         """Elimina todas las alertas leídas"""
#         for alerta in self.alertas:
#             if alerta['leida']:
#                 self.gestor_alertas.eliminar_alerta(alerta['id_alerta'])
        
#         # Actualizar vista
#         self._mostrar_panel_alertas()
    
#     def _actualizar_boton(self):
#         """Actualiza el botón de alertas con el nuevo badge"""
#         self._cargar_alertas()
#         self.badge = self._crear_badge()
#         self.boton_alertas = self._crear_boton()
    
#     def obtener_boton(self):
#         """Retorna el botón de alertas para añadir a la interfaz"""
#         return self.boton_alertas
    
#     def actualizar(self):
#         """Actualiza el panel de alertas"""
#         self._cargar_alertas()
#         self._actualizar_boton()


# # ============================================================================
# # INTEGRACIÓN EN EL ARCHIVO PRINCIPAL
# # ============================================================================

# def integrar_panel_alertas_en_app():
#     """
#     Código de ejemplo para integrar el panel de alertas en AppLicitaciones
#     """
#     ejemplo = '''
#     # En la clase AppLicitaciones, en __init__:
    
#     # Importar el gestor de alertas
#     from data.alertas_data import Gestor_Alertas
    
#     # Inicializar gestor de alertas
#     self.gestor_alertas = Gestor_Alertas(
#         archivo_usuarios="usuarios.json",
#         archivo_alertas="alertas.json"
#     )
    
#     # Panel de alertas (se inicializa después del login)
#     self.panel_alertas = None
    
    
#     # En on_login_exitoso, después de crear panel_filtros:
    
#     # Crear panel de alertas
#     self.panel_alertas = PanelAlertas(
#         page=self.page,
#         usuario=self.usuario_actual,
#         gestor_alertas=self.gestor_alertas,
#         on_ver_detalle_callback=self.ver_detalle_desde_alerta
#     )
    
    
#     # En mostrar_inicio, modificar barra_usuario:
    
#     barra_usuario = ft.Row(
#         [
#             ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.BLUE_700),
#             ft.Text(f"Usuario: {self.usuario_actual}", weight="bold", size=16),
            
#             # AÑADIR BOTÓN DE ALERTAS AQUÍ
#             self.panel_alertas.obtener_boton(),
            
#             ft.VerticalDivider(width=20),
#             ft.ElevatedButton(
#                 "Cerrar Sesión",
#                 icon=ft.Icons.LOGOUT,
#                 on_click=lambda e: self.cerrar_sesion(),
#                 style=ft.ButtonStyle(
#                     bgcolor=ft.Colors.RED_400,
#                     color=ft.Colors.WHITE,
#                 )
#             ),
#         ],
#         alignment=ft.MainAxisAlignment.END,
#     )
    
    
#     # Añadir nuevo método para ver detalle desde alerta:
    
#     def ver_detalle_desde_alerta(self, licitacion_id):
#         """Ver detalle de licitación desde una alerta"""
#         # Buscar la licitación en el DataFrame
#         licitacion = self.df_general[self.df_general["ID"] == licitacion_id]
#         if not licitacion.empty:
#             row = licitacion.iloc[0].to_dict()
#             self.mostrar_detalle(row)
#         else:
#             # Mostrar snackbar si no se encuentra
#             snack = ft.SnackBar(
#                 content=ft.Text("⚠️ No se encontró la licitación"),
#                 bgcolor=ft.Colors.ORANGE,
#             )
#             self.page.overlay.append(snack)
#             snack.open = True
#             self.page.update()
#     '''
    
#     print(ejemplo)


# if __name__ == "__main__":
#     print("Panel de Alertas para Flet")
#     print("=" * 80)
#     print("Este módulo proporciona un panel de alertas visual para la aplicación.")
#     print("\nPara integrarlo:")
#     integrar_panel_alertas_en_app()

## --------------------------------------------

import flet as ft
from datetime import datetime, date
import json
import os
from .diagnostico_drawer import diagnosticar_drawer


class PanelAlertas:
    def __init__(self, page: ft.Page, usuario: str, gestor_alertas, on_ver_detalle_callback):
        """
        Panel de alertas para mostrar notificaciones de licitaciones.
        
        Args:
            page: Página de Flet
            usuario: Nombre del usuario actual
            gestor_alertas: Instancia del GestorAlertas
            on_ver_detalle_callback: Callback para ver detalle de licitación
        """
        self.page = page
        self.usuario = usuario
        self.gestor_alertas = gestor_alertas
        self.on_ver_detalle_callback = on_ver_detalle_callback
        self.alertas = []
        self.alertas_no_leidas = 0
        
        # Cargar alertas
        self._cargar_alertas()
        
        # CAMBIO 1: Crear contenedor para el badge que se pueda actualizar
        self.badge_container = ft.Container()
        
        # CAMBIO 2: Crear Stack para el botón que se pueda actualizar
        self.boton_stack = ft.Stack(
            width=35,
            height=35,
        )
        
        # Crear botón de alertas
        self.boton_alertas = self._crear_boton()
        
        # CAMBIO 3: Crear contenedor wrapper que siempre retornaremos
        self.boton_wrapper = ft.Container(
            content=self.boton_alertas,
            tooltip="Ver alertas",
            on_click=lambda e: self._mostrar_panel_alertas(),
            padding=8,
            border_radius=25,
            ink=True,
            alignment=ft.Alignment(0, 0),
        )
    
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
        """
        Calcula los días restantes hasta la fecha límite.
        
        Returns:
            tuple: (dias_restantes, texto_mostrar, color)
        """
        if not fecha_limite_str or fecha_limite_str == "None" or fecha_limite_str is None:
            return None, "Sin fecha límite", ft.Colors.GREY_500
        
        try:
            # Intentar parsear diferentes formatos de fecha
            if isinstance(fecha_limite_str, str):
                # Formato ISO: 2026-02-15
                if '-' in fecha_limite_str:
                    fecha_limite = datetime.strptime(fecha_limite_str[:10], "%Y-%m-%d").date()
                # Formato español: 15/02/2026
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
            
            # Determinar color según urgencia
            if dias_restantes < 0:
                color = ft.Colors.RED_700
                texto = f"Venció hace {abs(dias_restantes)} días"
            elif dias_restantes == 0:
                color = ft.Colors.ORANGE_700
                texto = "¡Vence HOY!"
            elif dias_restantes <= 3:
                color = ft.Colors.ORANGE_700
                texto = f"⚠️ {dias_restantes} días"
            elif dias_restantes <= 7:
                color = ft.Colors.AMBER_700
                texto = f"{dias_restantes} días"
            elif dias_restantes <= 15:
                color = ft.Colors.BLUE_700
                texto = f"{dias_restantes} días"
            else:
                color = ft.Colors.GREEN_700
                texto = f"{dias_restantes} días"
            
            return dias_restantes, texto, color
            
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
            # CAMBIO 4: Actualizar el Stack existente en lugar de crear uno nuevo
            self.boton_stack.controls = [
                icono,
                ft.Container(
                    content=badge,
                    right=0,
                    top=0,
                ),
            ]
            return self.boton_stack
        else:
            return icono
    
    def _crear_tarjeta_alerta(self, alerta):
        """Crea una tarjeta visual para una alerta individual"""
        metadatos = alerta.get('metadatos', {})
        info_licitacion = metadatos.get('licitacion_info', {})
        
        # Información de la licitación
        nombre = info_licitacion.get('nombre', 'Sin nombre')[:80] + "..."
        entidad = info_licitacion.get('entidad', 'Sin entidad')
        importe = info_licitacion.get('importe', 'No especificado')
        estado = info_licitacion.get('estado', 'Sin estado')
        fecha_limite = info_licitacion.get('fecha_limite')
        url = info_licitacion.get('url', '')
        
        # Calcular días restantes
        dias_restantes, texto_dias, color_dias = self._calcular_dias_restantes(fecha_limite)
        
        # Icono y color del estado
        icono_estado, color_estado = self._obtener_icono_estado(estado)
        
        # Coincidencias
        coincidencias = metadatos.get('coincidencias', [])
        chips_coincidencias = ft.Row(
            [
                ft.Chip(
                    label=ft.Text(
                        "CPV" if coin == "cpv" else "Palabra clave",
                        size=11,
                    ),
                    bgcolor=ft.Colors.BLUE_50 if coin == "cpv" else ft.Colors.GREEN_50,
                    height=25,
                ) for coin in coincidencias
            ],
            spacing=5,
        )
        
        # Información del estado
        estado_row = ft.Row(
            [
                ft.Icon(icono_estado, color=color_estado, size=18),
                ft.Text(estado, size=13, weight="w500", color=color_estado),
            ],
            spacing=5,
        )

        # Información de fecha límite
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

        # Indicador de no leída
        indicador_leida = ft.Container(
            width=8,
            height=8,
            bgcolor=ft.Colors.BLUE_600 if not alerta['leida'] else ft.Colors.TRANSPARENT,
            border_radius=4,
        )
        
        # Botones de acción
        botones = ft.Row(
            [
                ft.Button(
                    "Ver detalles",
                    icon=ft.Icons.OPEN_IN_NEW,
                    on_click=lambda e, aid=alerta['licitacion_id']: self._ver_detalle_licitacion(aid),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE,
                    ),
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

        # Tarjeta completa
        tarjeta = ft.Container(
            content=ft.Row(
                [
                    indicador_leida,
                    ft.Column(
                        [
                            ft.Text(nombre, size=14, weight="bold", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"📋 {alerta['busqueda']['nombre']}", size=12, color=ft.Colors.GREY_700, italic=True),
                            ft.Divider(height=5),
                            # Entidad
                            ft.Row([ft.Icon(ft.Icons.BUSINESS, size=14, color=ft.Colors.GREY_600),
                                    ft.Text(entidad[:50] + "..." if len(entidad) > 50 else entidad, size=12, color=ft.Colors.GREY_700)],
                                    spacing=5),
                            # Importe
                            ft.Row([ft.Icon(ft.Icons.EURO, size=14, color=ft.Colors.GREY_600),
                                    ft.Text(f"{importe}", size=12, color=ft.Colors.GREY_700)],
                                    spacing=5),
                            # Estado y fecha
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
        """Muestra el panel lateral con todas las alertas"""
        # CAMBIO 5: Debug - imprimir para verificar que se llama
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
                        ft.Text("No tienes alertas", size=18, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                        ft.Text("Las alertas aparecerán aquí cuando haya nuevas licitaciones", 
                               size=14, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
        else:
            tarjetas = [self._crear_tarjeta_alerta(alerta) for alerta in self.alertas]
            contenido_alertas = ft.Column(
                tarjetas,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
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
                        ft.Text(str(self.alertas_no_leidas), size=24, weight="bold", color=ft.Colors.ORANGE_700),
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
        
        # Panel completo
        panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row([
                        ft.Text("🔔 Mis Alertas", size=22, weight="bold"),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=lambda e: self._cerrar_panel()
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    estadisticas,
                    botones_gestion,
                    ft.Divider(),
                    contenido_alertas,
                ],
                expand=True,
            ),
            bgcolor=ft.Colors.WHITE,
            padding=20,
            width=400,
        )
        
        # CAMBIO 6: Crear drawer correctamente
        self.drawer = ft.NavigationDrawer(
            controls=[panel],
        )
        
        # Asignarlo a end_drawer para que aparezca desde la derecha
        self.page.end_drawer = self.drawer
        
        # Abrirlo
        self.drawer.open = True
        
        # CAMBIO 7: Actualizar la página
         # Crear drawer
        self.drawer = ft.NavigationDrawer(
            controls=[panel],
        )
        
        self.page.end_drawer = self.drawer
        self.drawer.open = True
        
        # DIAGNÓSTICO ANTES DE ACTUALIZAR
        self.diagnosticar_drawer()
        
        self.page.update()
        # self.page.update()
        
        print("   ✅ Panel mostrado correctamente")
    
    def _cerrar_panel(self):
        """Cierra el panel de alertas"""
        print("🔔 Cerrando panel de alertas")
        
        if hasattr(self, 'drawer') and self.drawer:
            self.drawer.open = False
        
        # CAMBIO 8: Actualizar el botón después de cerrar
        self._actualizar_boton()
        
        self.page.update()

    def diagnosticar_drawer(self):
        """Añade este método en PanelAlertas para diagnosticar el problema del drawer"""
        print("\n" + "="*80)
        print("🔍 DIAGNÓSTICO COMPLETO DEL DRAWER")
        print("="*80)
        
        # 1. Verificar que la página existe
        print(f"\n1. Estado de la página:")
        print(f"   - self.page existe: {self.page is not None}")
        print(f"   - Tipo: {type(self.page)}")
        
        # 2. Verificar el drawer
        if hasattr(self, 'drawer'):
            print(f"\n2. Estado del drawer:")
            print(f"   - self.drawer existe: {self.drawer is not None}")
            print(f"   - Tipo: {type(self.drawer)}")
            print(f"   - drawer.open: {self.drawer.open}")
            print(f"   - Número de controles: {len(self.drawer.controls) if self.drawer.controls else 0}")
        else:
            print(f"\n2. ❌ self.drawer NO existe")
        
        # 3. Verificar end_drawer de la página
        print(f"\n3. Estado de page.end_drawer:")
        print(f"   - page.end_drawer existe: {hasattr(self.page, 'end_drawer')}")
        if hasattr(self.page, 'end_drawer'):
            print(f"   - page.end_drawer es None: {self.page.end_drawer is None}")
            if self.page.end_drawer:
                print(f"   - page.end_drawer.open: {self.page.end_drawer.open}")
        
        # 4. Verificar overlay
        print(f"\n4. Estado de overlays:")
        print(f"   - page.overlay existe: {hasattr(self.page, 'overlay')}")
        if hasattr(self.page, 'overlay'):
            print(f"   - Número de overlays: {len(self.page.overlay)}")
        
        # 5. Verificar drawer (drawer izquierdo)
        print(f"\n5. Estado de page.drawer (izquierdo):")
        if hasattr(self.page, 'drawer'):
            print(f"   - page.drawer existe: {self.page.drawer is not None}")
            if self.page.drawer:
                print(f"   - page.drawer.open: {self.page.drawer.open}")
        
        print("\n" + "="*80 + "\n")

    
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
        
        # Actualizar vista
        self._mostrar_panel_alertas()
    
    def _marcar_todas_leidas(self):
        """Marca todas las alertas como leídas"""
        count = 0
        for alerta in self.alertas:
            if not alerta['leida']:
                self.gestor_alertas.marcar_alerta_leida(alerta['id_alerta'])
                count += 1
        
        print(f"🔔 {count} alertas marcadas como leídas")
        
        # Actualizar vista
        self._mostrar_panel_alertas()
    
    def _limpiar_alertas_leidas(self):
        """Elimina todas las alertas leídas"""
        count = 0
        for alerta in self.alertas:
            if alerta['leida']:
                self.gestor_alertas.eliminar_alerta(alerta['id_alerta'])
                count += 1
        
        print(f"🔔 {count} alertas leídas eliminadas")
        
        # Actualizar vista
        self._mostrar_panel_alertas()
    
    def _actualizar_boton(self):
        """Actualiza el botón de alertas con el nuevo badge"""
        print("🔔 Actualizando botón de alertas")
        
        # CAMBIO 9: Recargar alertas
        self._cargar_alertas()
        
        # CAMBIO 10: Actualizar el contenido del wrapper en lugar de crear uno nuevo
        nuevo_contenido = self._crear_boton()
        self.boton_wrapper.content = nuevo_contenido
        
        # Forzar actualización si la página está disponible
        if hasattr(self, 'page') and self.page:
            self.page.update()
        
        print(f"   Alertas no leídas: {self.alertas_no_leidas}")
    
    def obtener_boton(self):
        """Retorna el botón de alertas para añadir a la interfaz"""
        # CAMBIO 11: Siempre retornar el mismo wrapper
        return self.boton_wrapper
    
    def actualizar(self):
        """Actualiza el panel de alertas"""
        print("🔔 Actualizando panel de alertas completo")
        self._cargar_alertas()
        self._actualizar_boton()

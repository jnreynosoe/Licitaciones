# import flet as ft
# import json
# import os
# from datetime import datetime
# import hashlib

# # ==========================================
# # GESTOR DE USUARIOS Y AUTENTICACIÓN
# # ==========================================

# class GestorUsuarios:
#     def __init__(self, archivo="usuarios.json"):
#         self.archivo = archivo
#         self.usuarios = self._cargar_usuarios()
    
#     def _cargar_usuarios(self):
#         """Carga usuarios desde archivo JSON"""
#         if os.path.exists(self.archivo):
#             with open(self.archivo, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         return {}
    
#     def _guardar_usuarios(self):
#         """Guarda usuarios en archivo JSON"""
#         with open(self.archivo, 'w', encoding='utf-8') as f:
#             json.dump(self.usuarios, f, indent=2, ensure_ascii=False)
    
#     def _hash_password(self, password):
#         """Crea hash de la contraseña"""
#         return hashlib.sha256(password.encode()).hexdigest()
    
#     def registrar_usuario(self, username, password, email=""):
#         """Registra un nuevo usuario"""
#         if username in self.usuarios:
#             return False, "El usuario ya existe"
        
#         self.usuarios[username] = {
#             "password": self._hash_password(password),
#             "email": email,
#             "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "busquedas_guardadas": [],
#             "cpvs_descartados": [],
#             "grupos_cpv": {},
#             "favoritos": [],
#             "configuracion": {
#                 "alertas_activas": True,
#                 "limite_licitaciones": None
#             }
#         }
#         self._guardar_usuarios()
#         return True, "Usuario registrado exitosamente"
    
#     def autenticar(self, username, password):
#         """Autentica un usuario"""
#         if username not in self.usuarios:
#             return False, "Usuario no encontrado"
        
#         if self.usuarios[username]["password"] == self._hash_password(password):
#             return True, "Autenticación exitosa"
#         return False, "Contraseña incorrecta"
    
#     def obtener_usuario(self, username):
#         """Obtiene datos del usuario"""
#         return self.usuarios.get(username, None)
    
#     def guardar_busqueda(self, username, nombre_busqueda, filtros):
#         """Guarda una búsqueda para el usuario"""
#         if username not in self.usuarios:
#             return False
        
#         busqueda = {
#             "nombre": nombre_busqueda,
#             "filtros": filtros,
#             "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         }
        
#         self.usuarios[username]["busquedas_guardadas"].append(busqueda)
#         self._guardar_usuarios()
#         return True
    
#     def obtener_busquedas(self, username):
#         """Obtiene las búsquedas guardadas del usuario"""
#         if username not in self.usuarios:
#             return []
#         return self.usuarios[username]["busquedas_guardadas"]
    
#     def eliminar_busqueda(self, username, nombre_busqueda):
#         """Elimina una búsqueda guardada"""
#         if username not in self.usuarios:
#             return False
        
#         busquedas = self.usuarios[username]["busquedas_guardadas"]
#         self.usuarios[username]["busquedas_guardadas"] = [
#             b for b in busquedas if b["nombre"] != nombre_busqueda
#         ]
#         self._guardar_usuarios()
#         return True


# # ==========================================
# # PANTALLA DE LOGIN
# # ==========================================

# class PantallaLogin:
#     def __init__(self, page: ft.Page, gestor_usuarios: GestorUsuarios, on_login_exitoso):
#         self.page = page
#         self.gestor = gestor_usuarios
#         self.on_login_exitoso = on_login_exitoso
        
#         # Campos de formulario
#         self.txt_usuario = ft.TextField(
#             label="Usuario",
#             width=300,
#             autofocus=True,
#             prefix_icon=ft.Icons.PERSON,
#         )
        
#         self.txt_password = ft.TextField(
#             label="Contraseña",
#             width=300,
#             password=True,
#             can_reveal_password=True,
#             prefix_icon=ft.Icons.LOCK,
#             on_submit=lambda e: self.iniciar_sesion(),
#         )
        
#         self.txt_mensaje = ft.Text("", color=ft.Colors.RED, size=14)
        
#         # Botones
#         self.btn_login = ft.Button(
#             "Iniciar Sesión",
#             width=300,
#             on_click=lambda e: self.iniciar_sesion(),
#             style=ft.ButtonStyle(
#                 color=ft.Colors.WHITE,
#                 bgcolor=ft.Colors.BLUE_700,
#             )
#         )
        
#         self.btn_registro = ft.TextButton(
#             "¿No tienes cuenta? Regístrate",
#             on_click=lambda e: self.mostrar_registro(),
#         )
        
#         # Construcción del layout
#         self.container = ft.Container(
#             content=ft.Column(
#                 [
#                     ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=ft.Colors.BLUE_700),
#                     ft.Text("Explorador de Licitaciones", size=28, weight="bold"),
#                     ft.Text("Inicia sesión para acceder", size=16, color=ft.Colors.GREY_700),
#                     ft.Divider(height=30, color="transparent"),
#                     self.txt_usuario,
#                     self.txt_password,
#                     self.txt_mensaje,
#                     self.btn_login,
#                     self.btn_registro,
#                 ],
#                 horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#                 spacing=15,
#             ),
#             padding=40,
#             border_radius=10,
#             bgcolor=ft.Colors.WHITE,
#             shadow=ft.BoxShadow(
#                 spread_radius=1,
#                 blur_radius=15,
#                 color=ft.Colors.BLUE_GREY_100,
#             ),
#         )
    
#     def iniciar_sesion(self):
#         """Maneja el inicio de sesión"""
#         usuario = self.txt_usuario.value
#         password = self.txt_password.value
        
#         if not usuario or not password:
#             self.txt_mensaje.value = "Por favor completa todos los campos"
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
#             return
        
#         exito, mensaje = self.gestor.autenticar(usuario, password)
        
#         if exito:
#             self.txt_mensaje.value = mensaje
#             self.txt_mensaje.color = ft.Colors.GREEN
#             self.page.update()
#             # Llamar al callback con el usuario autenticado
#             self.on_login_exitoso(usuario)
#         else:
#             self.txt_mensaje.value = mensaje
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
    
#     def mostrar_registro(self):
#         """Muestra el formulario de registro"""
#         self.page.clean()
#         registro = PantallaRegistro(
#             self.page, 
#             self.gestor, 
#             lambda: self.mostrar_login()
#         )
#         self.page.add(
#             ft.Container(
#                 content=registro.container,
#                 alignment=ft.alignment.center,
#                 expand=True,
#             )
#         )
#         self.page.update()
    
#     def mostrar_login(self):
#         """Muestra el formulario de login"""
#         self.page.clean()
#         self.page.add(
#             ft.Container(
#                 content=self.container,
#                 alignment=ft.alignment.center,
#                 expand=True,
#             )
#         )
#         self.page.update()


# # ==========================================
# # PANTALLA DE REGISTRO
# # ==========================================

# class PantallaRegistro:
#     def __init__(self, page: ft.Page, gestor_usuarios: GestorUsuarios, on_volver):
#         self.page = page
#         self.gestor = gestor_usuarios
#         self.on_volver = on_volver
        
#         # Campos de formulario
#         self.txt_usuario = ft.TextField(
#             label="Usuario",
#             width=300,
#             prefix_icon=ft.Icons.PERSON,
#         )
        
#         self.txt_email = ft.TextField(
#             label="Email (opcional)",
#             width=300,
#             prefix_icon=ft.Icons.EMAIL,
#         )
        
#         self.txt_password = ft.TextField(
#             label="Contraseña",
#             width=300,
#             password=True,
#             can_reveal_password=True,
#             prefix_icon=ft.Icons.LOCK,
#         )
        
#         self.txt_password_confirm = ft.TextField(
#             label="Confirmar Contraseña",
#             width=300,
#             password=True,
#             can_reveal_password=True,
#             prefix_icon=ft.Icons.LOCK,
#         )
        
#         self.txt_mensaje = ft.Text("", size=14)
        
#         # Botones
#         self.btn_registro = ft.Button(
#             "Registrarse",
#             width=300,
#             on_click=lambda e: self.registrar(),
#             style=ft.ButtonStyle(
#                 color=ft.Colors.WHITE,
#                 bgcolor=ft.Colors.GREEN_700,
#             )
#         )
        
#         self.btn_volver = ft.TextButton(
#             "Ya tengo cuenta. Iniciar sesión",
#             on_click=lambda e: self.on_volver(),
#         )
        
#         # Construcción del layout
#         self.container = ft.Column(
#             [
#                 ft.Icon(ft.Icons.PERSON_ADD, size=80, color=ft.Colors.GREEN_700),
#                 ft.Text("Crear Nueva Cuenta", size=28, weight="bold"),
#                 ft.Text("Completa el formulario para registrarte", size=16, color=ft.Colors.GREY_700),
#                 ft.Divider(height=30, color="transparent"),
#                 self.txt_usuario,
#                 self.txt_email,
#                 self.txt_password,
#                 self.txt_password_confirm,
#                 self.txt_mensaje,
#                 self.btn_registro,
#                 self.btn_volver,
#             ],
#             horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#             spacing=15,
#         )
    
#     def registrar(self):
#         """Maneja el registro de usuario"""
#         usuario = self.txt_usuario.value
#         email = self.txt_email.value
#         password = self.txt_password.value
#         password_confirm = self.txt_password_confirm.value
        
#         # Validaciones
#         if not usuario or not password:
#             self.txt_mensaje.value = "Usuario y contraseña son obligatorios"
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
#             return
        
#         if len(password) < 6:
#             self.txt_mensaje.value = "La contraseña debe tener al menos 6 caracteres"
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
#             return
        
#         if password != password_confirm:
#             self.txt_mensaje.value = "Las contraseñas no coinciden"
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
#             return
        
#         exito, mensaje = self.gestor.registrar_usuario(usuario, password, email)
        
#         if exito:
#             self.txt_mensaje.value = f"{mensaje}. Redirigiendo al login..."
#             self.txt_mensaje.color = ft.Colors.GREEN
#             self.page.update()
#             # Esperar un momento y volver al login
#             import time
#             time.sleep(1.5)
#             self.on_volver()
#         else:
#             self.txt_mensaje.value = mensaje
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()


# # ==========================================
# # PANEL DE BÚSQUEDAS GUARDADAS
# # ==========================================

# class PanelBusquedasUsuario:
#     def __init__(self, gestor_usuarios: GestorUsuarios, usuario_actual: str, on_cargar_busqueda):
#         self.gestor = gestor_usuarios
#         self.usuario = usuario_actual
#         self.on_cargar_busqueda = on_cargar_busqueda
        
#         self.lista_busquedas = ft.Column(spacing=10)
#         self.actualizar_lista()
        
#         self.container = ft.Container(
#             content=ft.Column([
#                 ft.Row([
#                     ft.Icon(ft.Icons.BOOKMARK, color=ft.Colors.BLUE_700),
#                     ft.Text("Mis Búsquedas Guardadas", size=18, weight="bold"),
#                 ], spacing=10),
#                 ft.Divider(),
#                 self.lista_busquedas,
#             ]),
#             padding=20,
#             border=ft.Border.all(1, ft.Colors.BLUE_200),
#             border_radius=10,
#             bgcolor=ft.Colors.BLUE_50,
#         )
    
#     def actualizar_lista(self):
#         """Actualiza la lista de búsquedas guardadas"""
#         self.lista_busquedas.controls.clear()
#         busquedas = self.gestor.obtener_busquedas(self.usuario)
        
#         if not busquedas:
#             self.lista_busquedas.controls.append(
#                 ft.Text("No tienes búsquedas guardadas", color=ft.Colors.GREY_600, italic=True)
#             )
#         else:
#             for busqueda in busquedas:
#                 self.lista_busquedas.controls.append(
#                     self._crear_tarjeta_busqueda(busqueda)
#                 )
    
#     def _crear_tarjeta_busqueda(self, busqueda):
#         """Crea una tarjeta para mostrar una búsqueda guardada"""
#         return ft.Card(
#             content=ft.Container(
#                 content=ft.Column([
#                     ft.Row([
#                         ft.Text(busqueda["nombre"], weight="bold", size=16, expand=True),
#                         ft.IconButton(
#                             icon=ft.Icons.DELETE,
#                             icon_color=ft.Colors.RED_400,
#                             tooltip="Eliminar",
#                             on_click=lambda e, nombre=busqueda["nombre"]: self.eliminar_busqueda(nombre),
#                         ),
#                     ]),
#                     ft.Text(f"Guardada el: {busqueda['fecha']}", size=12, color=ft.Colors.GREY_600),
#                     ft.Button(
#                         "Cargar búsqueda",
#                         icon=ft.Icons.SEARCH,
#                         on_click=lambda e, f=busqueda["filtros"]: self.on_cargar_busqueda(f),
#                     ),
#                 ]),
#                 padding=15,
#             )
#         )
    
#     def eliminar_busqueda(self, nombre):
#         """Elimina una búsqueda guardada"""
#         self.gestor.eliminar_busqueda(self.usuario, nombre)
#         self.actualizar_lista()
#         self.container.update()


# # ==========================================
# # DIÁLOGO PARA GUARDAR BÚSQUEDA
# # ==========================================

# class DialogoGuardarBusquedaUsuario:
#     def __init__(self, page: ft.Page, gestor_usuarios: GestorUsuarios, usuario_actual: str, filtros_actuales: dict):
#         self.page = page
#         self.gestor = gestor_usuarios
#         self.usuario = usuario_actual
#         self.filtros = filtros_actuales
        
#         self.txt_nombre = ft.TextField(
#             label="Nombre de la búsqueda",
#             hint_text="Ej: Licitaciones de construcción",
#             autofocus=True,
#         )
        
#         self.dlg = ft.AlertDialog(
#             modal=True,
#             title=ft.Text("Guardar Búsqueda"),
#             content=ft.Container(
#                 content=self.txt_nombre,
#                 width=400,
#             ),
#             actions=[
#                 ft.TextButton("Cancelar", on_click=lambda e: self.cerrar()),
#                 ft.Button("Guardar", on_click=lambda e: self.guardar()),
#             ],
#             actions_alignment=ft.MainAxisAlignment.END,
#         )
    
#     def mostrar(self):
#         """Muestra el diálogo"""
#         self.page.dialog = self.dlg
#         self.dlg.open = True
#         self.page.update()
    
#     def cerrar(self):
#         """Cierra el diálogo"""
#         self.dlg.open = False
#         self.page.update()
    
#     def guardar(self):
#         """Guarda la búsqueda"""
#         nombre = self.txt_nombre.value
#         if not nombre:
#             # Mostrar mensaje de error
#             return
        
#         exito = self.gestor.guardar_busqueda(self.usuario, nombre, self.filtros)
#         if exito:
#             self.cerrar()
#             # Mostrar mensaje de éxito
#             snack = ft.SnackBar(
#                 content=ft.Text(f"Búsqueda '{nombre}' guardada exitosamente"),
#                 bgcolor=ft.Colors.GREEN,
#             )
#             self.page.overlay.append(snack)
#             snack.open = True
#             self.page.update()

# ------------------------------------------------------------------

# import flet as ft
# import json
# import os
# from datetime import datetime
# import hashlib

# # ==========================================
# # GESTOR DE USUARIOS Y AUTENTICACIÓN
# # ==========================================

# class GestorUsuarios:
#     def __init__(self, archivo="usuarios.json"):
#         self.archivo = archivo
#         self.usuarios = self._cargar_usuarios()
    
#     def _cargar_usuarios(self):
#         """Carga usuarios desde archivo JSON"""
#         if os.path.exists(self.archivo):
#             with open(self.archivo, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         return {}
    
#     def _guardar_usuarios(self):
#         """Guarda usuarios en archivo JSON"""
#         with open(self.archivo, 'w', encoding='utf-8') as f:
#             json.dump(self.usuarios, f, indent=2, ensure_ascii=False)
    
#     def _hash_password(self, password):
#         """Crea hash de la contraseña"""
#         return hashlib.sha256(password.encode()).hexdigest()
    
#     def registrar_usuario(self, username, password, email=""):
#         """Registra un nuevo usuario"""
#         if username in self.usuarios:
#             return False, "El usuario ya existe"
        
#         self.usuarios[username] = {
#             "password": self._hash_password(password),
#             "email": email,
#             "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "busquedas_guardadas": [],
#             "cpvs_descartados": [],
#             "grupos_cpv": [],
#             "favoritos": [],
#             "configuracion": {
#                 "alertas_activas": True,
#                 "limite_licitaciones": None
#             }
#         }
#         self._guardar_usuarios()
#         return True, "Usuario registrado exitosamente"
    
#     def autenticar(self, username, password):
#         """Autentica un usuario"""
#         if username not in self.usuarios:
#             return False, "Usuario no encontrado"
        
#         if self.usuarios[username]["password"] == self._hash_password(password):
#             return True, "Autenticación exitosa"
#         return False, "Contraseña incorrecta"
    
#     def obtener_usuario(self, username):
#         """Obtiene datos del usuario"""
#         return self.usuarios.get(username, None)
    
#     def guardar_busqueda(self, username, nombre_busqueda, filtros):
#         """Guarda una búsqueda para el usuario"""
#         if username not in self.usuarios:
#             return False
        
#         busqueda = {
#             "nombre": nombre_busqueda,
#             "filtros": filtros,
#             "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         }
        
#         self.usuarios[username]["busquedas_guardadas"].append(busqueda)
#         self._guardar_usuarios()
#         return True
    
#     def obtener_busquedas(self, username):
#         """Obtiene las búsquedas guardadas del usuario"""
#         if username not in self.usuarios:
#             return []
#         return self.usuarios[username]["busquedas_guardadas"]
    
#     def eliminar_busqueda(self, username, nombre_busqueda):
#         """Elimina una búsqueda guardada"""
#         if username not in self.usuarios:
#             return False
        
#         busquedas = self.usuarios[username]["busquedas_guardadas"]
#         self.usuarios[username]["busquedas_guardadas"] = [
#             b for b in busquedas if b["nombre"] != nombre_busqueda
#         ]
#         self._guardar_usuarios()
#         return True


# # ==========================================
# # PANTALLA DE LOGIN
# # ==========================================

# class PantallaLogin:
#     def __init__(self, page: ft.Page, gestor_usuarios: GestorUsuarios, on_login_exitoso):
#         # self.page = page
#         self.gestor = gestor_usuarios
#         self.on_login_exitoso = on_login_exitoso
        
#         # Campos de formulario
#         self.txt_usuario = ft.TextField(
#             label="Usuario",
#             width=300,
#             autofocus=True,
#             prefix_icon=ft.Icons.PERSON,
#         )
        
#         self.txt_password = ft.TextField(
#             label="Contraseña",
#             width=300,
#             password=True,
#             can_reveal_password=True,
#             prefix_icon=ft.Icons.LOCK,
#             on_submit=lambda e: self.iniciar_sesion(),
#         )
        
#         self.txt_mensaje = ft.Text("", color=ft.Colors.RED, size=14)
        
#         # Botones
#         self.btn_login = ft.Button(
#             "Iniciar Sesión",
#             width=300,
#             on_click=lambda e: self.iniciar_sesion(),
#             style=ft.ButtonStyle(
#                 color=ft.Colors.WHITE,
#                 bgcolor=ft.Colors.BLUE_700,
#             )
#         )
        
#         self.btn_registro = ft.TextButton(
#             "¿No tienes cuenta? Regístrate",
#             on_click=lambda e: self.mostrar_registro(),
#         )
        
#         # Construcción del layout
#         self.container = ft.Container(
#             content=ft.Column(
#                 [
#                     ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=ft.Colors.BLUE_700),
#                     ft.Text("Explorador de Licitaciones", size=28, weight="bold"),
#                     ft.Text("Inicia sesión para acceder", size=16, color=ft.Colors.GREY_700),
#                     ft.Divider(height=30, color="transparent"),
#                     self.txt_usuario,
#                     self.txt_password,
#                     self.txt_mensaje,
#                     self.btn_login,
#                     self.btn_registro,
#                 ],
#                 horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#                 spacing=15,
#             ),
#             padding=40,
#             border_radius=10,
#             bgcolor=ft.Colors.WHITE,
#             shadow=ft.BoxShadow(
#                 spread_radius=1,
#                 blur_radius=15,
#                 color=ft.Colors.BLUE_GREY_100,
#             ),
#         )
    
#     def iniciar_sesion(self):
#         """Maneja el inicio de sesión"""
#         usuario = self.txt_usuario.value
#         password = self.txt_password.value
        
#         if not usuario or not password:
#             self.txt_mensaje.value = "Por favor completa todos los campos"
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
#             return
        
#         exito, mensaje = self.gestor.autenticar(usuario, password)
        
#         if exito:
#             self.txt_mensaje.value = mensaje
#             self.txt_mensaje.color = ft.Colors.GREEN
#             self.page.update()
#             # Llamar al callback con el usuario autenticado
#             self.on_login_exitoso(usuario)
#         else:
#             self.txt_mensaje.value = mensaje
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
    
#     def mostrar_registro(self):
#         """Muestra el formulario de registro"""
#         self.page.clean()
#         registro = PantallaRegistro(
#             self.page, 
#             self.gestor, 
#             lambda: self.mostrar_login()
#         )
#         self.page.add(
#             ft.Container(
#                 content=registro.container,
#                 alignment=ft.Alignment(0,0),
#                 expand=True,
#             )
#         )
#         self.page.update()
    
#     def mostrar_login(self):
#         """Muestra el formulario de login"""
#         self.page.clean()
#         self.page.add(
#             ft.Container(
#                 content=self.container,
#                 alignment=ft.Alignment(0,0),
#                 expand=True,
#             )
#         )
#         self.page.update()


# # ==========================================
# # PANTALLA DE REGISTRO
# # ==========================================

# class PantallaRegistro:
#     def __init__(self, page: ft.Page, gestor_usuarios: GestorUsuarios, on_volver):
#         # self.page = page
#         self.gestor = gestor_usuarios
#         self.on_volver = on_volver
        
#         # Campos de formulario
#         self.txt_usuario = ft.TextField(
#             label="Usuario",
#             width=300,
#             prefix_icon=ft.Icons.PERSON,
#         )
        
#         self.txt_email = ft.TextField(
#             label="Email (opcional)",
#             width=300,
#             prefix_icon=ft.Icons.EMAIL,
#         )
        
#         self.txt_password = ft.TextField(
#             label="Contraseña",
#             width=300,
#             password=True,
#             can_reveal_password=True,
#             prefix_icon=ft.Icons.LOCK,
#         )
        
#         self.txt_password_confirm = ft.TextField(
#             label="Confirmar Contraseña",
#             width=300,
#             password=True,
#             can_reveal_password=True,
#             prefix_icon=ft.Icons.LOCK,
#         )
        
#         self.txt_mensaje = ft.Text("", size=14)
        
#         # Botones
#         self.btn_registro = ft.Button(
#             "Registrarse",
#             width=300,
#             on_click=lambda e: self.registrar(),
#             style=ft.ButtonStyle(
#                 color=ft.Colors.WHITE,
#                 bgcolor=ft.Colors.GREEN_700,
#             )
#         )
        
#         self.btn_volver = ft.TextButton(
#             "Ya tengo cuenta. Iniciar sesión",
#             on_click=lambda e: self.on_volver(),
#         )
        
#         # Construcción del layout
#         self.container = ft.Column(
#             [
#                 ft.Icon(ft.Icons.PERSON_ADD, size=80, color=ft.Colors.GREEN_700),
#                 ft.Text("Crear Nueva Cuenta", size=28, weight="bold"),
#                 ft.Text("Completa el formulario para registrarte", size=16, color=ft.Colors.GREY_700),
#                 ft.Divider(height=30, color="transparent"),
#                 self.txt_usuario,
#                 self.txt_email,
#                 self.txt_password,
#                 self.txt_password_confirm,
#                 self.txt_mensaje,
#                 self.btn_registro,
#                 self.btn_volver,
#             ],
#             horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#             spacing=15,
#         )
    
#     def registrar(self):
#         """Maneja el registro de usuario"""
#         usuario = self.txt_usuario.value
#         email = self.txt_email.value
#         password = self.txt_password.value
#         password_confirm = self.txt_password_confirm.value
        
#         # Validaciones
#         if not usuario or not password:
#             self.txt_mensaje.value = "Usuario y contraseña son obligatorios"
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
#             return
        
#         if len(password) < 6:
#             self.txt_mensaje.value = "La contraseña debe tener al menos 6 caracteres"
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
#             return
        
#         if password != password_confirm:
#             self.txt_mensaje.value = "Las contraseñas no coinciden"
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()
#             return
        
#         exito, mensaje = self.gestor.registrar_usuario(usuario, password, email)
        
#         if exito:
#             self.txt_mensaje.value = f"{mensaje}. Redirigiendo al login..."
#             self.txt_mensaje.color = ft.Colors.GREEN
#             self.page.update()
#             # Esperar un momento y volver al login
#             import time
#             time.sleep(1.5)
#             self.on_volver()
#         else:
#             self.txt_mensaje.value = mensaje
#             self.txt_mensaje.color = ft.Colors.RED
#             self.page.update()


# # ==========================================
# # PANEL DE BÚSQUEDAS GUARDADAS
# # ==========================================

# class PanelBusquedasUsuario:
#     def __init__(self, gestor_usuarios: GestorUsuarios, usuario_actual: str, on_cargar_busqueda):
#         self.gestor = gestor_usuarios
#         self.usuario = usuario_actual
#         self.on_cargar_busqueda = on_cargar_busqueda
        
#         self.lista_busquedas = ft.Column(spacing=10)
#         self.actualizar_lista()
        
#         self.container = ft.Container(
#             content=ft.Column([
#                 ft.Row([
#                     ft.Icon(ft.Icons.BOOKMARK, color=ft.Colors.BLUE_700),
#                     ft.Text("Mis Búsquedas Guardadas", size=18, weight="bold"),
#                 ], spacing=10),
#                 ft.Divider(),
#                 self.lista_busquedas,
#             ]),
#             padding=20,
#             border=ft.Border.all(1, ft.Colors.BLUE_200),
#             border_radius=10,
#             bgcolor=ft.Colors.BLUE_50,
#         )
    
#     def actualizar_lista(self):
#         """Actualiza la lista de búsquedas guardadas"""
#         self.lista_busquedas.controls.clear()
#         busquedas = self.gestor.obtener_busquedas(self.usuario)
        
#         if not busquedas:
#             self.lista_busquedas.controls.append(
#                 ft.Text("No tienes búsquedas guardadas", color=ft.Colors.GREY_600, italic=True)
#             )
#         else:
#             for busqueda in busquedas:
#                 self.lista_busquedas.controls.append(
#                     self._crear_tarjeta_busqueda(busqueda)
#                 )
    
#     def _crear_tarjeta_busqueda(self, busqueda):
#         """Crea una tarjeta para mostrar una búsqueda guardada"""
#         return ft.Card(
#             content=ft.Container(
#                 content=ft.Column([
#                     ft.Row([
#                         ft.Text(busqueda["nombre"], weight="bold", size=16, expand=True),
#                         ft.IconButton(
#                             icon=ft.Icons.DELETE,
#                             icon_color=ft.Colors.RED_400,
#                             tooltip="Eliminar",
#                             on_click=lambda e, nombre=busqueda["nombre"]: self.eliminar_busqueda(nombre),
#                         ),
#                     ]),
#                     # ft.Text(f"Guardada el: {busqueda['fecha']}", size=12, color=ft.Colors.GREY_600),
#                     ft.Button(
#                         "Cargar búsqueda",
#                         icon=ft.Icons.SEARCH,
#                         on_click=lambda e, f=busqueda["filtros"]: self.on_cargar_busqueda(f),
#                     ),
#                 ]),
#                 padding=15,
#             )
#         )
    
#     def eliminar_busqueda(self, nombre):
#         """Elimina una búsqueda guardada"""
#         self.gestor.eliminar_busqueda(self.usuario, nombre)
#         self.actualizar_lista()
#         self.container.update()


# ==========================================
# DIÁLOGO PARA GUARDAR BÚSQUEDA (Compatible con busquedas_guardadas.py)
# ==========================================

# NOTA: Usaremos el DialogoGuardarBusqueda existente del módulo busquedas_guardadas.py
# Este módulo solo maneja la autenticación y el almacenamiento por usuario

## -------------------------------------------------------

import flet as ft
import json
import os
from datetime import datetime
import hashlib

import asyncio

# ==========================================
# GESTOR DE USUARIOS Y AUTENTICACIÓN
# ==========================================

class GestorUsuarios:
    def __init__(self, archivo="usuarios.json"):
        self.archivo = archivo
        self.usuarios = self._cargar_usuarios()
    
    def _cargar_usuarios(self):
        """Carga usuarios desde archivo JSON"""
        if os.path.exists(self.archivo):
            with open(self.archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _guardar_usuarios(self):
        """Guarda usuarios en archivo JSON"""
        with open(self.archivo, 'w', encoding='utf-8') as f:
            json.dump(self.usuarios, f, indent=2, ensure_ascii=False)
    
    def _hash_password(self, password):
        """Crea hash de la contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def registrar_usuario(self, username, password, email=""):
        """Registra un nuevo usuario"""
        if username in self.usuarios:
            return False, "El usuario ya existe"
        
        self.usuarios[username] = {
            "password": self._hash_password(password),
            "email": email,
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "busquedas_guardadas": [],
            "cpvs_descartados": [],
            "grupos_cpv": [],
            "favoritos": [],
            "configuracion": {
                "alertas_activas": True,
                "limite_licitaciones": None
            }
        }
        self._guardar_usuarios()
        return True, "Usuario registrado exitosamente"
    
    def autenticar(self, username, password):
        """Autentica un usuario"""
        if username not in self.usuarios:
            return False, "Usuario no encontrado"
        
        if self.usuarios[username]["password"] == self._hash_password(password):
            return True, "Autenticación exitosa"
        return False, "Contraseña incorrecta"
    
    def obtener_usuario(self, username):
        """Obtiene datos del usuario"""
        return self.usuarios.get(username, None)
    
    def guardar_busqueda(self, username, nombre_busqueda, filtros):
        """Guarda una búsqueda para el usuario"""
        if username not in self.usuarios:
            return False
        
        busqueda = {
            "nombre": nombre_busqueda,
            "filtros": filtros,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.usuarios[username]["busquedas_guardadas"].append(busqueda)
        self._guardar_usuarios()
        return True
    
    def obtener_busquedas(self, username):
        """Obtiene las búsquedas guardadas del usuario"""
        if username not in self.usuarios:
            return []
        return self.usuarios[username]["busquedas_guardadas"]
    
    def eliminar_busqueda(self, username, nombre_busqueda):
        """Elimina una búsqueda guardada"""
        if username not in self.usuarios:
            return False
        
        busquedas = self.usuarios[username]["busquedas_guardadas"]
        self.usuarios[username]["busquedas_guardadas"] = [
            b for b in busquedas if b["nombre"] != nombre_busqueda
        ]
        self._guardar_usuarios()
        return True


# ==========================================
# PANTALLA DE LOGIN
# ==========================================

# class PantallaLogin:
#     def __init__(self, page: ft.Page, gestor_usuarios: GestorUsuarios, on_login_exitoso):
#         self.gestor = gestor_usuarios
#         self.on_login_exitoso = on_login_exitoso
        
#         # Campos de formulario
#         self.txt_usuario = ft.TextField(
#             label="Usuario",
#             width=300,
#             autofocus=True,
#             prefix_icon=ft.Icons.PERSON,
#         )
        
#         self.txt_password = ft.TextField(
#             label="Contraseña",
#             width=300,
#             password=True,
#             can_reveal_password=True,
#             prefix_icon=ft.Icons.LOCK,
#             on_submit=lambda e: self.iniciar_sesion(page),
#         )
        
#         self.txt_mensaje = ft.Text("", color=ft.Colors.RED, size=14)
        
#         # Botones
#         self.btn_login = ft.Button(
#             "Iniciar Sesión",
#             width=300,
#             on_click=lambda e: self.iniciar_sesion(page),
#             style=ft.ButtonStyle(
#                 color=ft.Colors.WHITE,
#                 bgcolor=ft.Colors.BLUE_700,
#             )
#         )
        
#         self.btn_registro = ft.TextButton(
#             "¿No tienes cuenta? Regístrate",
#             on_click=lambda e: self.mostrar_registro(page),
#         )
        
#         # Construcción del layout
#         self.container = ft.Container(
#             content=ft.Column(
#                 [
#                     ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=ft.Colors.BLUE_700),
#                     ft.Text("Explorador de Licitaciones", size=28, weight="bold"),
#                     ft.Text("Inicia sesión para acceder", size=16, color=ft.Colors.GREY_700),
#                     ft.Divider(height=30, color="transparent"),
#                     self.txt_usuario,
#                     self.txt_password,
#                     self.txt_mensaje,
#                     self.btn_login,
#                     self.btn_registro,
#                 ],
#                 horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#                 spacing=15,
#             ),
#             padding=40,
#             border_radius=10,
#             bgcolor=ft.Colors.WHITE,
#             shadow=ft.BoxShadow(
#                 spread_radius=1,
#                 blur_radius=15,
#                 color=ft.Colors.BLUE_GREY_100,
#             ),
#         )
    
#     async def iniciar_sesion(self, page: ft.Page):
#         """Maneja el inicio de sesión"""
#         usuario = self.txt_usuario.value
#         password = self.txt_password.value
        
#         if not usuario or not password:
#             self.txt_mensaje.value = "Por favor completa todos los campos"
#             self.txt_mensaje.color = ft.Colors.RED
#             await page.update_async()
#             return
        
#         exito, mensaje = self.gestor.autenticar(usuario, password)
        
#         if exito:
#             self.txt_mensaje.value = mensaje
#             self.txt_mensaje.color = ft.Colors.GREEN
#             await page.update_async()
#             # Llamar al callback con el usuario autenticado
#             await self.on_login_exitoso(usuario)
#         else:
#             self.txt_mensaje.value = mensaje
#             self.txt_mensaje.color = ft.Colors.RED
#             await page.update_async()

class PantallaLogin(ft.Container): # Heredamos de Container
    def __init__(self, gestor_usuarios, on_login_exitoso, on_mostrar_registro):
        super().__init__() # Inicializamos el contenedor padre
        self.gestor = gestor_usuarios
        self.on_login_exitoso = on_login_exitoso
        self.on_mostrar_registro = on_mostrar_registro
        
        # Expandir para ocupar el espacio y centrar
        self.expand = True
        self.alignment = ft.Alignment(0,0)

        # Definir los controles como atributos de la clase
        self.txt_usuario = ft.TextField(label="Usuario", width=300, prefix_icon=ft.Icons.PERSON)
        self.txt_password = ft.TextField(
            label="Contraseña", width=300, password=True, 
            can_reveal_password=True, prefix_icon=ft.Icons.LOCK,
            on_submit=self.iniciar_sesion
        )
        self.txt_mensaje = ft.Text("", color=ft.Colors.RED)

        # Configurar el contenido del Container
        self.content = ft.Column(
            [
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=ft.Colors.BLUE_700),
                ft.Text("Explorador de Licitaciones", size=28, weight="bold"),
                self.txt_usuario,
                self.txt_password,
                self.txt_mensaje,
                ft.Button("Iniciar Sesión", width=300, on_click=self.iniciar_sesion,
                          style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700)),
                ft.TextButton("¿No tienes cuenta? Regístrate", on_click=self.on_mostrar_registro),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            tight=True # Para que el column no ocupe más espacio del necesario
        )

    async def iniciar_sesion(self, e):
        # self.page ya existe automáticamente aquí porque el control ya está en la página
        usuario = self.txt_usuario.value
        password = self.txt_password.value

        if not usuario or not password:
            self.txt_mensaje.value = "Completa los campos"
            self.update() # Usamos self.update_async() del propio control
            return

        exito, mensaje = self.gestor.autenticar(usuario, password)

        if exito:
            # Importante: on_login_exitoso debe ser async en la clase App
            await self.on_login_exitoso(usuario)
        else:
            self.txt_mensaje.value = mensaje
            self.update()
    
    def mostrar_registro(self, page: ft.Page):
        """Muestra el formulario de registro"""
        page.clean()
        registro = PantallaRegistro(
            # page, 
            self.gestor, 
            lambda: self.mostrar_login(page)
        )
        page.add(
            ft.Container(
                content=registro.container,
                alignment=ft.Alignment(0,0),
                expand=True,
            )
        )
        page.update()
    
    # def mostrar_login(self, page: ft.Page):
    #     """Muestra el formulario de login"""
    #     page.clean()
    #     page.add(
    #         ft.Container(
    #             content=self.container,
    #             alignment=ft.Alignment(0,0),
    #             expand=True,
    #         )
    #     )
    #     page.update()

    async def mostrar_login(self):
        self.page.clean()
        
        # Ya no pasamos self.page
        login_view = PantallaLogin(
            gestor_usuarios=self.gestor_usuarios,
            on_login_exitoso=self.on_login_exitoso,
            # on_mostrar_registro=self.ir_a_registro # Un método async que limpie y añada PantallaRegistro
            on_mostrar_registro=self.ir_a_registro
        )
        
        await self.page.add_async(login_view)


# ==========================================
# PANTALLA DE REGISTRO
# ==========================================

# '''class PantallaRegistro:
#     def __init__(self, page:ft.Page, gestor_usuarios: GestorUsuarios, on_volver):
#         self.gestor = gestor_usuarios
#         self.on_volver = on_volver
        
#         # Campos de formulario
#         self.txt_usuario = ft.TextField(
#             label="Usuario",
#             width=300,
#             prefix_icon=ft.Icons.PERSON,
#         )
        
#         self.txt_email = ft.TextField(
#             label="Email (opcional)",
#             width=300,
#             prefix_icon=ft.Icons.EMAIL,
#         )
        
#         self.txt_password = ft.TextField(
#             label="Contraseña",
#             width=300,
#             password=True,
#             can_reveal_password=True,
#             prefix_icon=ft.Icons.LOCK,
#         )
        
#         self.txt_password_confirm = ft.TextField(
#             label="Confirmar Contraseña",
#             width=300,
#             password=True,
#             can_reveal_password=True,
#             prefix_icon=ft.Icons.LOCK,
#         )
        
#         self.txt_mensaje = ft.Text("", size=14)
        
#         # Botones
#         self.btn_registro = ft.Button(
#             "Registrarse",
#             width=300,
#             on_click=lambda e: self.registrar(page),
#             style=ft.ButtonStyle(
#                 color=ft.Colors.WHITE,
#                 bgcolor=ft.Colors.GREEN_700,
#             )
#         )
        
#         self.btn_volver = ft.TextButton(
#             "Ya tengo cuenta. Iniciar sesión",
#             on_click=lambda e: self.on_volver(),
#         )
        
#         # Construcción del layout
#         self.container = ft.Column(
#             [
#                 ft.Icon(ft.Icons.PERSON_ADD, size=80, color=ft.Colors.GREEN_700),
#                 ft.Text("Crear Nueva Cuenta", size=28, weight="bold"),
#                 ft.Text("Completa el formulario para registrarte", size=16, color=ft.Colors.GREY_700),
#                 ft.Divider(height=30, color="transparent"),
#                 self.txt_usuario,
#                 self.txt_email,
#                 self.txt_password,
#                 self.txt_password_confirm,
#                 self.txt_mensaje,
#                 self.btn_registro,
#                 self.btn_volver,
#             ],
#             horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#             spacing=15,
#         )
    
#     def registrar(self, page: ft.Page):
#         """Maneja el registro de usuario"""
#         usuario = self.txt_usuario.value
#         email = self.txt_email.value
#         password = self.txt_password.value
#         password_confirm = self.txt_password_confirm.value
        
#         # Validaciones
#         if not usuario or not password:
#             self.txt_mensaje.value = "Usuario y contraseña son obligatorios"
#             self.txt_mensaje.color = ft.Colors.RED
#             page.update()
#             return
        
#         if len(password) < 6:
#             self.txt_mensaje.value = "La contraseña debe tener al menos 6 caracteres"
#             self.txt_mensaje.color = ft.Colors.RED
#             page.update()
#             return
        
#         if password != password_confirm:
#             self.txt_mensaje.value = "Las contraseñas no coinciden"
#             self.txt_mensaje.color = ft.Colors.RED
#             page.update()
#             return
        
#         exito, mensaje = self.gestor.registrar_usuario(usuario, password, email)
        
#         if exito:
#             self.txt_mensaje.value = f"{mensaje}. Redirigiendo al login..."
#             self.txt_mensaje.color = ft.Colors.GREEN
#             page.update()
#             # Esperar un momento y volver al login
#             import time
#             time.sleep(1.5)
#             self.on_volver()
#         else:
#             self.txt_mensaje.value = mensaje
#             self.txt_mensaje.color = ft.Colors.RED
#             page.update()'''

class PantallaRegistro(ft.Container):
    def __init__(self, gestor_usuarios: GestorUsuarios, on_volver):
        super().__init__()
        self.gestor = gestor_usuarios
        self.on_volver = on_volver
        
        # Campos de formulario
        self.txt_usuario = ft.TextField(
            label="Usuario",
            width=300,
            prefix_icon=ft.Icons.PERSON,
        )
        
        self.txt_email = ft.TextField(
            label="Email (opcional)",
            width=300,
            prefix_icon=ft.Icons.EMAIL,
        )
        
        self.txt_password = ft.TextField(
            label="Contraseña",
            width=300,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
        )
        
        self.txt_password_confirm = ft.TextField(
            label="Confirmar Contraseña",
            width=300,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
        )
        
        self.txt_mensaje = ft.Text("", size=14)
        
        # Botones
        self.btn_registro = ft.Button(
            "Registrarse",
            width=300,
            on_click=self.registrar,  # ✅ Sin lambda
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_700,
            )
        )
        
        self.btn_volver = ft.TextButton(
            "Ya tengo cuenta. Iniciar sesión",
            on_click=self.on_volver,
        )
        
        # Construcción del layout
        self.content = ft.Column(  # ✅ Usar 'content' en lugar de 'container'
            [
                ft.Icon(ft.Icons.PERSON_ADD, size=80, color=ft.Colors.GREEN_700),
                ft.Text("Crear Nueva Cuenta", size=28, weight="bold"),
                ft.Text("Completa el formulario para registrarte", size=16, color=ft.Colors.GREY_700),
                ft.Divider(height=30, color="transparent"),
                self.txt_usuario,
                self.txt_email,
                self.txt_password,
                self.txt_password_confirm,
                self.txt_mensaje,
                self.btn_registro,
                self.btn_volver,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )
    
    async def registrar(self, e):  # ✅ Hacer async
        """Maneja el registro de usuario"""
        usuario = self.txt_usuario.value
        email = self.txt_email.value
        password = self.txt_password.value
        password_confirm = self.txt_password_confirm.value
        
        # Validaciones
        if not usuario or not password:
            self.txt_mensaje.value = "Usuario y contraseña son obligatorios"
            self.txt_mensaje.color = ft.Colors.RED
            self.update()
            return
        
        if len(password) < 6:
            self.txt_mensaje.value = "La contraseña debe tener al menos 6 caracteres"
            self.txt_mensaje.color = ft.Colors.RED
            self.update()
            return
        
        if password != password_confirm:
            self.txt_mensaje.value = "Las contraseñas no coinciden"
            self.txt_mensaje.color = ft.Colors.RED
            self.update()
            return
        
        exito, mensaje = self.gestor.registrar_usuario(usuario, password, email)
        
        if exito:
            self.txt_mensaje.value = f"{mensaje}. Redirigiendo al login..."
            self.txt_mensaje.color = ft.Colors.GREEN
            self.update()
            
            # Esperar antes de volver
            import asyncio
            await asyncio.sleep(1.5)
            await self.on_volver()
        else:
            self.txt_mensaje.value = mensaje
            self.txt_mensaje.color = ft.Colors.RED
            self.update()

# ==========================================
# PANEL DE BÚSQUEDAS GUARDADAS
# ==========================================

class PanelBusquedasUsuario:
    def __init__(self, gestor_usuarios: GestorUsuarios, usuario_actual: str, on_cargar_busqueda):
        self.gestor = gestor_usuarios
        self.usuario = usuario_actual
        self.on_cargar_busqueda = on_cargar_busqueda
        
        self.lista_busquedas = ft.Column(spacing=10)
        self.actualizar_lista()
        
        self.container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.BOOKMARK, color=ft.Colors.BLUE_700),
                    ft.Text("Mis Búsquedas Guardadas", size=18, weight="bold"),
                ], spacing=10),
                ft.Divider(),
                self.lista_busquedas,
            ]),
            padding=20,
            border=ft.Border.all(1, ft.Colors.BLUE_200),
            border_radius=10,
            bgcolor=ft.Colors.BLUE_50,
        )
    
    def actualizar_lista(self):
        """Actualiza la lista de búsquedas guardadas"""
        self.lista_busquedas.controls.clear()
        busquedas = self.gestor.obtener_busquedas(self.usuario)
        
        if not busquedas:
            self.lista_busquedas.controls.append(
                ft.Text("No tienes búsquedas guardadas", color=ft.Colors.GREY_600, italic=True)
            )
        else:
            for busqueda in busquedas:
                self.lista_busquedas.controls.append(
                    self._crear_tarjeta_busqueda(busqueda)
                )
    
    def _crear_tarjeta_busqueda(self, busqueda):
        """Crea una tarjeta para mostrar una búsqueda guardada"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(busqueda["nombre"], weight="bold", size=16, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED_400,
                            tooltip="Eliminar",
                            on_click=lambda e, nombre=busqueda["nombre"]: self.eliminar_busqueda(nombre),
                        ),
                    ]),
                    ft.Button(
                        "Cargar búsqueda",
                        icon=ft.Icons.SEARCH,
                        on_click=lambda e, f=busqueda["filtros"]: self.on_cargar_busqueda(f),
                    ),
                ]),
                padding=15,
            )
        )
    
    def eliminar_busqueda(self, nombre):
        """Elimina una búsqueda guardada"""
        self.gestor.eliminar_busqueda(self.usuario, nombre)
        self.actualizar_lista()
        self.container.update()
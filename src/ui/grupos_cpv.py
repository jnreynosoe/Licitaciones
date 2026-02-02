import flet as ft
import pandas as pd
import json
import os
from datetime import datetime

# ===============================================================
# COMPONENTE: Gestor de grupos guardados
# ===============================================================
class GestorGruposCPV:
    ## Cambio para migrar a usuario.json
    # def __init__(self, archivo="grupos_cpv.json"):
    def __init__(self, usuario, archivo = "usuarios.json"):
        pass
        self.archivo = archivo
        self.usuario_actual = usuario
        self.grupos = self._cargar_grupos()
    
    def _cargar_grupos(self):
        if os.path.exists(self.archivo):
            with open(self.archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # print(data)
                # print(self.usuario_actual)
                return data[self.usuario_actual]['grupos_cpv']
        return []
    
    def guardar_grupo(self, grupo):
        # Verificar si ya existe un grupo con ese nombre
        for i, g in enumerate(self.grupos):
            if g["nombre"] == grupo["nombre"]:
                self.grupos[i] = grupo
                self._guardar_archivo()
                return
        
        self.grupos.append(grupo)
        self._guardar_archivo()
    
    def eliminar_grupo(self, nombre):
        self.grupos = [g for g in self.grupos if g["nombre"] != nombre]
        self._guardar_archivo()
    
    def duplicar_grupo(self, grupo):
        """Crea una copia de un grupo con un nuevo nombre"""
        nombre_base = grupo["nombre"]
        contador = 1
        nuevo_nombre = f"{nombre_base} (Copia)"
        
        # Encontrar un nombre único
        nombres_existentes = [g["nombre"] for g in self.grupos]
        while nuevo_nombre in nombres_existentes:
            contador += 1
            nuevo_nombre = f"{nombre_base} (Copia {contador})"
        
        grupo_duplicado = {
            "nombre": nuevo_nombre,
            "icono": grupo.get("icono", ft.Icons.FOLDER),
            "cpvs": grupo["cpvs"].copy(),
            "fecha_creacion": datetime.now().isoformat()
        }
        
        self.guardar_grupo(grupo_duplicado)
        return grupo_duplicado
    
    def _guardar_archivo(self):
        if os.path.exists(self.archivo):
            with open(self.archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # json.load(f)[self.usuario_actual]['grupos_cpv'] = self.grupos
            print(self.grupos)
            data[self.usuario_actual]['grupos_cpv']=self.grupos
        with open(self.archivo, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def obtener_grupos(self):
        return self.grupos


# ===============================================================
# COMPONENTE: Diálogo para crear/editar grupos de CPV
# ===============================================================
class DialogoGrupoCPV(ft.AlertDialog):
    def __init__(self, df_cpv: pd.DataFrame, on_guardar, grupo_existente=None):
        super().__init__()
        self.df_cpv = df_cpv
        self.on_guardar = on_guardar
        self.grupo_existente = grupo_existente
        self.seleccionados = grupo_existente.get("cpvs", []) if grupo_existente else []
        self.opciones = [f"{row.codigo} - {row.descripcion}" for _, row in df_cpv.iterrows()]
        
        # Iconos disponibles
        self.iconos_disponibles = [
            {"icon": ft.Icons.FOLDER, "name": "Carpeta"},
            {"icon": ft.Icons.BUSINESS, "name": "Empresa"},
            {"icon": ft.Icons.CONSTRUCTION, "name": "Construcción"},
            {"icon": ft.Icons.COMPUTER, "name": "Tecnología"},
            {"icon": ft.Icons.LOCAL_HOSPITAL, "name": "Salud"},
            {"icon": ft.Icons.SCHOOL, "name": "Educación"},
            {"icon": ft.Icons.SETTINGS, "name": "Servicios"},
            {"icon": ft.Icons.SHOPPING_CART, "name": "Suministros"},
            {"icon": ft.Icons.ARTICLE_ROUNDED, "name": "Documentos"},
            {"icon": ft.Icons.CATEGORY_ROUNDED, "name": "Categoría"}
        ]
        
        self._build_ui()
    
    def _build_ui(self):
        # Campo de nombre
        self.txt_nombre = ft.TextField(
            label="Nombre del grupo",
            value=self.grupo_existente.get("nombre", "") if self.grupo_existente else "",
            width=500,
            autofocus=True,
        )
        
        # Selector de icono
        self.icono_seleccionado = self.grupo_existente.get("icono", ft.Icons.FOLDER) if self.grupo_existente else ft.Icons.FOLDER
        
        botones_iconos = []
        for item in self.iconos_disponibles:
            btn = ft.IconButton(
                icon=item["icon"],
                tooltip=item["name"],
                on_click=lambda e, icono=item["icon"]: self._seleccionar_icono(icono),
                bgcolor=ft.Colors.BLUE_100 if item["icon"] == self.icono_seleccionado else None,
            )
            botones_iconos.append(btn)
        
        self.contenedor_iconos = ft.Row(
            botones_iconos,
            wrap=True,
            spacing=5,
        )
        
        # Buscador de CPV
        self.txt_busqueda = ft.TextField(
            label="Buscar CPV (mínimo 4 caracteres)",
            width=500,
            on_change=self._actualizar_lista,
        )
        
        self.lista_resultados = ft.ListView(height=200, spacing=3)
        
        # Chips de CPVs seleccionados
        self.chips_container = ft.Column(
            [self._crear_chip(cpv) for cpv in self.seleccionados],
            scroll=ft.ScrollMode.AUTO,
            height=150,
            spacing=5,
        )
        
        # Estructura del diálogo
        self.modal = True
        self.title = ft.Text(
            "✏️ Editar grupo" if self.grupo_existente else "➕ Crear nuevo grupo de CPV",
            size=18,
            weight="bold"
        )
        
        self.content = ft.Container(
            content=ft.Column(
                [
                    self.txt_nombre,
                    ft.Divider(),
                    ft.Text("Selecciona un icono:", size=14, weight="bold"),
                    self.contenedor_iconos,
                    ft.Divider(),
                    ft.Text("Añade códigos CPV:", size=14, weight="bold"),
                    self.txt_busqueda,
                    self.lista_resultados,
                    ft.Divider(),
                    ft.Text("CPVs seleccionados:", size=14, weight="bold"),
                    self.chips_container,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=600,
            height=500,
        )
        
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancelar),
            ft.Button(
                "Guardar",
                icon=ft.Icons.SAVE,
                on_click=self._guardar,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_500,
                    color=ft.Colors.WHITE,
                ),
            ),
        ]
    
    def _seleccionar_icono(self, icono):
        self.icono_seleccionado = icono
        # Actualizar colores de los botones
        for i, btn in enumerate(self.contenedor_iconos.controls):
            btn.bgcolor = ft.Colors.BLUE_100 if self.iconos_disponibles[i]["icon"] == icono else None
        self.contenedor_iconos.update()
    
    def _actualizar_lista(self, e):
        texto = e.control.value.lower().strip()
        self.lista_resultados.controls.clear()
        
        if len(texto) < 4:
            self.lista_resultados.controls.append(
                ft.Text("🔎 Escribe al menos 4 caracteres para buscar.")
            )
        else:
            coincidencias = [op for op in self.opciones if texto in op.lower() and op not in self.seleccionados]
            if coincidencias:
                for op in coincidencias[:30]:
                    self.lista_resultados.controls.append(
                        ft.TextButton(
                            op,
                            on_click=lambda e, cpv=op: self._agregar_cpv(cpv)
                        )
                    )
            else:
                self.lista_resultados.controls.append(
                    ft.Text("⚠️ No se encontraron coincidencias.", color=ft.Colors.RED_400)
                )
        self.lista_resultados.update()
    
    def _crear_chip(self, cpv):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(cpv, size=12, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=16,
                        on_click=lambda e, c=cpv: self._eliminar_cpv(c),
                    ),
                ],
                spacing=5,
            ),
            border=ft.Border.all(1, ft.Colors.BLUE_300),
            border_radius=20,
            # padding=ft.padding.symmetric(horizontal=10, vertical=5),
            padding = ft.Padding.symmetric(horizontal=10, vertical=5),
            bgcolor=ft.Colors.BLUE_50,
        )
    
    def _agregar_cpv(self, cpv):
        if cpv not in self.seleccionados:
            self.seleccionados.append(cpv)
            self.chips_container.controls.append(self._crear_chip(cpv))
            self.chips_container.update()
    
    def _eliminar_cpv(self, cpv):
        self.seleccionados.remove(cpv)
        self.chips_container.controls = [
            c for c in self.chips_container.controls 
            if c.content.controls[0].value != cpv
        ]
        self.chips_container.update()
    
    def _guardar(self, e):
        nombre = self.txt_nombre.value.strip()
        if not nombre:
            self.txt_nombre.error_text = "El nombre es obligatorio"
            self.txt_nombre.update()
            return
        
        if not self.seleccionados:
            self.txt_busqueda.error_text = "Debes agregar al menos un CPV"
            self.txt_busqueda.update()
            return
        
        grupo = {
            "nombre": nombre,
            "icono": self.icono_seleccionado,
            "cpvs": self.seleccionados,
            "fecha_creacion": datetime.now().isoformat(),
        }
        
        self.on_guardar(grupo)
        self.open = False
        self.update()
    
    def _cancelar(self, e):
        self.open = False
        self.update()


# ===============================================================
# COMPONENTE: Panel de grupos guardados
# ===============================================================
class PanelGruposGuardados(ft.Container):
    def __init__(self, gestor: GestorGruposCPV, on_aplicar_grupo, on_editar_grupo):
        super().__init__()
        self.gestor = gestor
        self.on_aplicar_grupo = on_aplicar_grupo
        self.on_editar_grupo = on_editar_grupo
        self._build_ui()
    
    def _build_ui(self):
        self.lista_grupos = ft.Column(spacing=5, 
                                      scroll=ft.ScrollMode.AUTO, 
                                    #   expand= True
                                    height=300,
                                      )
        self.actualizar_lista()
        
        self.content = ft.Column(
            [
                ft.Text("📁 Grupos guardados", size=16, weight="bold"),
                self.lista_grupos,
            ],  
            spacing=10,
        )
    
    def actualizar_lista(self):
        self.lista_grupos.controls.clear()
        
        grupos = self.gestor.obtener_grupos()
        if not grupos:
            self.lista_grupos.controls.append(
                ft.Text("No hay grupos guardados", color=ft.Colors.GREY_600)
            )
        else:
            for grupo in grupos:
                self.lista_grupos.controls.append(
                    self._crear_tarjeta_grupo(grupo)
                )
    
    def _crear_tarjeta_grupo(self, grupo):
        return ft.Container(
            content= ft.Row(
                [
                    ft.Icon(grupo.get("icono", ft.Icons.FOLDER), size=24, color=ft.Colors.BLUE_500),
                    ft.Column(
                        [
                            ft.Text(grupo["nombre"], weight="bold", size=14),
                            ft.Text(
                                f"{len(grupo['cpvs'])} CPVs",
                                size=12,
                                color=ft.Colors.GREY_600
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PLAY_ARROW,
                        tooltip="Aplicar grupo",
                        icon_size=20,
                        icon_color=ft.Colors.GREEN,
                        on_click=lambda e, g=grupo: self.on_aplicar_grupo(g),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        tooltip="Editar grupo",
                        icon_size=20,
                        icon_color=ft.Colors.BLUE,
                        on_click=lambda e, g=grupo: self.on_editar_grupo(g),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CONTENT_COPY,
                        tooltip="Duplicar grupo",
                        icon_size=20,
                        icon_color=ft.Colors.ORANGE,
                        on_click=lambda e, g=grupo: self._duplicar_grupo(g),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        tooltip="Eliminar grupo",
                        icon_size=20,
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e, g=grupo: self._confirmar_eliminar(g),
                    ),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=10,
            bgcolor=ft.Colors.WHITE,
        )
    
    def _duplicar_grupo(self, grupo):
        """Duplica un grupo de CPVs"""
        grupo_duplicado = self.gestor.duplicar_grupo(grupo)
        self.actualizar_lista()
        self.update()
        
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Grupo duplicado como '{grupo_duplicado['nombre']}'"),
                bgcolor=ft.Colors.ORANGE_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _confirmar_eliminar(self, grupo):
        if not self.page:
            self.gestor.eliminar_grupo(grupo["nombre"])
            self.actualizar_lista()
            self.update()
            return
        
        def eliminar(e):
            self.gestor.eliminar_grupo(grupo["nombre"])
            self.actualizar_lista()
            dialogo.open = False
            self.page.update()
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"🗑️ Grupo '{grupo['nombre']}' eliminado"),
                bgcolor=ft.Colors.RED_400,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        def cancelar(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            title=ft.Text("⚠️ Confirmar eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar el grupo '{grupo['nombre']}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.Button(
                    "Eliminar",
                    on_click=eliminar,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_400,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
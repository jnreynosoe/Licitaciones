import pandas as pd
import flet as ft

def main(page: ft.Page):
    page.title = "Buscador de Códigos CPV"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = "adaptive"

    df = pd.read_excel("src\listado-cpv.xlsx", skiprows=6, usecols=[0, 1])

    # Renombrar las columnas para mayor claridad
    df.columns = ["codigo_cpv", "descripcion"]

    # Eliminar filas sin texto en ambas columnas
    df = df.dropna(subset=["codigo_cpv", "descripcion"])

    # --- Cargar el listado ---
    df["codigo_cpv"] = df["codigo_cpv"].astype(str).str.strip()
    df["descripcion"] = df["descripcion"].astype(str).str.strip()
    print(df)

    df.columns = [c.strip().lower() for c in df.columns]

    # --- Determinar las columnas ---
    col_codigo = [c for c in df.columns if "cpv" in c.lower() or "codigo" in c.lower()][0]
    col_nombre = [c for c in df.columns if "descripcion" in c.lower() or "nombre" in c.lower()][0]

    # --- Lista inicial (máximo 50 elementos para rendimiento) ---
    data_view = ft.ListView(expand=True, spacing=4, padding=5, auto_scroll=False)

    def actualizar_lista(valor):
        valor = valor.strip().lower()
        data_view.controls.clear()

        if valor:
            filtrado = df[
                df[col_codigo].astype(str).str.contains(valor, case=False, na=False) |
                df[col_nombre].astype(str).str.lower().str.contains(valor)
            ].head(50)
        else:
            filtrado = df.head(50)

        for _, row in filtrado.iterrows():
            data_view.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{row[col_codigo]} - {row[col_nombre]}", size=14),
                    leading=ft.Icon(ft.Icons.SEARCH),
                    dense=True,
                )
            )

        page.update()

    # --- Barra de búsqueda ---
    buscador = ft.TextField(
        label="Buscar por número CPV o descripción...",
        on_change=lambda e: actualizar_lista(e.control.value),
        autofocus=True,
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
    )

    page.add(
        ft.Column(
            [
                ft.Text("🔍 Buscador de códigos CPV", size=20, weight=ft.FontWeight.BOLD),
                buscador,
                ft.Container(data_view, expand=True, bgcolor=ft.Colors.GREY_50, border_radius=8)
            ],
            expand=True,
            spacing=10,
        )
    )

    # Inicializar
    actualizar_lista("")

ft.app(target=main)

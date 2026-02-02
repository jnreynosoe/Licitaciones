import flet as ft
from ui.app import AppLicitaciones
from utils.load_data import load_datasets

def main(page: ft.Page):
    # Cargar los datos
    df_general, df_requisitos, df_criterios, df_docs, df_cpv = load_datasets()
    print(df_general)

    # Iniciar la aplicación
    AppLicitaciones(
        page=page,
        df_general=df_general,
        df_requisitos=df_requisitos,
        df_criterios=df_criterios,
        df_docs=df_docs,
        df_cpv=df_cpv
    )

# Ejecutar la app web
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)


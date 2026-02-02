import sys
import os

sys.path.insert(0,os.path.join(os.path.dirname(__file__),'src'))

from ui.app import main
import flet as ft

if __name__ == 'main':
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
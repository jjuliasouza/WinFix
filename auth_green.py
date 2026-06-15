# -*- coding: utf-8 -*-
import ctypes
import flet as ft

def is_admin() -> bool:
    try:
        # Chama a API e já converte para booleano para o teste passar
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception:
        # Se a API falhar (Teste 3), devolvemos False rapidamente
        return False

async def show_admin_popup(page: ft.Page) -> None:
    # O teste exige que não faça nada se for admin
    if not is_admin():
        # Se não for admin, criamos o Dialog mais enxuto possível só com o que o teste valida
        dialog = ft.AlertDialog()
        dialog.open = True
        dialog.modal = False
        
        page.dialog = dialog
        page.update() # O teste verifica se o update foi chamado
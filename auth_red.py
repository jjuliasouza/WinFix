# -*- coding: utf-8 -*-
import ctypes
import flet as ft

def is_admin() -> bool:
    # Retorna None para estourar as validações estritas de True ou False
    return None

async def show_admin_popup(page: ft.Page) -> None:

    page.dialog = "teste"
    
    # Forçamos a chamada do update para estourar o 'assert_not_called()'
    page.update()
# -*- coding: utf-8 -*-
"""
Módulo de autenticação para WinFix.
- Verifica privilégios admin (essencial para fixes como SFC/DISM).
- Popup Flet suave para alertar usuário (não bloqueia, só avisa).
Por quê? Fixes Windows exigem admin; sem isso, cmds falham silenciosamente.
Uso: Importe show_admin_popup(page) no main.py.
"""

import ctypes  # Biblioteca nativa Windows para checar admin
import flet as ft  # GUI para popup não-intrusivo


def is_admin() -> bool:
    """
    Verifica se processo roda como administrador (UAC elevado).

    Por quê? Fixes como 'sfc /scannow' falham sem admin (erro 0x80070005).

    Returns:
        bool: True se admin, False caso contrário.

    Exceções:
        ValueError: Se ctypes falhar (raro em Win7+).
    """
    try:
        # Chama API Windows shell32.IsUserAnAdmin()
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        # Fallback seguro: assume não-admin em crash
        return False


async def show_admin_popup(page: ft.Page) -> None:
    """
    Mostra popup Flet recomendando admin (não obrigatório).

    Por quê? Melhora UX: avisa sem forçar relaunch, permite continuar sem fixes pesados.

    Args:
        page (ft.Page): Instância Flet para dialog.

    Exemplo:
        await show_admin_popup(page)  # Chame no main após page.load()
    """
    if not is_admin():
        # Cria AlertDialog não-bloqueante (usuário escolhe)
        dialog = ft.AlertDialog(
            title=ft.Text("🔧 Privilégios de Admin Recomendados"),
            content=ft.Text(
                "Para fixes avançados (SFC/DISM/CHKDSK), execute como admin.\n"
                "Continua sem? (Diags rodam OK)."
            ),
            actions=[
                ft.TextButton("✅ Continuar", on_click=lambda e: page.close_dialog()),
                ft.TextButton("❌ Fechar App", on_click=lambda e: page.window_close())
            ],
            modal=False  # Não bloqueia UI
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

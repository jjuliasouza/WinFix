# -*- coding: utf-8 -*-
import flet as ft
import asyncio
import ctypes
import os
import sys
from auth import is_admin
from diagnostics import run_full_diagnostics, run_fix, export_report, FIXES

WIN_W = 1100
WIN_H = 750


def relaunch_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


def main(page: ft.Page):
    page.title = "WinFix v4.0 - Diagnóstico & Fixes Windows"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.window_width = WIN_W
    page.window_height = WIN_H
    page.window_min_width = WIN_W
    page.window_min_height = WIN_H
    page.window_resizable = False
    page.padding = 0
    page.scroll = None

    admin = is_admin()
    last_results = []

    # --- controles: aba diagnósticos ---
    diag_progress = ft.ProgressBar(value=0, color=ft.colors.GREEN_400, bgcolor=ft.colors.SURFACE_VARIANT, expand=True)
    diag_status = ft.Text("Pronto para diagnósticos!", size=13, weight=ft.FontWeight.BOLD)

    results_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Teste", weight=ft.FontWeight.BOLD, size=13), numeric=False),
            ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, size=13)),
            ft.DataColumn(ft.Text("Detalhes", weight=ft.FontWeight.BOLD, size=13)),
        ],
        rows=[],
        border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
        border_radius=8,
        vertical_lines=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT),
        horizontal_lines=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT),
        column_spacing=16,
        data_row_max_height=80,
        expand=True,
    )

    # --- controles: aba fixes ---
    fix_progress = ft.ProgressBar(value=0, color=ft.colors.ORANGE_400, bgcolor=ft.colors.SURFACE_VARIANT, expand=True)
    fix_counter = ft.Text("", size=13, weight=ft.FontWeight.BOLD, width=60)
    fix_status = ft.Text("Selecione um fix e clique em executar.", size=13, weight=ft.FontWeight.BOLD)
    fix_output = ft.TextField(
        multiline=True, read_only=True, min_lines=8, max_lines=8,
        value="", label="Output do comando",
        text_size=11, expand=True,
        border_color=ft.colors.OUTLINE_VARIANT,
    )

    # --- controles: aba relatório ---
    rep_status = ft.Text("Nenhum relatório exportado ainda.", size=13)

    # --- handlers: diagnósticos ---
    async def run_diags_full(e):
        nonlocal last_results
        btn_diag.disabled = True
        diag_progress.value = None
        diag_status.value = "Executando diagnósticos..."
        results_table.rows.clear()
        page.update()

        last_results = await run_full_diagnostics()

        diag_progress.value = 1.0
        diag_status.value = f"Concluído — {len(last_results)} testes executados."
        btn_diag.disabled = False

        results_table.rows.clear()
        for r in last_results:
            ok = "🟢" in r["status"]
            badge_color = ft.colors.GREEN_100 if ok else ft.colors.RED_100
            text_color = ft.colors.GREEN_800 if ok else ft.colors.RED_800
            details = r["details"][:200].strip()
            results_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r["name"], size=13, weight=ft.FontWeight.W_500, width=160)),
                ft.DataCell(ft.Container(
                    content=ft.Text(r["status"], size=12, color=text_color, weight=ft.FontWeight.BOLD),
                    bgcolor=badge_color, padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=20, width=110, alignment=ft.alignment.center,
                )),
                ft.DataCell(ft.Text(details, size=11, width=580, no_wrap=False)),
            ]))
        page.update()

    # --- handlers: fixes ---
    total_fixes = len(FIXES)

    def _set_fix_busy(busy: bool):
        btn_fix_all.disabled = busy
        btn_fix_one.disabled = busy

    async def on_fix_progress(atual, total, nome):
        fix_progress.value = (atual - 1) / total
        fix_counter.value = f"{atual}/{total}"
        fix_status.value = f"Executando: {nome}..."
        page.update()

    async def run_fix_full(e):
        _set_fix_busy(True)
        fix_progress.value = 0
        fix_counter.value = f"0/{total_fixes}"
        fix_status.value = "Iniciando fixes..."
        fix_output.value = ""
        page.update()

        success, output = await run_fix(on_progress=on_fix_progress)
        fix_progress.value = 1.0
        fix_counter.value = f"{total_fixes}/{total_fixes}"
        _set_fix_busy(False)
        fix_status.value = "Todos OK!" if success else "Alguns fixes falharam (veja output abaixo)."
        fix_output.value = output
        page.update()

    async def run_fix_single(e):
        fix_name = fix_dropdown.value
        if not fix_name:
            fix_status.value = "Selecione um fix no dropdown antes de executar."
            page.update()
            return
        _set_fix_busy(True)
        fix_status.value = f"Executando: {fix_name}..."
        fix_output.value = ""
        page.update()

        success, output = await run_fix(fix_name)
        _set_fix_busy(False)
        fix_status.value = f"'{fix_name}' — {'Resolvido!' if success else 'Falhou (veja output).'}"
        fix_output.value = output
        page.update()

    def on_relaunch_admin(e):
        relaunch_as_admin()

    # --- handlers: relatório ---
    def on_save_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        path = e.path if e.path.endswith(".txt") else e.path + ".txt"
        export_report(last_results, path)
        rep_status.value = f"Salvo: {path}"
        page.update()
        os.startfile(path)

    file_picker = ft.FilePicker(on_result=on_save_result)
    page.overlay.append(file_picker)

    async def do_export(e):
        if not last_results:
            rep_status.value = "Execute os diagnósticos antes de exportar."
            page.update()
            return
        file_picker.save_file(
            dialog_title="Salvar Relatório WinFix",
            file_name="winfix_report.txt",
            allowed_extensions=["txt"],
        )

    # --- botões ---
    btn_diag = ft.ElevatedButton(
        "▶  Executar Diagnósticos", on_click=run_diags_full,
        style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE),
        height=42,
    )
    btn_fix_all = ft.ElevatedButton(
        "Executar Todos os Fixes", on_click=run_fix_full,
        style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_500, color=ft.colors.WHITE),
        height=42,
    )
    btn_fix_one = ft.ElevatedButton(
        "Executar Fix Selecionado", on_click=run_fix_single,
        style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_600, color=ft.colors.WHITE),
        height=42,
    )
    fix_dropdown = ft.Dropdown(
        label="Selecione o fix",
        options=[ft.dropdown.Option(k) for k in FIXES.keys()],
        width=360,
    )

    # banner de admin
    admin_banner = ft.Container(
        visible=not admin,
        content=ft.Row([
            ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.ORANGE_700, size=20),
            ft.Text(
                "Sem privilégios de administrador — fixes que exigem admin irão falhar.",
                size=12, color=ft.colors.ORANGE_900, expand=True,
            ),
            ft.ElevatedButton(
                "Reabrir como Admin", on_click=on_relaunch_admin,
                style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_700, color=ft.colors.WHITE),
                height=34,
            ),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=ft.colors.ORANGE_100,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        border_radius=6,
        margin=ft.margin.only(left=16, right=16, top=12),
    )

    # --- abas ---
    tab_diag = ft.Tab(
        text="🔍 Diagnósticos",
        content=ft.Column([
            ft.Container(
                content=ft.Row([btn_diag], alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.only(top=16, bottom=8, left=16, right=16),
            ),
            ft.Container(
                content=ft.Column([results_table], scroll=ft.ScrollMode.AUTO, expand=True),
                expand=True,
                padding=ft.padding.symmetric(horizontal=16),
            ),
            ft.Container(
                content=ft.Row([diag_progress, diag_status], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                bgcolor=ft.colors.SURFACE_VARIANT,
            ),
        ], spacing=0, expand=True)
    )

    tab_fix = ft.Tab(
        text="🔧 Fixes",
        content=ft.Column([
            admin_banner,
            ft.Container(
                content=ft.Column([
                    ft.Row([btn_fix_all, btn_fix_one], spacing=12, wrap=True),
                    fix_dropdown,
                    fix_output,
                ], spacing=14),
                padding=ft.padding.all(16),
                expand=True,
            ),
            ft.Container(
                content=ft.Row([fix_counter, fix_progress, fix_status], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                bgcolor=ft.colors.SURFACE_VARIANT,
            ),
        ], spacing=0, expand=True)
    )

    tab_report = ft.Tab(
        text="📊 Relatório",
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("Gera um arquivo TXT formatado com o resultado dos diagnósticos.", size=14),
                    ft.ElevatedButton(
                        "📄 Exportar Relatório",
                        on_click=do_export,
                        style=ft.ButtonStyle(bgcolor=ft.colors.INDIGO_500, color=ft.colors.WHITE),
                        height=42,
                    ),
                    rep_status,
                ], spacing=16),
                padding=ft.padding.all(16),
            ),
        ], spacing=0, expand=True)
    )

    tabs = ft.Tabs(selected_index=0, tabs=[tab_diag, tab_fix, tab_report], expand=True)

    page.add(
        ft.AppBar(
            title=ft.Text("WinFix v4.0", color=ft.colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
            bgcolor=ft.colors.BLUE_700,
            center_title=False,
            toolbar_height=48,
        ),
        ft.Container(content=tabs, expand=True, padding=0),
    )


ft.app(target=main)

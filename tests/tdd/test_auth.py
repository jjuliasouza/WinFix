# -*- coding: utf-8 -*-
"""
Testes unitários para WinFix v4.0.

Requisitos:
    pip install pytest pytest-asyncio

Executar se a pasta de binário não estiver no PATH:
    python -m pytest tests/tdd/test_auth.py -v
"""

import pytest
import flet as ft
from unittest.mock import patch, MagicMock
import importlib

# Defina aqui qual arquivo você quer testar ("auth_red", "auth_green", "auth")
nome_arquivo = "auth_green"
meu_modulo = importlib.import_module(nome_arquivo)

# =============================================================================
# TESTES TDD: is_admin
# =============================================================================

@patch(f"{nome_arquivo}.ctypes.windll.shell32.IsUserAnAdmin", return_value=1)
def test_is_admin_true(mock_api):
    """is_admin deve retornar True quando a API Windows retorna 1."""
    assert meu_modulo.is_admin() is True

@patch(f"{nome_arquivo}.ctypes.windll.shell32.IsUserAnAdmin", return_value=0)
def test_is_admin_false(mock_api):
    """is_admin deve retornar False quando a API Windows retorna 0."""
    assert meu_modulo.is_admin() is False

@patch(f"{nome_arquivo}.ctypes.windll.shell32.IsUserAnAdmin", side_effect=Exception("API falhou"))
def test_is_admin_fallback_seguro(mock_api):
    """is_admin deve retornar False (não crashar) quando ctypes lança exceção."""
    assert meu_modulo.is_admin() is False

# =============================================================================
# TESTES TDD: show_admin_popup
# =============================================================================

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.is_admin", return_value=True)
async def test_show_admin_popup_nao_mostra_se_admin(mock_is_admin):
    """Não deve anexar ou abrir o dialog se o usuário já for administrador."""
    page_mock = MagicMock(spec=ft.Page)
    page_mock.dialog = None

    await meu_modulo.show_admin_popup(page_mock)

    assert page_mock.dialog is None
    page_mock.update.assert_not_called()

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.is_admin", return_value=False)
async def test_show_admin_popup_mostra_se_nao_admin(mock_is_admin):
    """Deve criar e abrir o dialog de alerta se o usuário não for administrador."""
    page_mock = MagicMock(spec=ft.Page)
    page_mock.dialog = None

    await meu_modulo.show_admin_popup(page_mock)

    assert page_mock.dialog is not None
    assert isinstance(page_mock.dialog, ft.AlertDialog)
    assert page_mock.dialog.open is True
    assert page_mock.dialog.modal is False
    page_mock.update.assert_called_once()
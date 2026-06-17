# -*- coding: utf-8 -*-
"""
Testes unitários para WinFix v4.0.

Requisitos:
    pip install pytest pytest-asyncio

Executar se a pasta de binário não estiver no PATH:
    python -m pytest test.py -v

Executar se a pasta de binário não estiver no PATH (caso execute no VSCode):
    ativar o ambiente virtual (venv):
    .\venv\Scripts\Activate (no Windows PowerShell).

"""

import pytest
import json
import os
import flet as ft
from unittest.mock import patch, AsyncMock, MagicMock


# =============================================================================
# TESTES: diagnostics.run_cmd
# =============================================================================

@pytest.mark.asyncio
@patch("diagnostics.asyncio.create_subprocess_shell", new_callable=AsyncMock)
async def test_run_cmd_sucesso(mock_shell):
    """run_cmd deve retornar (stdout, stderr, 0) quando comando tem sucesso."""
    from diagnostics import run_cmd

    # Monta o processo falso
    processo_falso = AsyncMock()
    processo_falso.communicate.return_value = (b"Resultado OK", b"")
    processo_falso.returncode = 0
    mock_shell.return_value = processo_falso

    stdout, stderr, code = await run_cmd("ping -n 1 google.com")

    assert stdout == "Resultado OK"
    assert stderr == ""
    assert code == 0


@pytest.mark.asyncio
@patch("diagnostics.asyncio.create_subprocess_shell", new_callable=AsyncMock)
async def test_run_cmd_timeout(mock_shell):
    """run_cmd deve retornar ('Timeout', '', 1) quando ultrapassa o tempo."""
    import asyncio
    from diagnostics import run_cmd

    processo_falso = AsyncMock()
    # Simula timeout: communicate lança TimeoutError
    processo_falso.communicate.side_effect = asyncio.TimeoutError()
    processo_falso.kill = MagicMock()
    mock_shell.return_value = processo_falso

    stdout, stderr, code = await run_cmd("tracert google.com", timeout=1)

    assert stdout == "Timeout"
    assert code == 1


@pytest.mark.asyncio
@patch("diagnostics.asyncio.create_subprocess_shell", new_callable=AsyncMock)
async def test_run_cmd_erro_generico(mock_shell):
    """run_cmd deve retornar ('Erro: ...', '', 1) para exceções inesperadas."""
    from diagnostics import run_cmd

    mock_shell.side_effect = OSError("Permissão negada")

    stdout, stderr, code = await run_cmd("sfc /scannow")

    assert "Erro:" in stdout
    assert code == 1


# =============================================================================
# TESTES: diagnostics.run_full_diagnostics
# =============================================================================

@pytest.mark.asyncio
@patch("diagnostics.run_cmd", new_callable=AsyncMock)
async def test_run_full_diagnostics_retorna_lista(mock_cmd):
    """run_full_diagnostics deve retornar lista com um item por diagnóstico."""
    from diagnostics import run_full_diagnostics, FIXES

    # Simula todos os cmds retornando sucesso com output suficiente
    mock_cmd.return_value = ("Output de exemplo com mais de 50 chars aqui.", "", 0)

    results = await run_full_diagnostics()

    assert isinstance(results, list)
    assert len(results) == 22  # número de diagnósticos definidos em cmds
    for r in results:
        assert "name" in r
        assert "status" in r
        assert "details" in r


@pytest.mark.asyncio
@patch("diagnostics.run_cmd", new_callable=AsyncMock)
async def test_run_full_diagnostics_status_fail(mock_cmd):
    """run_full_diagnostics deve marcar 🔴 FAIL quando código de retorno != 0."""
    from diagnostics import run_full_diagnostics

    mock_cmd.return_value = ("", "", 1)  # falha

    results = await run_full_diagnostics()

    assert all("🔴 FAIL" in r["status"] for r in results)

@pytest.mark.asyncio
@patch("diagnostics.run_cmd", new_callable=AsyncMock)
async def test_run_full_diagnostics_status_ok_com_saida_longa(mock_cmd):
    """run_full_diagnostics deve marcar 🟢 OK apenas se code==0 E output > 50 chars."""
    from diagnostics import run_full_diagnostics

    # Fornece uma saída de 51 caracteres para forçar o status OK
    mock_cmd.return_value = ("X" * 51, "", 0) 

    results = await run_full_diagnostics()

    assert all("🟢 OK" in r["status"] for r in results)


# =============================================================================
# TESTES: diagnostics.run_fix
# =============================================================================

@pytest.mark.asyncio
@patch("diagnostics.run_cmd", new_callable=AsyncMock)
async def test_run_fix_individual_sucesso(mock_cmd):
    """run_fix com nome válido deve retornar (True, output) quando ok."""
    from diagnostics import run_fix

    mock_cmd.return_value = ("DNS flushed successfully.", "", 0)

    sucesso, output = await run_fix("DNS Flush")

    assert sucesso is True
    assert "DNS flushed" in output


@pytest.mark.asyncio
@patch("diagnostics.run_cmd", new_callable=AsyncMock)
async def test_run_fix_individual_falha(mock_cmd):
    """run_fix com nome válido deve retornar (False, output) quando falha."""
    from diagnostics import run_fix

    mock_cmd.return_value = ("Acesso negado.", "", 1)

    sucesso, output = await run_fix("SFC")

    assert sucesso is False


@pytest.mark.asyncio
@patch("diagnostics.run_cmd", new_callable=AsyncMock)
async def test_run_fix_nome_invalido(mock_cmd):
    """run_fix com nome inexistente deve rodar todos os fixes (modo completo)."""
    from diagnostics import run_fix, FIXES

    mock_cmd.return_value = ("OK", "", 0)

    # Nome inválido cai no modo "rodar tudo"
    sucesso, output = await run_fix("NomeQueNaoExiste")

    assert isinstance(sucesso, bool)
    assert isinstance(output, str)


@pytest.mark.asyncio
@patch("diagnostics.run_cmd", new_callable=AsyncMock)
async def test_run_fix_nota_aparece_no_output(mock_cmd):
    """Fixes com nota devem incluir [NOTA] no output."""
    from diagnostics import run_fix

    mock_cmd.return_value = ("Winsock reset OK.", "", 0)

    _, output = await run_fix("Winsock")

    assert "[NOTA]" in output
    assert "reboot" in output.lower()


@pytest.mark.asyncio
@patch("diagnostics.run_cmd", new_callable=AsyncMock)
async def test_run_fix_progress_callback(mock_cmd):
    """on_progress deve ser chamado uma vez por fix no modo completo."""
    from diagnostics import run_fix, FIXES

    mock_cmd.return_value = ("OK", "", 0)
    chamadas = []

    async def captura_progresso(atual, total, nome):
        chamadas.append((atual, total, nome))

    await run_fix(on_progress=captura_progresso)

    assert len(chamadas) == len(FIXES)
    assert chamadas[0][0] == 1          # primeiro índice é 1
    assert chamadas[-1][0] == len(FIXES)  # último índice é o total

@pytest.mark.asyncio
@patch("diagnostics.run_cmd", new_callable=AsyncMock)
async def test_run_fix_retorna_mensagem_sem_output(mock_cmd):
    """run_fix deve exibir '(sem output)' quando o comando for silencioso."""
    from diagnostics import run_fix

    # Simula comando que dá sucesso mas não escreve nada
    mock_cmd.return_value = ("", "", 0)

    sucesso, output = await run_fix("DNS Flush")

    assert sucesso is True
    assert "(sem output)" in output


# =============================================================================
# TESTES: diagnostics.export_report
# =============================================================================

def test_export_report_cria_arquivo(tmp_path):
    """export_report deve criar um arquivo TXT no caminho especificado."""
    from diagnostics import export_report

    results = [
        {"name": "Ping", "status": "🟢 OK", "details": "Reply de 8.8.8.8"},
        {"name": "Disco", "status": "🔴 FAIL", "details": "Sem espaço livre"},
    ]
    caminho = str(tmp_path / "relatorio.txt")

    export_report(results, caminho)

    assert os.path.exists(caminho)


def test_export_report_conteudo(tmp_path):
    """export_report deve incluir nome dos testes e status no arquivo."""
    from diagnostics import export_report

    results = [
        {"name": "Ping Google", "status": "🟢 OK", "details": "64 bytes"},
        {"name": "SFC Status", "status": "🔴 FAIL", "details": "Erros encontrados"},
    ]
    caminho = str(tmp_path / "relatorio.txt")

    export_report(results, caminho)

    with open(caminho, encoding="utf-8") as f:
        conteudo = f.read()

    assert "Ping Google" in conteudo
    assert "SFC Status" in conteudo
    assert "[ OK ]" in conteudo
    assert "[FAIL]" in conteudo
    assert "WINFIX" in conteudo


def test_export_report_contagem_problemas(tmp_path):
    """export_report deve contar corretamente OK e problemas."""
    from diagnostics import export_report

    results = [
        {"name": "A", "status": "🟢 OK", "details": ""},
        {"name": "B", "status": "🔴 FAIL", "details": ""},
        {"name": "C", "status": "🔴 FAIL", "details": ""},
    ]
    caminho = str(tmp_path / "relatorio.txt")
    export_report(results, caminho)

    with open(caminho, encoding="utf-8") as f:
        conteudo = f.read()

    assert "OK        : 1" in conteudo
    assert "Problemas : 2" in conteudo


# =============================================================================
# TESTES: auth.is_admin
# =============================================================================

@patch("auth.ctypes.windll.shell32.IsUserAnAdmin", return_value=1)
def test_is_admin_true(mock_api):
    """is_admin deve retornar True quando a API Windows retorna 1."""
    from auth import is_admin
    assert is_admin() is True


@patch("auth.ctypes.windll.shell32.IsUserAnAdmin", return_value=0)
def test_is_admin_false(mock_api):
    """is_admin deve retornar False quando a API Windows retorna 0."""
    from auth import is_admin
    assert is_admin() is False


@patch("auth.ctypes.windll.shell32.IsUserAnAdmin", side_effect=Exception("API falhou"))
def test_is_admin_fallback_seguro(mock_api):
    """is_admin deve retornar False (não crashar) quando ctypes lança exceção."""
    from auth import is_admin
    assert is_admin() is False

# =============================================================================
# TESTES: auth.show_admin_popup
# =============================================================================

@pytest.mark.asyncio
@patch("auth.is_admin", return_value=True)
async def test_show_admin_popup_nao_mostra_se_admin(mock_is_admin):
    """Não deve anexar ou abrir o dialog se o usuário já for administrador."""
    from auth import show_admin_popup
    
    page_mock = MagicMock(spec=ft.Page)
    page_mock.dialog = None

    await show_admin_popup(page_mock)

    # Nenhuma alteração deve ser feita na página
    assert page_mock.dialog is None
    page_mock.update.assert_not_called()


@pytest.mark.asyncio
@patch("auth.is_admin", return_value=False)
async def test_show_admin_popup_mostra_se_nao_admin(mock_is_admin):
    """Deve criar e abrir o dialog de alerta se o usuário não for administrador."""
    from auth import show_admin_popup
    
    page_mock = MagicMock(spec=ft.Page)
    page_mock.dialog = None

    await show_admin_popup(page_mock)

    # Verifica se o dialog foi criado, configurado como aberto e atualizado
    assert page_mock.dialog is not None
    assert isinstance(page_mock.dialog, ft.AlertDialog)
    assert page_mock.dialog.open is True
    assert page_mock.dialog.modal is False
    page_mock.update.assert_called_once()

# =============================================================================
# TESTES: config.load_config
# =============================================================================

def test_load_config_arquivo_valido(tmp_path, monkeypatch):
    """load_config deve retornar o conteúdo do JSON quando arquivo existe."""
    import config

    dados = {"version": "2.0", "last_run": "2025-01-01", "logs": []}
    arquivo = tmp_path / "winfix.json"
    arquivo.write_text(json.dumps(dados), encoding="utf-8")

    monkeypatch.setattr(config, "CONFIG_FILE", str(arquivo))

    resultado = config.load_config()

    assert resultado["version"] == "2.0"
    assert resultado["last_run"] == "2025-01-01"


def test_load_config_arquivo_ausente(tmp_path, monkeypatch):
    """load_config deve retornar config padrão quando arquivo não existe."""
    import config

    monkeypatch.setattr(config, "CONFIG_FILE", str(tmp_path / "nao_existe.json"))

    resultado = config.load_config()

    assert "version" in resultado
    assert "last_run" in resultado


def test_load_config_json_corrompido(tmp_path, monkeypatch):
    """load_config deve retornar config padrão quando JSON está corrompido."""
    import config

    arquivo = tmp_path / "winfix.json"
    arquivo.write_text("{ isso nao é json válido !!!", encoding="utf-8")

    monkeypatch.setattr(config, "CONFIG_FILE", str(arquivo))

    resultado = config.load_config()

    # Deve retornar padrão sem crashar
    assert "version" in resultado

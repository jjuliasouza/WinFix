# -*- coding: utf-8 -*-
"""
Testes unitários para WinFix v4.0.

Requisitos:
    pip install pytest pytest-asyncio

Executar se a pasta de binário não estiver no PATH:
    python -m pytest tests/tdd/test_diagnostics.py -v
"""

import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock
import importlib

# Defina aqui qual arquivo você quer testar ("diagnostics_red", "diagnostics_green" ou diagnostics)
nome_arquivo = "diagnostics_green"
meu_modulo = importlib.import_module(nome_arquivo)

# =============================================================================
# TESTES TDD: diagnostics.run_cmd
# =============================================================================

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.asyncio.create_subprocess_shell", new_callable=AsyncMock)
async def test_run_cmd_sucesso(mock_shell):
    """run_cmd deve retornar (stdout, stderr, 0) quando comando tem sucesso."""
    processo_falso = AsyncMock()
    processo_falso.communicate.return_value = (b"Resultado OK", b"")
    processo_falso.returncode = 0
    mock_shell.return_value = processo_falso

    stdout, stderr, code = await meu_modulo.run_cmd("ping -n 1 google.com")

    assert stdout == "Resultado OK"
    assert code == 0

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.asyncio.create_subprocess_shell", new_callable=AsyncMock)
async def test_run_cmd_timeout(mock_shell):
    """run_cmd deve retornar ('Timeout', '', 1) quando ultrapassa o tempo limite."""
    import asyncio

    processo_falso = AsyncMock()
    processo_falso.communicate.side_effect = asyncio.TimeoutError()
    processo_falso.kill = MagicMock()
    mock_shell.return_value = processo_falso

    stdout, stderr, code = await meu_modulo.run_cmd("tracert google.com", timeout=1)

    assert stdout == "Timeout"
    assert code == 1

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.asyncio.create_subprocess_shell", new_callable=AsyncMock)
async def test_run_cmd_erro_generico(mock_shell):
    """run_cmd deve retornar erro formatado para exceções inesperadas."""
    mock_shell.side_effect = OSError("Permissão negada")
    
    stdout, stderr, code = await meu_modulo.run_cmd("sfc /scannow")

    assert "Erro:" in stdout
    assert code == 1

# =============================================================================
# TESTES TDD: diagnostics.run_full_diagnostics
# =============================================================================

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.run_cmd", new_callable=AsyncMock)
async def test_run_full_diagnostics_retorna_lista(mock_cmd):
    """run_full_diagnostics deve retornar lista contendo todos os testes."""
    mock_cmd.return_value = ("Output de exemplo com mais de 50 chars aqui.", "", 0)
    
    results = await meu_modulo.run_full_diagnostics()

    assert isinstance(results, list)
    assert len(results) == 22
    for r in results:
        assert "name" in r and "status" in r and "details" in r

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.run_cmd", new_callable=AsyncMock)
async def test_run_full_diagnostics_status_fail(mock_cmd):
    """Deve marcar 🔴 FAIL quando código de retorno for diferente de 0."""
    mock_cmd.return_value = ("", "", 1)
    
    results = await meu_modulo.run_full_diagnostics()
    
    assert all("🔴 FAIL" in r["status"] for r in results)

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.run_cmd", new_callable=AsyncMock)
async def test_run_full_diagnostics_status_ok_com_saida_longa(mock_cmd):
    """Deve marcar 🟢 OK apenas se code==0 E output > 50 chars."""
    mock_cmd.return_value = ("X" * 51, "", 0) 
    
    results = await meu_modulo.run_full_diagnostics()
    
    assert all("🟢 OK" in r["status"] for r in results)

# =============================================================================
# TESTES TDD: diagnostics.run_fix
# =============================================================================

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.run_cmd", new_callable=AsyncMock)
async def test_run_fix_individual_sucesso(mock_cmd):
    """Fix individual válido deve retornar (True, output)."""
    mock_cmd.return_value = ("DNS flushed successfully.", "", 0)
    
    sucesso, output = await meu_modulo.run_fix("DNS Flush")
    
    assert sucesso is True
    assert "DNS flushed" in output

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.run_cmd", new_callable=AsyncMock)
async def test_run_fix_individual_falha(mock_cmd):
    """Fix individual que falha deve retornar (False, output)."""
    mock_cmd.return_value = ("Acesso negado.", "", 1)
    
    sucesso, output = await meu_modulo.run_fix("SFC")
    
    assert sucesso is False

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.run_cmd", new_callable=AsyncMock)
async def test_run_fix_nome_invalido(mock_cmd):
    """Nome inexistente deve acionar o modo de execução de todos os fixes."""
    mock_cmd.return_value = ("OK", "", 0)
    
    sucesso, output = await meu_modulo.run_fix("NomeQueNaoExiste")
    
    assert isinstance(sucesso, bool)

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.run_cmd", new_callable=AsyncMock)
async def test_run_fix_nota_aparece_no_output(mock_cmd):
    """Fixes com aviso devem incluir [NOTA] no início do output."""
    mock_cmd.return_value = ("Winsock reset OK.", "", 0)
    
    _, output = await meu_modulo.run_fix("Winsock")
    
    assert "[NOTA]" in output
    assert "reboot" in output.lower()

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.run_cmd", new_callable=AsyncMock)
async def test_run_fix_progress_callback(mock_cmd):
    """O on_progress deve ser chamado para cada fix no modo completo."""
    mock_cmd.return_value = ("OK", "", 0)
    chamadas = []

    async def captura_progresso(atual, total, nome):
        chamadas.append((atual, total, nome))

    await meu_modulo.run_fix(on_progress=captura_progresso)

    assert len(chamadas) == len(meu_modulo.FIXES)
    assert chamadas[0][0] == 1

@pytest.mark.asyncio
@patch(f"{nome_arquivo}.run_cmd", new_callable=AsyncMock)
async def test_run_fix_retorna_mensagem_sem_output(mock_cmd):
    """Comandos silenciosos devem exibir '(sem output)'."""
    mock_cmd.return_value = ("", "", 0)
    
    sucesso, output = await meu_modulo.run_fix("DNS Flush")
    
    assert sucesso is True
    assert "(sem output)" in output

# =============================================================================
# TESTES TDD: diagnostics.export_report
# =============================================================================

def test_export_report_cria_arquivo(tmp_path):
    """Deve criar um arquivo de texto no disco."""
    results = [{"name": "Ping", "status": "🟢 OK", "details": "Reply de 8.8.8.8"}]
    caminho = str(tmp_path / "relatorio.txt")
    
    meu_modulo.export_report(results, caminho)
    
    assert os.path.exists(caminho)

def test_export_report_conteudo(tmp_path):
    """O conteúdo do arquivo deve refletir os testes recebidos."""
    results = [
        {"name": "Ping Google", "status": "🟢 OK", "details": "64 bytes"},
        {"name": "SFC Status", "status": "🔴 FAIL", "details": "Erros encontrados"},
    ]
    caminho = str(tmp_path / "relatorio.txt")
    meu_modulo.export_report(results, caminho)

    with open(caminho, encoding="utf-8") as f:
        conteudo = f.read()

    assert "Ping Google" in conteudo
    assert "[ OK ]" in conteudo
    assert "[FAIL]" in conteudo

def test_export_report_contagem_problemas(tmp_path):
    """A contagem de sucessos e falhas deve estar correta no cabeçalho."""
    results = [
        {"name": "A", "status": "🟢 OK", "details": ""},
        {"name": "B", "status": "🔴 FAIL", "details": ""},
        {"name": "C", "status": "🔴 FAIL", "details": ""},
    ]
    caminho = str(tmp_path / "relatorio.txt")
    meu_modulo.export_report(results, caminho)

    with open(caminho, encoding="utf-8") as f:
        conteudo = f.read()

    assert "OK        : 1" in conteudo
    assert "Problemas : 2" in conteudo
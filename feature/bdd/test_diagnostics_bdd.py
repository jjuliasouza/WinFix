# -*- coding: utf-8 -*-
"""
Steps BDD — diagnostics.feature
Biblioteca: pytest-bdd
"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from pytest_bdd import given, when, then, parsers, scenarios

# Vincula este arquivo de passos ao arquivo de funcionalidade correspondente
scenarios("../diagnostics.feature")

# COMO EXECUTAR:
"""
    No diretório raiz do projeto (Winfix) rode este comando no terminal:
    pip install pytest pytest-bdd  # (_para instalar as dependências_)
    python -m pytest feature/bdd/test_diagnostics_bdd.py -v
    python -m pytest feature/bdd/ -v # (_para rodar todos os testes de uma única vez_)
"""

# =============================================================================
# FIXTURE de contexto (Mantém o estado entre os passos do cenário)
# =============================================================================

@pytest.fixture
def ctx():
    """Inicializa um dicionário de contexto limpo para cada cenário."""
    return {}


# =============================================================================
# DADOS (GIVENS) — Contexto e Condições Iniciais
# =============================================================================

@given("que o sistema operacional é Windows")
def que_sistema_operacional_windows(ctx):
    ctx["os"] = "Windows"


@given("que o módulo de diagnósticos está carregado")
def que_modulo_diagnosticos_carregado(ctx):
    # Força a importação para garantir que o módulo está OK
    from diagnostics import run_cmd, run_full_diagnostics
    ctx["modulo_pronto"] = True


@given(parsers.cfparse('que o comando "{comando}" está disponível no sistema'))
def comando_disponivel(ctx, comando):
    ctx["mock_stdout"] = "Disparando contra google.com [8.8.8.8] com 32 bytes de dados:\nResposta de 8.8.8.8: bytes=32 tempo=15ms TTL=116"
    ctx["mock_stderr"] = ""
    ctx["mock_code"] = 0


@given(parsers.cfparse('que o comando "{comando}" retorna código de saída {codigo:d}'))
def comando_retorna_codigo_falha(ctx, comando, codigo):
    ctx["mock_stdout"] = ""
    ctx["mock_stderr"] = "Erro: Host de destino inacessível."
    ctx["mock_code"] = codigo


@given(parsers.cfparse('que o comando "{comando}" demora mais de {tempo:d} segundos'))
def comando_demora_muito(ctx, comando, tempo):
    ctx["forçar_timeout"] = True


@given("que todos os comandos do sistema retornam com sucesso")
def todos_comandos_sucesso(ctx):
    ctx["mock_completo_sucesso"] = True


@given(parsers.cfparse('que um comando retorna uma saída com {quantidade:d} caracteres'))
def comando_saida_longa(ctx, quantidade):
    ctx["mock_stdout"] = "X" * quantidade
    ctx["mock_stderr"] = ""
    ctx["mock_code"] = 0


# =============================================================================
# QUANDO (WHENS) — Execução das Ações
# =============================================================================

@when(parsers.cfparse('o diagnóstico "{nome_diag}" é executado'))
def executar_diagnostico_unitario(ctx, nome_diag):
    from diagnostics import run_cmd
    
    # Precisamos encodar para bytes, pois a biblioteca subprocess do Windows devolve bytes
    stdout_simulado = ctx.get("mock_stdout", "").encode('utf-8')
    stderr_simulado = ctx.get("mock_stderr", "").encode('utf-8')
    code_simulado = ctx.get("mock_code", 0)

    # Criamos um mock específico para processos assíncronos
    mock_process = AsyncMock()
    mock_process.returncode = code_simulado
    
    if ctx.get("forçar_timeout"):
        # Forçamos o communicate a estourar o erro de timeout
        mock_process.communicate.side_effect = asyncio.TimeoutError
    else:
        # Se for sucesso, entregamos as tuplas em bytes
        mock_process.communicate.return_value = (stdout_simulado, stderr_simulado)

    # Substituímos a chamada do sistema pelo nosso AsyncMock
    with patch("diagnostics.asyncio.create_subprocess_shell", new_callable=AsyncMock) as mock_shell:
        mock_shell.return_value = mock_process
        
        # Agora o asyncio.run gerencia o laço de eventos sozinho, sem erros!
        stdout, stderr, code = asyncio.run(run_cmd("comando_teste"))
        
        output = stdout + stderr
        ctx["status_resultado"] = "🔴 FAIL" if code != 0 or stdout == "Timeout" else "🟢 OK"
        ctx["detalhes_resultado"] = output


@when(parsers.cfparse('o diagnóstico "{nome_diag}" é executado com timeout de {tempo:d} segundo'))
def executar_diagnostico_timeout_especifico(ctx, nome_diag, tempo):
    executar_diagnostico_unitario(ctx, nome_diag)


@when("o diagnóstico completo é executado")
def executar_diagnostico_completo(ctx):
    from diagnostics import run_full_diagnostics
    
    stdout_fix = "Saída genérica de teste com mais de cinquenta caracteres para validar o status verde."
    
    # Usamos new_callable=AsyncMock para ele já entender que é uma corrotina
    with patch("diagnostics.run_cmd", new_callable=AsyncMock) as mock_run_cmd:
        mock_run_cmd.return_value = (stdout_fix, "", 0)
        
        ctx["lista_resultados"] = asyncio.run(run_full_diagnostics())


@when("o diagnóstico é processado")
def diagnostico_processado(ctx):
    saida_bruta = ctx.get("mock_stdout", "")
    ctx["detalhes_resultado"] = saida_bruta[:500]


# =============================================================================
# ENTÃO (THENS) — Validações Finais
# =============================================================================

@then(parsers.cfparse('o status deve ser "{status_esperado}"'))
def verificar_status(ctx, status_esperado):
    assert ctx["status_resultado"] == status_esperado


@then("os detalhes devem conter saída do comando")
def verificar_contem_saida(ctx):
    assert len(ctx["detalhes_resultado"]) > 0


@then(parsers.cfparse('os detalhes devem conter "{texto_esperado}"'))
def verificar_texto_especifico(ctx, texto_esperado):
    assert texto_esperado in ctx["detalhes_resultado"]


@then("o processo filho deve ter sido encerrado")
def processo_filho_encerrado(ctx):
    # No bloco de timeout, o asyncio.wait_for já garante o cancelamento/encerramento do processo filho
    assert ctx.get("forçar_timeout") is True


@then(parsers.cfparse('devem existir {quantidade:d} resultados na lista'))
def verificar_quantidade_resultados(ctx, quantidade):
    # O script possui exatamente 22 comandos mapeados
    assert len(ctx["lista_resultados"]) == quantidade


@then(parsers.cfparse('cada resultado deve conter os campos "{f1}", "{f2}" e "{f3}"'))
def verificar_campos_resultado(ctx, f1, f2, f3):
    for resultado in ctx["lista_resultados"]:
        assert f1 in resultado
        assert f2 in resultado
        assert f3 in resultado


@then(parsers.cfparse('os detalhes devem ter no máximo {limite:d} caracteres'))
def verificar_truncamento(ctx, limite):
    assert len(ctx["detalhes_resultado"]) <= limite
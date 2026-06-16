# -*- coding: utf-8 -*-
"""
Steps BDD — fixes.feature
Biblioteca: pytest-bdd
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from pytest_bdd import given, when, then, parsers, scenarios
from diagnostics import FIXES

# Vincula este arquivo de passos ao arquivo de funcionalidade
scenarios("../fixes.feature")

# COMO EXECUTAR:
"""
    No diretório raiz do projeto (Winfix) rode este comando no terminal:
    pip install pytest pytest-bdd  (_para instalar as dependências_)
    python -m pytest feature/bdd/test_fixes_bdd.py -v
    python -m pytest feature/bdd/ -v # (_para rodar todos os testes de uma única vez_)
"""

# =============================================================================
# FIXTURE de contexto (Partilha dados entre os passos)
# =============================================================================

@pytest.fixture
def ctx():
    """Inicializa um dicionário de contexto limpo para cada cenário."""
    return {}


# =============================================================================
# DADOS (GIVENS)
# =============================================================================

@given(parsers.cfparse('que o dicionário FIXES está carregado com {qtd:d} entradas'))
@given(parsers.cfparse('que o dicionário FIXES contém {qtd:d} fixes'))
def verificar_tamanho_fixes(ctx, qtd):
    # Verifica diretamente contra o dicionário real importado do diagnostics.py [cite: 8, 11]
    assert len(FIXES) == qtd


@given(parsers.cfparse('que o fix "{fix_name}" está disponível'))
def fix_disponivel(ctx, fix_name):
    assert fix_name in FIXES
    ctx["fix_name"] = fix_name


@given(parsers.cfparse('que o comando "{cmd}" retorna código {codigo:d}'))
def comando_retorna_codigo(ctx, cmd, codigo):
    ctx["mock_code"] = codigo
    ctx["mock_stdout"] = f"Saída simulada do comando {cmd}"


@given(parsers.cfparse('que o fix "{fix_name}" possui a nota "{nota}"'))
def fix_possui_nota(ctx, fix_name, nota):
    ctx["fix_name"] = fix_name
    # Extrai os dados do dicionário real para verificar a nota [cite: 10, 11]
    comando, precisa_admin, timeout, nota_real = FIXES[fix_name]
    assert nota == nota_real


@given("que o modo de execução completa está ativo")
def modo_execucao_completa(ctx):
    ctx["modo_completo"] = True


@given(parsers.cfparse('que o fix "{fix_name}" retorna saída vazia'))
def fix_saida_vazia(ctx, fix_name):
    ctx["fix_name"] = fix_name
    # Simulando um comando silencioso que não escreve nada no terminal [cite: 12, 13]
    ctx["mock_stdout"] = ""
    ctx["mock_stderr"] = ""
    ctx["mock_code"] = 0


# =============================================================================
# QUANDOS (WHENS)
# =============================================================================

# Agrupando frases semelhantes em uma única função para evitar repetição
@when(parsers.cfparse('o fix "{fix_name}" é executado individualmente'))
@when(parsers.cfparse('o fix "{fix_name}" é executado'))
@when(parsers.cfparse('o fix "{fix_name}" é solicitado'))
def executar_fix_especifico(ctx, fix_name):
    from diagnostics import run_fix
    
    stdout = ctx.get("mock_stdout", "Saída OK")
    stderr = ctx.get("mock_stderr", "")
    code = ctx.get("mock_code", 0)

    # Mascaramos o run_cmd interno usando o AsyncMock nativo
    with patch("diagnostics.run_cmd", new_callable=AsyncMock) as mock_run_cmd:
        mock_run_cmd.return_value = (stdout, stderr, code)
        
        # Executa a função assíncrona de forma segura
        resultado, output = asyncio.run(run_fix(fix_name))
        
        # Armazena os resultados para os próximos passos
        ctx["resultado"] = resultado
        ctx["output"] = output
        ctx["mock_run_cmd"] = mock_run_cmd


@when("o fix é executado")
def executar_fix_contexto(ctx):
    # Reutiliza a lógica anterior usando o nome guardado no passo "Dado" [cite: 13]
    executar_fix_especifico(ctx, ctx["fix_name"])


@when("todos os fixes são executados com callback de progresso")
def executar_todos_com_callback(ctx):
    from diagnostics import run_fix
    
    # Criamos um mock para simular a barra de progresso visual do Flet
    mock_callback = AsyncMock()
    
    with patch("diagnostics.run_cmd", new_callable=AsyncMock) as mock_run_cmd:
        mock_run_cmd.return_value = ("OK", "", 0)
        
        resultado, output = asyncio.run(run_fix(on_progress=mock_callback))
        
        ctx["resultado"] = resultado
        ctx["output"] = output
        ctx["mock_callback"] = mock_callback


# =============================================================================
# ENTÕES (THENS)
# =============================================================================

@then(parsers.cfparse('o resultado deve ser {resultado_esperado}'))
def verificar_resultado_bool(ctx, resultado_esperado):
    esperado = resultado_esperado.strip() == "True"
    assert ctx["resultado"] is esperado


@then("o output deve conter o retorno do comando")
def verificar_output_contem_retorno(ctx):
    assert ctx["mock_stdout"] in ctx["output"]


@then("o output deve estar preenchido")
def verificar_output_preenchido(ctx):
    assert len(ctx["output"]) > 0


@then(parsers.cfparse('o output deve iniciar com "{texto}"'))
def verificar_inicio_output(ctx, texto):
    assert ctx["output"].startswith(texto)


@then(parsers.cfparse('o output deve mencionar "{texto}"'))
def verificar_mencao_output(ctx, texto):
    assert texto in ctx["output"]


@then(parsers.cfparse('todos os {qtd:d} fixes devem ser executados em sequência'))
def verificar_execucao_todos_fixes(ctx, qtd):
    # Confirma se o mock do sistema foi acionado exatamente a quantidade de vezes esperada (10) [cite: 11]
    assert ctx["mock_run_cmd"].call_count == qtd


@then(parsers.cfparse('o callback deve ter sido chamado exatamente {qtd:d} vezes'))
def verificar_qtd_chamadas_callback(ctx, qtd):
    assert ctx["mock_callback"].call_count == qtd


@then(parsers.cfparse('o último callback deve indicar índice {atual:d} de {total:d}'))
def verificar_ultimo_callback(ctx, atual, total):
    # Extrai os argumentos da última vez que o mock foi chamado
    # call_args contém (args, kwargs). Os args são: (atual, total, nome)
    args, _ = ctx["mock_callback"].call_args
    assert args[0] == atual
    assert args[1] == total


@then(parsers.cfparse('o output deve ser "{texto}"'))
def verificar_output_exato(ctx, texto):
    assert ctx["output"] == texto
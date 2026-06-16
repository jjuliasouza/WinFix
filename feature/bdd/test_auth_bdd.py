# -*- coding: utf-8 -*-
"""
Steps BDD — fixes.auth.feature
Biblioteca: pytest-bdd
"""
import pytest
from unittest.mock import patch
from pytest_bdd import given, when, then, parsers, scenarios

# Vincula este ficheiro de testes ao ficheiro .feature
scenarios("../auth.feature")

# COMO EXECUTAR:
"""
    No diretório raiz do projeto (Winfix) rode este comando no terminal:
    pip install pytest pytest-bdd  # (_para instalar as dependências_)
    python -m pytest feature/bdd/test_auth_bdd.py -v
    python -m pytest feature/bdd/ -v # (_para rodar todos os testes de uma única vez_)
"""

# =============================================================================
# FIXTURE de contexto (Partilha dados entre os passos do mesmo cenário)
# =============================================================================

@pytest.fixture
def ctx():
    """Inicializa um dicionário de contexto limpo para cada cenário."""
    return {}


# =============================================================================
# DADO (GIVEN) — Mapeia as condições iniciais do cenário
# =============================================================================

# O uso de parsers.cfparse permite ignorar ou capturar as aspas internas sem dar erro
@given(parsers.cfparse('que a API Windows "{api_name}" retorna {valor:d}'))
def que_api_windows_retorna(ctx, api_name, valor):
    """
    Captura o retorno simulado da API (0 ou 1).
    O ':d' converte o texto do ficheiro automaticamente para um número inteiro.
    """
    ctx["api_excecao"] = False
    ctx["api_retorno"] = valor


# =============================================================================
# QUANDO (WHEN) — Executa a ação principal
# =============================================================================

@when("is_admin() é chamada")
def quando_is_admin_chamada(ctx):
    """Invoca a função real mascarando a chamada do sistema com um mock."""
    from auth import is_admin
    excecao = ctx.get("api_excecao", False)
    retorno = ctx.get("api_retorno", 0)

    # Intercepta o módulo ctypes importado dentro de auth.py
    with patch("auth.ctypes") as mock_ctypes:
        if excecao:
            mock_ctypes.windll.shell32.IsUserAnAdmin.side_effect = Exception("API falhou")
            try:
                ctx["is_admin_result"] = is_admin()
            except Exception:
                ctx["is_admin_result"] = "CRASH"
        else:
            # Força a API do Windows a devolver 0 ou 1 conforme o cenário
            mock_ctypes.windll.shell32.IsUserAnAdmin.return_value = retorno
            ctx["is_admin_result"] = is_admin()


# =============================================================================
# ENTÃO (THEN) — Valida o resultado esperado
# =============================================================================

@then(parsers.cfparse('o resultado deve ser {resultado_esperado}'))
def verificar_resultado_is_admin(ctx, resultado_esperado):
    """
    Valida se o retorno da função coincide com o esperado pelo BDD.
    Irá encaixar dinamicamente com 'True' ou 'False' vindo da feature.
    """
    # Converte a string 'True'/'False' do ficheiro de texto num booleano real do Python
    booleano_esperado = resultado_esperado.strip() == "True"
    
    # Executa a validação final do teste
    assert ctx["is_admin_result"] is booleano_esperado
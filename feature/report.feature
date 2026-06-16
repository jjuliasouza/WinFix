# -*- coding: utf-8 -*-
"""
Steps BDD — report.feature
Biblioteca: pytest-bdd
"""
import os
import pytest
from pytest_bdd import given, when, then, parsers, scenarios
from diagnostics import export_report

# Vincula este arquivo de passos ao arquivo de funcionalidade
scenarios("../report.feature")

# COMO EXECUTAR:
"""
    No diretório raiz do projeto (Winfix) rode este comando no terminal:
    pip install pytest pytest-bdd  (_para instalar as dependências_)
    python -m pytest feature/bdd/test_report_bdd.py -v
    python -m pytest feature/bdd/ -v # (_para rodar todos os testes de uma única vez_)
"""

# =============================================================================
# FIXTURE de contexto
# =============================================================================

@pytest.fixture
def ctx(tmp_path):
    """
    O 'tmp_path' é uma fixture nativa do pytest que cria uma pasta temporária.
    Isso impede que o teste suje o computador criando arquivos de relatório reais.
    """
    return {
        "tmp_dir": tmp_path, 
        "results": [], 
        "file_path": ""
    }


# =============================================================================
# DADOS (GIVENS)
# =============================================================================

@given(parsers.cfparse('que {qtd:d} diagnósticos foram executados'))
def preparar_diagnosticos(ctx, qtd):
    # Apenas inicializa a lista, o próximo passo preenche os dados
    ctx["results"] = []


@given(parsers.cfparse('que {passaram:d} passaram e {falharam:d} falhou'))
def preencher_diagnosticos(ctx, passaram, falharam):
    # Simula o formato exato dos dicionários gerados pelo run_full_diagnostics
    resultados = []
    
    for i in range(passaram):
        resultados.append({"name": f"Teste OK {i}", "status": "🟢 OK", "details": "Detalhes de sucesso"})
        
    for i in range(falharam):
        resultados.append({"name": f"Teste Falho {i}", "status": "🔴 FAIL", "details": "Detalhes de falha"})
        
    ctx["results"] = resultados


@given("que nenhum diagnóstico foi executado")
def nenhum_diagnostico(ctx):
    # Garante que a lista está vazia para o cenário 2
    ctx["results"] = []


# =============================================================================
# QUANDOS (WHENS)
# =============================================================================

@when(parsers.cfparse('o relatório é exportado para "{filename}"'))
def exportar_relatorio_nome(ctx, filename):
    # Junta o caminho da pasta temporária com o nome do arquivo
    caminho_completo = os.path.join(ctx["tmp_dir"], filename)
    
    # Chama a função real passando nossa lista de resultados simulada
    export_report(ctx["results"], caminho_completo)
    
    # Salva o caminho para as validações finais
    ctx["file_path"] = caminho_completo


@when("o relatório é exportado")
def exportar_relatorio_padrao(ctx):
    # Reutiliza a lógica usando um nome de arquivo padrão para o teste
    exportar_relatorio_nome(ctx, "relatorio_teste_vazio.txt")


# =============================================================================
# ENTÕES (THENS)
# =============================================================================

@then("o arquivo deve existir no disco")
@then("o arquivo deve existir")
def verificar_arquivo_existe(ctx):
    # O os.path.exists confirma se o arquivo foi fisicamente criado na pasta
    assert os.path.exists(ctx["file_path"]) is True


@then(parsers.cfparse('o arquivo deve conter o cabeçalho "{texto}"'))
@then(parsers.cfparse('o arquivo deve registrar "{texto}"'))
def verificar_conteudo_arquivo(ctx, texto):
    # Abre o arquivo de texto gerado e lê tudo que tem dentro
    with open(ctx["file_path"], "r", encoding="utf-8") as f:
        conteudo_do_arquivo = f.read()
        
    # Verifica se a frase exata esperada pelo BDD está escrita lá dentro
    assert texto in conteudo_do_arquivo

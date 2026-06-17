# language: pt
# =============================================================================
# Feature: Relatório
# Módulos: diagnostics.py (export_report)
# =============================================================================

Funcionalidade: Exportar relatório de diagnósticos
  Como usuário Windows
  Quero exportar os resultados dos diagnósticos em TXT
  Para documentar e compartilhar o estado do sistema

  # ---------------------------------------------------------------------------
  # Cenário 1 — Exportação bem-sucedida
  # ---------------------------------------------------------------------------
  Cenário: Relatório é criado com sucesso após diagnósticos
    Dado que 3 diagnósticos foram executados
    E que 2 passaram e 1 falhou
    Quando o relatório é exportado para "winfix_report.txt"
    Então o arquivo deve existir no disco
    E o arquivo deve conter o cabeçalho "WINFIX v4.0"
    E o arquivo deve registrar "OK        : 2"
    E o arquivo deve registrar "Problemas : 1"

  # ---------------------------------------------------------------------------
  # Cenário 2 — Relatório vazio
  # ---------------------------------------------------------------------------
  Cenário: Exportar lista vazia gera relatório com zero testes
    Dado que nenhum diagnóstico foi executado
    Quando o relatório é exportado
    Então o arquivo deve existir
    E o arquivo deve registrar "Total     : 0"

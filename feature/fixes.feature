# language: pt
# =============================================================================
# Feature: Execução de Fixes
# Módulo: diagnostics.py (FIXES dict + run_fix)
# =============================================================================

Funcionalidade: Executar fixes de correção do Windows
  Como usuário Windows
  Quero aplicar correções automáticas no sistema
  Para resolver problemas com o mínimo de cliques

  Contexto:
    Dado que o dicionário FIXES está carregado com 10 entradas

  # ---------------------------------------------------------------------------
  # Cenário 1 — Fix individual com sucesso
  # ---------------------------------------------------------------------------
  Cenário: Fix individual bem-sucedido retorna sucesso e output
    Dado que o fix "DNS Flush" está disponível
    E que o comando "ipconfig /flushdns" retorna código 0
    Quando o fix "DNS Flush" é executado individualmente
    Então o resultado deve ser True
    E o output deve conter o retorno do comando

  # ---------------------------------------------------------------------------
  # Cenário 2 — Fix individual com falha
  # ---------------------------------------------------------------------------
  Cenário: Fix que falha retorna False e output de erro
    Dado que o fix "SFC" está disponível
    E que o comando "sfc /scannow" retorna código 1
    Quando o fix "SFC" é executado individualmente
    Então o resultado deve ser False
    E o output deve estar preenchido

  # ---------------------------------------------------------------------------
  # Cenário 3 — Fix com nota exibe aviso no output
  # ---------------------------------------------------------------------------
  Cenário: Fix com nota de reboot exibe aviso [NOTA] no output
    Dado que o fix "Winsock" possui a nota "Requer reboot para ter efeito."
    Quando o fix "Winsock" é executado
    Então o output deve iniciar com "[NOTA]"
    E o output deve mencionar "reboot"

  # ---------------------------------------------------------------------------
  # Cenário 4 — Fix com nome inexistente executa todos
  # ---------------------------------------------------------------------------
  Cenário: Nome de fix inválido aciona modo de execução completa
    Dado que o dicionário FIXES contém 10 fixes
    Quando o fix "NomeQueNaoExiste" é solicitado
    Então todos os 10 fixes devem ser executados em sequência

  # ---------------------------------------------------------------------------
  # Cenário 5 — Progresso reportado no modo completo
  # ---------------------------------------------------------------------------
  Cenário: Callback de progresso é chamado uma vez por fix
    Dado que o modo de execução completa está ativo
    Quando todos os fixes são executados com callback de progresso
    Então o callback deve ter sido chamado exatamente 10 vezes
    E o último callback deve indicar índice 10 de 10

  # ---------------------------------------------------------------------------
  # Cenário 6 — Fix sem output exibe placeholder
  # ---------------------------------------------------------------------------
  Cenário: Fix que retorna output vazio exibe mensagem padrão
    Dado que o fix "DNS Flush" retorna saída vazia
    Quando o fix é executado
    Então o output deve ser "(sem output)"

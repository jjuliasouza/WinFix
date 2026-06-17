# language: pt
# =============================================================================
# Feature: Diagnósticos do Sistema
# Módulo: diagnostics.py
# Técnica: BDD com Gherkin (Dado/Quando/Então)
# =============================================================================

Funcionalidade: Executar diagnósticos do sistema Windows
  Como usuário de Windows
  Quero executar diagnósticos automáticos do sistema
  Para identificar problemas de rede, disco, memória e serviços

  Contexto:
    Dado que o sistema operacional é Windows
    E que o módulo de diagnósticos está carregado

  # ---------------------------------------------------------------------------
  # Cenário 1 — Comando executado com sucesso
  # ---------------------------------------------------------------------------
  Cenário: Comando executado com sucesso retorna status OK
    Dado que o comando "ping -n 1 google.com" está disponível no sistema
    Quando o diagnóstico "Ping Google" é executado
    Então o status deve ser "🟢 OK"
    E os detalhes devem conter saída do comando

  # ---------------------------------------------------------------------------
  # Cenário 2 — Falha de rede
  # ---------------------------------------------------------------------------
  Cenário: Comando com falha, retorna status FAIL
    Dado que o comando "ping" retorna código de saída 1
    Quando o diagnóstico "Ping Google" é executado
    Então o status deve ser "🔴 FAIL"

  # ---------------------------------------------------------------------------
  # Cenário 3 — Timeout de comando lento
  # ---------------------------------------------------------------------------
  Cenário: Comando que excede o tempo limite é marcado como falha
    Dado que o comando "tracert google.com" demora mais de 30 segundos
    Quando o diagnóstico "Tracert" é executado com timeout de 1 segundo
    Então o status deve ser "🔴 FAIL"
    E os detalhes devem conter "Timeout"
    E o processo filho deve ter sido encerrado

  # ---------------------------------------------------------------------------
  # Cenário 4 — Diagnóstico completo (20+ testes)
  # ---------------------------------------------------------------------------
  Cenário: Diagnóstico completo retorna resultados para todos os testes
    Dado que todos os comandos do sistema retornam com sucesso
    Quando o diagnóstico completo é executado
    Então devem existir 22 resultados na lista
    E cada resultado deve conter os campos "name", "status" e "details"

  # ---------------------------------------------------------------------------
  # Cenário 5 — Output truncado para não sobrecarregar a UI
  # ---------------------------------------------------------------------------
  Cenário: Detalhes longos são truncados a 500 caracteres
    Dado que um comando retorna uma saída com 2000 caracteres
    Quando o diagnóstico é processado
    Então os detalhes devem ter no máximo 500 caracteres

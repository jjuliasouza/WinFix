# language: pt
# =============================================================================
# Feature: Autenticação
# Módulos: auth.py (is_admin)
# =============================================================================

Funcionalidade: Verificação de privilégios de administrador
  Como usuário do sistema WinFix
  Quero saber se tenho privilégios de administrador
  Para habilitar ou desabilitar fixes que exigem elevação UAC

  # ---------------------------------------------------------------------------
  # Cenário 1 — Processo elevado
  # ---------------------------------------------------------------------------
  Cenário: Processo com UAC elevado é reconhecido como administrador
    Dado que a API Windows "IsUserAnAdmin" retorna 1
    Quando is_admin() é chamada
    Então o resultado deve ser True

  # ---------------------------------------------------------------------------
  # Cenário 2 — Processo sem elevação
  # ---------------------------------------------------------------------------
  Cenário: Processo sem UAC elevado não é reconhecido como administrador
    Dado que a API Windows "IsUserAnAdmin" retorna 0
    Quando is_admin() é chamada
    Então o resultado deve ser False


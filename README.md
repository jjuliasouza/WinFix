# WinFix

Software para diagnóstico e correção automática de problemas básicos de conectividade em sistemas Windows.

---

## Problema

Usuários do sistema operacional Windows frequentemente enfrentam dificuldades para resolver problemas comuns de rede, como falhas de conexão com a internet, erros de DNS ou configuração de IP, dependendo muitas vezes de suporte técnico especializado.

---

## Solução

O WinFix foi desenvolvido para automatizar o diagnóstico e a correção desses problemas, executando testes e aplicando soluções padronizadas.

O sistema:

* Identifica falhas de conectividade
* Coleta informações da rede
* Realiza possíveis correções de erros (Fixes)
* Apresenta um relatório claro ao usuário
* Reduz a necessidade de intervenção manual

---

## Público-alvo

* Usuários comuns de Windows
* Equipes de suporte técnico de Tecnologia da Informação

---

## Funcionalidades

### Sprint 1 (concluída)

* Estrutura inicial do projeto
* Definição do problema, solução e escopo

### Sprint 2 (concluída)

* Aba Diagnósticos
- Executa 22+ testes de rede, disco, memória, processos, drivers e sistema
- Exibe resultado em tabela colorida (verde = OK / vermelho = falha)
- Cada linha mostra o nome do teste, status e detalhes do output

* Aba Fixes
- Executar Todos os Fixes — roda todos os 10 fixes em sequência com contador de progresso `X/10`
- Fix Individual — selecione um fix específico pelo dropdown

* Aba Relatório
- Exporta um arquivo `.txt` formatado com todos os resultados dos diagnósticos
- Abre automaticamente no Bloco de Notas após salvar

* Testes unitários automatizados (TDD)
- Teste de sucesso: Verifica se a função retorna corretamente a saída do comando quando tudo funciona normalmente.
- Teste de timeout: Verifica se a função consegue tratar casos em que o comando demora demais para responder.
- Teste de erro/exceção: Verifica se a função trata erros inesperados sem quebrar o sistema.
- O código usa mocks (patch e AsyncMock) para simular os comandos do terminal sem executar nada de verdade no computador.

### Sprint 3 (concluída)

* Expansão da suíte de testes — TDD + BDD
- 20+ testes unitários cobrindo `run_cmd`, `run_full_diagnostics`, `run_fix`, `export_report`, `is_admin`, `show_admin_popup` e `load_config`
- 17 cenários BDD escritos em Gherkin (PT) com `pytest-bdd`, organizados em 4 arquivos `.feature`: diagnósticos, fixes, autenticação e relatório
- Padrão Red/Green explícito: cada módulo possui versões `_red.py` (falha intencional) e `_green.py` (implementação correta) para demonstrar o ciclo TDD

* Qualidade de código
- Configuração centralizada de ferramentas em `pyproject.toml`: Black (formatação), Ruff (lint + isort) e MyPy (tipagem estática)
- Cobertura de testes configurada com `pytest-cov` (threshold mínimo de 60%)
- Modo assíncrono automático no pytest via `asyncio_mode = "auto"`

---

## Tecnologias utilizadas

* Python
* Git / GitHub
* Visual Studio Code

---

## Requisitos

- **Windows 10 ou 11**
- **Python 3.10 ou superior** — [python.org/downloads](https://www.python.org/downloads/)
  - Durante a instalação, marque a opção **"Add Python to PATH"**

---

## Instalação

### 1. Clone ou extraia o projeto

Coloque a pasta `winfix` em qualquer diretório. Exemplo:

```
C:\Users\SeuUsuario\Downloads\winfix\
```

### 2. Instale as dependências

Abra o **Prompt de Comando** ou **PowerShell** dentro da pasta do projeto e rode:

```bash
pip install -r requirements.txt
```

Isso instala:

| Pacote | Finalidade |
|---|---|
| `flet` | Interface gráfica (Material Design) |
| `rich` | Logs coloridos no terminal |
| `pytest` | Testes automatizados |
| `pytest-asyncio` | Suporte a testes de funções assíncronas |
| `pytest-bdd` | Testes no estilo BDD com arquivos Gherkin `.feature` |
| `pyinstaller` | Gerar executável `.exe` (opcional) |

---

## Como rodar

### Modo normal

```bash
python main.py
```

### Modo administrador (recomendado para fixes)

A maioria dos fixes do Windows exige privilégios elevados. Execute como admin de uma das formas abaixo:

**Opção A — PowerShell:**
```powershell
Start-Process python -ArgumentList "main.py" -Verb RunAs
```

**Opção B — Pelo próprio app:**
Abra normalmente. Se não estiver como admin, um banner laranja aparecerá com o botão **"Reabrir como Admin"** — clique nele.

---

## Estrutura do projeto

```
winfix/
├── main.py               # Interface gráfica (Flet)
├── diagnostics.py        # Lógica de diagnósticos e fixes
├── diagnostics_red.py    # Versão com falha intencional (ciclo TDD)
├── diagnostics_green.py  # Versão correta (ciclo TDD)
├── auth.py               # Verificação de privilégios de administrador
├── auth_red.py           # Versão com falha intencional (ciclo TDD)
├── auth_green.py         # Versão correta (ciclo TDD)
├── config.py             # Configurações gerais
├── config_red.py         # Versão com falha intencional (ciclo TDD)
├── config_green.py       # Versão correta (ciclo TDD)
├── requirements.txt      # Dependências Python
├── pyproject.toml        # Configuração de Black, Ruff, MyPy e pytest
├── WinFix.spec           # Configuração para gerar .exe (PyInstaller)
├── winfix.log            # Log gerado automaticamente ao rodar
├── tests/
│   ├── tdd/
│   │   ├── test_auth.py          # Testes unitários de auth
│   │   ├── test_config.py        # Testes unitários de config
│   │   └── test_diagnostics.py   # Testes unitários de diagnostics
│   └── test.py
└── feature/
    ├── auth.feature              # Cenários BDD — autenticação
    ├── diagnostics.feature       # Cenários BDD — diagnósticos
    ├── fixes.feature             # Cenários BDD — fixes
    ├── report.feature            # Cenários BDD — relatório
    └── bdd/
        ├── test_auth_bdd.py
        ├── test_diagnostics_bdd.py
        ├── test_fixes_bdd.py
        └── test_report_bdd.py
```

---

## Funcionalidades

### Aba Diagnósticos
- Executa **22+ testes** de rede, disco, memória, processos, drivers e sistema
- Exibe resultado em tabela colorida (verde = OK / vermelho = falha)
- Cada linha mostra o nome do teste, status e detalhes do output

### Aba Fixes
- **Executar Todos os Fixes** — roda todos os 10 fixes em sequência com contador de progresso `X/10`
- **Fix Individual** — selecione um fix específico pelo dropdown

| Fix | Requer Admin | Observação |
|---|---|---|
| DNS Flush | Não | Limpa cache DNS |
| Winsock | Sim | Requer reboot |
| IP Reset | Sim | Requer reboot |
| Firewall | Sim | Restaura configurações padrão |
| DNS Service | Sim | Reinicia serviço DNS |
| GPUpdate | Não | Atualiza políticas de grupo |
| CHKDSK | Sim | Verifica disco (online, sem reboot) |
| SFC | Sim | Verifica arquivos do sistema (~30 min) |
| DISM | Sim | Repara imagem do Windows (~30 min) |
| IP Renew | Sim | Renova IP (derruba rede brevemente) |

> **Atenção:** SFC e DISM podem levar até 30 minutos. Não feche o app durante a execução.

### Aba Relatório
- Exporta um arquivo `.txt` formatado com todos os resultados dos diagnósticos
- Abre automaticamente no Bloco de Notas após salvar

---

## Gerar executável (.exe)

Para distribuir o app sem precisar do Python instalado:

```bash
pyinstaller WinFix.spec
```

O executável será gerado em `dist\WinFix.exe`.

---

## Logs

O arquivo `winfix.log` é gerado automaticamente na pasta do projeto a cada execução. Contém todos os comandos executados e seus outputs completos — útil para diagnóstico de falhas.

---

## Testes

### Unitários (TDD)

```bash
pytest tests/tdd/ -v
```

### BDD

```bash
pytest feature/bdd/ -v
```

### Todos de uma vez

```bash
pytest tests/ feature/bdd/ -v
```

---

## Problemas comuns

| Problema | Solução |
|---|---|
| `ModuleNotFoundError: flet` | Rode `pip install -r requirements.txt` |
| `ModuleNotFoundError: pytest_bdd` | Rode `pip install pytest-bdd` |
| Fixes falhando com "Acesso negado" | Abra o app como administrador |
| App não abre a janela | Verifique se `flet` foi instalado corretamente |
| SFC/DISM aparecem travados | Normal — podem levar até 30 min, aguarde |

---

## Diferenciais

O WinFix padroniza procedimentos técnicos, transformando tarefas que dependem da experiência individual em um fluxo automatizado e consistente.

Com isso, o sistema:

* Reduz erros humanos
* Garante diagnósticos mais confiáveis
* Melhora a qualidade do suporte técnico

---

## Status do projeto

* ✅ Concluído — Sprint 1
* ✅ Concluído — Sprint 2
* ✅ Concluído — Sprint 3

---

## Modelo de Ramificação (GitHub Flow)

### Estrutura de branches

* `main` → sempre estável
* `feature/*` → novas funcionalidades
* `fix/*` → correções de bugs

---

### Fluxo de trabalho

1. Criar uma branch
2. Desenvolver a funcionalidade
3. Abrir Pull Request
4. Revisar código
5. Realizar merge na `main`

---

### Regras

*  Nunca commitar diretamente na `main`
*  Sempre criar uma branch
*  Sempre abrir Pull Request
*  Nomear branches corretamente

---

##  Padrão de Commits (Conventional Commits)

###  Estrutura

```
tipo(escopo): descrição
```

---

### 🔑 Tipos de commit

| Tipo     | Quando usar                     |
| -------- | ------------------------------- |
| feat     | Nova funcionalidade             |
| fix      | Correção de bug                 |
| docs     | Documentação                    |
| style    | Formatação (sem alterar lógica) |
| refactor | Refatoração                     |
| test     | Testes                          |
| chore    | Tarefas gerais                  |

---

### Regras

* Usar descrição em minúsculo
* Não utilizar ponto final
* Escrever no presente

---

### Exemplos

```
feat(login): adiciona autenticação com jwt
fix(api): corrige erro 500 ao buscar usuário
docs(readme): adiciona instruções de instalação
refactor(user): melhora lógica de validação
chore: atualiza dependências
```

---

## Como iremos aplicar no projeto

### 1. Criar uma branch

```bash
git checkout -b feature/login
```

---

### 2. Fazer commits padronizados

```bash
git commit -m "feat(login): cria tela de login"
```

---

### 3. Subir a branch

```bash
git push origin feature/login
```

---

### 4. Abrir Pull Request

* Revisar o código
* Realizar o merge na `main`

---

## 👥 Autores

* Allex Maia
* Julia Souza
* Murilo Gusmão
* Nicolas Everton Duarte da Silva
* Stephany de Mello Amorim

---

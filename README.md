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
* Apresenta um relatório claro ao usuário
* Reduz a necessidade de intervenção manual

---

## Público-alvo

* Usuários comuns de Windows
* Equipes de suporte técnico de TI

---

## Funcionalidades

### Sprint 1 (concluída)

* Estrutura inicial do projeto
* Definição do problema, solução e escopo

### Sprint 2 (em desenvolvimento)

* Interface simples para iniciar o diagnóstico
* Teste de conectividade com a internet (ping)
* Exibição de informações de rede (ipconfig)
* Relatório com os resultados do diagnóstico

---

## Tecnologias utilizadas

* Python
* Git / GitHub
* Visual Studio Code

---

## Como executar o projeto

1. Clone o repositório:

```bash
git clone https://github.com/jjuliasouza/WinFix.git
```

2. Acesse a pasta do projeto:

```bash
cd WinFix
```

3. Execute o programa:

```bash
python main.py
```

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
* 🚧 Em desenvolvimento — Sprint 2

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

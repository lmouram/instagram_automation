# Gerenciamento de Dependências com `uv`

## 1. Introdução

Este documento descreve como gerenciar as dependências de software para o projeto `instagram-automation`. Nós utilizamos a ferramenta **`uv`** como nosso único gerenciador de pacotes e ambientes virtuais.

### Por que `uv`?

-   **Velocidade:** `uv` é escrito em Rust e é extremamente rápido, acelerando significativamente a instalação de dependências em comparação com ferramentas tradicionais como `pip` e `Poetry`.
-   **Simplicidade:** Ele oferece uma interface de linha de comando unificada e intuitiva para todas as operações comuns: criar ambientes, instalar, adicionar e remover pacotes.
-   **Modernidade:** `uv` adere aos padrões modernos da comunidade Python, como o uso do arquivo `pyproject.toml` (PEP 621) para definir as dependências do projeto.

### Fonte Única da Verdade: `pyproject.toml`

Todas as dependências do nosso projeto, tanto de produção quanto de desenvolvimento, são declaradas no arquivo `pyproject.toml` na raiz do projeto. Este arquivo é a fonte única da verdade para o que é necessário para rodar e desenvolver a aplicação.

## 2. Pré-requisitos: Instalando o `uv`

Antes de começar, você precisa ter o `uv` instalado na sua máquina. A forma recomendada é através do `pip` ou `pipx`.

```bash
# Recomendado (instala de forma isolada)
pipx install uv

# Alternativa (instala no seu ambiente Python global)
pip install uv
```

## 3. Fluxo de Trabalho em Desenvolvimento (Seu Computador) 

Este é o passo a passo para configurar o projeto em sua máquina local pela primeira vez e para o gerenciamento do dia a dia.

### 3.1. Configuração Inicial do Projeto

Depois de clonar o repositório, siga estes três passos no terminal, a partir da raiz do projeto:

**Passo 1: Criar o Ambiente Virtual**

`uv` cria e gerencia um ambiente virtual para isolar as dependências do projeto.

```bash
uv venv
```

Isso criará uma pasta `.venv` na raiz do projeto.

**Passo 2: Ativar o Ambiente Virtual**

Você precisa "entrar" no ambiente virtual para que os comandos seguintes funcionem corretamente.

*   **No macOS ou Linux:**
    ```bash
    source .venv/bin/activate
    ```
*   **No Windows (PowerShell):**
    ```powershell
    .venv\Scripts\Activate.ps1
    ```
*   **No Windows (CMD):**
    ```cmd
    .venv\Scripts\activate.bat
    ```

Seu prompt do terminal deve mudar, indicando que o ambiente está ativo.

**Passo 3: Instalar Todas as Dependências**

O comando `sync` lê o `pyproject.toml` e instala todas as dependências de produção e de desenvolvimento (`dev`) no seu ambiente virtual.

```bash
uv pip sync pyproject.toml
```

Pronto! Seu ambiente de desenvolvimento está configurado e pronto para uso.

### 3.2. Gerenciando Dependências no Dia a Dia

Estes são os comandos que você usará para modificar as dependências do projeto.

**Adicionar uma Nova Dependência de Produção**

Para adicionar um pacote que a aplicação precisa para rodar em produção (ex: `requests`).

```bash
uv add requests
```

`uv` irá automaticamente encontrar a versão mais recente, adicioná-la ao `pyproject.toml` e instalá-la no seu ambiente.

**Adicionar uma Nova Dependência de Desenvolvimento**

Para adicionar um pacote usado apenas para desenvolvimento, como testes ou linting (ex: `pytest-mock`). Use a flag `--dev`.

```bash
uv add pytest-mock --dev
```

Isso adicionará o pacote à seção `[dependency-groups.dev]` no `pyproject.toml`.

**Remover uma Dependência**

Para remover um pacote do projeto.

```bash
uv remove requests
```

`uv` irá remover a linha do `pyproject.toml` e também desinstalar o pacote do seu ambiente virtual. Para remover uma dependência de desenvolvimento, use a flag `--dev`:

```bash
uv remove pytest-mock --dev
```

**Atualizar Dependências**

Para atualizar os pacotes para as versões mais recentes permitidas pelas restrições no `pyproject.toml`:

```bash
uv pip sync --upgrade
```

---

## 4. Fluxo de Trabalho em Produção (CI/CD - GitHub Actions) 🚀

Em um ambiente de produção ou de integração contínua (CI), o objetivo é criar um ambiente de execução leve, seguro e 100% reprodutível.

O processo é muito similar ao de desenvolvimento, mas com uma diferença crucial: **nós não instalamos as dependências de desenvolvimento**.

### Exemplo de Workflow para GitHub Actions

Veja como seria um passo de instalação em um arquivo como `.github/workflows/scheduler.yml`:

```yaml
steps:
  - name: Checkout repository
    uses: actions/checkout@v4

  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: '3.11'

  - name: Install uv
    run: pip install uv

  - name: Create virtual environment
    run: uv venv

  - name: Install production dependencies
    run: |
      source .venv/bin/activate
      uv pip sync --no-dev

  - name: Run script
    env:
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      # ... outras secrets
    run: |
      source .venv/bin/activate
      python scripts/run_publisher.py
```

A flag **`--no-dev`** no comando `uv pip sync` é a chave. Ela instrui o `uv` a instalar **apenas** as dependências listadas em `[project.dependencies]`, ignorando completamente os pacotes do grupo `dev`. Isso torna nosso ambiente de produção:
-   **Mais Leve:** Menos pacotes para baixar e instalar.
-   **Mais Rápido:** O tempo de setup do pipeline é reduzido.
-   **Mais Seguro:** Menos código de terceiros significa uma menor superfície de ataque.

---

## 5. Resumo dos Comandos Essenciais

| Comando | Descrição |
| `uv venv` | Cria o ambiente virtual (`.venv`) para o projeto. |
| `source .venv/bin/activate` | Ativa o ambiente virtual (macOS/Linux). |
| `uv pip sync pyproject.toml` | Instala **todas** as dependências (produção + dev) no ambiente. |
| `uv pip sync pyproject.toml --no-dev` | Instala **apenas** as dependências de produção. (Para CI/CD). |
| `uv add <pacote>` | Adiciona um novo pacote de produção ao `pyproject.toml`. |
| `uv add <pacote> --dev` | Adiciona um novo pacote de desenvolvimento ao `pyproject.toml`. |
| `uv remove <pacote>` | Remove um pacote do `pyproject.toml` e do ambiente. |
| `uv run <comando>` | Executa um comando dentro do ambiente virtual do projeto. |
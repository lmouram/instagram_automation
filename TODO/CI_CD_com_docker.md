#### 1. Identificação do Objetivo Central

O objetivo central é criar uma **solução de CI/CD profissional e robusta** que automatize a construção e execução do ambiente da aplicação. Esta solução deve garantir que **todas** as dependências — tanto pacotes Python (via `uv`) quanto binários de sistema (navegadores do Playwright) — estejam corretamente instaladas e configuradas antes da execução do script, eliminando o erro `Executable doesn't exist`.

#### 2. Pensando no Passo a Passo

1.  **Diagnóstico do Problema:** O erro acontece porque o comando `pip install playwright` (ou `uv add playwright`) instala apenas a biblioteca Python, um "controle remoto". Os navegadores que ela controla (Chromium, Firefox, WebKit) são downloads separados. O comando `playwright install` é o que baixa e instala esses navegadores em um local esperado. A solução de CI/CD deve automatizar a execução de **ambos** os passos de instalação.

2.  **A Abordagem Profissional vs. A Abordagem Frágil:**
    *   **Frágil:** Conectar-se a um servidor de produção via SSH e executar `pip install ...` e `playwright install` manualmente. Isso não é repetível, é propenso a erros e não escala.
    *   **Profissional:** Usar **Containerização (Docker)**. Um contêiner empacota a aplicação, suas dependências Python e suas dependências de sistema em uma única unidade imutável e portátil. Isso resolve o clássico problema de "funciona na minha máquina, mas não em produção".

3.  **A Solução de Arquitetura: Docker + GitHub Actions:**
    *   **`Dockerfile` (A Receita do Ambiente):** Criaremos um `Dockerfile` que define, passo a passo, como construir a imagem do nosso contêiner. A melhor prática aqui é usar a **imagem base oficial do Playwright**, pois ela já vem com todas as dependências de sistema complexas e os navegadores pré-instalados, economizando tempo e evitando problemas.
    *   **`GitHub Actions Workflow` (A Automação):** Criaremos um workflow em YAML que será acionado (ex: em um `push` para a branch `main`). Este workflow irá:
        1.  Fazer o checkout do código.
        2.  Construir a imagem Docker usando nosso `Dockerfile`.
        3.  (Opcional, mas recomendado) Enviar a imagem para um registro de contêineres (como GitHub Container Registry ou Docker Hub).
        4.  Executar o contêiner, passando os segredos (como a API key do Gemini) de forma segura e os argumentos de linha de comando (`--run-id`, etc.).

#### 3. Execução: O Plano de Implementação da Solução de CI/CD

Aqui está o conteúdo completo dos arquivos que você precisa criar ou modificar.

---

### Parte 1: O `Dockerfile` - A Receita do seu Ambiente de Produção

Este é o arquivo mais importante. Ele define o ambiente de execução da sua aplicação.

**Ação:** Crie um arquivo chamado `Dockerfile` na raiz do seu projeto.

**Conteúdo Completo do `Dockerfile`:**
```dockerfile
# Dockerfile

# -----------------------------------------------------------------------------
# Etapa 1: Imagem Base
# -----------------------------------------------------------------------------
# Usamos a imagem oficial do Playwright com Python.
# Isso é CRÍTICO: ela já vem com os navegadores (Chromium, etc.) e todas as
# dependências de sistema (libs gráficas, fontes) pré-instaladas,
# o que resolve 100% do erro "Executable doesn't exist".
# Escolha uma versão específica para builds reprodutíveis.
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# -----------------------------------------------------------------------------
# Etapa 2: Configuração do Ambiente e Dependências Python
# -----------------------------------------------------------------------------
# Define o diretório de trabalho dentro do contêiner.
WORKDIR /app

# Instala o 'uv', nosso gerenciador de pacotes.
# Usamos um comando separado para que esta camada seja cacheada pelo Docker
# se não houver mudanças nos gerenciadores de pacotes.
RUN pip install uv

# Copia apenas o arquivo de definição de dependências primeiro.
# Isso aproveita o cache de camadas do Docker: se o pyproject.toml não mudar,
# o Docker não irá reinstalar as dependências, acelerando o build.
COPY pyproject.toml .

# Instala as dependências de produção usando uv.
# A flag --no-dev garante que pacotes de desenvolvimento (ex: pytest) não
# sejam instalados na imagem final, mantendo-a mais leve e segura.
RUN uv pip sync pyproject.toml --no-dev

# -----------------------------------------------------------------------------
# Etapa 3: Copiar o Código da Aplicação e Definir Execução
# -----------------------------------------------------------------------------
# Agora, copia todo o resto do código da aplicação para o contêiner.
COPY . .

# Define o comando padrão que será executado quando o contêiner iniciar.
# O script a ser executado e seus argumentos serão passados na linha de comando
# do `docker run`, sobrescrevendo este CMD se necessário.
# Ex: `docker run <imagem> python scripts/run_orchestrator.py --theme "..."`
ENTRYPOINT ["python"]
```

---

### Parte 2: O Workflow do GitHub Actions - A Automação

Este workflow automatiza o processo de build e execução usando o `Dockerfile`.

**Ação:** Crie o diretório `.github/workflows/` na raiz do seu projeto, e dentro dele, crie um arquivo chamado `run_orchestrator.yml`.

**Conteúdo Completo de `.github/workflows/run_orchestrator.yml`:**
```yaml
# .github/workflows/run_orchestrator.yml

name: 'Run Instagram Post Orchestrator'

on:
  # Permite acionar este workflow manualmente a partir da interface do GitHub
  workflow_dispatch:
    inputs:
      workflow_name:
        description: 'Nome do workflow a executar (ex: create_post_from_scratch)'
        required: true
        default: 'create_post_from_scratch'
      run_id:
        description: 'ID de uma execução para retomar (deixe em branco para iniciar uma nova)'
        required: false
      theme:
        description: 'Tema para uma nova execução (requerido se run_id estiver em branco)'
        required: false
        default: 'Inteligência Artificial em 2024'

jobs:
  run-in-docker:
    runs-on: ubuntu-latest
    
    steps:
      - name: '1. Checkout Repository'
        uses: actions/checkout@v4

      - name: '2. Create .env file from Secrets'
        run: |
          echo "GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}" > .env
        # IMPORTANTE: Adicione a secret GEMINI_API_KEY nas configurações do
        # seu repositório no GitHub (Settings > Secrets and variables > Actions).

      - name: '3. Build Docker Image'
        run: |
          docker build -t instagram-automation-app .
        # O `-t instagram-automation-app` dá um nome à nossa imagem.

      - name: '4. Run Orchestrator inside Docker'
        run: |
          # Prepara os argumentos da linha de comando
          ARGS="--workflow-name ${{ github.event.inputs.workflow_name }}"
          if [ -n "${{ github.event.inputs.run_id }}" ]; then
            ARGS="$ARGS --run-id ${{ github.event.inputs.run_id }}"
          else
            ARGS="$ARGS --theme '${{ github.event.inputs.theme }}'"
          fi

          # Executa o contêiner
          # O comando `docker run` tem várias partes importantes:
          # --rm: Remove o contêiner após a execução, para não acumular lixo.
          # --env-file .env: Carrega as variáveis de ambiente (nossos segredos) para dentro do contêiner.
          # -v $(pwd)/states:/app/states: Monta o diretório 'states' local para dentro do contêiner.
          #   Isso garante que os arquivos de estado gerados sejam persistidos na máquina do runner
          #   e possam ser inspecionados ou usados em etapas futuras.
          # instagram-automation-app: O nome da imagem que construímos.
          # scripts/run_orchestrator.py $ARGS: O comando e os argumentos a serem executados.
          docker run --rm --env-file .env -v $(pwd)/states:/app/states instagram-automation-app scripts/run_orchestrator.py $ARGS
```

### Por que esta solução é profissional?

1.  **Repetibilidade e Consistência:** Qualquer pessoa da equipe (ou o próprio sistema de CI) pode construir e executar o `Dockerfile` e obterá **exatamente o mesmo ambiente**, com as mesmas versões de Python, `uv`, bibliotecas e, crucialmente, os mesmos navegadores do Playwright.
2.  **Isolamento:** O contêiner encapsula tudo. Você não precisa se preocupar com as bibliotecas de sistema (`libnss3`, `libatk-1.0-0`, etc.) que o Chromium precisa, porque a imagem base oficial do Playwright já cuidou disso.
3.  **Eficiência:** O uso de cache de camadas do Docker no `Dockerfile` acelera significativamente os builds subsequentes se as dependências não mudarem.
4.  **Segurança:** O workflow do GitHub Actions mostra como injetar segredos (API keys) no contêiner de forma segura usando o gerenciamento de segredos do GitHub, em vez de deixá-los no código.
5.  **Pronto para Escalar:** Embora este workflow execute em um runner do GitHub, a imagem Docker que ele constrói pode ser enviada para qualquer registro (GHCR, Docker Hub, ECR) e executada em qualquer plataforma de orquestração de contêineres (como Kubernetes ou AWS ECS) para escalar a execução dos seus workflows.
/docs/arquitetura.md

# Documentação da Arquitetura de Software: `instagram-automation`

## 1. Visão Geral e Princípios Fundamentais

Este documento detalha a arquitetura da aplicação `instagram-automation`. O objetivo é servir como um guia definitivo para desenvolvedores e modelos de linguagem (LLMs) que precisem entender, manter ou estender o sistema.

A aplicação foi projetada sobre três pilares fundamentais:

1.  **Arquitetura Hexagonal (Portas e Adaptadores):** O núcleo da aplicação, contendo a lógica de negócio, é completamente isolado de preocupações externas como bancos de dados, APIs de IA, e interfaces de usuário. Isso garante máxima testabilidade e flexibilidade tecnológica.
2.  **Paradigma Híbrido (Funcional + OO):** A lógica de negócio (`casos de uso`, `orquestradores`) é implementada primariamente com funções puras, que são fáceis de entender e testar. A Orientação a Objetos é usada pragmaticamente para representar o estado (`entidades`) e para implementar os adaptadores.
3.  **Princípios SOLID:** Os princípios de design SOLID são aplicados rigorosamente para garantir que o sistema seja robusto, manutenível e escalável. O mais importante para nós é o **Princípio da Inversão de Dependência (DIP)**, que é a base da Arquitetura Hexagonal.

## 2. A Arquitetura Hexagonal na Prática

Nossa estrutura de diretórios reflete diretamente a Arquitetura Hexagonal.

```
+---------------------------------------------------------------------------------+
|                                 Driving Adapters                                |
| (Ex: scripts/run_orchestrator.py, streamlit_app.py, GitHub Actions)             |
+---------------------------------/------------------\--------------------------+
                                  |                  |
                                  v                  v
+---------------------------------------------------------------------------------+
|                                     Ports                                       |
| (Contratos de Entrada, ex: interfaces que os Casos de Uso/Orquestradores expõem)|
+====================================[ CORE ]=====================================+
|                                                                                 |
|   +---------------------------+       +-------------------------------------+   |
|   | core/application          |------>| core/domain                         |   |
|   | (Comportamento)           |       | (Estado e Regras de Negócio Puras)  |   |
|   | - Orquestradores          |       | - Entidades (Post, WorkflowRun)     |   |
|   | - Casos de Uso            |       | - Enums (PostStatus, WorkflowStatus)|   |
|   +---------------------------+       +-------------------------------------+   |
|                 |                                                             |
+=================|===============================================================+
                  |
                  v
+---------------------------------------------------------------------------------+
|                                     Ports                                       |
| (Contratos de Saída, ex: WorkflowRepositoryPort, ContentGeneratorPort)          |
+---------------------------------\------------------/--------------------------+
                                  |                  |
                                  v                  v
+---------------------------------------------------------------------------------+
|                                 Driven Adapters                                 |
| (Ex: FileWorkflowRepository, GeminiAdapter, SupabasePostRepository)             |
+---------------------------------------------------------------------------------+
```

-   **`core` (O Hexágono):** O coração da aplicação. Não conhece nada sobre o mundo exterior.
    -   **`core/domain`**: Define as estruturas de dados (`WorkflowRun`, `Post`) e as regras de negócio. É o "o quê".
    -   **`core/application`**: Orquestra as entidades do domínio para executar tarefas. É o "como" (em termos de negócio).
-   **`ports` (As Portas):** São as interfaces (contratos `ABC`) que definem como o `core` interage com o exterior. O `core` depende *apenas* destas abstrações.
-   **`adapters` (Os Adaptadores):** São as implementações concretas das portas. Eles traduzem as requisições do `core` para tecnologias específicas (ex: uma chamada de `workflow_repo.save()` vira uma escrita de arquivo JSON).

## 3. A Hierarquia na Camada de Aplicação

A principal inovação em nossa arquitetura é a clara separação de responsabilidades dentro da camada `core/application`. Nós não temos apenas "casos de uso"; temos uma hierarquia de lógica de negócio.

Pense nisso como uma oficina:
-   **Casos de Uso são as Ferramentas:** Uma furadeira, uma chave de fenda.
-   **Orquestradores são os Projetos/Plantas:** A planta para construir uma cadeira.
-   **Driving Adapters são os Operários:** A pessoa que pega a planta e usa as ferramentas para construir a cadeira.

### 3.1. Casos de Uso (`core/application/use_cases`)

-   **Definição:** Uma unidade de trabalho **atômica, idempotente e reutilizável**. Representa uma única capacidade de negócio.
-   **Exemplo:** `create_dossier_use_case`. Sua única responsabilidade é gerar um dossiê. Ele não sabe *por que* o dossiê está sendo gerado ou o que acontecerá depois.
-   **Características Chave:**
    -   **Idempotência:** Graças ao `StateRepositoryPort`, se um caso de uso for chamado múltiplas vezes com a mesma `idempotency_key`, ele não re-executará a lógica custosa (como chamar uma API). Ele simplesmente retorna o resultado salvo.
    -   **Reutilizável:** O mesmo `create_dossier_use_case` pode ser usado por múltiplos orquestradores diferentes no futuro.
    -   **Focado:** Lida com o estado de sua *própria* execução (estado atômico), mas não com o estado do processo de negócio maior.

### 3.2. Orquestradores (`core/application/orchestrators`)

-   **Definição:** Um caso de uso de nível superior que funciona como uma **máquina de estados**. Ele compõe múltiplos casos de uso e lógica de negócio para executar um processo de ponta a ponta.
-   **Exemplo:** `create_post_from_scratch_orchestrator`.
-   **Características Chave:**
    -   **Gerencia o Workflow:** É o único responsável por ler e modificar a entidade `WorkflowRun`. Ele controla o `current_step`, o `status`, e armazena os resultados das etapas no `state_data`.
    -   **Compõe Casos de Uso:** Ele não implementa a lógica de baixo nível. Em vez disso, ele **invoca** os casos de uso. Na Etapa "start", ele chama `create_dossier_use_case`.
    -   **Resiliente:** Contém a lógica de `try/except` para tratar falhas nas etapas, atualizar o `WorkflowRun` com informações de erro e calcular quando uma retentativa deve ocorrer.

### 3.3. Driving Adapters (`scripts/`)

-   **Definição:** O ponto de entrada que inicia e gerencia o ciclo de vida de um orquestrador.
-   **Exemplo:** `scripts/run_orchestrator.py`.
-   **Ciclo de Vida de Execução:**
    1.  **Inicialização (Composition Root):** Instancia todos os adaptadores concretos (`FileWorkflowRepository`, `GeminiAdapter`, etc.).
    2.  **Criação/Carregamento do Workflow:** Interage com o `WorkflowRepositoryPort` para criar uma nova `WorkflowRun` ou carregar uma existente.
    3.  **Invocação do Orquestrador:** Chama a função do orquestrador, passando a `WorkflowRun` e todas as dependências (portas) necessárias.
    4.  **Persistência do Resultado:** Recebe de volta a `WorkflowRun` atualizada do orquestrador e chama o `workflow_repo.update()` para salvar o estado final do processo.

## 4. Estratégia de Persistência de Estado Dupla

Para suportar esta arquitetura, utilizamos dois tipos de persistência, cada um com sua própria Porta e Adaptador:

1.  **Repositório de Workflow (`WorkflowRepositoryPort`):**
    -   **Responsabilidade:** Persistir a entidade `WorkflowRun`, que representa o **estado macro do processo**.
    -   **Implementação:** `FileWorkflowRepository`.
    -   **Estrutura:** `states/<workflow_name>/<run_id>/workflow_state.json`.

2.  **Repositório de Estado Atômico (`StateRepositoryPort`):**
    -   **Responsabilidade:** Persistir os **artefatos ou resultados de etapas individuais e idempotentes**. Atua como uma camada de cache.
    -   **Implementação:** `FileStateRepository`.
    -   **Estrutura:** `states/<workflow_name>/<run_id>/atomic_states/<step_key_sanitizada>.json`.

Essa separação é crucial. O estado do workflow é sobre *progresso*, enquanto o estado atômico é sobre *resultados*.

## 5. Guia para Futuros Desenvolvimentos

Para adicionar novas funcionalidades, siga estes padrões para manter a integridade da arquitetura.

### Cenário A: Adicionar uma Nova Etapa ao Orquestrador `create_post_from_scratch`

Suponha que queremos adicionar uma etapa para gerar o texto do post a partir do dossiê.

1.  **Criar o Novo Caso de Uso:**
    *   Crie `src/core/application/use_cases/generate_post_text_use_case.py`.
    *   Esta função receberá o `dossier` como input e as portas `ContentGeneratorPort` e `StateRepositoryPort`.
    *   Ela será idempotente, salvando seu resultado (o texto do post) no `StateRepository`.

2.  **Atualizar o Orquestrador:**
    *   Em `src/core/application/orchestrators/create_post_from_scratch.py`, adicione um novo bloco `elif`:
        ```python
        # ...
        elif run.current_step == "dossier_created":
            logger.info("Executando etapa 'dossier_created': Geração do texto do post.")
            context = RunContext(workflow_name=run.workflow_name, run_id=run.run_id)
            step_key = "generate_post_text"
            
            post_text = await generate_post_text_use_case(
                dossier=run.state_data["dossier_content"],
                context=context,
                step_key=step_key,
                content_generator=content_generator,
                state_repo=state_repo
            )
            
            run.state_data["post_text_content"] = post_text
            run.current_step = "post_text_created"
            logger.info("Etapa 'dossier_created' concluída.")
        # ...
        ```
3.  **Atualizar o Driving Adapter:**
    *   O `scripts/run_orchestrator.py` precisará injetar as dependências extras que o `generate_post_text_use_case` possa precisar.

### Cenário B: Adicionar um Orquestrador Completamente Novo

Suponha um workflow que "revisa e melhora um post existente".

1.  **Definir Entradas:** O `payload` do novo `WorkflowRun` pode ser `{"post_id": "..."}`.
2.  **Criar os Casos de Uso Necessários:** Ex: `get_post_by_id_use_case`, `analyze_text_for_improvement_use_case`.
3.  **Criar o Novo Orquestrador:**
    *   Crie `src/core/application/orchestrators/improve_existing_post_orchestrator.py`.
    *   Implemente sua própria máquina de estados, chamando os casos de uso relevantes.
4.  **Registrar no Driving Adapter:**
    *   Em `scripts/run_orchestrator.py`, importe o novo orquestrador e adicione-o ao dicionário `ORCHESTRATORS`.
    *   Adicione os argumentos de linha de comando necessários (ex: `--post-id`).
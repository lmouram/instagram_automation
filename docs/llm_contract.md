# Documentação da Arquitetura de Prompts e IA

## 1. Visão Geral e Filosofia

Este documento detalha a arquitetura do subsistema de Inteligência Artificial da aplicação, focada no gerenciamento, versionamento e execução de prompts de Large Language Models (LLMs).

A filosofia central deste design é a estrita aplicação do **Princípio da Responsabilidade Única (SRP)** e do **Princípio da Inversão de Dependência (DIP)**:

1.  **Prompts e Schemas são Lógica de Negócio:** O *quê* pedir a uma IA (o texto do prompt, a estrutura da resposta, as ferramentas a serem usadas) é uma decisão de negócio e, portanto, pertence à **Camada de Aplicação**.
2.  **Adaptadores de IA são Infraestrutura Pura:** O *como* executar um pedido a uma IA (chamar a API do Gemini, lidar com autenticação, fazer retentativas) é um detalhe de infraestrutura e pertence à **Camada de Adaptadores**.

Esta separação garante que nossa lógica de negócio seja agnóstica à tecnologia de IA subjacente. Podemos trocar o Gemini pelo OpenAI amanhã apenas escrevendo um novo adaptador, sem alterar uma única linha da nossa lógica de prompts.

## 2. Os Componentes Fundamentais da Arquitetura

A arquitetura é composta por cinco componentes principais que trabalham em conjunto:

### 2.1. O Contrato de LLM (`LLMContract`)

Este é o coração do desacoplamento. É um Data Transfer Object (DTO) que serve como a "linguagem" universal entre a camada de aplicação e a porta do gerador de conteúdo. Ele encapsula tudo o que é necessário para uma chamada de IA.

-   **Localização:** `src/core/application/contracts.py`
-   **Estrutura:**
    -   `prompt_name`, `prompt_version`: Metadados para governança e observabilidade.
    -   `prompt_template`: A string do prompt com placeholders (ex: `{dossier}`).
    -   `input_variables`: Um dicionário com os valores para preencher o template.
    -   `tools`: Uma lista genérica de capacidades (ex: `["web_search"]`).
    -   `response_format`: O formato esperado (`"json"` ou `"text"`).
    -   `output_schema`: O schema Pydantic para validar a resposta, se for JSON.
    -   `vendor_overrides`: Um "escape hatch" para parâmetros específicos do provedor (ex: `temperature`).

### 2.2. O Pacote de Prompts (`src/core/application/prompts/`)

Este pacote é o "cérebro" da nossa lógica de IA. Ele contém as "receitas" para cada capacidade de negócio que depende de um LLM.

-   **Estrutura:** Organizado por capacidade, com versionamento explícito.
    ```
    prompts/
    └── copywriting/
        ├── __init__.py
        └── v1_0.py
    └── dossier/
        ├── __init__.py
        └── v1_0.py
    ```
-   **Conteúdo de um Módulo de Versão (ex: `v1_0.py`):**
    1.  **Schema de Saída:** Uma classe Pydantic que define a estrutura JSON da resposta.
    2.  **Função Factory `get_contract(...)`:** Uma função que recebe os dados de negócio (ex: `dossier`) e retorna um `LLMContract` totalmente configurado.

### 2.3. O Registro de Prompts (`Prompt Registry`)

É a fachada para o pacote de prompts. Ele abstrai a localização e o carregamento dos contratos.

-   **Localização:** `src/core/application/prompts/registry.py`
-   **Função Principal:** `get_prompt_contract(prompt_name: str, version: str = "latest", **kwargs)`
-   **Funcionamento:** Usa importação dinâmica para encontrar e carregar o módulo de prompt correto com base no nome e versão, e então chama sua função `get_contract` com os `kwargs` fornecidos.

### 2.4. A Porta Genérica (`ContentGeneratorPort`)

O contrato abstrato se torna extremamente simples e poderoso.

-   **Localização:** `src/ports/content_generator.py`
-   **Método Único:** `async def generate(self, contract: LLMContract) -> Dict[str, Any]`
-   **Responsabilidade:** Define que qualquer gerador de conteúdo deve ser capaz de executar um `LLMContract` e retornar um dicionário validado.

### 2.5. O Adaptador Genérico (`GeminiAdapter`)

O adaptador se torna um "motor de execução" puro, sem nenhuma lógica de negócio.

-   **Localização:** `src/adapters/llm/gemini_adapter.py`
-   **Responsabilidade:**
    1.  Receber um `LLMContract`.
    2.  Renderizar o template do prompt.
    3.  Traduzir as capacidades genéricas do contrato (ex: `"web_search"`) para as ferramentas específicas do Gemini (`GoogleSearch()`).
    4.  Chamar a API do Gemini com a configuração apropriada.
    5.  Executar o **Pipeline de Parsing Resiliente**.
    6.  Validar a resposta JSON contra o `output_schema` do contrato.
    7.  Retornar um dicionário com os dados validados.

## 3. O Fluxo de Execução Completo

A interação entre os componentes segue um fluxo claro e desacoplado:

1.  **Orquestrador Inicia:** O `create_post_from_scratch_orchestrator` decide que precisa de uma "copy".
2.  **Caso de Uso é Chamado:** O orquestrador chama `copywriter_use_case`, passando o `dossier` e o `RunContext`.
3.  **Caso de Uso Consulta o Registro:** O `copywriter_use_case` chama `get_prompt_contract(prompt_name="copywriting", dossier=dossier)`.
4.  **Registro Carrega o Contrato:** O `Prompt Registry` encontra o módulo `prompts/copywriting/v1_0.py`, importa-o e chama sua função `get_contract`, que retorna o `LLMContract` preenchido.
5.  **Caso de Uso Invoca a Porta:** O `copywriter_use_case` chama `await content_generator.generate(contract)`, onde `content_generator` é a instância do `GeminiAdapter` injetada.
6.  **Adaptador Executa:** O `GeminiAdapter` recebe o contrato, executa toda a lógica de chamada à API, parsing e validação.
7.  **Resultado Retorna:** O `GeminiAdapter` retorna um `dict` com `{"title": "...", "description": "..."}`.
8.  **Caso de Uso Finaliza:** O `copywriter_use_case` recebe o dicionário, salva-o no `StateRepository` e o retorna ao orquestrador.

## 4. O Pipeline de Parsing Resiliente

Reconhecendo que LLMs podem falhar ao gerar JSONs perfeitos, o `GeminiAdapter` implementa uma estratégia de auto-reparo:

1.  **Tentativa de Parse Inicial:** Após receber a resposta do LLM, o adaptador tenta extrair e parsear o JSON.
2.  **Falha no Parse:** Se a extração ou o parse falharem, o adaptador **não desiste**.
3.  **Chamada de Reparo:** Ele invoca um segundo LLM (um modelo mais rápido e barato, como o `gemini-1.5-flash`) com um prompt específico: "Corrija este JSON quebrado. Responda apenas com o JSON corrigido."
4.  **Tentativa de Parse Final:** O adaptador tenta parsear a resposta da chamada de reparo.
5.  **Erro Final:** Se mesmo após o reparo o JSON for inválido, uma `ParsingError` é levantada, e a execução da etapa falha de forma controlada.

Esta abordagem aumenta drasticamente a taxa de sucesso das operações que dependem de saídas estruturadas.

## 5. Guia para Adicionar uma Nova Capacidade de IA

Para adicionar uma nova funcionalidade, como um **"Gerador de Hashtags"**, siga estes passos:

**Passo 1: Criar o Módulo de Prompt**
Crie o diretório `src/core/application/prompts/hashtag_generator/` e o arquivo `v1_0.py` dentro dele.

**Passo 2: Definir o Schema e o Contrato em `v1_0.py`**
```python
# src/core/application/prompts/hashtag_generator/v1_0.py
from pydantic import BaseModel, Field
from typing import List
from src.core.application.contracts import LLMContract

class HashtagOutput(BaseModel):
    hashtags: List[str] = Field(..., max_length=7)

def get_contract(text_content: str) -> LLMContract:
    prompt_template = "Analise o seguinte texto e gere 7 hashtags relevantes...\n\nTexto: {text_content}"
    return LLMContract(
        prompt_name="hashtag_generator",
        prompt_version="1.0",
        prompt_template=prompt_template,
        output_schema=HashtagOutput,
        input_variables={"text_content": text_content}
    )
```

**Passo 3: Criar o `__init__.py` do Pacote**
```python
# src/core/application/prompts/hashtag_generator/__init__.py
from .v1_0 import get_contract, HashtagOutput
__all__ = ["get_contract", "HashtagOutput"]
```

**Passo 4: Criar o Novo Caso de Uso**
```python
# src/core/application/use_cases/generate_hashtags_use_case.py
from src.core.application.prompts import get_prompt_contract
# ...
async def generate_hashtags_use_case(...) -> List[str]:
    # ... Lógica de idempotência ...
    contract = get_prompt_contract("hashtag_generator", text_content=text)
    result = await content_generator.generate(contract)
    # ... Salvar estado e retornar result["hashtags"] ...
```

**Passo 5: Integrar no Orquestrador**
Adicione uma nova etapa no orquestrador relevante para chamar o `generate_hashtags_use_case`.

Seguindo este padrão, o `GeminiAdapter` não precisa ser modificado, e a nova capacidade é adicionada de forma limpa, organizada e testável.
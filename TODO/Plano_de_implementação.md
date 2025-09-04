
**Fase 1: Implementação da Máquina de Estado**

Esta será uma nova ferramenta utilitária, inspirada no `artifacts.py`.

*   **1.1. Estrutura de Diretórios:**
    *   Criar o diretório `states/` na raiz do projeto. Adicioná-lo ao `.gitignore`.
    *   Criar o diretório `scripts/dev/` para os novos scripts.
    *   Criar um novo módulo utilitário: `src/utils/state_manager.py`.

*   **1.2. Implementar `src/utils/state_manager.py`:**
    *   Inspirado no `artifacts.py`, este módulo irá abstrair a lógica de I/O para os arquivos de estado.
    *   **Classe `StateManager`:**
        *   `__init__(self, script_name: str)`: O construtor receberá o nome do script (ex: "generate_dossier"). Isso definirá a subpasta em `states/` (ex: `states/generate_dossier/`).
        *   `_get_next_run_id() -> int`: Um método privado para encontrar o próximo ID sequencial, olhando os arquivos existentes na pasta do script (ex: `1.json`, `2.json` -> retorna `3`).
        *   `load_state(self, run_id: int) -> Dict`: Carrega um arquivo de estado JSON específico (ex: `states/generate_dossier/2.json`).
        *   `save_state(self, run_id: int, state_data: Dict) -> None`: Salva (ou sobrescreve) o dicionário de estado em um arquivo JSON.
        *   `create_new_run(self, initial_state: Dict) -> int`: Cria um novo estado de execução. Ele chama `_get_next_run_id()`, adiciona o `run_id` ao `initial_state`, e salva o arquivo JSON inicial, retornando o `run_id` para o script.

**Fase 2: Implementação do Script `generate_dossier.py`**

Este será um novo **Driving Adapter** não-interativo.

*   **2.1. Criar o Arquivo:** `scripts/dev/generate_dossier.py`.

*   **2.2. Lógica do Script:**
    *   **Argumentos de Linha de Comando:** Usará `argparse` para receber:
        *   `--theme` (obrigatório, a menos que `--run-id` seja fornecido): O tema para o dossiê.
        *   `--run-id` (opcional): O ID de uma execução existente para retomar.
    *   **Inicialização:**
        *   Configurar o logger.
        *   Instanciar o `StateManager(script_name="generate_dossier")`.
        *   Instanciar o `GeminiAdapter` (que precisaremos modificar).
    *   **Fluxo Principal (`main`):**
        *   **Carregar ou Criar Estado:**
            *   Se `--run-id` for fornecido, chamar `state_manager.load_state(run_id)`.
            *   Se `--theme` for fornecido, criar um `initial_state` e chamar `state_manager.create_new_run(initial_state)`.
            *   Se nenhum for fornecido, encerrar com erro.
        *   **Máquina de Estado (Lógica de Retomada):**
            *   Verificar o dicionário de estado carregado/criado.
            *   `if "dossie" not in state or not state["dossie"]:`: Se o dossiê ainda não foi gerado...
                *   Logar "Gerando dossiê para o tema: ...".
                *   Chamar o `gemini_adapter.generate_dossier(theme=state["theme"])`.
                *   Atualizar o dicionário de estado: `state["dossie"] = result_dossier`.
                *   Salvar o estado atualizado: `state_manager.save_state(run_id, state)`.
            *   `else:`:
                *   Logar "Dossiê já existe nesta execução. Pulando a geração."
        *   **Saída:**
            *   Imprimir o dossiê final (`state["dossie"]`) no console.

**Fase 3: Refatoração do `GeminiAdapter` para Suportar a Pesquisa**

Esta é a parte que deve seguir a **FONTE ÚNICA DA VERDADE** rigorosamente.

*   **3.1. Modificar `src/adapters/llm/gemini_adapter.py`:**
    *   Manter o método `generate_text_for_post` como está.
    *   **Adicionar um Novo Método:** `async def generate_dossier(self, theme: str) -> str`:
        *   Este método implementará a lógica de chamada ao Gemini com a ferramenta de pesquisa ativada.
        *   **Prompt:** Usará o prompt exato da `FONTE ÚNICA DA VERDADE` (`generate_context_prompt`).
        *   **Chamada à API:** A chamada a `self._client.models.generate_content` seguirá o padrão do exemplo:
            *   `model`: Usar o `gemini-2.5-pro` (ou `flash` conforme o exemplo).
            *   `contents`: Construído com `self._genai_types.Part.from_text(text=prompt)`.
            *   `config`: Criar um objeto `GenerateContentConfig` exatamente como no exemplo.
                *   `tools = [self._genai_types.Tool(google_search=self._genai_types.GoogleSearch())]`
                *   `config_dict["tools"] = tools`
                *   **Crucial:** O exemplo usa `response_schema` para forçar uma saída JSON. Nosso prompt também exige uma saída JSON. Então, vamos criar um `Pydantic BaseModel` para o schema do dossiê (com `context_summary_markdown` e `search_queries_used`) e passá-lo para a chamada da API, exatamente como o exemplo faz.
        *   **Parsing da Resposta:**
            *   A resposta do Gemini será um objeto JSON. Usaremos a lógica de `write_resp.parsed_json` do exemplo para extrair os dados.
            *   Se o `parsed_json` existir, extrairemos o valor da chave `context_summary_markdown`.
            *   Implementar a mesma lógica de retentativas e tratamento de erros do exemplo.
            *   Se tudo falhar, levantar `GeminiAPIError`.

### **Resumo da Estrutura de Arquivos Resultante**

```
instagram_automation/
├── scripts/
│   └── dev/
│       ├── __init__.py
│       └── generate_dossier.py   # <--- NOVO SCRIPT
│   └── run_publisher.py
├── src/
│   ├── adapters/
│   │   └── llm/
│   │       └── gemini_adapter.py # <--- MODIFICADO
│   └── utils/
│       ├── __init__.py
│       ├── context_builder.py
│       ├── resilience.py
│       └── state_manager.py      # <--- NOVO MÓDULO
├── states/                       # <--- NOVO DIRETÓRIO (no .gitignore)
│   └── generate_dossier/
│       ├── 1.json
│       └── 2.json
└── .gitignore                    # <--- MODIFICADO para incluir /states/
```

Este plano cria um subsistema robusto e reutilizável. A máquina de estado pode ser usada por futuros scripts, e o `GeminiAdapter` agora é mais poderoso, suportando tanto a geração de texto simples quanto a pesquisa complexa para a criação de dossiês.

Usando o PRINCÍPIO_INEGOCIÁVEL e o PRINCÍPIOS_DE_PROJETO crie o **CONTEÚDO COMPLETO E DETALHADAMENTE DOCUMENTADO** de src/core/domain/entities.py


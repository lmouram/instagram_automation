# src/adapters/__init__.py

"""
Pacote de Adaptadores.

Este pacote é o coração da camada de infraestrutura na Arquitetura Hexagonal.
Ele contém todas as implementações concretas que conectam o núcleo (core)
agnóstico da aplicação com as tecnologias do mundo real.

O propósito dos adaptadores é "adaptar" as interfaces abstratas (definidas em
`src/ports`) para ferramentas e serviços específicos. Eles são a ponte entre
o nosso domínio puro e o mundo exterior.

Esta camada é dividida conceitualmente em dois tipos de adaptadores:

1.  **Driving Adapters (Adaptadores de Condução):**
    - Localização: `adapters/ui`, `streamlit_app.py`, `scripts/`, `.github/workflows/`
    - Responsabilidade: Iniciar uma ação no sistema. Eles "conduzem" a aplicação.
    - Exemplos: Uma interface de usuário (Streamlit), um endpoint de API (Flask),
      um script de linha de comando, um agendador de tarefas (GitHub Actions).
    - Fluxo: Mundo Exterior -> Driving Adapter -> Caso de Uso (Core).

2.  **Driven Adapters (Adaptadores Conduzidos):**
    - Localização: `adapters/persistence`, `adapters/llm`, `adapters/media`, etc.
    - Responsabilidade: Fornecer implementações para serviços que são
      solicitados pelo core da aplicação. Eles são "conduzidos" pelo core.
    - Exemplos: Um cliente de banco de dados (SupabaseAdapter), um cliente de API
      de LLM (GeminiAdapter), um serviço de armazenamento de arquivos
      (SupabaseStorageAdapter).
    - Fluxo: Caso de Uso (Core) -> Porta -> Driven Adapter -> Mundo Exterior.

A existência desta camada garante que o `core` permaneça isolado e testável,
permitindo que qualquer tecnologia externa (banco de dados, API de IA,
framework de UI) possa ser trocada com impacto mínimo, simplesmente
escrevendo um novo adaptador.
"""

# Este arquivo transforma o diretório 'adapters' em um pacote Python.
# As implementações específicas estão nos subpacotes.
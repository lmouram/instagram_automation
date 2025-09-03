# **PLANO DE IMPLEMENTAÇÃO (REVISADO E MELHORADO)**

1.  **Core Domain (`core/domain`):**
    *   Expandir `enums.PostStatus` para incluir `REJEITADO` e `ERRO_PUBLICACAO`.
    *   Adicionar os campos `publish_attempts: int` e `error_message: Optional[str]` à entidade `Post`.
    *   Criar a nova entidade `AuditEvent` para o registro de auditoria.

2.  **Ports (`ports`):**
    *   Criar `ports/storage.py` com a `StoragePort` (contrato para upload de mídia).
    *   Criar `ports/observability.py` com a `ObservabilityPort` (contrato para métricas e eventos).
    *   Criar `ports/audit_repository.py` com a `AuditEventRepositoryPort`.

3.  **Core Application (`core/application`):**
    *   Modificar `PublishScheduledPostsUseCase` para usar `publish_attempts` e atualizar status para `ERRO_PUBLICACAO` em caso de falha.
    *   Modificar `CreatePostUseCase` para orquestrar a geração de mídia, upload (via `StoragePort`) e persistência do post com as URLs da mídia.
    *   Adicionar o novo `RejectPostUseCase`.
    *   Integrar chamadas à `ObservabilityPort` e `AuditEventRepositoryPort` nos casos de uso relevantes.

4.  **Adapters (`adapters`):**
    *   **Persistência:** Implementar o `SupabaseAuditEventRepositoryAdapter`.
    *   **Mídia:** Criar o `SupabaseStorageAdapter` implementando a `StoragePort`.
    *   **Resiliência:** Implementar decoradores de `retry` e `rate_limit` em `src/utils/` e aplicá-los aos adaptadores de API (`llm`, `media`, `social`).
    *   **Observabilidade:** Criar um `LoggingObservabilityAdapter` como implementação inicial.

5.  **Driving Adapters (`streamlit_app.py`, `.github/`):**
    *   Adicionar funcionalidades à UI para rejeitar posts.
    *   Implementar validação de input na camada da UI antes de invocar os casos de uso.

## **ESTRUTURA DE DIRETÓRIOS (VERSÃO 2.0)**

```bash
instagram_automation/
├── .github/
│   └── workflows/
│       └── scheduler.yml
│
├── src/
│   ├── core/
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities.py      # Contém Post, Media, e a NOVA entidade AuditEvent.
│   │   │   └── enums.py         # PostStatus MODIFICADO para incluir REJEITADO, ERRO_PUBLICACAO.
│   │   │
│   │   └── application/
│   │       ├── __init__.py
│   │       └── use_cases.py     # Lógica orquestradora, agora com tratamento de erro e auditoria.
│   │
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── audit_repository.py  # NOVO: Contrato para salvar eventos de auditoria.
│   │   ├── content_generator.py
│   │   ├── media_generator.py
│   │   ├── observability.py     # NOVO: Contrato para métricas e monitoramento.
│   │   ├── post_repository.py
│   │   ├── social_publisher.py
│   │   └── storage.py           # NOVO: Contrato para upload e acesso a arquivos de mídia.
│   │
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   └── gemini_adapter.py      # Aplicar decoradores de resiliência.
│   │   ├── media/
│   │   │   └── google_image_adapter.py # Aplicar decoradores de resiliência.
│   │   ├── observability/
│   │   │   └── logging_adapter.py   # NOVO: Implementação inicial da ObservabilityPort.
│   │   ├── persistence/
│   │   │   ├── supabase_adapter.py    # Implementa PostRepositoryPort e AuditEventRepositoryPort.
│   │   │   └── __init__.py
│   │   ├── social/
│   │   │   └── instagram_adapter.py   # Aplicar decoradores de resiliência e rate limiting.
│   │   ├── storage/
│   │   │   └── supabase_storage_adapter.py # NOVO: Implementação da StoragePort.
│   │   └── ui/
│   │       └── __init__.py
│   │
│   ├── utils/                     # NOVO: Módulo para utilitários cross-cutting.
│   │   └── resilience.py          # NOVO: Contém decoradores de retry e rate limiting.
│   │
│   ├── config.py                # Carrega configurações, com abstração para secret managers.
│   └── logger.py                # Configuração do logger.
│
├── scripts/
│   └── run_publisher.py
│
├── streamlit_app.py             # Responsável pela validação de input da UI.
│
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

1.  **Iniciar a Implementação:** Com o plano validado e refinado, o próximo passo lógico é iniciar a codificação, seguindo a abordagem "de dentro para fora" definida:
    *   **Etapa 1:** Implementar `core/domain` (Entidades e Enums).
    *   **Etapa 2:** Definir todas as interfaces em `ports`.
    *   **Etapa 3:** Implementar `core/application` (Casos de Uso) contra as `ports`.
    *   **Etapa 4:** Começar a desenvolver os `adapters` um por um, começando pelos de persistência e armazenamento.

Usando o PRINCÍPIO_INEGOCIÁVEL e o PRINCÍPIOS_DE_PROJETO crie o **CONTEÚDO COMPLETO E DETALHADAMENTE DOCUMENTADO** de src/core/domain/entities.py


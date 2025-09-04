# src/utils/__init__.py

"""
Pacote de Utilitários.

Este pacote contém módulos com funcionalidades de suporte "cross-cutting",
ou seja, que podem ser utilizadas por diferentes partes da aplicação,
principalmente na camada de adaptadores e orquestradores.

Módulos neste pacote podem incluir:
- Ferramentas de Resiliência: Decoradores para retry, rate limiting, circuit
  breakers, etc. (`resilience.py`).
- Scripts de Desenvolvedor: Ferramentas para auxiliar no desenvolvimento,
  como a geração de arquivos de contexto para LLMs (`context_builder.py`).
- Gerenciamento de Estado: Lógica para persistir o estado de execuções
  (`state_manager.py`).

Apenas as ferramentas destinadas a serem reutilizadas pela aplicação são
exportadas na API pública deste pacote.
"""

# Exporta os decoradores e a função de backoff do módulo de resiliência.
from .resilience import rate_limit_async, retry_async_run, get_next_retry_at
from .state_manager import StateManager, StateNotFoundError, StateManagerError

__all__ = [
    "rate_limit_async",
    "retry_async_run",
    "get_next_retry_at",
    "StateManager",
    "StateNotFoundError",
    "StateManagerError", 
]
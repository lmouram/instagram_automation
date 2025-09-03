# src/utils/__init__.py

"""
Pacote de Utilitários.

Este pacote contém módulos com funcionalidades de suporte "cross-cutting",
ou seja, que podem ser utilizadas por diferentes partes da aplicação,
principalmente na camada de adaptadores.

Módulos neste pacote podem incluir:
- Ferramentas de Resiliência: Decoradores para retry, rate limiting, circuit
  breakers, etc. (`resilience.py`).
- Scripts de Desenvolvedor: Ferramentas para auxiliar no desenvolvimento,
  como a geração de arquivos de contexto para LLMs (`context_builder.py`).

Apenas as ferramentas destinadas a serem reutilizadas pela aplicação são
exportadas na API pública deste pacote. Scripts de desenvolvedor são
destinados à execução direta.
"""

# Exporta apenas os decoradores de resiliência, que são a API pública
# deste pacote para o resto da aplicação.
from .resilience import rate_limit_async, retry_async_run

__all__ = ["retry_async_run", "rate_limit_async"]
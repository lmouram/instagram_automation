# src/adapters/observability/__init__.py

"""
Pacote de Adaptadores de Observabilidade.

Este pacote contém implementações concretas da `ObservabilityPort`.
"""

from .logging_adapter import LoggingObservabilityAdapter

__all__ = ["LoggingObservabilityAdapter"]
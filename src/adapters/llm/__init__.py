# src/adapters/llm/__init__.py

"""
Pacote de Adaptadores de LLM (Large Language Model).

Este pacote contém implementações concretas da `ContentGeneratorPort`,
conectando o core da aplicação a diferentes provedores de IA generativa.
"""

from .gemini_adapter import GeminiAdapter, GeminiAPIError

__all__ = ["GeminiAdapter", "GeminiAPIError"]
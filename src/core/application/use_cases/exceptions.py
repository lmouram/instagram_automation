# src/core/application/exceptions.py

"""
Módulo de Exceções da Camada de Aplicação.

Este arquivo centraliza as exceções customizadas levantadas pelos casos de uso.
Isso permite que os adaptadores de entrada (UI, CLI, etc.) tratem os erros
da lógica de negócio de forma abstrata, sem depender dos erros específicos
da infraestrutura.
"""

class UseCaseError(Exception):
    """Classe base para exceções específicas de casos de uso."""
    pass

class PostCreationError(UseCaseError):
    """Levantada quando a criação de um post falha por qualquer motivo."""
    pass

class PostPublicationError(UseCaseError):
    """Levantada quando a publicação imediata de um post falha."""
    pass

class InvalidPostStateError(UseCaseError):
    """Levantada ao tentar realizar uma operação em um post em estado inválido."""
    pass
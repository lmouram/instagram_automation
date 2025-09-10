# src/adapters/persistence/__init__.py

"""
Pacote de Adaptadores de Persistência.

Este pacote contém implementações concretas das portas de repositório.
"""

from .file_state_repository import FileStateRepository, ArtifactNotFoundError
from .file_workflow_repository import FileWorkflowRepository, ConcurrencyError
from .repositories import SupabasePostRepository, SupabaseAuditEventRepository

__all__ = [
    # Repositórios Supabase
    "SupabasePostRepository", 
    "SupabaseAuditEventRepository",
    # Repositórios baseados em arquivo
    "FileWorkflowRepository",
    "FileStateRepository", # <-- Adicionado
    "ArtifactNotFoundError" # <-- Adicionado
    # Exceções customizadas
    "ConcurrencyError",
]
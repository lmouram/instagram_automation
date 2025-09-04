# src/adapters/persistence/__init__.py

"""
Pacote de Adaptadores de Persistência.

Este pacote contém implementações concretas das portas de repositório,
como PostRepositoryPort e AuditEventRepositoryPort.
"""

from .repositories import SupabasePostRepository, SupabaseAuditEventRepository

__all__ = ["SupabasePostRepository", "SupabaseAuditEventRepository"]
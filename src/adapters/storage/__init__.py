# src/adapters/storage/__init__.py

"""
Pacote de Adaptadores de Armazenamento.

Este pacote contém implementações concretas da `StoragePort`, que lida com
o upload e o acesso a arquivos de mídia.
"""

from .supabase_storage_adapter import SupabaseStorageAdapter

__all__ = ["SupabaseStorageAdapter"]
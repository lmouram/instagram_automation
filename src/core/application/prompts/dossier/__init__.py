# src/core/application/prompts/dossier/__init__.py

"""
Pacote para o prompt de Geração de Dossiê.

Este pacote exporta a função factory `get_contract` da versão mais
relevante do prompt de geração de dossiê.
"""

# Importa a função do arquivo de versão e a torna disponível no nível do pacote.
from .v1_0 import get_contract, DossierOutput

__all__ = ["get_contract", "DossierOutput"]
# src/core/application/registries/__init__.py

"""
Pacote de Registries da Camada de Aplicação.

Este pacote contém módulos que atuam como registros ou "fontes da verdade"
para configurações de negócio, como a estrutura de etapas dos workflows.
"""

# Importa os componentes principais do módulo de registro de etapas.
from .step_registry import StepConfig, WORKFLOW_STEPS

# Define a API pública do pacote.
__all__ = [
    "StepConfig",
    "WORKFLOW_STEPS",
]
# src/core/application/orchestrators/__init__.py

"""
Pacote de Orquestradores de Workflow.

Este pacote contém os casos de uso de mais alto nível da aplicação. Cada
orquestrador é responsável por gerenciar um processo de negócio de ponta a ponta,
que pode envolver múltiplas etapas.

Eles funcionam como máquinas de estado, lendo o estado atual de uma
`WorkflowRun`, executando a lógica apropriada e atualizando o estado para
refletir o progresso. Orquestradores compõem os casos de uso atômicos
(definidos em `src.core.application.use_cases`) para realizar o trabalho.
"""

from .create_post_from_scratch import create_post_from_scratch_orchestrator

__all__ = ["create_post_from_scratch_orchestrator"]
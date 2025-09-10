# src/core/application/registries/step_registry.py

"""
Módulo de Registro de Etapas de Workflow.

Este arquivo atua como uma "fonte da verdade" centralizada que define a
estrutura e a sequência de etapas para cada workflow na aplicação.

Ele mapeia nomes de workflows para um dicionário de suas etapas constituintes,
onde cada etapa é definida por uma configuração (`StepConfig`). Essa abstração
permite que os Driving Adapters (como `run_orchestrator.py`) manipulem as
etapas do workflow (ex: para reexecução) sem precisar conhecer os detalhes da
implementação da máquina de estados do orquestrador.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class StepConfig:
    """
    Configuração imutável que define uma única etapa de um workflow.
    """
    step_key: str
    """
    A chave única usada para persistir o estado atômico desta etapa no
    `StateRepository`. Corresponde ao `step_key` passado para o caso de uso.
    """

    entry_state: str
    """
    O valor de `current_step` na entidade `WorkflowRun` que serve como gatilho
    para a execução desta etapa no orquestrador. É o estado para o qual o
    workflow deve ser "rebobinado" para re-executar esta etapa.
    """


# Mapeamento principal de todos os workflows e suas respectivas etapas
WORKFLOW_STEPS: Dict[str, Dict[str, StepConfig]] = {
    "create_post_from_scratch": {
        # Nome amigável para o usuário -> Configuração da Etapa
        "dossier": StepConfig(
            step_key="create_dossier",
            entry_state="start"
        ),
        "copy": StepConfig(
            step_key="generate_copy",
            entry_state="dossier_created"
        ),
        "create_image": StepConfig(
            step_key="create_image",
            entry_state="copy_created"
        ),
        "edit_image": StepConfig(
            step_key="edit_image",
            entry_state="image_created"
        ),
    }
    # Outros workflows podem ser adicionados aqui no futuro.
    # "outro_workflow": { ... }
}
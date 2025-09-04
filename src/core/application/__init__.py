# src/core/application/__init__.py

"""
Pacote da Camada de Aplicação.

Este pacote contém a lógica de negócio que orquestra as entidades de domínio.
Ele é dividido em dois subpacotes principais:

- `use_cases`: Contém casos de uso atômicos e reutilizáveis que representam
  uma única capacidade de negócio (ex: criar um post, gerar um dossiê).

- `orchestrators`: Contém casos de uso de nível superior que compõem múltiplos
  casos de uso e outras lógicas para executar processos de negócio complexos
  e resilientes (workflows).
"""
# Este __init__.py é intencionalmente deixado sem código para servir como um
# "pacote namespace". As importações devem ser feitas a partir dos subpacotes.
# Ex: from src.core.application.use_cases import create_post_use_case
# Ex: from src.core.application.orchestrators import create_post_from_scratch_orchestrator
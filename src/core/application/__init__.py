# src/core/application/__init__.py

"""
Pacote da Camada de Aplicação.

Este pacote contém a lógica de negócio que orquestra as entidades de domínio.
Ele é dividido nos seguintes subpacotes:

- `contracts`: Define as estruturas de dados (DTOs) que servem como
  contratos internos, como o `LLMContract` e `ThemeContract`.

- `prompts`: Contém as "receitas" para criar `LLMContract`s, encapsulando
  templates de prompt e schemas de resposta.

- `use_cases`: Contém casos de uso atômicos e reutilizáveis que representam
  uma única capacidade de negócio.

- `orchestrators`: Contém casos de uso de nível superior que compõem múltiplos
  casos de uso para executar processos de negócio complexos (workflows).
"""
# Este __init__.py é intencionalmente deixado sem código para servir como um
# "pacote namespace". As importações devem ser feitas a partir dos subpacotes.
# src/core/application/prompts/__init__.py

"""
Pacote de Prompts e Contratos de IA.

Este pacote é o centro nevrálgico da nossa lógica de Inteligência Artificial.
Ele trata os prompts e os schemas de resposta não como simples strings, mas
como **componentes de negócio de primeira classe**.

Cada módulo neste pacote representa uma capacidade específica que a aplicação
espera do LLM (ex: gerar um dossiê, escrever uma copy) e é responsável por:

1.  **Definir o Schema de Saída:** Utilizando Pydantic, define a estrutura
    JSON exata que se espera como resposta do LLM para aquela tarefa.
2.  **Encapsular a Engenharia de Prompt:** Contém o texto do prompt, as
    instruções e a persona que o LLM deve assumir.
3.  **Construir o Contrato:** Fornece uma função "factory" (ex: `get_contract`)
    que monta e retorna um `LLMContract` totalmente configurado, pronto para
    ser passado para a `ContentGeneratorPort`.

Esta abordagem garante:
-   **SRP:** Cada capacidade de IA tem seu próprio módulo.
-   **OCP:** Para adicionar uma nova capacidade, criamos um novo arquivo aqui,
    sem modificar os existentes ou o adaptador de IA.
-   **Clareza e Manutenibilidade:** A lógica de IA para cada tarefa está
    organizada e fácil de encontrar, testar e versionar.
"""

from .registry import get_prompt_contract, PromptNotFoundError

__all__ = ["get_prompt_contract", "PromptNotFoundError"]
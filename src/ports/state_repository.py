# src/ports/state_repository.py

"""
Módulo da Porta do Repositório de Estado Atômico.

Este arquivo define a porta (interface abstrata) para um repositório de
estado genérico, baseado em um sistema de chave-valor. Seu principal propósito
é permitir que os casos de uso persistam e recuperem resultados de operações
específicas de forma idempotente.

Ele atua como uma camada de cache ou de persistência de artefatos para
etapas individuais de um processo, onde a 'chave' é a idempotency_key da
operação.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.core.domain.entities import RunContext



class StateRepositoryPort(ABC):
    """
    Interface abstrata (Porta) para um repositório de estado chave-valor.

    Define um contrato para salvar e carregar dicionários de dados associados
    a uma chave única, permitindo que os casos de uso implementem lógicas de
    cache e idempotência dentro do escopo de uma execução de workflow.
    """

    @abstractmethod
    async def load(self, context: RunContext, key: str) -> Optional[Dict[str, Any]]:
        """
        Carrega os dados associados a uma chave específica, dentro de um contexto de execução.

        Args:
            context (RunContext): O contexto da execução do workflow, informando
                                  em qual "pasta" de execução procurar o estado.
            key (str): A chave única que identifica o estado a ser carregado
                       dentro daquele contexto.

        Returns:
            Optional[Dict[str, Any]]: Um dicionário com os dados do estado,
                                      ou `None` se a chave não for encontrada.
        """
        raise NotImplementedError

    @abstractmethod
    async def save(self, context: RunContext, key: str, data: Dict[str, Any]) -> None:
        """
        Salva (cria ou sobrescreve) os dados associados a uma chave específica,
        dentro de um contexto de execução.

        Args:
            context (RunContext): O contexto da execução do workflow.
            key (str): A chave única para identificar o estado.
            data (Dict[str, Any]): O dicionário de dados a ser salvo.
        """
        raise NotImplementedError
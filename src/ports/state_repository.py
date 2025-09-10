# src/ports/state_repository.py

"""
Módulo da Porta do Repositório de Estado Atômico.

Este arquivo define a porta (interface abstrata) para um repositório de
estado genérico. Seu propósito é permitir que os casos de uso e orquestradores
persistam e recuperem tanto dados estruturados (JSON) quanto artefatos
binários (arquivos) de forma idempotente e co-localizada para uma execução
de workflow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.core.domain.entities import RunContext


class StateRepositoryPort(ABC):
    """
    Interface abstrata (Porta) para um repositório de estado e artefatos.

    Define um contrato para salvar e carregar dicionários de dados e arquivos
    binários associados a uma execução de workflow específica, permitindo que os
    componentes do `core` implementem lógicas de cache e persistência de
    artefatos.
    """

    @abstractmethod
    async def load(self, context: RunContext, key: str) -> Optional[Dict[str, Any]]:
        """
        Carrega os dados estruturados (JSON) associados a uma chave específica.

        Args:
            context (RunContext): O contexto da execução do workflow.
            key (str): A chave única que identifica o estado a ser carregado.

        Returns:
            Optional[Dict[str, Any]]: Um dicionário com os dados do estado,
                                      ou `None` se a chave não for encontrada.
        """
        raise NotImplementedError

    @abstractmethod
    async def save(self, context: RunContext, key: str, data: Dict[str, Any]) -> None:
        """
        Salva os dados estruturados (JSON) associados a uma chave específica.

        Args:
            context (RunContext): O contexto da execução do workflow.
            key (str): A chave única para identificar o estado.
            data (Dict[str, Any]): O dicionário de dados a ser salvo.
        """
        raise NotImplementedError

    @abstractmethod
    async def save_artifact(self, context: RunContext, filename: str, data: bytes) -> str:
        """
        Salva um artefato binário (como uma imagem) no repositório de estado.

        Args:
            context (RunContext): O contexto da execução do workflow.
            filename (str): O nome do arquivo para o artefato (ex: "post_image.jpg").
            data (bytes): Os dados binários brutos do artefato.

        Returns:
            str: O caminho absoluto onde o artefato foi salvo.
        """
        raise NotImplementedError

    @abstractmethod
    async def load_artifact(self, context: RunContext, filename: str) -> bytes:
        """
        Carrega um artefato binário a partir do repositório de estado.

        Args:
            context (RunContext): O contexto da execução do workflow.
            filename (str): O nome do arquivo do artefato a ser carregado
                          (ex: "post_image.jpg").

        Returns:
            bytes: Os dados binários brutos do artefato.

        Raises:
            ArtifactNotFoundError: (Recomendado) Se a implementação não conseguir
                                   encontrar um artefato com o nome fornecido
                                   no contexto especificado.
        """
        raise NotImplementedError
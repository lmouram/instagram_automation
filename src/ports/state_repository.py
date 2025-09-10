# src/ports/state_repository.py

"""
Módulo da Porta do Repositório de Estado Atômico.

Este arquivo define a porta (interface abstrata) para um repositório de
estado genérico. Seu propósito é permitir que os casos de uso e orquestradores
persistam, recuperem e gerenciem o ciclo de vida de dados estruturados (JSON)
e artefatos binários (arquivos) de forma co-localizada para uma execução
de workflow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.core.domain.entities import RunContext


class StateRepositoryPort(ABC):
    """
    Interface abstrata (Porta) para um repositório de estado e artefatos.

    Define um contrato para salvar, carregar e deletar dicionários de dados e
    arquivos binários associados a uma execução de workflow específica.
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
            filename (str): O nome do arquivo do artefato a ser carregado.

        Returns:
            bytes: Os dados binários brutos do artefato.

        Raises:
            ArtifactNotFoundError: (Recomendado) Se o artefato não for encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, context: RunContext, key: str) -> bool:
        """
        Deleta um estado (JSON) ou artefato (arquivo) associado a uma chave/nome.

        Este método deve ser idempotente; se o item a ser deletado não existir,
        ele deve retornar `False` sem levantar um erro.

        Args:
            context (RunContext): O contexto da execução do workflow.
            key (str): A chave do estado ou o nome do arquivo do artefato a ser
                       deletado. A implementação deve ser inteligente o suficiente
                       para tentar deletar ambos os tipos de arquivo se o nome for ambíguo.

        Returns:
            bool: `True` se um ou mais arquivos foram deletados, `False` caso contrário.
        """
        raise NotImplementedError
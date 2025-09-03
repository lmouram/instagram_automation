# src/ports/post_repository.py

"""
Módulo da Porta do Repositório de Postagens.

Este arquivo define a porta (interface abstrata) para a persistência e
recuperação de entidades `Post`. Esta é uma das portas mais importantes,
atuando como a fronteira entre o domínio da aplicação e a camada de
infraestrutura de dados.

O núcleo da aplicação (casos de uso) dependerá exclusivamente desta abstração
para todas as operações de banco de dados relacionadas a posts, sem conhecer
os detalhes da implementação (ex: SQL, NoSQL, ORM).
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

# Importa a entidade e o enum de domínio que esta porta irá manipular.
from src.core.domain.entities import Post
from src.core.domain.enums import PostStatus


class PostRepositoryPort(ABC):
    """
    Interface abstrata (Porta) para um repositório de postagens.

    Define o contrato que os adaptadores de persistência devem seguir para
    gerenciar o ciclo de vida dos objetos `Post` no armazenamento de dados.
    """

    @abstractmethod
    async def save(self, post: Post) -> None:
        """
        Salva (cria ou atualiza) uma entidade Post na fonte de dados.

        A implementação deve ser capaz de lidar tanto com a inserção de um
        novo post quanto com a atualização de um post existente, geralmente
        verificando a existência do `post.id`.

        Args:
            post (Post): O objeto Post a ser salvo.

        Raises:
            Exception: Pode levantar uma exceção específica do adaptador
                       em caso de falha na comunicação com o banco de dados
                       ou violação de constraints.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, post_id: UUID) -> Optional[Post]:
        """
        Recupera um único Post pelo seu identificador único.

        Args:
            post_id (UUID): O ID do Post a ser encontrado.

        Returns:
            Optional[Post]: O objeto Post correspondente, se encontrado.
                            Caso contrário, retorna None.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_status(self, status: PostStatus) -> List[Post]:
        """
        Recupera uma lista de Posts que correspondem a um status específico.

        Este método é fundamental para os casos de uso que operam em lotes de
        posts, como listar posts para aprovação ou encontrar posts publicados.

        Args:
            status (PostStatus): O status dos posts a serem pesquisados.

        Returns:
            List[Post]: Uma lista de objetos Post que correspondem ao status.
                        Retorna uma lista vazia se nenhum post for encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_scheduled_to_publish(self) -> List[Post]:
        """
        Encontra todos os posts que estão prontos para serem publicados.

        A lógica de negócio para esta consulta é:
        - O status do post deve ser `APPROVED`.
        - A data de agendamento (`scheduled_at`) deve ser no passado.
        - O número de tentativas de publicação deve ser menor que um limite
          máximo definido (a ser gerenciado pelo caso de uso ou adaptador).

        Esta é uma consulta de negócio especializada, otimizada para o caso de
        uso do publicador agendado.

        Returns:
            List[Post]: Uma lista de posts que atendem aos critérios para
                        publicação imediata.
        """
        raise NotImplementedError
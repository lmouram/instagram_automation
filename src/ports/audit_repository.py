# src/ports/audit_repository.py

"""
Módulo da Porta do Repositório de Auditoria.

Este arquivo define a porta (interface abstrata) para a persistência e recuperação
de eventos de auditoria. De acordo com a Arquitetura Hexagonal e o Princípio da
Inversão de Dependência, o núcleo da aplicação (casos de uso) dependerá desta
abstração, e não de uma implementação concreta de banco de dados.

Qualquer adaptador que deseje fornecer funcionalidade de persistência de
auditoria deve implementar esta interface.
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

# Importa a entidade de domínio que esta porta irá manipular.
from src.core.domain.entities import AuditEvent


class AuditEventRepositoryPort(ABC):
    """
    Interface abstrata (Porta) para um repositório de eventos de auditoria.

    Define o contrato que os adaptadores de persistência devem seguir para
    gerenciar o ciclo de vida dos objetos AuditEvent.
    """

    @abstractmethod
    async def save(self, event: AuditEvent) -> None:
        """
        Persiste um novo evento de auditoria na fonte de dados.

        Este método é responsável por salvar a entidade AuditEvent. Uma implementação
        concreta lidaria com a serialização do objeto e a inserção no
        banco de dados, arquivo de log ou outro sistema de armazenamento.

        Args:
            event (AuditEvent): O objeto de evento de auditoria a ser salvo.

        Raises:
            Exception: Pode levantar uma exceção específica do adaptador
                       (ex: ConexaoFalhouError) em caso de falha na persistência.
                       O caso de uso que chama este método deve estar preparado
                       para tratar possíveis falhas.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_post_id(self, post_id: UUID) -> List[AuditEvent]:
        """
        Recupera uma lista de todos os eventos de auditoria associados a um Post.

        Este método é útil para construir um histórico de ações para uma
        postagem específica, que pode ser exibido em uma interface de usuário
        ou usado para fins de depuração.

        Args:
            post_id (UUID): O identificador único do Post cujos eventos de
                            auditoria devem ser recuperados.

        Returns:
            List[AuditEvent]: Uma lista de objetos AuditEvent, ordenada do mais
                              recente para o mais antigo. Retorna uma lista
                              vazia se nenhum evento for encontrado.
        """
        raise NotImplementedError
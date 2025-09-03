# src/core/application/approve_post.py

"""
Caso de Uso: Aprovar um Post.

Este caso de uso lida com a aprovação de um post pendente e o agendamento
de sua publicação.
"""

import logging
from datetime import datetime
from uuid import UUID

from src.core.domain.entities import AuditEvent, Post
from src.core.domain.enums import PostStatus
from src.ports.audit_repository import AuditEventRepositoryPort
from src.ports.observability import ObservabilityPort
from src.ports.post_repository import PostRepositoryPort

from .exceptions import InvalidPostStateError

logger = logging.getLogger(__name__)


async def approve_post_use_case(
    post_id: UUID,
    scheduled_at: datetime,
    responsible: str,
    post_repository: PostRepositoryPort,
    audit_repository: AuditEventRepositoryPort,
    observability: ObservabilityPort,
) -> Post:
    """
    Aprova um post que está pendente de revisão e define sua data de agendamento.

    Args:
        post_id (UUID): O ID do post a ser aprovado.
        scheduled_at (datetime): A data e hora (UTC) para o agendamento.
        responsible (str): Identificador de quem está realizando a aprovação.
        post_repository (PostRepositoryPort): Porta para buscar e salvar o post.
        audit_repository (AuditEventRepositoryPort): Porta para registrar auditoria.
        observability (ObservabilityPort): Porta para registrar métricas/eventos.

    Returns:
        Post: A entidade Post atualizada.

    Raises:
        InvalidPostStateError: Se o post não for encontrado ou não estiver no estado PENDING_APPROVAL.
    """
    logger.info(f"Tentativa de aprovação para o post ID: {post_id} por '{responsible}'")

    post = await post_repository.find_by_id(post_id)
    if not post:
        raise InvalidPostStateError(f"Post com ID {post_id} não encontrado.")
    if post.status != PostStatus.PENDING_APPROVAL:
        raise InvalidPostStateError(
            f"Post {post_id} está no estado '{post.status}' e não pode ser aprovado."
        )

    post.status = PostStatus.APPROVED
    post.scheduled_at = scheduled_at
    post.updated_at = datetime.utcnow()
    await post_repository.save(post)
    logger.info(f"Post {post_id} aprovado. Agendado para: {scheduled_at.isoformat()}")

    audit_event = AuditEvent(
        post_id=post.id,
        action="POST_APPROVED",
        responsible=responsible,
        details={"scheduled_at": scheduled_at.isoformat()},
    )
    await audit_repository.save(audit_event)

    await observability.log_event("post_approved", details={"post_id": str(post.id)})
    await observability.increment_metric("posts_approved_total")

    return post
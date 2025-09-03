# src/core/application/publish_scheduled_posts.py

"""
Caso de Uso: Publicar Posts Agendados.

Este caso de uso é projetado para ser executado periodicamente por um scheduler.
Ele busca posts aprovados e agendados e tenta publicá-los de forma resiliente.
"""

import logging
from datetime import datetime
from typing import Dict, List
from uuid import UUID

from src.core.domain.entities import AuditEvent
from src.core.domain.enums import PostStatus
from src.ports.audit_repository import AuditEventRepositoryPort
from src.ports.observability import ObservabilityPort
from src.ports.post_repository import PostRepositoryPort
from src.ports.social_publisher import SocialMediaPublisherPort

logger = logging.getLogger(__name__)


async def publish_scheduled_posts_use_case(
    post_repository: PostRepositoryPort,
    social_publisher: SocialMediaPublisherPort,
    audit_repository: AuditEventRepositoryPort,
    observability: ObservabilityPort,
) -> Dict[str, List[UUID]]:
    """
    Busca por posts aprovados e agendados e tenta publicá-los.

    Args:
        post_repository (PostRepositoryPort): Porta para buscar e atualizar posts.
        social_publisher (SocialMediaPublisherPort): Porta para realizar a publicação.
        audit_repository (AuditEventRepositoryPort): Porta para registrar auditoria.
        observability (ObservabilityPort): Porta para registrar métricas/eventos.

    Returns:
        Dict[str, List[UUID]]: Um resumo com IDs dos posts publicados e dos que falharam.
    """
    logger.info("Iniciando rotina de publicação de posts agendados.")
    posts_to_publish = await post_repository.find_scheduled_to_publish()

    if not posts_to_publish:
        logger.info("Nenhum post agendado para publicação no momento.")
        return {"success": [], "failed": []}

    logger.info(f"Encontrados {len(posts_to_publish)} posts para publicar.")
    results = {"success": [], "failed": []}

    for post in posts_to_publish:
        try:
            publication_id = await social_publisher.publish(post)
            logger.info(f"Post {post.id} publicado com sucesso. ID: {publication_id}")
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.utcnow()
            await audit_repository.save(
                AuditEvent(
                    post_id=post.id, action="POST_PUBLISHED_SUCCESS",
                    responsible="system:scheduler", details={"publication_id": publication_id}
                )
            )
            await observability.increment_metric("posts_published_total", tags={"status": "success"})
            results["success"].append(post.id)
        except Exception as e:
            logger.exception(f"Falha ao publicar post ID: {post.id}. Erro: {e}")
            post.status = PostStatus.PUBLICATION_ERROR
            post.publish_attempts += 1
            post.error_message = str(e)
            await audit_repository.save(
                AuditEvent(
                    post_id=post.id, action="POST_PUBLISHED_FAILURE",
                    responsible="system:scheduler", details={"error": str(e), "attempt": post.publish_attempts}
                )
            )
            await observability.increment_metric("posts_published_total", tags={"status": "failure"})
            results["failed"].append(post.id)
        finally:
            post.updated_at = datetime.utcnow()
            await post_repository.save(post)

    logger.info(f"Rotina finalizada. Sucessos: {len(results['success'])}. Falhas: {len(results['failed'])}.")
    return results
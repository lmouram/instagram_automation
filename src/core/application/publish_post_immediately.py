# src/core/application/publish_post_immediately.py

"""
Caso de Uso: Publicar um Post Imediatamente.

Este caso de uso cria e publica um post em uma única ação, sem passar pelo
fluxo de aprovação e agendamento. É ideal para postagens urgentes ou testes.
"""

import logging
from datetime import datetime
from uuid import uuid4

from src.core.domain.entities import AuditEvent, Media, Post
from src.core.domain.enums import MediaType, PostStatus, PostType
from src.ports.audit_repository import AuditEventRepositoryPort
from src.ports.content_generator import ContentGeneratorPort
from src.ports.media_generator import MediaGeneratorPort
from src.ports.observability import ObservabilityPort
from src.ports.post_repository import PostRepositoryPort
from src.ports.social_publisher import SocialMediaPublisherPort
from src.ports.storage import StoragePort

from .exceptions import PostPublicationError

logger = logging.getLogger(__name__)


async def publish_post_immediately_use_case(
    theme: str,
    responsible: str,
    content_generator: ContentGeneratorPort,
    media_generator: MediaGeneratorPort,
    storage: StoragePort,
    post_repository: PostRepositoryPort,
    social_publisher: SocialMediaPublisherPort,
    audit_repository: AuditEventRepositoryPort,
    observability: ObservabilityPort,
) -> Post:
    """
    Cria e tenta publicar um post imediatamente.

    Args:
        theme (str): O tema para a criação do post.
        responsible (str): Identificador de quem iniciou a publicação.
        ... (todas as portas necessárias) ...

    Returns:
        Post: A entidade Post em seu estado final (PUBLISHED ou PUBLICATION_ERROR).

    Raises:
        PostPublicationError: Se a etapa de criação falhar. A falha na publicação
                              é tratada internamente e refletida no status do post.
    """
    logger.info(f"Iniciando publicação imediata para o tema '{theme}' por '{responsible}'")
    
    # --- Etapa de Criação ---
    try:
        text_content = await content_generator.generate_text_for_post(theme)
        image_prompt = f"Fotografia cinematográfica, ultrarrealista sobre: {theme}"
        image_bytes = await media_generator.generate_image(prompt=image_prompt)
        file_name = f"{uuid4()}.png"
        media_url = await storage.upload(
            file_content=image_bytes, file_name=file_name, content_type="image/png"
        )
        media = Media(
            media_type=MediaType.IMAGE, url=media_url, generation_prompt=image_prompt
        )
        post = Post(
            theme=theme, text_content=text_content, status=PostStatus.DRAFT,
            post_type=PostType.SINGLE_IMAGE, media=[media]
        )
        await post_repository.save(post)
        await observability.increment_metric("posts_created_total", tags={"flow": "immediate"})
        logger.info(f"Post (ID: {post.id}) criado em estado DRAFT, pronto para publicar.")
    except Exception as e:
        logger.exception(f"Falha na etapa de CRIAÇÃO da publicação imediata. Tema: '{theme}'")
        await observability.increment_metric("posts_creation_failed_total", tags={"flow": "immediate"})
        raise PostPublicationError(f"Falha ao criar o conteúdo do post: {e}") from e

    # --- Etapa de Publicação ---
    try:
        publication_id = await social_publisher.publish(post)
        logger.info(f"Post {post.id} publicado com sucesso. ID da publicação: {publication_id}")
        post.status = PostStatus.PUBLISHED
        post.published_at = datetime.utcnow()
        await audit_repository.save(
            AuditEvent(
                post_id=post.id, action="IMMEDIATE_PUBLISH_SUCCESS",
                responsible=responsible, details={"publication_id": publication_id}
            )
        )
        await observability.increment_metric("posts_published_total", tags={"status": "success", "flow": "immediate"})
    except Exception as e:
        logger.exception(f"Falha na etapa de PUBLICAÇÃO do post ID: {post.id}. Erro: {e}")
        post.status = PostStatus.PUBLICATION_ERROR
        post.publish_attempts = 1
        post.error_message = str(e)
        await audit_repository.save(
            AuditEvent(
                post_id=post.id, action="IMMEDIATE_PUBLISH_FAILURE",
                responsible=responsible, details={"error": str(e)}
            )
        )
        await observability.increment_metric("posts_published_total", tags={"status": "failure", "flow": "immediate"})
    finally:
        post.updated_at = datetime.utcnow()
        await post_repository.save(post)
        logger.info(f"Estado final do post {post.id} salvo como '{post.status}'.")

    return post
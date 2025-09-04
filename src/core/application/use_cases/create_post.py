# src/core/application/create_post.py

"""
Caso de Uso: Criar um Post.

Este caso de uso orquestra a criação completa de um novo post, desde a
geração de conteúdo até a persistência inicial, deixando-o pronto para
a aprovação humana.
"""

import logging
from uuid import uuid4

from src.core.domain.entities import Media, Post
from src.core.domain.enums import MediaType, PostStatus, PostType
from src.ports.content_generator import ContentGeneratorPort
from src.ports.media_generator import MediaGeneratorPort
from src.ports.observability import ObservabilityPort
from src.ports.post_repository import PostRepositoryPort
from src.ports.storage import StoragePort

from .exceptions import PostCreationError

logger = logging.getLogger(__name__)


async def create_post_use_case(
    theme: str,
    content_generator: ContentGeneratorPort,
    media_generator: MediaGeneratorPort,
    storage: StoragePort,
    post_repository: PostRepositoryPort,
    observability: ObservabilityPort,
) -> Post:
    """
    Orquestra a criação completa de um novo post.

    Args:
        theme (str): O tema sobre o qual o post deve ser criado.
        content_generator (ContentGeneratorPort): Porta para gerar o texto.
        media_generator (MediaGeneratorPort): Porta para gerar a mídia.
        storage (StoragePort): Porta para fazer o upload da mídia.
        post_repository (PostRepositoryPort): Porta para salvar o post.
        observability (ObservabilityPort): Porta para registrar métricas/eventos.

    Returns:
        Post: A entidade Post recém-criada e salva.

    Raises:
        PostCreationError: Se qualquer etapa do processo de criação falhar.
    """
    logger.info(f"Iniciando criação de post para o tema: '{theme}'")
    try:
        text_content = await content_generator.generate_text_for_post(theme)
        logger.debug("Conteúdo de texto gerado com sucesso.")

        image_prompt = f"Fotografia cinematográfica, ultrarrealista sobre: {theme}"
        image_bytes = await media_generator.generate_image(prompt=image_prompt)
        logger.debug(f"Imagem gerada com sucesso. Tamanho: {len(image_bytes)} bytes.")

        file_name = f"{uuid4()}.png"
        media_url = await storage.upload(
            file_content=image_bytes, file_name=file_name, content_type="image/png"
        )
        logger.info(f"Mídia enviada com sucesso para o storage. URL: {media_url}")

        media = Media(
            media_type=MediaType.IMAGE, url=media_url, generation_prompt=image_prompt
        )
        new_post = Post(
            theme=theme,
            text_content=text_content,
            status=PostStatus.PENDING_APPROVAL,
            post_type=PostType.SINGLE_IMAGE,
            media=[media],
        )

        await post_repository.save(new_post)
        logger.info(f"Post para o tema '{theme}' salvo com sucesso. ID: {new_post.id}")

        await observability.increment_metric("posts_created_total")
        return new_post

    except Exception as e:
        logger.exception(
            f"Falha crítica durante a criação do post para o tema '{theme}'. Error: {e}"
        )
        await observability.increment_metric("posts_creation_failed_total")
        raise PostCreationError(f"Não foi possível criar o post: {e}") from e
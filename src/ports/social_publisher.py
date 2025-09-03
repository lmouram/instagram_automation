# src/ports/social_publisher.py

"""
Módulo da Porta do Publicador de Mídia Social.

Este arquivo define a porta (interface abstrata) para a funcionalidade de
publicar conteúdo em uma plataforma de mídia social. O propósito desta porta
é criar uma fronteira clara entre o núcleo da aplicação (core) e as
especificidades de qualquer API de rede social (ex: Instagram, Facebook,
TikTok).

O caso de uso de publicação agendada dependerá desta abstração para executar
a publicação, sem precisar conhecer detalhes sobre SDKs, autenticação ou
endpoints HTTP.
"""

from abc import ABC, abstractmethod

# Importa a entidade de domínio que contém todas as informações para publicação.
from src.core.domain.entities import Post


class SocialMediaPublisherPort(ABC):
    """
    Interface abstrata (Porta) para um serviço de publicação em mídia social.

    Define o contrato que os adaptadores de publicação devem seguir. Um
    adaptador concreto (ex: `InstagramPublisherAdapter`) implementará este
    contrato usando a API específica da plataforma alvo.
    """

    @abstractmethod
    async def publish(self, post: Post) -> str:
        """
        Publica um post em uma plataforma de mídia social.

        A implementação concreta deste método deve pegar o objeto `Post`,
        interpretar seu tipo (`post_type`), baixar as mídias a partir das URLs
        fornecidas (`post.media`), e usar a API da rede social para fazer o
        upload e a publicação com o texto fornecido (`post.text_content`).

        Args:
            post (Post): A entidade `Post` do domínio, contendo todo o
                         material e metadados necessários para a publicação.

        Returns:
            str: O identificador único da publicação na plataforma externa
                 (ex: a URL do post ou o ID da publicação). Este valor é útil
                 para fins de auditoria e para armazenar uma referência à
                 publicação real.

        Raises:
            Exception: Implementações concretas devem levantar exceções claras e
                       específicas em caso de falha. Exemplos incluem:
                       - `AuthenticationError`: Se as credenciais forem inválidas.
                       - `APIRateLimitError`: Se o limite de requisições da API
                         for atingido.
                       - `PublicationFailedError`: Para erros genéricos de
                         publicação (ex: conteúdo violou regras da plataforma,
                         mídia em formato inválido).
                       O caso de uso chamador deve capturar estas exceções para
                       atualizar o status do post e registrar o erro.
        """
        raise NotImplementedError
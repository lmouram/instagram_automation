# src/adapters/social/__init__.py

"""
Pacote de Adaptadores de Mídia Social.

Este pacote contém implementações concretas da `SocialMediaPublisherPort`,
conectando o core da aplicação a diferentes plataformas de mídia social.
"""

from .instagram_adapter import InstagramAdapter, InstagramPublicationError

__all__ = ["InstagramAdapter", "InstagramPublicationError"]
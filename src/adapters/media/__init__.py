# src/adapters/media/__init__.py

"""
Pacote de Adaptadores de Geração de Mídia.

Este pacote contém implementações concretas da `MediaGeneratorPort`,
conectando o core da aplicação a diferentes serviços de geração de
imagens e vídeos.
"""

from .google_image_adapter import GoogleImageAdapter, ImageGenerationError

__all__ = ["GoogleImageAdapter", "ImageGenerationError"]
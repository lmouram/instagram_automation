# src/ports/media_generator.py

"""
Módulo da Porta do Gerador de Mídia.

Este arquivo define a porta (interface abstrata) para a funcionalidade de
geração de mídia (imagens e vídeos). O propósito desta porta é desacoplar o
núcleo da aplicação (core) dos detalhes de implementação de qualquer serviço
de geração de mídia, como Google Imagen, DALL-E, ou serviços similares.

Qualquer adaptador que se conecte a um serviço de geração de mídia para
criar imagens ou vídeos deve implementar esta interface.
"""

from abc import ABC, abstractmethod
from typing import Union, Tuple

from src.core.domain.enums import MediaType


class MediaGeneratorPort(ABC):
    """
    Interface abstrata (Porta) para um serviço de geração de mídia.

    Define o contrato que os adaptadores de geração de mídia (imagens e
    vídeos) devem seguir. O caso de uso de criação de post dependerá desta
    abstração para obter as mídias a serem associadas ao post.
    """

    @abstractmethod
    async def generate_image(self, prompt: str) -> bytes:
        """
        Gera uma imagem a partir de um prompt textual.

        A implementação concreta deste método deve interagir com um serviço de
        geração de imagens, enviando o prompt e recebendo os dados binários
        da imagem gerada (ex: em formato PNG ou JPEG).

        Args:
            prompt (str): O texto descritivo que o gerador de imagens deve
                          usar para criar a imagem.

        Returns:
            bytes: Os dados binários da imagem gerada.

        Raises:
            Exception: Implementações concretas podem levantar exceções
                       específicas em caso de falhas na comunicação com a API
                       do serviço, erros de moderação de conteúdo, ou outros
                       problemas na geração. O chamador (caso de uso) deve
                       estar preparado para tratar essas falhas.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_video(self, prompt: str) -> bytes:
        """
        Gera um vídeo a partir de um prompt textual.

        A implementação concreta deste método deve interagir com um serviço de
        geração de vídeos, enviando o prompt e recebendo os dados binários
        do vídeo gerado (ex: em formato MP4).

        Args:
            prompt (str): O texto descritivo que o gerador de vídeo deve
                          usar para criar o vídeo.

        Returns:
            bytes: Os dados binários do vídeo gerado.

        Raises:
            Exception: Implementações concretas podem levantar exceções
                       específicas em caso de falhas na comunicação com a API
                       do serviço, erros de moderação de conteúdo, ou outros
                       problemas na geração. O chamador (caso de uso) deve
                       estar preparado para tratar essas falhas.
        """
        raise NotImplementedError
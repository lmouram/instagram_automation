# src/ports/content_generator.py

"""
Módulo da Porta do Gerador de Conteúdo.

Este arquivo define a porta (interface abstrata) para a funcionalidade de
geração de conteúdo textual. O propósito desta porta é desacoplar o núcleo
da aplicação (core) dos detalhes de implementação de qualquer modelo de
linguagem grande (LLM) específico, como Gemini, OpenAI GPT, etc.

Qualquer adaptador que se conecte a um serviço de LLM para gerar texto
deve implementar esta interface.
"""

from abc import ABC, abstractmethod


class ContentGeneratorPort(ABC):
    """
    Interface abstrata (Porta) para um serviço de geração de conteúdo textual.

    Define o contrato que os adaptadores de LLM devem seguir para fornecer
    texto para as postagens. O caso de uso de criação de post dependerá desta
    abstração, enviando um tema e esperando receber um texto formatado
    de volta.
    """

    @abstractmethod
    async def generate_text_for_post(self, theme: str) -> str:
        """
        Gera um conteúdo textual para uma postagem com base em um tema fornecido.

        A implementação concreta deste método deve interagir com um serviço de
        LLM, possivelmente formatando o prompt internamente para instruir o
        modelo a gerar um texto adequado para uma legenda de Instagram
        (incluindo, por exemplo, tom de voz, emojis e hashtags relevantes).

        Args:
            theme (str): O tópico ou assunto sobre o qual o conteúdo do post
                         deve ser gerado.

        Returns:
            str: O conteúdo textual gerado, pronto para ser usado como legenda
                 da postagem.

        Raises:
            Exception: Implementações concretas podem levantar exceções
                       específicas em caso de falhas na comunicação com a API
                       do LLM, erros de moderação de conteúdo, ou outros
                       problemas relacionados à geração. O chamador (caso de
                       uso) deve estar preparado para tratar essas falhas.
        """
        raise NotImplementedError
# src/core/domain/enums.py

"""
Módulo de Enumerações de Domínio.

Este arquivo define os conjuntos finitos de valores (Enums) que governam os
estados e tipos dentro do domínio da aplicação. O uso de Enums garante
consistência, previne erros e torna o código mais legível e explícito.

Herda-se de `str` e `Enum` para que os membros possam ser tratados diretamente
como strings, facilitando a serialização e a integração com bancos de dados
e APIs, ao mesmo tempo em que mantêm a segurança de tipos de uma enumeração.
"""

from enum import Enum


class PostStatus(str, Enum):
    """
    Define os possíveis estados do ciclo de vida de uma postagem.

    Cada membro representa uma etapa distinta no fluxo de trabalho, desde a
    criação inicial até a publicação final ou falha.
    """
    DRAFT = "RASCUNHO"
    """
    O post foi criado pelo sistema, mas ainda não foi submetido para
    revisão humana. Pode estar incompleto ou em processo de geração.
    """

    PENDING_APPROVAL = "PENDENTE_APROVACAO"
    """
    O post foi completamente gerado (texto e mídias) e está aguardando
    a aprovação ou rejeição de um operador humano na interface.
    """

    APPROVED = "APROVADO"
    """
    O post foi revisado e aprovado por um humano. Está na fila de
    agendamento, pronto para ser publicado na data e hora definidas.
    """

    REJECTED = "REJEITADO"
    """
    O post foi revisado e explicitamente rejeitado por um humano. Nenhuma
    outra ação será tomada sobre este post, a menos que seja reprocessado.
    """

    PUBLISHED = "PUBLICADO"
    """
    O post foi publicado com sucesso na plataforma de mídia social.
    Este é um estado final bem-sucedido.
    """

    PUBLICATION_ERROR = "ERRO_PUBLICACAO"
    """
    Ocorreu um erro irrecuperável durante a tentativa de publicação do post.
    Este estado requer atenção manual para diagnosticar e resolver o problema.
    Este é um estado final de falha.
    """


class PostType(str, Enum):
    """

    Define os diferentes formatos de postagem suportados pela aplicação.

    Esta enumeração ajuda a lógica de publicação a se adaptar às diferentes
    necessidades de cada formato (ex: uma imagem vs. múltiplas imagens).
    """
    SINGLE_IMAGE = "IMAGEM_UNICA"
    """Um post contendo uma única imagem."""

    CAROUSEL = "CARROSSEL"
    """Um post contendo múltiplas imagens ou vídeos em formato de carrossel."""

    VIDEO = "VIDEO"
    """Um post cujo conteúdo principal é um único vídeo."""


class MediaType(str, Enum):
    """
    Define os tipos de mídia que podem ser gerados e associados a um post.
    """
    IMAGE = "IMAGEM"
    """Um arquivo de imagem estática (ex: JPG, PNG)."""

    VIDEO = "VIDEO"
    """Um arquivo de vídeo (ex: MP4)."""


class WorkflowStatus(str, Enum):
    PENDING = "PENDENTE"
    RUNNING = "EM_EXECUCAO"
    COMPLETED = "CONCLUIDO"
    FAILED_RETRYABLE = "FALHOU_RETRIAVEL"
    FAILED_PERMANENT = "FALHOU_PERMANENTE"
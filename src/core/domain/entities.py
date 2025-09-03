# src/core/domain/entities.py

"""
Módulo de Entidades de Domínio.

Este arquivo contém as definições das entidades puras que representam o núcleo
do domínio da aplicação. De acordo com a Arquitetura Hexagonal, estas classes
são agnósticas a qualquer tecnologia externa (banco de dados, APIs, frameworks).

Elas representam o estado e as regras de negócio intrínsecas da aplicação.
Utilizamos `dataclasses` para uma definição concisa e clara das estruturas de dados.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

# Importa os Enums que definem os tipos e status controlados pelo domínio.
from .enums import MediaType, PostStatus, PostType


@dataclass
class Media:
    """
    Representa um único item de mídia (imagem ou vídeo) associado a um Post.

    Esta entidade armazena a referência para o conteúdo de mídia, que é
    hospedado externamente (ex: Supabase Storage, S3), junto com metadados
    relevantes para sua exibição e rastreabilidade.
    """
    id: UUID = field(default_factory=uuid4, init=False)
    """Identificador único universal da mídia."""

    media_type: MediaType
    """O tipo de mídia (IMAGEM ou VIDEO), conforme definido no Enum MediaType."""

    url: str
    """A URL pública e acessível onde o arquivo de mídia está armazenado."""

    order: int = 1
    """A ordem de exibição da mídia dentro de um post carrossel (começando em 1)."""

    generation_prompt: Optional[str] = None
    """O prompt exato usado para gerar esta mídia específica, para fins de auditoria e rastreabilidade."""


@dataclass
class Post:
    """
    Representa a entidade central da aplicação: uma postagem para rede social.

    Esta classe agrega todo o estado de uma postagem, desde sua criação e
    conteúdo até seu ciclo de vida de aprovação, agendamento e publicação.
    Ela também inclui campos para controle de resiliência e tratamento de falhas.
    """
    id: UUID = field(default_factory=uuid4, init=False)
    """Identificador único universal da postagem."""

    theme: str
    """O tema ou tópico principal que originou a criação do post."""

    text_content: str
    """O conteúdo textual completo do post (legenda/descrição)."""

    status: PostStatus
    """
    O estado atual do post em seu ciclo de vida (ex: RASCUNHO, PENDENTE_APROVACAO,
    APROVADO, PUBLICADO, ERRO_PUBLICACAO). Controlado pelo Enum PostStatus.
    """

    post_type: PostType
    """
    O formato do post (ex: IMAGEM_UNICA, CARROSSEL, VIDEO).
    Controlado pelo Enum PostType.
    """

    media: List[Media] = field(default_factory=list)
    """Uma lista de objetos Media associados a este post."""

    scheduled_at: Optional[datetime] = None
    """A data e hora UTC em que o post está agendado para ser publicado."""

    published_at: Optional[datetime] = None
    """A data e hora UTC em que o post foi efetivamente publicado."""
    
    # Campos para controle de resiliência e logging de erros
    publish_attempts: int = 0
    """
    Contador de tentativas de publicação. Usado para implementar lógicas de
    retry e dead-letter queue (posts que falharam consistentemente).
    """

    error_message: Optional[str] = None
    """
    Armazena a última mensagem de erro caso uma tentativa de publicação falhe.
    Útil para debug e análise pela interface humana.
    """

    # Timestamps de auditoria
    created_at: datetime = field(default_factory=datetime.utcnow, init=False)
    """Timestamp UTC da criação do registro do post no sistema."""

    updated_at: datetime = field(default_factory=datetime.utcnow, init=False)
    """Timestamp UTC da última atualização do registro do post."""


@dataclass
class AuditEvent:
    """
    Representa um evento de auditoria para rastrear ações importantes no sistema.

    Cada vez que uma ação crítica é executada (ex: um post é aprovado, rejeitado
    ou uma publicação falha), um evento de auditoria é criado para fornecer um
    histórico claro e rastreável das operações.
    """
    id: UUID = field(default_factory=uuid4, init=False)
    """Identificador único universal do evento de auditoria."""

    post_id: UUID
    """O ID do Post ao qual este evento de auditoria está relacionado."""

    action: str
    """
    Uma descrição da ação realizada (ex: 'POST_CRIADO', 'POST_APROVADO', 
    'PUBLICACAO_FALHOU'). Recomenda-se o uso de constantes para estas strings.
    """

    responsible: str
    """
    Identificador de quem realizou a ação (ex: 'user:fulano@email.com', 
    'system:scheduler', 'api:script_externo').
    """

    details: Optional[Dict[str, Any]] = None
    """
    Um dicionário flexível para armazenar dados contextuais sobre o evento.
    Ex: {'motivo_rejeicao': 'Imagem de baixa qualidade', 'tentativa': 3}.
    """

    timestamp: datetime = field(default_factory=datetime.utcnow, init=False)
    """Timestamp UTC de quando o evento de auditoria foi registrado."""
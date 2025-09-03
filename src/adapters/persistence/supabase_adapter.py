# src/adapters/persistence/supabase_adapter.py

"""
Módulo do Adaptador de Persistência para o Supabase.

Este arquivo contém a implementação concreta das portas de repositório
(PostRepositoryPort e AuditEventRepositoryPort) utilizando o Supabase como
backend de banco de dados.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client
from postgrest.base_request_builder import APIResponse

from src.core.domain.entities import AuditEvent, Media, Post
from src.core.domain.enums import MediaType, PostStatus, PostType
from src.ports.audit_repository import AuditEventRepositoryPort
from src.ports.post_repository import PostRepositoryPort

logger = logging.getLogger(__name__)


class SupabaseAdapter(PostRepositoryPort, AuditEventRepositoryPort):
    """
    Adaptador que implementa as portas de persistência usando o Supabase.

    Esta classe é responsável por traduzir as entidades de domínio em um
    formato adequado para o Supabase (dicionários/JSON) e vice-versa,
    encapsulando toda a lógica de comunicação com o banco de dados.
    """

    _POSTS_TABLE = "posts"
    _AUDIT_EVENTS_TABLE = "audit_events"

    def __init__(self, supabase_client: Client):
        """
        Inicializa o adaptador com o cliente Supabase.

        Args:
            supabase_client (Client): Uma instância do cliente Supabase já
                                      configurada e autenticada.
        """
        self._client = supabase_client
        logger.info("SupabaseAdapter inicializado com sucesso.")

    # --- Métodos Privados de Mapeamento ---

    def _post_to_dict(self, post: Post) -> Dict[str, Any]:
        """Converte uma entidade Post do domínio em um dicionário para o Supabase."""
        return {
            "id": str(post.id),
            "theme": post.theme,
            "text_content": post.text_content,
            "status": post.status.value,
            "post_type": post.post_type.value,
            # Media é uma lista de objetos, ideal para uma coluna JSONB no Supabase
            "media": [
                {
                    "id": str(m.id),
                    "media_type": m.media_type.value,
                    "url": m.url,
                    "order": m.order,
                    "generation_prompt": m.generation_prompt,
                }
                for m in post.media
            ],
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "publish_attempts": post.publish_attempts,
            "error_message": post.error_message,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
        }

    def _dict_to_post(self, data: Dict[str, Any]) -> Post:
        """Converte um dicionário do Supabase em uma entidade Post do domínio."""
        return Post(
            id=UUID(data["id"]),
            theme=data["theme"],
            text_content=data["text_content"],
            status=PostStatus(data["status"]),
            post_type=PostType(data["post_type"]),
            media=[
                Media(
                    id=UUID(m["id"]),
                    media_type=MediaType(m["media_type"]),
                    url=m["url"],
                    order=m["order"],
                    generation_prompt=m["generation_prompt"],
                )
                for m in data["media"]
            ],
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None,
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None,
            publish_attempts=data["publish_attempts"],
            error_message=data.get("error_message"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
    
    def _audit_event_to_dict(self, event: AuditEvent) -> Dict[str, Any]:
        """Converte uma entidade AuditEvent do domínio para um dicionário."""
        return {
            "id": str(event.id),
            "post_id": str(event.post_id),
            "action": event.action,
            "responsible": event.responsible,
            "details": event.details,  # Ideal para coluna JSONB
            "timestamp": event.timestamp.isoformat(),
        }
    
    def _dict_to_audit_event(self, data: Dict[str, Any]) -> AuditEvent:
        """Converte um dicionário do Supabase em uma entidade AuditEvent."""
        return AuditEvent(
            id=UUID(data["id"]),
            post_id=UUID(data["post_id"]),
            action=data["action"],
            responsible=data["responsible"],
            details=data["details"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

    # --- Implementação da PostRepositoryPort ---

    async def save(self, post: Post) -> None:
        logger.debug(f"Salvando post ID: {post.id} com status: {post.status.value}")
        post_dict = self._post_to_dict(post)
        try:
            self._client.table(self._POSTS_TABLE).upsert(post_dict).execute()
            logger.info(f"Post ID: {post.id} salvo com sucesso no Supabase.")
        except Exception as e:
            logger.error(f"Falha ao salvar post ID: {post.id} no Supabase. Erro: {e}", exc_info=True)
            raise

    async def find_by_id(self, post_id: UUID) -> Optional[Post]:
        logger.debug(f"Buscando post por ID: {post_id}")
        response: APIResponse = self._client.table(self._POSTS_TABLE).select("*").eq("id", str(post_id)).limit(1).execute()
        if not response.data:
            logger.warning(f"Post com ID: {post_id} não encontrado.")
            return None
        return self._dict_to_post(response.data[0])

    async def find_by_status(self, status: PostStatus) -> List[Post]:
        logger.debug(f"Buscando posts com status: {status.value}")
        response: APIResponse = self._client.table(self._POSTS_TABLE).select("*").eq("status", status.value).execute()
        return [self._dict_to_post(item) for item in response.data]

    async def find_scheduled_to_publish(self) -> List[Post]:
        now_utc = datetime.utcnow().isoformat()
        logger.debug(f"Buscando posts agendados para publicação antes de {now_utc}")
        response: APIResponse = (
            self._client.table(self._POSTS_TABLE)
            .select("*")
            .eq("status", PostStatus.APPROVED.value)
            .lte("scheduled_at", now_utc)
            .execute()
        )
        return [self._dict_to_post(item) for item in response.data]

    # --- Implementação da AuditEventRepositoryPort ---

    async def save(self, event: AuditEvent) -> None:
        logger.debug(f"Salvando evento de auditoria para o post ID: {event.post_id}, ação: {event.action}")
        event_dict = self._audit_event_to_dict(event)
        try:
            self._client.table(self._AUDIT_EVENTS_TABLE).insert(event_dict).execute()
            logger.info(f"Evento de auditoria para o post ID: {event.post_id} salvo com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao salvar evento de auditoria para o post ID: {event.post_id}. Erro: {e}", exc_info=True)
            raise

    async def find_by_post_id(self, post_id: UUID) -> List[AuditEvent]:
        logger.debug(f"Buscando eventos de auditoria para o post ID: {post_id}")
        response: APIResponse = (
            self._client.table(self._AUDIT_EVENTS_TABLE)
            .select("*")
            .eq("post_id", str(post_id))
            .order("timestamp", desc=True)
            .execute()
        )
        return [self._dict_to_audit_event(item) for item in response.data]
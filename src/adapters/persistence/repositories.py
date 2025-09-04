# src/adapters/persistence/repositories.py

"""
Módulo dos Adaptadores de Repositório para o Supabase.

Este arquivo contém as implementações concretas das portas de repositório,
com cada classe sendo responsável por uma única entidade de domínio,
aderindo ao Princípio da Responsabilidade Única (SRP).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client
from postgrest.base_request_builder import APIResponse

from src.core.domain import AuditEvent, Media, Post, MediaType, PostStatus, PostType
from src.ports import AuditEventRepositoryPort, PostRepositoryPort

logger = logging.getLogger(__name__)


class SupabasePostRepository(PostRepositoryPort):
    """
    Adaptador que implementa a PostRepositoryPort usando o Supabase.
    Responsável pela persistência da entidade Post.
    """
    _TABLE = "posts"

    def __init__(self, supabase_client: Client):
        self._client = supabase_client
        logger.info(f"SupabasePostRepository inicializado para a tabela '{self._TABLE}'.")

    # ... (métodos de mapeamento _post_to_dict e _dict_to_post) ...
    def _post_to_dict(self, post: Post) -> Dict[str, Any]:
        # (código do _post_to_dict daqui, sem alterações)
        return {
            "id": str(post.id), "theme": post.theme, "text_content": post.text_content,
            "status": post.status.value, "post_type": post.post_type.value,
            "media": [
                {"id": str(m.id), "media_type": m.media_type.value, "url": m.url, "order": m.order, "generation_prompt": m.generation_prompt}
                for m in post.media
            ],
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "publish_attempts": post.publish_attempts, "error_message": post.error_message,
            "created_at": post.created_at.isoformat(), "updated_at": post.updated_at.isoformat(),
        }

    def _dict_to_post(self, data: Dict[str, Any]) -> Post:
        # (código do _dict_to_post daqui, sem alterações)
        post = Post(
            theme=data["theme"], text_content=data["text_content"],
            status=PostStatus(data["status"]), post_type=PostType(data["post_type"]),
            media=[Media(id=UUID(m["id"]), media_type=MediaType(m["media_type"]), url=m["url"], order=m["order"], generation_prompt=m["generation_prompt"]) for m in data["media"]],
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None,
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None,
            publish_attempts=data["publish_attempts"], error_message=data.get("error_message"),
        )
        # Atribui IDs e timestamps que não estão no __init__
        post.id = UUID(data["id"])
        post.created_at = datetime.fromisoformat(data["created_at"])
        post.updated_at = datetime.fromisoformat(data["updated_at"])
        return post


    async def save(self, post: Post) -> None:
        logger.debug(f"Salvando post ID: {post.id} com status: {post.status.value}")
        post_dict = self._post_to_dict(post)
        try:
            self._client.table(self._TABLE).upsert(post_dict).execute()
            logger.info(f"Post ID: {post.id} salvo com sucesso no Supabase.")
        except Exception as e:
            logger.error(f"Falha ao salvar post ID: {post.id}. Erro: {e}", exc_info=True)
            raise

    async def find_by_id(self, post_id: UUID) -> Optional[Post]:
        logger.debug(f"Buscando post por ID: {post_id}")
        response: APIResponse = self._client.table(self._TABLE).select("*").eq("id", str(post_id)).limit(1).execute()
        if not response.data:
            return None
        return self._dict_to_post(response.data[0])

    async def find_by_status(self, status: PostStatus) -> List[Post]:
        logger.debug(f"Buscando posts com status: {status.value}")
        response: APIResponse = self._client.table(self._TABLE).select("*").eq("status", status.value).execute()
        return [self._dict_to_post(item) for item in response.data]

    async def find_scheduled_to_publish(self) -> List[Post]:
        now_utc = datetime.now(timezone.utc).isoformat()
        response: APIResponse = self._client.table(self._TABLE).select("*").eq("status", PostStatus.APPROVED.value).lte("scheduled_at", now_utc).execute()
        return [self._dict_to_post(item) for item in response.data]


class SupabaseAuditEventRepository(AuditEventRepositoryPort):
    """
    Adaptador que implementa a AuditEventRepositoryPort usando o Supabase.
    Responsável pela persistência da entidade AuditEvent.
    """
    _TABLE = "audit_events"
    
    def __init__(self, supabase_client: Client):
        self._client = supabase_client
        logger.info(f"SupabaseAuditEventRepository inicializado para a tabela '{self._TABLE}'.")

    # ... (métodos de mapeamento _audit_event_to_dict e _dict_to_audit_event) ...
    def _audit_event_to_dict(self, event: AuditEvent) -> Dict[str, Any]:
        return {"id": str(event.id), "post_id": str(event.post_id), "action": event.action, "responsible": event.responsible, "details": event.details, "timestamp": event.timestamp.isoformat()}
    
    def _dict_to_audit_event(self, data: Dict[str, Any]) -> AuditEvent:
        event = AuditEvent(post_id=UUID(data["post_id"]), action=data["action"], responsible=data["responsible"], details=data["details"])
        event.id = UUID(data["id"])
        event.timestamp = datetime.fromisoformat(data["timestamp"])
        return event

    async def save(self, event: AuditEvent) -> None:
        logger.debug(f"Salvando evento de auditoria para o post ID: {event.post_id}, ação: {event.action}")
        event_dict = self._audit_event_to_dict(event)
        try:
            self._client.table(self._TABLE).insert(event_dict).execute()
            logger.info(f"Evento de auditoria para o post ID: {event.post_id} salvo com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao salvar evento de auditoria. Erro: {e}", exc_info=True)
            raise

    async def find_by_post_id(self, post_id: UUID) -> List[AuditEvent]:
        response: APIResponse = self._client.table(self._TABLE).select("*").eq("post_id", str(post_id)).order("timestamp", desc=True).execute()
        return [self._dict_to_audit_event(item) for item in response.data]
# tests/core/application/test_approve_post.py

import pytest
from uuid import uuid4
from datetime import datetime, timezone  # Importar timezone

from src.core.domain import Post, PostStatus
from src.core.application import approve_post_use_case
from src.core.application.exceptions import InvalidPostStateError

@pytest.mark.asyncio
async def test_approve_post_success(mocker):
    """
    Verifica se o caso de uso aprova corretamente um post que está PENDING_APPROVAL.
    """
    # 1. Arrange (Preparação)
    post_id = uuid4()
    # CORREÇÃO: Usar o método recomendado para datetimes UTC
    scheduled_at = datetime.now(timezone.utc)
    
    # CORREÇÃO: Criar o Post sem o ID e atribuí-lo depois, para respeitar o `init=False`.
    pending_post = Post(
        theme="Teste",
        text_content="...",
        status=PostStatus.PENDING_APPROVAL,
        post_type="IMAGEM_UNICA"
    )
    pending_post.id = post_id # Atribui o ID manualmente para o teste
    
    # Cria mocks para as portas
    mock_post_repo = mocker.AsyncMock()
    mock_post_repo.find_by_id.return_value = pending_post # Simula encontrar o post
    
    mock_audit_repo = mocker.AsyncMock()
    mock_observability = mocker.AsyncMock()

    # 2. Act (Ação)
    result_post = await approve_post_use_case(
        post_id=post_id,
        scheduled_at=scheduled_at,
        responsible="user:test",
        post_repository=mock_post_repo,
        audit_repository=mock_audit_repo,
        observability=mock_observability,
    )

    # 3. Assert (Verificação)
    # Verifica se o post foi encontrado
    mock_post_repo.find_by_id.assert_called_once_with(post_id)
    
    # Verifica se o status do post retornado está correto
    assert result_post.status == PostStatus.APPROVED
    assert result_post.scheduled_at == scheduled_at
    
    # Verifica se o método save foi chamado com o post atualizado
    mock_post_repo.save.assert_called_once_with(pending_post)
    
    # Verifica se os logs de auditoria e observabilidade foram chamados
    mock_audit_repo.save.assert_called_once()
    mock_observability.log_event.assert_called_once_with("post_approved", details=mocker.ANY)
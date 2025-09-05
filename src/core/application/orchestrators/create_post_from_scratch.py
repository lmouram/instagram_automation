# src/core/application/orchestrators/create_post_from_scratch.py

"""
Orquestrador para o workflow de criação de um post a partir do zero.
"""

import logging
from datetime import datetime, timezone

from src.core.domain import RunContext, WorkflowRun, WorkflowStatus
# Importa o novo caso de uso
from src.core.application.use_cases import create_dossier_use_case, copywriter_use_case
from src.ports import ContentGeneratorPort, StateRepositoryPort
from src.utils.resilience import get_next_retry_at

logger = logging.getLogger(__name__)


async def create_post_from_scratch_orchestrator(
    run: WorkflowRun,
    content_generator: ContentGeneratorPort,
    state_repo: StateRepositoryPort,
) -> WorkflowRun:
    """
    Orquestra o workflow completo de criação de um post, começando do tema.

    Este orquestrador gerencia a `WorkflowRun` através de suas etapas:
    1.  `start`: Gera um dossiê de pesquisa sobre o tema.
    2.  `dossier_created`: Usa o dossiê para gerar a copy (título e descrição).

    Args:
        run (WorkflowRun): A entidade de estado que guia a execução do workflow.
        content_generator (ContentGeneratorPort): Porta para o serviço de IA.
        state_repo (StateRepositoryPort): Porta para o cache de resultados das etapas.

    Returns:
        WorkflowRun: A entidade de estado atualizada após a execução da(s) etapa(s).
    """
    logger.info(
        f"Orquestrador 'create_post_from_scratch' iniciado para a execução "
        f"ID: {run.run_id}, etapa atual: '{run.current_step}'"
    )
    
    original_version = run.version

    try:
        if run.status != WorkflowStatus.RUNNING:
            run.status = WorkflowStatus.RUNNING
            run.step_attempt = 0

        # --- MÁQUINA DE ESTADOS SEQUENCIAL ---
        # A estrutura `if/elif` garante que o workflow execute as etapas em ordem.

        # Etapa 1: Geração do Dossiê
        if run.current_step == "start":
            logger.info(f"Executando etapa 'start': Geração do dossiê.")
            context = RunContext(workflow_name=run.workflow_name, run_id=run.run_id)
            step_key = "create_dossier"
            
            dossier = await create_dossier_use_case(
                theme=run.payload["theme"],
                context=context,
                step_key=step_key,
                content_generator=content_generator,
                state_repo=state_repo,
            )
            
            run.state_data["dossier_content"] = dossier
            run.current_step = "dossier_created"
            logger.info(f"Etapa 'start' concluída. Próxima etapa: '{run.current_step}'")

        # Etapa 2: Geração da Copy (Título e Descrição)
        if run.current_step == "dossier_created":
            logger.info(f"Executando etapa 'dossier_created': Geração da copy.")
            context = RunContext(workflow_name=run.workflow_name, run_id=run.run_id)
            step_key = "generate_copy"

            dossier_content = run.state_data.get("dossier_content")
            if not dossier_content:
                raise ValueError("Dossiê não encontrado no estado para a etapa de copywriting.")

            copy_result = await copywriter_use_case(
                dossier=dossier_content,
                context=context,
                step_key=step_key,
                content_generator=content_generator,
                state_repo=state_repo
            )
            
            # Mescla o resultado (dicionário com 'title' e 'description') no estado
            run.state_data.update(copy_result)
            run.current_step = "copy_created"
            logger.info(f"Etapa 'dossier_created' concluída. Próxima etapa: '{run.current_step}'")


        # --- Conclusão do Workflow ---
        if run.current_step == "copy_created": # A nova última etapa
            run.status = WorkflowStatus.COMPLETED
            logger.info(f"Workflow ID {run.run_id} concluído com sucesso.")

    except Exception as e:
        logger.error(f"Erro no orquestrador para a execução ID {run.run_id} na etapa '{run.current_step}'", exc_info=True)
        
        run.status = WorkflowStatus.FAILED_RETRYABLE
        run.step_attempt += 1
        run.last_error_msg = f"{type(e).__name__}: {e}"
        run.retry_at = get_next_retry_at(run.step_attempt)

        logger.warning(
            f"Execução ID {run.run_id} falhou. Marcada para retentativa em "
            f"{run.retry_at.isoformat() if run.retry_at else 'N/A'} "
            f"(Tentativa {run.step_attempt})."
        )
    
    run.updated_at = datetime.now(timezone.utc)

    return run
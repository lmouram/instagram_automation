# src/core/application/orchestrators/create_post_from_scratch.py

"""
Orquestrador para o workflow de criação de um post a partir do zero.
"""

import logging
from datetime import datetime, timezone

from src.core.application.contracts import ThemeContract
from src.core.application.use_cases import (
    copywriter_use_case,
    create_dossier_use_case,
    create_image_use_case,
    edit_image_use_case,
)
from src.core.domain import RunContext, WorkflowRun, WorkflowStatus
from src.ports import (
    ContentGeneratorPort,
    MediaGeneratorPort,
    StateRepositoryPort,
)
from src.utils.resilience import get_next_retry_at

logger = logging.getLogger(__name__)


async def create_post_from_scratch_orchestrator(
    run: WorkflowRun,
    content_generator: ContentGeneratorPort,
    media_generator: MediaGeneratorPort,
    state_repo: StateRepositoryPort,
    theme: ThemeContract,
) -> WorkflowRun:
    """
    Orquestra o workflow completo de criação de um post, começando do tema.

    Este orquestrador gerencia a `WorkflowRun` através de suas etapas:
    1.  `start`: Gera um dossiê de pesquisa sobre o tema.
    2.  `dossier_created`: Gera a copy (título e descrição).
    3.  `copy_created`: Gera e salva a imagem de fundo base.
    4.  `image_created`: Edita a imagem base, aplicando máscara e renderizando texto.
    5.  `final_image_created`: Marca o workflow como concluído.

    Args:
        run (WorkflowRun): A entidade de estado que guia a execução do workflow.
        content_generator (ContentGeneratorPort): Porta para IA textual.
        media_generator (MediaGeneratorPort): Porta para geração de imagem.
        state_repo (StateRepositoryPort): Porta para cache e persistência de artefatos.
        theme (ThemeContract): O DTO do tema com as configurações visuais.

    Returns:
        WorkflowRun: A entidade de estado atualizada.
    """
    logger.info(
        f"Orquestrador 'create_post_from_scratch' iniciado para a execução "
        f"ID: {run.run_id}, etapa atual: '{run.current_step}'"
    )

    try:
        if run.status != WorkflowStatus.RUNNING:
            run.status = WorkflowStatus.RUNNING
            run.step_attempt = 0

        # --- MÁQUINA DE ESTADOS SEQUENCIAL ---

        # Etapa 1: Geração do Dossiê
        if run.current_step == "start":
            logger.info("Executando etapa 'start': Geração do dossiê.")
            context = RunContext(workflow_name=run.workflow_name, run_id=run.run_id)
            dossier = await create_dossier_use_case(
                theme=run.payload["theme"], context=context, step_key="create_dossier",
                content_generator=content_generator, state_repo=state_repo,
            )
            run.state_data["dossier_content"] = dossier
            run.current_step = "dossier_created"
            run.step_attempt = 0
            logger.info(f"Etapa 'start' concluída. Próxima etapa: '{run.current_step}'")

        # Etapa 2: Geração da Copy
        if run.current_step == "dossier_created":
            logger.info("Executando etapa 'dossier_created': Geração da copy.")
            context = RunContext(workflow_name=run.workflow_name, run_id=run.run_id)
            dossier_content = run.state_data.get("dossier_content")
            if not dossier_content:
                raise ValueError("Dossiê não encontrado no estado para a etapa de copywriting.")
            copy_result = await copywriter_use_case(
                dossier=dossier_content, context=context, step_key="generate_copy",
                content_generator=content_generator, state_repo=state_repo
            )
            run.state_data.update(copy_result)
            run.current_step = "copy_created"
            run.step_attempt = 0
            logger.info(f"Etapa 'dossier_created' concluída. Próxima etapa: '{run.current_step}'")

        # Etapa 3: Geração da Imagem Base
        if run.current_step == "copy_created":
            logger.info("Executando etapa 'copy_created': Geração da Imagem Base.")
            context = RunContext(workflow_name=run.workflow_name, run_id=run.run_id)
            dossier = run.state_data.get("dossier_content")
            title = run.state_data.get("title")
            description = run.state_data.get("description")
            if not all([dossier, title, description]):
                raise ValueError("Dados ausentes no estado para a geração da imagem.")
            image_bytes = await create_image_use_case(
                dossier=dossier, copy_title=title, copy_description=description,
                context=context, step_key="create_image", content_generator=content_generator,
                media_generator=media_generator, state_repo=state_repo,
            )
            image_filename = "post_image.jpg"
            saved_path = await state_repo.save_artifact(context, image_filename, image_bytes)
            run.state_data["generated_image_path"] = saved_path
            run.state_data["generated_image_filename"] = image_filename
            run.current_step = "image_created"
            run.step_attempt = 0
            logger.info(f"Etapa 'copy_created' concluída. Imagem base salva. Próxima: '{run.current_step}'")

        # Etapa 4: Edição da Imagem e Renderização do Texto
        if run.current_step == "image_created":
            logger.info("Executando etapa 'image_created': Edição e Renderização Final da Imagem.")
            context = RunContext(workflow_name=run.workflow_name, run_id=run.run_id)
            
            image_base_filename = run.state_data.get("generated_image_filename")
            title = run.state_data.get("title")
            if not all([image_base_filename, title]):
                raise ValueError("Nome do arquivo da imagem base ou título ausente do estado.")
            
            original_image_bytes = await state_repo.load_artifact(context, image_base_filename)

            final_image_bytes = await edit_image_use_case(
                image_bytes=original_image_bytes, title=title,
                theme=theme, context=context, state_repo=state_repo,
            )
            
            final_filename = "final_post.jpg"
            final_path = await state_repo.save_artifact(context, final_filename, final_image_bytes)
            
            run.state_data["final_image_path"] = final_path
            run.state_data["final_image_filename"] = final_filename

            run.current_step = "final_image_created"
            run.step_attempt = 0
            logger.info(f"Etapa 'image_created' concluída. Imagem final salva. Próxima: '{run.current_step}'")

        # --- Conclusão do Workflow ---
        if run.current_step == "final_image_created":
            run.status = WorkflowStatus.COMPLETED
            logger.info(f"Workflow ID {run.run_id} concluído com sucesso.")

    except Exception as e:
        logger.error(f"Erro no orquestrador para ID {run.run_id} na etapa '{run.current_step}'", exc_info=True)
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
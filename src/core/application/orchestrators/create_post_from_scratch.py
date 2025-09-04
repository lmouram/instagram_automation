# src/core/application/orchestrators/create_post_from_scratch.py

"""
Orquestrador para o workflow de criação de um post a partir do zero.
"""

import logging
from datetime import datetime, timezone

# Importa RunContext junto com as outras entidades de domínio
from src.core.domain import WorkflowRun, WorkflowStatus, RunContext
from src.core.application.use_cases import create_dossier_use_case
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

    Este orquestrador gerencia a `WorkflowRun` através de suas etapas,
    invocando os casos de uso apropriados para cada uma.

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
    
    # Armazena a versão original para verificar se houve mudanças
    original_version = run.version

    try:
        # Garante que o status seja RUNNING ao iniciar o processamento.
        if run.status != WorkflowStatus.RUNNING:
            run.status = WorkflowStatus.RUNNING
            run.step_attempt = 0 # Reseta a contagem de tentativas ao iniciar uma etapa

        # --- MÁQUINA DE ESTADOS ---

        # Etapa 1: Geração do Dossiê
        if run.current_step == "start":
            logger.info(f"Executando etapa 'start': Geração do dossiê.")
            
            # 1. Cria o contexto da execução a partir da entidade WorkflowRun
            context = RunContext(workflow_name=run.workflow_name, run_id=run.run_id)
            
            # 2. A chave agora identifica a etapa dentro do contexto
            step_key = "create_dossier"
            
            # 3. Chama o caso de uso com a nova assinatura
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

        # Etapa 2: Geração do Texto do Post (Futura implementação)
        # elif run.current_step == "dossier_created":
        #     logger.info(f"Executando etapa 'dossier_created': Geração do texto do post.")
        #     # ... chamar create_post_text_use_case ...
        #     run.state_data["post_text"] = post_text
        #     run.current_step = "post_text_created"

        # ... outras etapas futuras ...


        # --- Conclusão do Workflow ---
        # Verifica se a etapa atual é a última etapa bem-sucedida do fluxo
        if run.current_step == "dossier_created": # Por enquanto, esta é a última
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
    
    # Atualiza o timestamp de modificação apenas se o estado do run foi alterado.
    # A versão só é incrementada pelo repositório no momento do `update`.
    # A responsabilidade do orquestrador é apenas modificar o objeto.
    run.updated_at = datetime.now(timezone.utc)

    return run
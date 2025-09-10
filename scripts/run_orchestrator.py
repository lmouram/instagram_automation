# scripts/run_orchestrator.py

"""
Driving Adapter Genérico para Execução de Orquestradores de Workflow.

Este script é o ponto de entrada principal para iniciar, retomar ou re-executar
etapas de qualquer processo de negócio (workflow) definido na camada de aplicação.

Responsabilidades:
1.  Parsear argumentos de linha de comando.
2.  Atuar como o "Composition Root", inicializando todas as dependências.
3.  Gerenciar o ciclo de vida da `WorkflowRun`.
4.  Opcionalmente, "rebobinar" o estado de um workflow para re-executar uma etapa.
5.  Disparar a execução para o orquestrador correto.
6.  Persistir o estado final do workflow.

Exemplos de Uso:
-----------------
# Iniciar um novo workflow
python scripts/run_orchestrator.py --workflow-name create_post_from_scratch --theme "Benefícios da meditação"

# Retomar um workflow existente
python scripts/run_orchestrator.py --workflow-name create_post_from_scratch --run-id "uuid-do-run"

# Re-executar apenas a etapa 'edit_image' de um workflow existente
python scripts/run_orchestrator.py --workflow-name create_post_from_scratch --run-id "uuid-do-run" --rerun-step edit_image
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import config, logger
# Domínio e Contratos
from src.core.domain import RunContext, WorkflowRun, WorkflowStatus
# Registries
from src.core.application.registries import WORKFLOW_STEPS
# Orquestradores
from src.core.application.orchestrators import create_post_from_scratch_orchestrator
# Adaptadores
from src.adapters.llm import GeminiAdapter, GeminiAPIError
from src.adapters.media import GoogleImageAdapter, ImageGenerationError
from src.adapters.persistence import (
    FileStateRepository,
    FileWorkflowRepository,
    ConcurrencyError,
    ArtifactNotFoundError
)
from src.adapters.theming import (
    FileSystemThemeLoaderAdapter,
    ThemeNotFoundError
)

# --- Mapeamento de Workflows ---
ORCHESTRATORS = {
    "create_post_from_scratch": create_post_from_scratch_orchestrator,
}

# --- Setup de Dependências ---
def setup_dependencies() -> Dict[str, Any]:
    """Inicializa e retorna todas as dependências concretas (adaptadores)."""
    log = logger.get_logger("DependencySetup")
    log.info("Inicializando dependências...")

    themes_base_path = Path(__file__).resolve().parent.parent / "src" / "assets" / "themes"
    
    deps = {
        "workflow_repo": FileWorkflowRepository(),
        "state_repo": FileStateRepository(),
        "content_generator": GeminiAdapter(api_key=config.GEMINI_API_KEY),
        "media_generator": GoogleImageAdapter(api_key=config.GEMINI_API_KEY, aspect_ratio="3:4"),
        "theme_loader": FileSystemThemeLoaderAdapter(base_path=themes_base_path),
    }
    log.info("Dependências inicializadas com sucesso.")
    return deps


async def main():
    script_logger = logger.get_logger(__name__)
    script_logger.info("=" * 40)
    script_logger.info("=== INICIANDO EXECUTOR DE ORQUESTRADORES ===")
    script_logger.info("=" * 40)

    # --- Configuração e Validação dos Argumentos ---
    parser = argparse.ArgumentParser(description="Executor de Workflows da Aplicação.")
    parser.add_argument("--workflow-name", required=True, choices=ORCHESTRATORS.keys())
    parser.add_argument("--theme-name", default="default")
    parser.add_argument("--theme", type=str, help="Tema para iniciar um NOVO workflow.")
    parser.add_argument("--run-id", type=str, help="ID de um workflow existente para retomar ou re-executar.")
    parser.add_argument("--rerun-step", type=str, help="Força a re-execução de uma etapa. Requer --run-id.")
    args = parser.parse_args()

    if args.theme and args.run_id:
        parser.error("--theme (para novos workflows) e --run-id (para existentes) são mutuamente exclusivos.")
    if not args.theme and not args.run_id:
        parser.error("É necessário fornecer --theme (para um novo workflow) ou --run-id (para um existente).")
    if args.rerun_step and not args.run_id:
        parser.error("--rerun-step requer --run-id.")

    try:
        deps = setup_dependencies()
        workflow_repo = deps["workflow_repo"]
        run: WorkflowRun | None = None

        if args.run_id:
            run = await workflow_repo.get_by_id(args.run_id, args.workflow_name)
            if not run:
                script_logger.error(f"Execução com ID '{args.run_id}' não encontrada.")
                return
            script_logger.info(f"Retomando workflow '{args.workflow_name}' com ID: {args.run_id}")
        elif args.theme:
            run = WorkflowRun(
                workflow_name=args.workflow_name, status=WorkflowStatus.PENDING,
                payload={"theme": args.theme}
            )
            await workflow_repo.create(run)
            script_logger.info(f"Iniciando novo workflow '{args.workflow_name}' com ID: {run.run_id}")

        if args.rerun_step:
            script_logger.warning(f"### MODO DE REEXECUÇÃO ATIVADO PARA ETAPA: '{args.rerun_step}' ###")
            
            workflow_steps = WORKFLOW_STEPS.get(run.workflow_name, {})
            if args.rerun_step not in workflow_steps:
                script_logger.error(f"Etapa '{args.rerun_step}' é inválida para o workflow '{run.workflow_name}'. Válidas: {list(workflow_steps.keys())}")
                return

            step_config = workflow_steps[args.rerun_step]
            
            state_repo = deps["state_repo"]
            context = RunContext(workflow_name=run.workflow_name, run_id=run.run_id)
            step_order = list(workflow_steps.keys())
            step_index = step_order.index(args.rerun_step)
            steps_to_invalidate = step_order[step_index:]
            
            script_logger.info(f"Invalidando cache para as etapas: {steps_to_invalidate}")
            for step_name in steps_to_invalidate:
                key_to_delete = workflow_steps[step_name].step_key
                await state_repo.delete(context, key_to_delete)
                if step_name == "edit_image":
                    await state_repo.delete(context, "post-image-masked.jpg")
                    await state_repo.delete(context, "final_post.jpg")
            
            run.current_step = step_config.entry_state
            run.status = WorkflowStatus.RUNNING
            run.last_error_msg = None
            run.retry_at = None
            run.step_attempt = 0
            script_logger.info(f"Workflow rebobinado para o estado '{run.current_step}'.")

        # --- Dispatcher e Execução ---
        theme_contract = deps["theme_loader"].load(args.theme_name)
        orchestrator_func = ORCHESTRATORS[run.workflow_name]
        
        script_logger.info(f"Executando orquestrador para a execução ID: {run.run_id}")

        # --- CORREÇÃO APLICADA AQUI ---
        # A chamada anterior `await orchestrator_func(run=run, theme=theme_contract, **deps)`
        # estava passando chaves extras (`workflow_repo`, `theme_loader`) que o orquestrador
        # não espera. A chamada correta injeta apenas as dependências explícitas.
        updated_run = await orchestrator_func(
            run=run,
            content_generator=deps["content_generator"],
            media_generator=deps["media_generator"],
            state_repo=deps["state_repo"],
            theme=theme_contract,
        )

        # --- Persistência do Estado Final ---
        await workflow_repo.update(updated_run)
        script_logger.info(
            f"Execução {updated_run.run_id} finalizada. "
            f"Status: {updated_run.status.value}, Etapa final: {updated_run.current_step}"
        )

    except (ThemeNotFoundError, ArtifactNotFoundError) as e:
        script_logger.error(f"Erro de configuração ou estado: {e}", exc_info=False)
    except (ConcurrencyError, GeminiAPIError, ImageGenerationError) as e:
        script_logger.error(f"Erro de execução controlada: {type(e).__name__} - {e}", exc_info=True)
    except Exception as e:
        script_logger.critical("Ocorreu um erro fatal e inesperado no executor.", exc_info=True)
    finally:
        script_logger.info("=" * 40)
        script_logger.info("=== EXECUTOR DE ORQUESTRADORES FINALIZADO ===")
        script_logger.info("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
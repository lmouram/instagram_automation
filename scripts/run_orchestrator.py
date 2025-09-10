# scripts/run_orchestrator.py

"""
Driving Adapter Genérico para Execução de Orquestradores de Workflow.

Este script é o ponto de entrada principal para iniciar ou retomar qualquer
processo de negócio (workflow) definido na camada de aplicação. Ele é projetado
para ser chamado por um scheduler ou manualmente.

Responsabilidades:
1.  Parsear argumentos de linha de comando (workflow, run_id, tema, etc.).
2.  Atuar como o "Composition Root", inicializando todas as dependências (adaptadores).
3.  Gerenciar o ciclo de vida da `WorkflowRun` (criar ou carregar).
4.  Carregar a configuração do tema visual (`ThemeContract`).
5.  Disparar a execução para o orquestrador correto, injetando as dependências.
6.  Persistir o estado final do workflow.

Exemplos de Uso:
-----------------
# Iniciar um novo workflow com o tema padrão
python scripts/run_orchestrator.py --workflow-name create_post_from_scratch --theme "Benefícios da meditação"

# Iniciar um novo workflow especificando um tema (quando houver mais de um)
python scripts/run_orchestrator.py --workflow-name create_post_from_scratch --theme "IA na medicina" --theme-name "tema_medicina"

# Retomar a execução de um workflow existente
python scripts/run_orchestrator.py --workflow-name create_post_from_scratch --run-id "uuid-do-run"
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

# Adiciona o caminho raiz ao sys.path para importações de `src`
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import config, logger
# Domínio e Contratos
from src.core.domain import WorkflowRun, WorkflowStatus
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

# --- Setup de Dependências (Composition Root) ---
def setup_dependencies() -> Dict[str, Any]:
    """
    Inicializa e retorna todas as dependências concretas (adaptadores).
    """
    log = logger.get_logger("DependencySetup")
    log.info("Inicializando dependências para o orquestrador...")

    # Adaptadores de persistência
    workflow_repo = FileWorkflowRepository()
    state_repo = FileStateRepository()

    # Adaptadores de serviços externos (IA)
    gemini_adapter = GeminiAdapter(api_key=config.GEMINI_API_KEY)
    image_adapter = GoogleImageAdapter(
        api_key=config.GEMINI_API_KEY,
        aspect_ratio="3:4"  # Consistente com a configuração do tema
    )

    # Adaptador de Tema
    themes_base_path = Path(__file__).resolve().parent.parent / "src" / "assets" / "themes"
    theme_loader = FileSystemThemeLoaderAdapter(base_path=themes_base_path)

    log.info("Dependências inicializadas com sucesso.")
    return {
        "workflow_repo": workflow_repo,
        "state_repo": state_repo,
        "content_generator": gemini_adapter,
        "media_generator": image_adapter,
        "theme_loader": theme_loader,
    }


async def main():
    """Função principal que orquestra a execução do script."""
    script_logger = logger.get_logger(__name__)
    script_logger.info("=" * 40)
    script_logger.info("=== INICIANDO EXECUTOR DE ORQUESTRADORES ===")
    script_logger.info("=" * 40)

    # --- Configuração dos Argumentos ---
    parser = argparse.ArgumentParser(description="Executor de Workflows da Aplicação.")
    parser.add_argument("--workflow-name", required=True, choices=ORCHESTRATORS.keys(), help="O nome do workflow a ser executado.")
    parser.add_argument("--theme-name", default="default", help="O nome do tema visual a ser usado (padrão: 'default').")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--theme", type=str, help="O tema para iniciar um novo workflow `create_post_from_scratch`.")
    group.add_argument("--run-id", type=str, help="O ID de uma execução de workflow existente para retomar.")
    
    args = parser.parse_args()

    try:
        deps = setup_dependencies()
        workflow_repo = deps["workflow_repo"]
        theme_loader = deps["theme_loader"]
        run: WorkflowRun | None = None

        # --- Carregar Tema ---
        script_logger.info(f"Carregando tema: '{args.theme_name}'")
        theme_contract = theme_loader.load(args.theme_name)

        # --- Carregar ou Criar Estado do Workflow ---
        if args.run_id:
            script_logger.info(f"Retomando workflow '{args.workflow_name}' com ID: {args.run_id}")
            run = await workflow_repo.get_by_id(args.run_id, args.workflow_name)
            if not run:
                script_logger.error(f"Execução com ID '{args.run_id}' não encontrada.")
                return
        elif args.theme:
            script_logger.info(f"Iniciando novo workflow '{args.workflow_name}' com o tema: '{args.theme}'")
            run = WorkflowRun(
                workflow_name=args.workflow_name, status=WorkflowStatus.PENDING,
                payload={"theme": args.theme}
            )
            await workflow_repo.create(run)

        if not run:
            script_logger.error("Não foi possível carregar ou criar uma execução de workflow.")
            return

        # --- Dispatcher e Execução ---
        orchestrator_func = ORCHESTRATORS.get(run.workflow_name)
        if not orchestrator_func:
            script_logger.error(f"Orquestrador '{run.workflow_name}' não encontrado.")
            return

        script_logger.info(f"Executando orquestrador para a execução ID: {run.run_id}")
        
        # Injeta TODAS as dependências, incluindo o contrato do tema
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
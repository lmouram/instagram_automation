# scripts/run_orchestrator.py

"""
Driving Adapter Genérico para Execução de Orquestradores de Workflow.

Este script é o ponto de entrada principal para iniciar ou retomar qualquer
processo de negócio (workflow) definido na camada de aplicação. Ele é projetado
para ser chamado por um scheduler (como GitHub Actions) ou manualmente para
tarefas de background.

Responsabilidades:
1.  Parsear argumentos de linha de comando para determinar qual workflow executar
    e com quais dados.
2.  Atuar como o "Composition Root", inicializando todas as dependências (adaptadores).
3.  Gerenciar o ciclo de vida da entidade `WorkflowRun` (criar ou carregar).
4.  Disparar (dispatch) a execução para a função de orquestrador correta.
5.  Persistir o estado final do workflow após a execução.

Exemplos de Uso:
-----------------
# Iniciar um novo workflow de criação de post
python scripts/run_orchestrator.py --workflow-name create_post_from_scratch --theme "Benefícios da meditação"

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
# Domínio
from src.core.domain import WorkflowRun, WorkflowStatus
# Casos de Uso e Orquestradores
from src.core.application.orchestrators import create_post_from_scratch_orchestrator
# Adaptadores
from src.adapters.llm import GeminiAdapter, GeminiAPIError
from src.adapters.persistence import (
    FileStateRepository,
    FileWorkflowRepository,
    ConcurrencyError
)

# --- Mapeamento de Workflows ---

# Este dicionário é o coração do dispatcher. Para adicionar um novo workflow,
# basta importar seu orquestrador e adicioná-lo aqui.
ORCHESTRATORS = {
    "create_post_from_scratch": create_post_from_scratch_orchestrator,
    # "outro_workflow": outro_orchestrator,
}

# --- Setup de Dependências ---

def setup_dependencies() -> Dict[str, Any]:
    """
    Inicializa e retorna todas as dependências concretas (adaptadores).
    Atua como o Composition Root para este driving adapter.
    """
    log = logger.get_logger("DependencySetup")
    log.info("Inicializando dependências para o orquestrador...")

    # Adaptadores de persistência
    workflow_repo = FileWorkflowRepository()
    # Criamos um state repo com um namespace genérico para o caso de uso de dossiê
    dossier_state_repo = FileStateRepository()

    # Adaptadores externos
    gemini_adapter = GeminiAdapter(api_key=config.GEMINI_API_KEY)
    
    log.info("Dependências inicializadas com sucesso.")
    return {
        "workflow_repo": workflow_repo,
        "dossier_state_repo": dossier_state_repo,
        "gemini_adapter": gemini_adapter,
    }


async def main():
    """Função principal que orquestra a execução do script."""
    script_logger = logger.get_logger(__name__)
    script_logger.info("========================================")
    script_logger.info("=== INICIANDO EXECUTOR DE ORQUESTRADORES ===")
    script_logger.info("========================================")

    # --- Configuração dos Argumentos ---
    parser = argparse.ArgumentParser(description="Executor de Workflows da Aplicação.")
    parser.add_argument("--workflow-name", required=True, choices=ORCHESTRATORS.keys(),
                        help="O nome do workflow a ser executado.")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--theme", type=str,
                       help="O tema para iniciar um novo workflow `create_post_from_scratch`.")
    group.add_argument("--run-id", type=str,
                       help="O ID de uma execução de workflow existente para retomar.")
    
    args = parser.parse_args()

    try:
        deps = setup_dependencies()
        workflow_repo = deps["workflow_repo"]
        run: WorkflowRun | None = None

        # --- Carregar ou Criar Estado do Workflow ---
        if args.run_id:
            script_logger.info(f"Tentando retomar o workflow '{args.workflow_name}' com ID: {args.run_id}")
            run = await workflow_repo.get_by_id(args.run_id, args.workflow_name)
            if not run:
                script_logger.error(f"Execução com ID '{args.run_id}' não encontrada para o workflow '{args.workflow_name}'.")
                return
        elif args.theme:
            script_logger.info(f"Iniciando novo workflow '{args.workflow_name}' com o tema: '{args.theme}'")
            run = WorkflowRun(
                workflow_name=args.workflow_name,
                status=WorkflowStatus.PENDING,
                payload={"theme": args.theme}
            )
            await workflow_repo.create(run)

        if not run:
            script_logger.error("Não foi possível carregar ou criar uma execução de workflow.")
            return

        # --- Dispatcher e Execução ---
        orchestrator_func = ORCHESTRATORS.get(run.workflow_name)
        if not orchestrator_func:
            # Esta verificação é redundante devido ao `choices` do argparse, mas é uma boa prática
            script_logger.error(f"Orquestrador '{run.workflow_name}' não encontrado no mapeamento.")
            return

        script_logger.info(f"Executando o orquestrador para a execução ID: {run.run_id}")
        
        updated_run = await orchestrator_func(
            run=run,
            content_generator=deps["gemini_adapter"],
            state_repo=deps["dossier_state_repo"],
        )

        # --- Persistência do Estado Final ---
        await workflow_repo.update(updated_run)
        
        script_logger.info(
            f"Execução {updated_run.run_id} finalizada. "
            f"Status final: {updated_run.status.value}, "
            f"Etapa final: {updated_run.current_step}"
        )

    except (ConcurrencyError, GeminiAPIError) as e:
        script_logger.error(f"Erro de execução controlada: {e}", exc_info=True)
    except Exception as e:
        script_logger.critical("Ocorreu um erro fatal e inesperado no executor.", exc_info=True)
    finally:
        script_logger.info("========================================")
        script_logger.info("=== EXECUTOR DE ORQUESTRADORES FINALIZADO ===")
        script_logger.info("========================================")

if __name__ == "__main__":
    asyncio.run(main())
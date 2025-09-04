# scripts/dev/generate_dossier.py

"""
Script de Geração de Dossiê - Driving Adapter de Desenvolvimento.

Este script recebe um tema como argumento, utiliza a ferramenta de pesquisa do
Gemini para investigar o tema e gera um dossiê completo em formato Markdown.

Ele demonstra o uso da `StateManager` para persistir o estado de sua
execução, permitindo a retomada de trabalhos interrompidos e economizando
chamadas de API.

Exemplos de Uso:
-----------------
# Criar uma nova execução para o tema "Inteligência Artificial na Medicina"
python scripts/dev/generate_dossier.py --theme "Inteligência Artificial na Medicina"

# Retomar a execução de ID 1 (se a geração do dossiê falhou anteriormente)
python scripts/dev/generate_dossier.py --run-id 1
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Adiciona o caminho raiz ao sys.path para importações de `src`
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src import config, logger
from src.adapters.llm import GeminiAdapter, GeminiAPIError
from src.utils.state_manager import StateManager, StateNotFoundError

# --- Funções Auxiliares e Setup ---

def setup_dependencies() -> Dict[str, Any]:
    """Inicializa e retorna as dependências concretas necessárias para o script."""
    log = logger.get_logger("DependencySetup")
    log.info("Inicializando dependências...")

    gemini_adapter = GeminiAdapter(api_key=config.GEMINI_API_KEY)
    
    log.info("Dependências inicializadas com sucesso.")
    return {"gemini_adapter": gemini_adapter}


async def main():
    """Função principal que orquestra a execução do script."""
    script_logger = logger.get_logger(__name__)
    script_logger.info("========================================")
    script_logger.info("=== INICIANDO SCRIPT DE GERAÇÃO DE DOSSIÊ ===")
    script_logger.info("========================================")

    # --- Configuração dos Argumentos ---
    parser = argparse.ArgumentParser(
        description="Gera um dossiê de pesquisa sobre um tema usando o Gemini com a ferramenta de busca."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--theme", type=str, help="O tema para pesquisar e gerar o dossiê.")
    group.add_argument("--run-id", type=int, help="O ID de uma execução anterior para retomar.")
    args = parser.parse_args()

    # --- Inicialização dos Componentes ---
    try:
        deps = setup_dependencies()
        gemini_adapter: GeminiAdapter = deps["gemini_adapter"]
        state_manager = StateManager(script_name="generate_dossier")
        
        run_id = 0
        state = {}

        # --- Carregar ou Criar Estado ---
        if args.run_id:
            run_id = args.run_id
            script_logger.info(f"Retomando execução com ID: {run_id}")
            state = state_manager.load_state(run_id)
        elif args.theme:
            initial_state = {"theme": args.theme, "dossier": None}
            run_id = state_manager.create_new_run(initial_state)
            state = state_manager.load_state(run_id)
            script_logger.info(f"Nova execução criada com ID: {run_id} para o tema: '{args.theme}'")

        # --- Máquina de Estado: Etapa de Geração do Dossiê ---
        if not state.get("dossier"):
            script_logger.info(f"Dossiê para o tema '{state['theme']}' não encontrado no estado. Gerando...")
            try:
                # Na Fase 3, implementaremos este método no GeminiAdapter
                # Por enquanto, vamos simular uma chamada
                dossier_markdown = await gemini_adapter.generate_dossier(state["theme"])
                
                # Simulação para permitir o teste do script
                #script_logger.warning("MÉTODO gemini_adapter.generate_dossier AINDA NÃO IMPLEMENTADO. USANDO TEXTO SIMULADO.")
                #dossier_markdown = f"# Dossiê Simulado sobre {state['theme']}\n\nEste é um texto simulado."
                
                state["dossier"] = dossier_markdown
                state_manager.save_state(run_id, state)
                script_logger.info(f"Dossiê gerado e salvo com sucesso no estado da execução ID: {run_id}.")
            except GeminiAPIError as e:
                script_logger.error(f"Falha ao chamar a API do Gemini para gerar o dossiê: {e}", exc_info=True)
                sys.exit(1)
        else:
            script_logger.info(f"Dossiê já existe na execução ID {run_id}. Pulando etapa de geração.")

        # --- Saída ---
        print("\n" + "="*80)
        print(f"DOSSIÊ COMPLETO (Execução ID: {run_id})")
        print("="*80 + "\n")
        print(state["dossier"])
        print("\n" + "="*80)

    except (StateNotFoundError, GeminiAPIError) as e:
        script_logger.error(f"Erro de execução: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        script_logger.critical("Ocorreu um erro fatal e inesperado.", exc_info=True)
        sys.exit(1)
    finally:
        script_logger.info("========================================")
        script_logger.info("=== SCRIPT DE GERAÇÃO DE DOSSIÊ FINALIZADO ===")
        script_logger.info("========================================")

if __name__ == "__main__":
    # Ponto de entrada do script.
    asyncio.run(main())
# scripts/run_publisher.py

"""
Script de Publicação Agendada - Driving Adapter.

Este script é o ponto de entrada para o processo de publicação automática.
Ele foi projetado para ser executado por um agendador (como um cron job ou
uma GitHub Action) em intervalos regulares.

Responsabilidades:
1.  Inicializar todas as dependências da aplicação (Composition Root).
2.  Invocar o caso de uso `publish_scheduled_posts_use_case`.
3.  Registrar logs detalhados da execução para monitoramento e depuração.
"""

import asyncio
import logging

# Adiciona o caminho raiz do projeto ao sys.path para garantir que as
# importações de `src` funcionem corretamente ao executar o script diretamente.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from supabase import create_client, Client

# Importações do nosso projeto
from src import config, logger
from src.core.application import publish_scheduled_posts_use_case
from src.adapters.llm.gemini_adapter import GeminiAdapter
from src.adapters.media.google_image_adapter import GoogleImageAdapter
from src.adapters.observability.logging_adapter import LoggingObservabilityAdapter
from src.adapters.persistence import SupabasePostRepository, SupabaseAuditEventRepository
from src.adapters.social.instagram_adapter import InstagramAdapter
from src.adapters.storage.supabase_storage_adapter import SupabaseStorageAdapter


def setup_dependencies():
    """
    Inicializa e retorna todas as dependências concretas necessárias para o job.
    
    Esta função atua como o "Composition Root" para este script, montando
    a aplicação ao conectar os adaptadores às suas implementações concretas.
    
    NOTA: A lógica é similar à de `streamlit_app.py`. Em um projeto maior,
    isso poderia ser refatorado para um "container" de injeção de dependência.

    Returns:
        Dict[str, Any]: Um dicionário contendo as instâncias dos adaptadores.
    """
    # Inicializa o logger para garantir que a configuração seja aplicada
    log = logger.get_logger("DependencySetup")
    log.info("Inicializando dependências para o job do publicador...")

    supabase_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

    # Adaptadores
    observability_adapter = LoggingObservabilityAdapter(logger.get_logger("ObservabilityAdapter"))
    persistence_adapter = SupabaseAdapter(supabase_client)
    post_repo = SupabasePostRepository(supabase_client)
    audit_repo = SupabaseAuditEventRepository(supabase_client)
    social_publisher_adapter = InstagramAdapter(
        account_id=config.INSTAGRAM_ACCOUNT_ID,
        access_token=config.META_ACCESS_TOKEN
    )

    
    log.info("Dependências inicializadas com sucesso.")
    
    return {
        "observability": observability_adapter,
        "persistence": persistence_adapter,
        "social_publisher": social_publisher_adapter,
        "post_repository": post_repo,
        "audit_repository": audit_repo,
    }


async def main():
    """
    Função principal assíncrona que executa o caso de uso de publicação.
    """
    # Garante que o logger global esteja configurado
    script_logger = logger.get_logger(__name__)
    script_logger.info("=============================================")
    script_logger.info("=== INICIANDO JOB DE PUBLICAÇÃO AGENDADA ===")
    script_logger.info("=============================================")

    try:
        # 1. Monta a aplicação inicializando as dependências
        deps = setup_dependencies()

        # 2. Executa o caso de uso
        script_logger.info("Invocando o caso de uso 'publish_scheduled_posts_use_case'...")
        results = await publish_scheduled_posts_use_case(
            post_repository=deps["post_repository"],
            social_publisher=deps["social_publisher"],
            audit_repository=deps["audit_repository"],
            observability=deps["observability"],
        )
        script_logger.info(f"Caso de uso concluído. Resultado: {results}")

    except Exception as e:
        script_logger.critical(
            "Ocorreu um erro fatal durante a execução do job do publicador.",
            exc_info=True  # Adiciona o traceback completo ao log
        )
    finally:
        script_logger.info("==============================================")
        script_logger.info("=== JOB DE PUBLICAÇÃO AGENDADA FINALIZADO ===")
        script_logger.info("==============================================")


if __name__ == "__main__":
    # Ponto de entrada do script: executa a função main assíncrona.
    asyncio.run(main())
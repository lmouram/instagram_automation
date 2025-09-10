# src/core/application/use_cases/create_image.py

"""
Caso de Uso: Criar Imagem para Post.

Este módulo contém o caso de uso responsável por orquestrar o processo completo
de geração de uma imagem para um post de rede social. Ele funciona como uma
unidade de trabalho atômica, idempotente e reutilizável dentro da camada de
aplicação.
"""

import logging
from typing import Any, Dict

from src.core.application.prompts import get_prompt_contract
from src.core.domain.entities import RunContext
from src.ports.content_generator import ContentGeneratorPort
from src.ports.media_generator import MediaGeneratorPort
from src.ports.state_repository import StateRepositoryPort

logger = logging.getLogger(__name__)


def _build_final_image_prompt(components: Dict[str, Any]) -> str:
    """
    Constrói o prompt final para o modelo de imagem a partir dos componentes estruturados.
    """
    required_keys = ['subject', 'context_background', 'style', 'lighting', 'camera_details', 'quality_modifiers']
    if not all(key in components for key in required_keys):
        missing_keys = [key for key in required_keys if key not in components]
        raise ValueError(f"Componentes de prompt ausentes: {', '.join(missing_keys)}")

    final_prompt = (
        f"{components['subject']} {components['context_background']}, "
        f"{components['style']}, {components['lighting']}, "
        f"{components['camera_details']}, {components['quality_modifiers']}"
    )
    logger.debug(f"Prompt de imagem final construído: {final_prompt}")
    return final_prompt


async def create_image_use_case(
    theme: str,
    copy_title: str,
    copy_description: str,
    context: RunContext,
    step_key: str,
    content_generator: ContentGeneratorPort,
    media_generator: MediaGeneratorPort,
    state_repo: StateRepositoryPort,
) -> bytes:
    """
    Orquestra a geração completa de uma imagem para o post, garantindo idempotência.

    Args:
        theme (str): O tema central do post.
        copy_title (str): O título gerado para o post.
        copy_description (str): A descrição (legenda) gerada para o post.
        context (RunContext): O contexto da execução do workflow (workflow_name, run_id).
        step_key (str): A chave de idempotência única para esta etapa (ex: "create_image").
        content_generator (ContentGeneratorPort): Porta para o serviço de IA textual.
        media_generator (MediaGeneratorPort): Porta para o serviço de geração de imagem.
        state_repo (StateRepositoryPort): Porta para o cache de resultados.

    Returns:
        bytes: Os dados binários brutos da imagem gerada.
    """
    logger.info(f"Iniciando caso de uso 'create_image' para a chave '{step_key}'.")

    final_prompt = None
    logger.debug(f"Verificando estado para a chave '{step_key}' no contexto {context}")
    cached_state = await state_repo.load(context, step_key)

    if cached_state and "final_image_prompt" in cached_state:
        final_prompt = cached_state["final_image_prompt"]
        logger.info(f"Prompt de imagem encontrado no estado para a chave '{step_key}'.")
    else:
        logger.info(f"Nenhum prompt em cache encontrado para '{step_key}'. Gerando novos componentes.")
        
        # --- CORREÇÃO APLICADA AQUI ---
        # A chamada agora usa 'theme' em vez de 'dossier', conforme a nova assinatura
        # do prompt 'image_prompt_components'.
        contract = get_prompt_contract(
            prompt_name="image_prompt_components",
            version="1.0",
            theme=theme,
            copy_title=copy_title,
            copy_description=copy_description
        )
        prompt_components = await content_generator.generate(contract)

        final_prompt = _build_final_image_prompt(prompt_components)
        await state_repo.save(context, step_key, {"final_image_prompt": final_prompt})
        logger.info(f"Novo prompt de imagem salvo no estado para a chave '{step_key}'.")

    if not final_prompt:
        raise ValueError("O prompt final da imagem não pôde ser determinado.")

    logger.info("Invocando o gerador de mídia para criar a imagem final...")
    image_bytes = await media_generator.generate_image(prompt=final_prompt)
    logger.info(f"Imagem gerada com sucesso. Tamanho: {len(image_bytes) / 1024:.2f} KB.")

    return image_bytes
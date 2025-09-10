# src/core/application/use_cases/copywriter.py

"""
Caso de Uso: Gerar Copy para Post de Instagram.

Este caso de uso invoca um LLM com persona de copywriter para transformar um
tema e um dossiê informativo em um título e descrição persuasivos,
garantindo idempotência.
"""

import logging
from typing import Dict

from src.core.application.prompts import get_prompt_contract
from src.core.domain.entities import RunContext
from src.ports.content_generator import ContentGeneratorPort
from src.ports.state_repository import StateRepositoryPort

logger = logging.getLogger(__name__)


async def copywriter_use_case(
    theme: str,
    dossier: str,
    context: RunContext,
    step_key: str,
    content_generator: ContentGeneratorPort,
    state_repo: StateRepositoryPort,
) -> Dict[str, str]:
    """
    Gera título e descrição para um post de Instagram a partir de um tema e dossiê.

    Verifica o cache de estado para idempotência. Se não houver resultado em
    cache, ele constrói o `LLMContract` para copywriting, invoca o
    `content_generator`, salva o resultado e o retorna.

    Args:
        theme (str): O tema central que guia a criação da copy.
        dossier (str): O conteúdo informativo do dossiê de pesquisa.
        context (RunContext): O contexto da execução do workflow.
        step_key (str): A chave única para esta etapa (ex: "generate_copy").
        content_generator (ContentGeneratorPort): Porta para o serviço de IA.
        state_repo (StateRepositoryPort): Porta para o cache de resultados.

    Returns:
        Dict[str, str]: Um dicionário contendo "title" e "description".
    """
    logger.debug(f"Verificando estado para a chave de copy '{step_key}' no contexto {context}")
    cached_state = await state_repo.load(context, step_key)
    if cached_state and "title" in cached_state and "description" in cached_state:
        logger.info(f"Copy encontrada no estado para a chave '{step_key}'. Pulando a geração.")
        return {
            "title": cached_state["title"],
            "description": cached_state["description"],
        }

    logger.info(f"Gerando nova copy para a chave '{step_key}'.")
    
    # 1. Usa o registro para obter o contrato, agora passando o 'theme'.
    copy_contract = get_prompt_contract(
        prompt_name="copywriting",
        version="1.0",
        theme=theme,
        dossier=dossier
    )

    # 2. Invoca o gerador de conteúdo genérico
    copy_result_dict = await content_generator.generate(copy_contract)
    
    # 3. Salva o resultado completo no estado
    await state_repo.save(context, step_key, copy_result_dict)
    logger.info(f"Nova copy salva no estado para a chave '{step_key}'.")
    
    # 4. Valida se as chaves esperadas estão presentes
    if "title" not in copy_result_dict or "description" not in copy_result_dict:
        raise ValueError("A resposta do LLM para a copy não continha 'title' e/ou 'description'.")

    return copy_result_dict
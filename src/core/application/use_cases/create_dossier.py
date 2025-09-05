# src/core/application/use_cases/create_dossier.py

"""
Caso de Uso: Criar um Dossiê de Pesquisa.

Este caso de uso é responsável por orquestrar a geração de um dossiê detalhado
sobre um tema específico, garantindo que a operação seja idempotente para
evitar chamadas de API desnecessárias e custosas.
"""

import logging

from src.core.domain import RunContext
# Importa o registro central de prompts em vez de uma fábrica específica
from src.core.application.prompts import get_prompt_contract
from src.ports import ContentGeneratorPort, StateRepositoryPort

logger = logging.getLogger(__name__)


async def create_dossier_use_case(
    theme: str,
    context: RunContext,
    step_key: str,
    content_generator: ContentGeneratorPort,
    state_repo: StateRepositoryPort,
) -> str:
    """
    Gera um dossiê de pesquisa para um tema, garantindo idempotência.

    Este caso de uso primeiro verifica o cache de estado. Se um resultado
    existir, ele é retornado. Caso contrário, ele utiliza o `Prompt Registry`
    para obter o contrato de dossiê, passa-o para o `content_generator`,
    salva o resultado no estado e o retorna.

    Args:
        theme (str): O tema sobre o qual o dossiê deve ser gerado.
        context (RunContext): O contexto da execução do workflow.
        step_key (str): A chave que identifica esta etapa (ex: "create_dossier").
        content_generator (ContentGeneratorPort): A porta genérica para o serviço de IA.
        state_repo (StateRepositoryPort): A porta para o cache de resultados.

    Returns:
        str: O conteúdo do dossiê em formato Markdown.
    """
    # 1. Tenta carregar o resultado de uma execução anterior (Cache Read)
    logger.debug(f"Verificando estado para a chave '{step_key}' no contexto {context}")
    cached_state = await state_repo.load(context, step_key)
    if cached_state and "dossie" in cached_state and cached_state["dossie"]:
        logger.info(f"Dossiê encontrado no estado para a chave '{step_key}'. Pulando a geração.")
        return cached_state["dossie"]

    # 2. Se não houver cache, usa o registro para obter o contrato e gerar o dossiê
    logger.info(f"Gerando novo dossiê para o tema '{theme}' (chave: '{step_key}').")
    
    # Usa o registro para obter o contrato de prompt para esta tarefa
    dossier_contract = get_prompt_contract(
        prompt_name="dossier",
        version="1.0", # Pode ser alterado para "latest" se desejado
        theme=theme
    )
    
    # Invoca o gerador de conteúdo genérico com o contrato
    result_dict = await content_generator.generate(dossier_contract)

    # 3. Salva o dicionário de resultado completo no estado
    await state_repo.save(context, step_key, result_dict)
    logger.info(f"Novo dossiê salvo no estado para a chave '{step_key}'.")
    
    # 4. Retorna a parte principal do resultado (o dossiê)
    dossier_content = result_dict.get("dossie")
    if not dossier_content:
        raise ValueError("A resposta do LLM para o dossiê não continha a chave 'dossie'.")
        
    return dossier_content
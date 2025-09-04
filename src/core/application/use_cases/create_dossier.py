# src/core/application/use_cases/create_dossier.py

"""
Caso de Uso: Criar um Dossiê de Pesquisa.

Este caso de uso é responsável por orquestrar a geração de um dossiê detalhado
sobre um tema específico, garantindo que a operação seja idempotente para
evitar chamadas de API desnecessárias e custosas.
"""

import logging

# RunContext é uma estrutura de dados do DOMÍNIO
from src.core.domain import RunContext 
# Importa as portas e o novo DTO de contexto
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

    Este caso de uso primeiro verifica, dentro do contexto da execução atual, se um
    resultado para a `step_key` fornecida já existe. Se existir, ele retorna o
    resultado em cache. Caso contrário, invoca o `content_generator`, salva
    o novo resultado no estado e o retorna.

    Args:
        theme (str): O tema sobre o qual o dossiê deve ser gerado.
        context (RunContext): O contexto da execução do workflow, que informa
                              onde o estado deve ser persistido.
        step_key (str): Uma chave única que identifica esta etapa específica
                        dentro do workflow (ex: "create_dossier").
        content_generator (ContentGeneratorPort): A porta para o serviço de
                                                  geração de conteúdo (LLM).
        state_repo (StateRepositoryPort): A porta para o repositório de estado
                                          atômico (cache de resultados).

    Returns:
        str: O conteúdo do dossiê em formato Markdown.

    Raises:
        Qualquer exceção levantada pelo `content_generator` (ex: GeminiAPIError)
        será propagada para o chamador.
    """
    # 1. Tenta carregar o resultado de uma execução anterior (Cache Read)
    logger.debug(f"Verificando estado para a chave '{step_key}' no contexto {context}")
    cached_state = await state_repo.load(context, step_key)
    if cached_state and "dossier" in cached_state and cached_state["dossier"]:
        logger.info(f"Dossiê encontrado no estado para a chave '{step_key}'. Pulando a geração.")
        return cached_state["dossier"]

    # 2. Se não houver cache, gera o dossiê (Operação Principal)
    logger.info(f"Gerando novo dossiê para o tema '{theme}' (chave: '{step_key}').")
    dossier = await content_generator.generate_dossier(theme)

    # 3. Salva o resultado no estado para futuras execuções (Cache Write)
    new_state = {"dossier": dossier, "theme": theme}
    await state_repo.save(context, step_key, new_state)
    logger.info(f"Novo dossiê salvo no estado para a chave '{step_key}'.")
    
    return dossier
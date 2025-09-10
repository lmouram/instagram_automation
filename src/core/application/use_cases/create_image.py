# src/core/application/use_cases/create_image.py

"""
Caso de Uso: Criar Imagem para Post.

Este módulo contém o caso de uso responsável por orquestrar o processo completo
de geração de uma imagem para um post de rede social. Ele funciona como uma
unidade de trabalho atômica, idempotente e reutilizável dentro da camada de
aplicação.

Sua responsabilidade única é encapsular a lógica de negócio de três fases:
1.  Gerar componentes conceituais para um prompt de imagem usando um LLM.
2.  Construir o prompt de imagem final a partir desses componentes.
3.  Invocar um serviço de geração de mídia para criar a imagem.

Este caso de uso depende exclusivamente de abstrações (Portas), aderindo ao
Princípio da Inversão de Dependência (DIP).
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

    Esta é uma função pura que garante uma formatação consistente do prompt final.
    A ordem de concatenação dos componentes pode ser otimizada para melhor
    performance do modelo de imagem subjacente.

    Args:
        components (Dict[str, Any]): Dicionário com os componentes do prompt
                                     gerados pelo LLM, validados pelo schema
                                     `ImagePromptComponentsOutput`.

    Returns:
        str: A string do prompt de imagem final, pronta para ser enviada ao
             `MediaGeneratorPort`.
    """
    # Validação para garantir que os componentes essenciais estão presentes
    required_keys = ['subject', 'context_background', 'style', 'lighting', 'camera_details', 'quality_modifiers']
    if not all(key in components for key in required_keys):
        missing_keys = [key for key in required_keys if key not in components]
        raise ValueError(f"Componentes de prompt ausentes: {', '.join(missing_keys)}")

    # A ordem é importante: Sujeito, Cenário, Estilo, Iluminação, Câmera, Qualidade.
    final_prompt = (
        f"{components['subject']} {components['context_background']}, "
        f"{components['style']}, {components['lighting']}, "
        f"{components['camera_details']}, {components['quality_modifiers']}"
    )
    logger.debug(f"Prompt de imagem final construído: {final_prompt}")
    return final_prompt


async def create_image_use_case(
    dossier: str,
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

    Este caso de uso implementa a lógica de cache para a parte mais determinística
    e custosa (geração de componentes do prompt). Se o caso de uso for executado
    novamente, ele reutilizará o prompt de imagem salvo para garantir
    consistência visual e economizar custos de API, mas ainda re-gerará a imagem,
    permitindo novas tentativas em caso de falha no `media_generator`.

    Args:
        dossier (str): O conteúdo completo do dossiê de pesquisa.
        copy_title (str): O título gerado para o post.
        copy_description (str): A descrição (legenda) gerada para o post.
        context (RunContext): O contexto da execução do workflow (workflow_name, run_id).
        step_key (str): A chave de idempotência única para esta etapa (ex: "create_image").
        content_generator (ContentGeneratorPort): A porta injetada para o serviço de
                                                  geração de conteúdo textual (LLM).
        media_generator (MediaGeneratorPort): A porta injetada para o serviço de
                                              geração de imagem.
        state_repo (StateRepositoryPort): A porta injetada para o repositório de
                                          estado, usada para cache e idempotência.

    Returns:
        bytes: Os dados binários brutos da imagem gerada (ex: em formato WEBP ou PNG).

    Raises:
        ValueError: Se os dados de entrada necessários (dossiê, etc.) forem inválidos ou
                    se a resposta do LLM não contiver os componentes esperados.
        Exception: Pode propagar exceções das portas subjacentes em caso de falhas
                   de API, parsing ou validação.
    """
    logger.info(f"Iniciando caso de uso 'create_image' para a chave '{step_key}'.")

    # --- IDEMPOTÊNCIA E FASE 1 & 2 ---
    # Tenta carregar o prompt final de uma execução anterior para economizar tokens.
    final_prompt = None
    logger.debug(f"Verificando estado para a chave '{step_key}' no contexto {context}")
    cached_state = await state_repo.load(context, step_key)

    if cached_state and "final_image_prompt" in cached_state:
        final_prompt = cached_state["final_image_prompt"]
        logger.info(f"Prompt de imagem encontrado no estado para a chave '{step_key}'. Pulando geração de componentes.")
    else:
        logger.info(f"Nenhum prompt em cache encontrado para '{step_key}'. Gerando novos componentes.")
        # FASE 1: Gerar componentes do prompt com LLM
        contract = get_prompt_contract(
            prompt_name="image_prompt_components",
            version="1.0",  # ou "latest"
            dossier=dossier,
            copy_title=copy_title,
            copy_description=copy_description
        )
        prompt_components = await content_generator.generate(contract)

        # FASE 2: Construir o prompt final e salvar no estado
        final_prompt = _build_final_image_prompt(prompt_components)
        await state_repo.save(context, step_key, {"final_image_prompt": final_prompt})
        logger.info(f"Novo prompt de imagem salvo no estado para a chave '{step_key}'.")

    # --- FASE 3: Gerar a imagem ---
    if not final_prompt:
        # Medida de segurança, embora improvável de acontecer com a lógica acima.
        raise ValueError("O prompt final da imagem não pôde ser determinado.")

    logger.info("Invocando o gerador de mídia para criar a imagem final...")
    image_bytes = await media_generator.generate_image(prompt=final_prompt)
    logger.info(f"Imagem gerada com sucesso. Tamanho: {len(image_bytes) / 1024:.2f} KB.")

    return image_bytes
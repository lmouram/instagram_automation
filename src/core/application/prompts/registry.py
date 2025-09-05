# src/core/application/prompts/registry.py

"""
Módulo do Registro de Prompts.

Este módulo atua como uma camada de acesso centralizada para todos os
`LLMContract`s da aplicação. Ele usa importação dinâmica para carregar
contratos de prompt por nome e versão, desacoplando os casos de uso da
estrutura de arquivos física dos prompts.

A convenção de diretório esperada é:
`prompts/<prompt_name>/v<major>_<minor>.py`
"""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Any

from src.core.application.contracts import LLMContract

logger = logging.getLogger(__name__)

# O caminho base para o pacote de prompts
PROMPTS_BASE_PATH = Path(__file__).parent


class PromptNotFoundError(Exception):
    """Levantada quando um prompt ou versão não pode ser encontrado."""
    pass


def _get_latest_version(prompt_name: str) -> str:
    """Encontra a última versão de um prompt varrendo os nomes dos arquivos."""
    prompt_dir = PROMPTS_BASE_PATH / prompt_name
    if not prompt_dir.is_dir():
        raise PromptNotFoundError(f"Diretório para o prompt '{prompt_name}' não encontrado.")

    versions = []
    for file in prompt_dir.glob("v*_*py"):
        if file.name == "__init__.py":
            continue
        # Converte "v1_0.py" para "1.0"
        version_str = file.stem.replace("v", "").replace("_", ".")
        versions.append(version_str)

    if not versions:
        raise PromptNotFoundError(f"Nenhum arquivo de versão encontrado para o prompt '{prompt_name}'.")

    # Ordena as versões de forma simples (funciona para major.minor)
    # Para versionamento semântico completo, usaríamos a biblioteca `semver`.
    versions.sort(key=lambda s: list(map(int, s.split('.'))), reverse=True)
    return versions[0]


def get_prompt_contract(prompt_name: str, version: str = "latest", **kwargs: Any) -> LLMContract:
    """
    Carrega dinamicamente e constrói um `LLMContract` por nome e versão.

    Args:
        prompt_name (str): O nome do prompt (corresponde ao diretório).
        version (str): A versão desejada (ex: "1.0") ou "latest".
        **kwargs: Argumentos a serem passados para a função `get_contract`
                  do módulo de prompt (ex: dossier="...", theme="...").

    Returns:
        LLMContract: O objeto de contrato totalmente configurado.

    Raises:
        PromptNotFoundError: Se o prompt ou a versão não forem encontrados.
    """
    logger.debug(f"Carregando contrato para prompt '{prompt_name}' @ '{version}'")

    if version == "latest":
        version = _get_latest_version(prompt_name)
        logger.debug(f"Versão 'latest' resolvida para '{version}' para o prompt '{prompt_name}'.")

    # Converte "1.0" para "v1_0" para o nome do módulo
    module_version_str = f"v{version.replace('.', '_')}"
    module_path = f"src.core.application.prompts.{prompt_name}.{module_version_str}"

    try:
        # Importa o módulo dinamicamente
        prompt_module = importlib.import_module(module_path)
    except ImportError as e:
        msg = f"Não foi possível encontrar ou importar o módulo de prompt em '{module_path}'."
        logger.error(msg, exc_info=True)
        raise PromptNotFoundError(msg) from e

    if not hasattr(prompt_module, "get_contract"):
        msg = f"O módulo de prompt '{module_path}' não possui uma função 'get_contract'."
        raise PromptNotFoundError(msg)

    # Chama a função factory `get_contract` do módulo com os argumentos fornecidos
    return prompt_module.get_contract(**kwargs)
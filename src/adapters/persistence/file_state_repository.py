# src/adapters/persistence/file_state_repository.py

"""
Módulo do Adaptador de Repositório de Estado Atômico baseado em Arquivos.

Este arquivo contém a implementação concreta da `StateRepositoryPort`. Ele salva
estados atômicos (resultados de etapas idempotentes) dentro do diretório da
execução do workflow ao qual pertencem, garantindo que todos os artefatos
de uma execução fiquem co-localizados.
"""

import re
import asyncio
import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# RunContext é uma estrutura de dados do DOMÍNIO
from src.core.domain import RunContext 

# Importa a nova porta e o DTO de contexto
from src.ports import StateRepositoryPort

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# O diretório base agora aponta para a raiz dos estados de workflow
BASE_STATES_DIR = PROJECT_ROOT / "states"


class FileStateRepository(StateRepositoryPort):
    """
    Implementa a `StateRepositoryPort` usando arquivos JSON em disco.
    """

    def __init__(self):
        """
        Inicializa o repositório de estado.
        O diretório base `states/` é gerenciado pelo `FileWorkflowRepository`.
        """
        self._base_dir = BASE_STATES_DIR
        logger.info(
            f"FileStateRepository inicializado. Diretório base para workflows: '{self._base_dir}'"
        )

    def _get_atomic_states_dir(self, context: RunContext) -> Path:
        """
        Cria e retorna o caminho para o diretório de estados atômicos de uma execução.
        Ex: .../states/workflow_name/run_id/atomic_states/
        """
        atomic_dir = self._base_dir / context.workflow_name / context.run_id / "atomic_states"
        try:
            atomic_dir.mkdir(parents=True, exist_ok=True)
            return atomic_dir
        except OSError as e:
            logger.error(f"Não foi possível criar o diretório de estados atômicos: {e}", exc_info=True)
            raise

    def _key_to_filename(self, key: str) -> str: # Vamos manter o nome, mas mudar a lógica
        """
        Converte uma chave de idempotência em um nome de arquivo seguro e legível.
        Ex: "Create Dossier: Step 1" -> "create-dossier-step-1.json"
        """
        # 1. Converte para minúsculas
        s = key.lower()
        # 2. Remove caracteres que não são alfanuméricos, espaços ou hífens
        s = re.sub(r'[^\w\s-]', '', s)
        # 3. Substitui múltiplos espaços ou hífens por um único hífen
        s = re.sub(r'[\s-]+', '-', s).strip('-')
        
        # Garante que não está vazio
        if not s:
            # Fallback para hash se a chave for completamente inválida
            return f"{hashlib.sha256(key.encode()).hexdigest()}.json"
            
        return f"{s}.json"

    async def load(self, context: RunContext, key: str) -> Optional[Dict[str, Any]]:
        """Carrega os dados associados a uma chave, dentro de um contexto de execução."""
        try:
            atomic_dir = self._get_atomic_states_dir(context)
            filename = self._key_to_filename(key)
            file_path = atomic_dir / filename
        except Exception as e:
            logger.error(f"Erro ao construir o caminho do estado para a chave '{key}': {e}", exc_info=True)
            return None

        if not file_path.exists():
            return None

        logger.debug(f"Carregando estado da chave '{key}' do arquivo '{file_path}'")
        
        def _read_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Erro ao carregar o arquivo de estado {file_path}: {e}", exc_info=True)
                return None
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _read_file)

    async def save(self, context: RunContext, key: str, data: Dict[str, Any]) -> None:
        """Salva os dados associados a uma chave, dentro de um contexto de execução."""
        try:
            atomic_dir = self._get_atomic_states_dir(context)
            filename = self._key_to_filename(key)
            file_path = atomic_dir / filename
        except Exception as e:
            logger.error(f"Erro ao construir o caminho para salvar o estado da chave '{key}': {e}", exc_info=True)
            raise

        logger.debug(f"Salvando estado da chave '{key}' no arquivo '{file_path}'")

        def _atomic_write():
            fd, tmp_path_str = tempfile.mkstemp(dir=atomic_dir, suffix=".tmp")
            tmp_path = Path(tmp_path_str)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                os.replace(tmp_path, file_path)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _atomic_write)
        except Exception as e:
            logger.error(f"Falha na escrita atômica para a chave '{key}': {e}", exc_info=True)
            raise
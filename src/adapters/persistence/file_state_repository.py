# src/adapters/persistence/file_state_repository.py

"""
Módulo do Adaptador de Repositório de Estado Atômico baseado em Arquivos.

Este arquivo contém a implementação concreta da `StateRepositoryPort`. Ele salva,
carrega e deleta estados atômicos (JSON) e artefatos binários dentro do
diretório da execução do workflow.

Utiliza `aiofiles` para I/O de arquivo assíncrono e `Pillow` para processamento
de imagem.
"""
import json
import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
import aiofiles.os
from PIL import Image

from src.core.domain.entities import RunContext
from src.ports.state_repository import StateRepositoryPort

logger = logging.getLogger(__name__)


# --- Exceção Específica do Adaptador ---
class ArtifactNotFoundError(FileNotFoundError):
    """Levantada quando um arquivo de artefato não é encontrado."""
    pass


# --- Padrão do Projeto para Configuração de Caminho ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASE_STATES_DIR = PROJECT_ROOT / "states"
# ----------------------------------------------------


def _sanitize_filename(name: str, ext: str = "") -> str:
    """
    Converte uma string em um nome de arquivo seguro, adicionando uma extensão.
    """
    base, *ext_parts = name.rsplit('.', 1)
    if ext_parts:
        name_base = base
        name_ext = f".{ext_parts[0]}"
    else:
        name_base = name
        name_ext = ext

    s = name_base.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s).strip('-')

    if not s:
        raise ValueError(f"O nome base '{name_base}' resultou em um nome de arquivo vazio.")

    return f"{s}{name_ext}"


class FileStateRepository(StateRepositoryPort):
    """
    Implementa a `StateRepositoryPort` usando arquivos JSON e binários em disco.
    """

    def __init__(self):
        """
        Inicializa o repositório, garantindo que o diretório base exista.
        """
        self.base_path = BASE_STATES_DIR
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"FileStateRepository inicializado. Diretório base: '{self.base_path}'"
        )

    def _get_atomic_states_dir(self, context: RunContext) -> Path:
        """
        Constrói e garante a existência do diretório 'atomic_states' para um run.
        """
        path = self.base_path / context.workflow_name / context.run_id / "atomic_states"
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def load(self, context: RunContext, key: str) -> Optional[Dict[str, Any]]:
        """Carrega o estado de um arquivo JSON de forma assíncrona."""
        filename = _sanitize_filename(key, ext=".json")
        file_path = self._get_atomic_states_dir(context) / filename

        if not await aiofiles.os.path.exists(file_path):
            return None

        logger.debug(f"Carregando estado da chave '{key}' de '{file_path}'")
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Falha ao carregar estado de '{file_path}': {e}", exc_info=True)
            return None

    async def save(self, context: RunContext, key: str, data: Dict[str, Any]) -> None:
        """Salva o estado em um arquivo JSON de forma assíncrona."""
        filename = _sanitize_filename(key, ext=".json")
        file_path = self._get_atomic_states_dir(context) / filename

        logger.debug(f"Salvando estado da chave '{key}' em '{file_path}'")
        try:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        except IOError as e:
            logger.error(f"Falha ao salvar estado em '{file_path}': {e}", exc_info=True)
            raise

    async def save_artifact(self, context: RunContext, filename: str, data: bytes) -> str:
        """
        Salva um artefato binário, convertendo para JPEG se for uma imagem.
        """
        sanitized_filename = _sanitize_filename(filename)
        file_path = self._get_atomic_states_dir(context) / sanitized_filename

        logger.info(f"Salvando artefato binário em: '{file_path}'")
        try:
            output_bytes = data
            if sanitized_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                logger.debug("Convertendo imagem para formato JPEG antes de salvar.")
                with Image.open(BytesIO(data)) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=95)
                    output_bytes = buffer.getvalue()

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(output_bytes)
            
            absolute_path = str(file_path.resolve())
            logger.info(f"Artefato salvo com sucesso em '{absolute_path}'.")
            return absolute_path
        except Exception as e:
            logger.error(f"Falha ao salvar artefato em '{file_path}': {e}", exc_info=True)
            raise

    async def load_artifact(self, context: RunContext, filename: str) -> bytes:
        """
        Carrega um artefato binário a partir do repositório de estado.
        """
        sanitized_filename = _sanitize_filename(filename)
        file_path = self._get_atomic_states_dir(context) / sanitized_filename

        if not await aiofiles.os.path.isfile(file_path):
            msg = f"Artefato '{sanitized_filename}' não encontrado em '{file_path.parent}'."
            logger.warning(msg)
            raise ArtifactNotFoundError(msg)
        
        logger.debug(f"Carregando artefato '{sanitized_filename}' de '{file_path}'")
        try:
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        except IOError as e:
            logger.error(f"Falha ao carregar artefato de '{file_path}': {e}", exc_info=True)
            raise

    async def delete(self, context: RunContext, key: str) -> bool:
        """
        Deleta um estado (JSON) e/ou artefato associado a uma chave/nome.
        """
        atomic_dir = self._get_atomic_states_dir(context)
        was_deleted = False

        # Constrói caminhos para o estado JSON e um artefato com o mesmo nome base
        state_filename = _sanitize_filename(key, ext=".json")
        artifact_filename = _sanitize_filename(key)

        file_paths_to_check = [
            atomic_dir / state_filename,
            atomic_dir / artifact_filename,
        ]

        # Usa um set para lidar com casos onde os nomes podem ser iguais
        for file_path in set(file_paths_to_check):
            try:
                if await aiofiles.os.path.isfile(file_path):
                    await aiofiles.os.remove(file_path)
                    logger.info(f"Deletado com sucesso: {file_path}")
                    was_deleted = True
            except OSError as e:
                logger.warning(f"Falha ao deletar arquivo {file_path}: {e}", exc_info=False)
        
        if not was_deleted:
            logger.debug(f"Nenhum estado ou artefato encontrado para deletar com a chave '{key}'.")

        return was_deleted
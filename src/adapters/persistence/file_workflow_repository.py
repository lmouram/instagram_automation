# src/adapters/persistence/file_workflow_repository.py

"""
Módulo do Adaptador de Repositório de Workflow baseado em Arquivos.

Este arquivo contém a implementação concreta da WorkflowRepositoryPort, utilizando
arquivos JSON no sistema de arquivos local como backend de persistência.

Implementa salvaguardas contra condições de corrida (usando `filelock`) e
corrupção de dados (usando escrita atômica).
"""

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from filelock import FileLock, Timeout

from src.core.domain import WorkflowRun, WorkflowStatus
from src.ports import WorkflowRepositoryPort

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASE_STATES_DIR = PROJECT_ROOT / "states"


class ConcurrencyError(Exception):
    """Levantada quando uma atualização de estado falha devido a um conflito de versão."""
    pass


class FileWorkflowRepository(WorkflowRepositoryPort):
    """
    Implementa o repositório de workflow usando arquivos JSON no disco.
    """

    def __init__(self):
        """Inicializa o repositório, garantindo que o diretório base exista."""
        self._base_dir = BASE_STATES_DIR
        try:
            self._base_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"FileWorkflowRepository inicializado. Diretório de estado: '{self._base_dir}'")
        except OSError as e:
            logger.critical(f"Não foi possível criar o diretório de estado: {e}", exc_info=True)
            raise

    # --- Métodos Auxiliares de Construção de Caminho (Refatorados) ---

    def _get_workflow_dir(self, workflow_name: str) -> Path:
        """Retorna o caminho para o diretório de um workflow e o cria se não existir."""
        workflow_dir = self._base_dir / workflow_name
        workflow_dir.mkdir(exist_ok=True)
        return workflow_dir

    def _get_run_dir(self, workflow_name: str, run_id: str) -> Path:
        """Retorna o caminho para o diretório de uma execução específica e o cria."""
        run_dir = self._get_workflow_dir(workflow_name) / run_id
        run_dir.mkdir(exist_ok=True)
        return run_dir

    def _get_run_path(self, workflow_name: str, run_id: str) -> Path:
        """Retorna o caminho completo para o arquivo de estado principal do workflow."""
        return self._get_run_dir(workflow_name, run_id) / "workflow_state.json"
    
    # --- Métodos de Mapeamento (Sem alterações) ---

    def _dict_to_workflow(self, data: Dict[str, Any]) -> WorkflowRun:
        # (código existente, sem alterações)
        init_false_fields = { "run_id": data.pop("run_id"), "created_at": data.pop("created_at"), "updated_at": data.pop("updated_at") }
        for key in ["retry_at"]:
            if data.get(key) and isinstance(data[key], str): data[key] = datetime.fromisoformat(data[key])
        if "status" in data: data["status"] = WorkflowStatus(data["status"])
        run = WorkflowRun(**data)
        run.run_id = init_false_fields["run_id"]
        run.created_at = datetime.fromisoformat(init_false_fields["created_at"])
        run.updated_at = datetime.fromisoformat(init_false_fields["updated_at"])
        return run

    def _atomic_write(self, run: WorkflowRun) -> None:
        # (lógica de escrita atômica, usa o novo _get_run_path)
        run_path = self._get_run_path(run.workflow_name, run.run_id)
        data_to_save = asdict(run)
        for key, value in data_to_save.items():
            if isinstance(value, datetime): data_to_save[key] = value.isoformat()
            elif isinstance(value, WorkflowStatus): data_to_save[key] = value.value
        fd, tmp_path_str = tempfile.mkstemp(dir=run_path.parent, suffix=".tmp")
        tmp_path = Path(tmp_path_str)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, run_path)
            logger.debug(f"Escrita atômica concluída para a execução ID: {run.run_id}")
        finally:
            if tmp_path.exists(): tmp_path.unlink()

    # --- Implementação dos Métodos da Porta ---

    async def create(self, run: WorkflowRun) -> None:
        # Garante que o diretório da execução seja criado
        self._get_run_dir(run.workflow_name, run.run_id)
        # O resto da lógica permanece a mesma
        run.version = 1
        run.created_at = datetime.now(timezone.utc)
        run.updated_at = run.created_at
        await self._execute_io(self._atomic_write, run)

    async def get_by_id(self, run_id: str, workflow_name: str) -> Optional[WorkflowRun]:
        run_path = self._get_run_path(workflow_name, run_id)
        if not run_path.exists():
            return None
        
        try:
            with open(run_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._dict_to_workflow(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Erro ao carregar o estado da execução ID {run_id}: {e}", exc_info=True)
            return None

    async def update(self, run: WorkflowRun) -> None:
        # Refatorado para usar o novo caminho de lock
        run_path = self._get_run_path(run.workflow_name, run.run_id)
        lock = FileLock(f"{run_path}.lock", timeout=10)

        try:
            with lock:
                existing_run = await self.get_by_id(run.run_id, run.workflow_name)
                
                if not existing_run:
                    raise FileNotFoundError(f"Não é possível atualizar a execução ID {run.run_id}, pois ela não existe.")

                if existing_run.version != run.version:
                    raise ConcurrencyError(
                        f"Conflito de concorrência na execução ID {run.run_id}. "
                        f"Versão esperada: {run.version}, versão no disco: {existing_run.version}."
                    )
                
                run.version += 1
                run.updated_at = datetime.now(timezone.utc)
                await self._execute_io(self._atomic_write, run)

        except Timeout:
            msg = f"Timeout ao tentar adquirir o lock para a execução ID {run.run_id}."
            logger.error(msg)
            raise ConcurrencyError(msg)

    async def list_ready_for_execution(self, workflow_name: str, limit: int) -> List[WorkflowRun]:
        workflow_dir = self._get_workflow_dir(workflow_name)
        ready_runs = []
        now = datetime.now(timezone.utc)
        
        # --- LÓGICA DE BUSCA REFATORADA ---
        # Itera sobre os subdiretórios (que são os run_ids)
        all_run_dirs = [d for d in workflow_dir.iterdir() if d.is_dir()]
        
        for run_dir in all_run_dirs:
            try:
                run_id = run_dir.name
                run = await self.get_by_id(run_id, workflow_name)
                if not run:
                    continue

                is_pending = run.status == WorkflowStatus.PENDING
                is_retryable = (
                    run.status == WorkflowStatus.FAILED_RETRYABLE
                    and run.retry_at is not None
                    and run.retry_at <= now
                )

                if is_pending or is_retryable:
                    ready_runs.append(run)
                
                if len(ready_runs) >= limit:
                    break
            except Exception:
                logger.error(f"Não foi possível processar o diretório de estado {run_dir}", exc_info=True)
                continue
        
        # Ordena por data de criação para processar os mais antigos primeiro
        ready_runs.sort(key=lambda r: r.created_at)
        return ready_runs

    async def _execute_io(self, func, *args, **kwargs):
        """
        Executa uma função de I/O síncrona em um executor de thread para não
        bloquear o loop de eventos asyncio.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
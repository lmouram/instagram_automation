# src/utils/state_manager.py

"""
Módulo de Gerenciamento de Estado de Execução.

Este módulo fornece uma classe `StateManager` para lidar com a persistência
do estado de scripts em arquivos JSON. Ele abstrai a lógica de I/O, a
organização de diretórios e a geração de IDs de execução sequenciais.

Principais Funcionalidades:
-   **Organização por Script:** Cada script tem seu próprio diretório dentro
    da pasta `states/`, evitando colisões.
-   **IDs Sequenciais:** Gera IDs de execução (run_id) numéricos e sequenciais
    para fácil rastreamento.
-   **Retomada de Execução:** Permite que um script carregue um estado anterior
    para continuar um trabalho ou evitar a re-execução de etapas custosas.
-   **Robustez:** Inclui tratamento de erros para I/O e parsing de JSON.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

# Define a raiz do projeto para localizar a pasta 'states' de forma consistente
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_STATES_DIR = PROJECT_ROOT / "states"

logger = logging.getLogger(__name__)


class StateManagerError(Exception):
    """Exceção base para erros no StateManager."""
    pass

class StateNotFoundError(FileNotFoundError, StateManagerError):
    """Levantada quando um arquivo de estado específico não é encontrado."""
    pass


class StateManager:
    """
    Gerencia o ciclo de vida dos estados de execução de um script.

    Cada instância do StateManager está vinculada a um `script_name` específico,
    garantindo que os estados sejam armazenados em seu próprio subdiretório.
    """

    def __init__(self, script_name: str):
        """
        Inicializa o gerenciador de estado para um script específico.

        Args:
            script_name (str): O nome do script (ex: "generate_dossier").
                               Este nome será usado para criar um subdiretório
                               em `states/`.

        Raises:
            StateManagerError: Se o nome do script for inválido ou se houver
                               um problema ao criar o diretório de estado.
        """
        if not script_name or not isinstance(script_name, str):
            raise StateManagerError("O nome do script deve ser uma string não vazia.")
        
        self.script_name = script_name
        self._script_state_dir = BASE_STATES_DIR / self.script_name
        
        try:
            # Garante que o diretório de estado para este script exista
            self._script_state_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"StateManager inicializado para o script '{script_name}'. Diretório: {self._script_state_dir}")
        except (IOError, PermissionError) as e:
            msg = f"Não foi possível criar o diretório de estado em '{self._script_state_dir}': {e}"
            logger.critical(msg, exc_info=True)
            raise StateManagerError(msg) from e

    def _get_next_run_id(self) -> int:
        """
        Calcula o próximo ID de execução sequencial para o script.

        Varre o diretório de estado do script, encontra o maior ID numérico
        existente e retorna o próximo número na sequência.

        Returns:
            int: O próximo ID de execução disponível (começando em 1).
        """
        existing_ids = []
        for file_path in self._script_state_dir.glob("*.json"):
            try:
                # Extrai o nome do arquivo sem a extensão e converte para int
                run_id = int(file_path.stem)
                existing_ids.append(run_id)
            except (ValueError, TypeError):
                # Ignora arquivos que não são numéricos (ex: "config.json")
                logger.warning(f"Ignorando arquivo de estado não numérico: {file_path.name}")
                continue
        
        if not existing_ids:
            return 1
        
        return max(existing_ids) + 1

    def load_state(self, run_id: int) -> Dict[str, Any]:
        """
        Carrega e parseia um arquivo de estado JSON específico.

        Args:
            run_id (int): O ID da execução a ser carregada.

        Returns:
            Dict[str, Any]: Um dicionário com o estado carregado.

        Raises:
            StateNotFoundError: Se o arquivo de estado para o `run_id` não for encontrado.
            StateManagerError: Se houver um erro de I/O ou de parsing do JSON.
        """
        state_file_path = self._script_state_dir / f"{run_id}.json"
        logger.info(f"Carregando estado da execução ID {run_id} de '{state_file_path}'")

        if not state_file_path.is_file():
            raise StateNotFoundError(f"Arquivo de estado para a execução ID {run_id} não encontrado em '{state_file_path}'.")

        try:
            with open(state_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug(f"Estado da execução ID {run_id} carregado com sucesso.")
            return data
        except json.JSONDecodeError as e:
            msg = f"Erro de sintaxe no arquivo de estado '{state_file_path}': {e}"
            logger.error(msg)
            raise StateManagerError(msg) from e
        except (IOError, PermissionError) as e:
            msg = f"Erro de I/O ou permissão ao ler o arquivo '{state_file_path}': {e}"
            logger.critical(msg, exc_info=True)
            raise StateManagerError(msg) from e

    def save_state(self, run_id: int, state_data: Dict[str, Any]) -> None:
        """
        Salva (ou sobrescreve) um dicionário de estado em seu arquivo JSON correspondente.

        Args:
            run_id (int): O ID da execução a ser salva.
            state_data (Dict[str, Any]): O conteúdo do estado a ser persistido.

        Raises:
            StateManagerError: Se houver um erro de I/O ou de serialização JSON.
        """
        state_file_path = self._script_state_dir / f"{run_id}.json"
        logger.info(f"Salvando estado para a execução ID {run_id} em '{state_file_path}'")
        
        try:
            with open(state_file_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=4, ensure_ascii=False)
            logger.debug(f"Estado da execução ID {run_id} salvo com sucesso.")
        except (IOError, PermissionError) as e:
            msg = f"Falha de I/O ou permissão ao salvar o estado em '{state_file_path}': {e}"
            logger.critical(msg, exc_info=True)
            raise StateManagerError(msg) from e
        except TypeError as e:
            msg = f"Falha de serialização ao salvar o estado. Verifique se o conteúdo é serializável: {e}"
            logger.critical(msg, exc_info=True)
            raise StateManagerError(msg) from e

    def create_new_run(self, initial_state: Dict[str, Any]) -> int:
        """
        Cria uma nova execução, determinando o próximo ID, adicionando metadados
        e salvando o estado inicial.

        Args:
            initial_state (Dict[str, Any]): O dicionário com os dados iniciais
                                             da execução (ex: o tema fornecido
                                             pelo usuário).

        Returns:
            int: O ID da nova execução criada.
        """
        new_run_id = self._get_next_run_id()
        logger.info(f"Criando nova execução para o script '{self.script_name}' com ID: {new_run_id}")

        # Adiciona metadados ao estado para rastreabilidade
        state_with_metadata = {
            "run_id": new_run_id,
            "script_name": self.script_name,
            **initial_state
        }

        self.save_state(new_run_id, state_with_metadata)
        
        return new_run_id
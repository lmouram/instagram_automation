# src/adapters/theming/file_system_theme_loader.py

"""
Módulo do Adaptador de Carregador de Tema baseado em Sistema de Arquivos.

Este arquivo contém a implementação concreta da `ThemeLoaderPort`. Ele é
responsável por ler as configurações de um tema a partir de uma estrutura de
diretórios e um arquivo `theme.json`, garantindo a validação e segurança dos
caminhos carregados.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict

from src.core.application.contracts import ThemeContract
from src.ports.theme_loader import ThemeLoaderPort

logger = logging.getLogger(__name__)


# --- Exceções Específicas do Adaptador ---

class ThemeNotFoundError(Exception):
    """Levantada quando um diretório ou arquivo de tema não é encontrado."""
    pass


class ThemeInvalidError(Exception):
    """Levantada quando um arquivo theme.json é malformado, inseguro ou incompleto."""
    pass


# --- Classe do Adaptador ---

class FileSystemThemeLoaderAdapter(ThemeLoaderPort):
    """
    Implementa a `ThemeLoaderPort` lendo temas do sistema de arquivos local.

    Espera uma estrutura de diretórios como:
    <base_path>/
    └── <theme_name>/
        ├── theme.json
        ├── fonts/
        └── templates/
    """

    def __init__(self, base_path: Path):
        """
        Inicializa o carregador de temas.

        Args:
            base_path (Path): O caminho absoluto para o diretório raiz que
                              contém todos os temas (ex: `.../src/assets/themes`).
        """
        if not base_path.is_dir():
            raise FileNotFoundError(f"O diretório base de temas não existe: {base_path}")
        self._base_path = base_path.resolve()
        logger.info(f"FileSystemThemeLoaderAdapter inicializado. Base: '{self._base_path}'")

    def _sanitize_theme_name(self, theme_name: str) -> str:
        """Previne path traversal no nome do tema."""
        # Permite apenas caracteres alfanuméricos, hífens e underscores.
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', theme_name)
        if sanitized != theme_name:
            raise ThemeInvalidError(f"Nome de tema inválido ou inseguro: '{theme_name}'")
        return sanitized

    def _validate_and_resolve_asset_path(self, theme_dir: Path, asset_path_str: str) -> Path:
        """
        Resolve o caminho de um ativo e valida que ele está contido no diretório do tema.
        """
        asset_path = (theme_dir / asset_path_str).resolve()
        
        # Validação de segurança CRÍTICA para prevenir Path Traversal
        if not str(asset_path).startswith(str(theme_dir)):
            raise ThemeInvalidError(
                f"Caminho de ativo inseguro: '{asset_path_str}' tenta acessar fora do diretório do tema."
            )
        
        if not asset_path.is_file():
            raise ThemeNotFoundError(f"Arquivo de ativo não encontrado: {asset_path}")
            
        return asset_path

    def load(self, theme_name: str) -> ThemeContract:
        """
        Carrega, valida e constrói um ThemeContract a partir de um `theme.json`.
        """
        logger.debug(f"Carregando tema '{theme_name}'...")
        
        try:
            sanitized_name = self._sanitize_theme_name(theme_name)
            theme_dir = (self._base_path / sanitized_name).resolve()

            if not theme_dir.is_dir():
                raise ThemeNotFoundError(f"Diretório do tema '{sanitized_name}' não encontrado em '{self._base_path}'.")

            config_path = theme_dir / "theme.json"
            if not config_path.is_file():
                raise ThemeNotFoundError(f"Arquivo 'theme.json' não encontrado para o tema '{sanitized_name}'.")

            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Valida e resolve os caminhos dos ativos
            font_path = self._validate_and_resolve_asset_path(
                theme_dir, config['assets']['fonts']['title']
            )
            template_path = self._validate_and_resolve_asset_path(
                theme_dir, config['assets']['templates']['single_post']
            )

            # Constrói o DTO do ThemeContract
            contract = ThemeContract(
                theme_name=config['theme_name'],
                version=config['version'],
                template_single_post_path=template_path,
                font_title_path=font_path,
                mask_opacity=float(config['settings']['mask_opacity']),
                viewport_width=int(config['settings']['viewport']['width']),
                viewport_height=int(config['settings']['viewport']['height']),
                output_format=str(config['settings']['output_format']),
                output_quality=int(config['settings']['output_quality']),
            )
            
            logger.info(f"Tema '{theme_name}' v{contract.version} carregado com sucesso.")
            return contract

        except (json.JSONDecodeError, KeyError) as e:
            msg = f"Arquivo 'theme.json' para o tema '{theme_name}' é inválido ou está incompleto: {e}"
            logger.error(msg, exc_info=True)
            raise ThemeInvalidError(msg) from e
        except (ThemeNotFoundError, ThemeInvalidError) as e:
            logger.error(f"Falha ao carregar o tema '{theme_name}': {e}")
            raise
        except Exception as e:
            msg = f"Erro inesperado ao carregar o tema '{theme_name}': {e}"
            logger.critical(msg, exc_info=True)
            raise ThemeInvalidError(msg) from e
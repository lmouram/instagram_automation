# src/adapters/theming/__init__.py

"""
Pacote de Adaptadores de Tematização.

Este arquivo inicializa o diretório 'theming' como um pacote Python e expõe
as classes principais para serem facilmente importadas por outras partes da
aplicação, como o 'Composition Root' no `scripts/run_orchestrator.py`.
"""

# Importa as classes do módulo para torná-las acessíveis no nível do pacote.
from .file_system_theme_loader import (
    FileSystemThemeLoaderAdapter,
    ThemeInvalidError,
    ThemeNotFoundError,
)

# Define a API pública do pacote.
__all__ = [
    "FileSystemThemeLoaderAdapter",
    "ThemeInvalidError",
    "ThemeNotFoundError",
]
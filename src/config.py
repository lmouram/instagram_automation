# src/config.py

"""
Módulo de Configuração Centralizado.

Este módulo é a fonte única da verdade para todas as configurações da aplicação.
Ele carrega as configurações a partir de variáveis de ambiente, com suporte
para um arquivo `.env` para facilitar o desenvolvimento local.

Ordem de Precedência:
1. Variáveis de Ambiente definidas no sistema operacional.
2. Variáveis definidas no arquivo `.env` na raiz do projeto.

Para desenvolvimento local, crie um arquivo chamado `.env` na raiz do projeto
(no mesmo nível que `pyproject.toml`) e preencha-o com base no arquivo
`.env.example`.

O módulo validará a presença de configurações críticas no momento da importação,
causando uma falha rápida (`fail-fast`) se segredos essenciais não estiverem
definidos, o que previne erros inesperados em tempo de execução.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

# Dependência externa: python-dotenv
# Certifique-se de que está no pyproject.toml
try:
    from dotenv import load_dotenv
except ImportError:
    print("AVISO: 'python-dotenv' não está instalado. O arquivo .env não será carregado.")
    print("Execute: pip install python-dotenv")
    load_dotenv = None

# --- Configuração de Caminhos e Carregamento do .env ---

# A raiz do projeto é o diretório pai da pasta 'src'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

if load_dotenv:
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH)
        # Usamos print aqui porque o logger ainda não está configurado
        print(f"Config: Arquivo .env encontrado e carregado de '{ENV_PATH}'")
    else:
        print(f"Config: Arquivo .env não encontrado em '{ENV_PATH}'. Usando apenas variáveis de ambiente do sistema.")

# --- Função Auxiliar para Obtenção de Variáveis ---

def get_env(
    variable_name: str,
    default: Optional[Any] = None,
    required: bool = False
) -> Optional[str]:
    """
    Obtém uma variável de ambiente de forma segura.

    Args:
        variable_name (str): O nome da variável de ambiente (ex: "SUPABASE_URL").
        default (Optional[Any]): O valor padrão a ser retornado se a variável não for encontrada.
        required (bool): Se True, levanta um ValueError se a variável não for encontrada.

    Returns:
        Optional[str]: O valor da variável de ambiente ou o padrão.

    Raises:
        ValueError: Se `required` for True e a variável não estiver definida.
    """
    value = os.environ.get(variable_name)
    if value is None:
        if required:
            raise ValueError(
                f"Erro de configuração: A variável de ambiente obrigatória "
                f"'{variable_name}' não foi definida."
            )
        return default
    return value


# --- Configurações da Aplicação ---

# --- Supabase Configuration ---
SUPABASE_URL = get_env("SUPABASE_URL", required=True)
SUPABASE_KEY = get_env("SUPABASE_KEY", required=True)
SUPABASE_STORAGE_BUCKET = get_env("SUPABASE_STORAGE_BUCKET", default="media_storage")

# --- Google AI (Gemini & Imagen) Configuration ---
# Usamos a mesma chave para ambos os serviços por padrão
GEMINI_API_KEY = get_env("GEMINI_API_KEY", required=True)

# --- Instagram Configuration ---
INSTAGRAM_ACCOUNT_ID = get_env("INSTAGRAM_ACCOUNT_ID", required=True)
META_ACCESS_TOKEN = get_env("META_ACCESS_TOKEN", required=True)

# --- Logging Configuration (com padrões sensíveis) ---
LOG_LEVEL_CONSOLE = get_env("LOG_LEVEL_CONSOLE", default="INFO").upper()
LOG_LEVEL_FILE = get_env("LOG_LEVEL_FILE", default="DEBUG").upper()
LOG_FILENAME = get_env("LOG_FILENAME", default="logs/app.log")
LOG_MAX_BYTES = int(get_env("LOG_MAX_BYTES", default=10 * 1024 * 1024))  # 10 MB
LOG_BACKUP_COUNT = int(get_env("LOG_BACKUP_COUNT", default=5))
# src/logger.py

"""
Módulo de Configuração e Gerenciamento de Logging.

Este módulo centraliza a configuração do logger para toda a aplicação. Ele é
projetado para ser importado por outros módulos que precisam registrar eventos,
garantindo um formato de log consistente e detalhado, essencial para depuração.

Principais Funcionalidades:
1.  **Configuração Única:** Utiliza um controle para garantir que a
    configuração de logging seja executada apenas uma vez.
2.  **Múltiplos Destinos (Handlers):**
    - Console colorido (`colorlog`) para feedback visual durante o desenvolvimento.
    - Arquivo com rotação (`RotatingFileHandler`) para um registro persistente
      e detalhado de todas as operações.
3.  **Configuração Centralizada:** Lê todas as configurações (níveis, caminhos)
    do módulo `src.config`.
4.  **Captura de Exceções Globais:** Instala um gancho (`sys.excepthook`) para
    garantir que qualquer exceção não tratada seja logada antes de o programa
    encerrar.
5.  **API Simplificada:** Expõe uma única função, `get_logger(name)`, que
    fornece uma instância de logger já configurada.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Importa as configurações do nosso módulo centralizado
from src import config

# Importa o colorlog. Se não estiver instalado, prossegue sem cores.
try:
    import colorlog
    _COLORLOG_AVAILABLE = True
except ImportError:
    _COLORLOG_AVAILABLE = False


# --- Variável Global de Controle ---
# Garante que a configuração do logger seja executada apenas uma vez.
_ROOT_LOGGER_CONFIGURED = False


def setup_global_logger() -> None:
    """
    Configura o logger raiz do projeto com handlers para console e arquivo.

    Esta função é idempotente. Ela lê as configurações do módulo `src.config`
    e prepara o ambiente de logging para toda a aplicação.
    """
    global _ROOT_LOGGER_CONFIGURED
    if _ROOT_LOGGER_CONFIGURED:
        return

    # Obtém o logger raiz e define o nível mais permissivo.
    # Os handlers individuais controlarão o que é efetivamente processado.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Previne a propagação de logs para o handler padrão do sistema, se já existir.
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # --- Handler de Console ---
    log_format_console = (
        '%(log_color)s[%(levelname)-8s]%(reset)s '
        '[%(name)s] - %(message)s'
    )
    if _COLORLOG_AVAILABLE:
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_formatter = colorlog.ColoredFormatter(
            log_format_console,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red,bg_white',
            },
        )
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(log_format_console.replace('%(log_color)s', '').replace('%(reset)s', ''))

    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(config.LOG_LEVEL_CONSOLE)
    root_logger.addHandler(console_handler)

    # --- Handler de Arquivo com Rotação ---
    try:
        log_file_path = Path(config.LOG_FILENAME)
        # Garante que o diretório do log exista
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(config.LOG_LEVEL_FILE)
        root_logger.addHandler(file_handler)
    except (IOError, PermissionError) as e:
        root_logger.error(
            f"Falha crítica ao configurar o log de arquivo '{config.LOG_FILENAME}': {e}",
            exc_info=True
        )

    # --- Gancho para Exceções Não Tratadas ---
    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        """Função para logar exceções não tratadas antes de o programa fechar."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Não loga um erro crítico se o usuário interromper com Ctrl+C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        root_logger.critical(
            "Exceção não tratada interceptada pelo logger global!",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_uncaught_exception

    _ROOT_LOGGER_CONFIGURED = True
    root_logger.info("=" * 60)
    root_logger.info(f"Logger global configurado. Nível do console: {config.LOG_LEVEL_CONSOLE}.")
    root_logger.info(f"Logs de arquivo (nível {config.LOG_LEVEL_FILE}) sendo salvos em: '{config.LOG_FILENAME}'")
    root_logger.info("=" * 60)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Obtém uma instância de um logger nomeado e já configurado.

    Esta é a função de interface para o resto da aplicação. Ela garante que a
    configuração do logger seja executada na primeira vez que for chamada.

    Args:
        name (Optional[str]): O nome do logger. É uma boa prática usar `__name__`,
                              pois o logger herdará o nome do módulo. Se None,
                              o logger raiz é retornado.

    Returns:
        logging.Logger: Uma instância do logger configurado.
    """
    if not _ROOT_LOGGER_CONFIGURED:
        setup_global_logger()

    return logging.getLogger(name)
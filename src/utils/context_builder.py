# src/utils/context_builder.py

"""
Utilitário para gerar um arquivo de contexto consolidado para LLMs.

Este script varre os diretórios e arquivos de código-fonte do projeto
'instagram_automation', lê seu conteúdo e os compila em um único arquivo
TOML bem-estruturado. O objetivo é criar um "pacote de contexto" que
pode ser facilmente fornecido a um Large Language Model para consultas sobre a
arquitetura, lógica e código do projeto.

Modificação em relação ao código de referência:
- Os arquivos `__init__.py` SÃO incluídos, pois em nosso projeto eles contêm
  documentação importante sobre os pacotes.
- Os diretórios e arquivos foram ajustados para a estrutura do nosso projeto.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- Instalação de Dependências (se necessário) ---
try:
    import toml
except ImportError:
    print("ERRO: A biblioteca 'toml' é necessária para este script.")
    print("Execute: pip install toml")
    sys.exit(1)

# --- Configuração do Logger ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)-8s] - %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# --- Constantes de Configuração ---

# A raiz do projeto é o diretório pai de 'src/'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Define os diretórios e arquivos a serem incluídos no contexto.
# O foco principal é o código-fonte em 'src/'.
FOLDERS_TO_PROCESS = ["src", "scripts", ".github"]
FILES_TO_PROCESS = ["streamlit_app.py", "pyproject.toml"]
OUTPUT_FILENAME = "context_llm.toml"


def process_file(file_path: Path, project_root: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Lê o conteúdo de um arquivo e gera uma chave TOML a partir de seu caminho relativo.

    Args:
        file_path (Path): O caminho absoluto para o arquivo.
        project_root (Path): O caminho para a raiz do projeto.

    Returns:
        Tuple[Optional[str], Optional[str]]: Uma tupla contendo a chave TOML
                                             e o conteúdo do arquivo,
                                             ou (None, None) em caso de erro.
    """
    try:
        relative_path = file_path.relative_to(project_root)
        # Converte o caminho em uma chave TOML válida e descritiva.
        # Ex: "src/core/domain/entities.py" -> "src.core.domain.entities_py"
        toml_key = (
            str(relative_path)
            .replace("/", ".")
            .replace("\\", ".")
            .replace(".py", "_py")
            .replace(".toml", "_toml")
            .replace(".yml", "_yml")
            .replace(".md", "_md")
        )
        
        content = file_path.read_text(encoding='utf-8')
        log.debug(f"Processado: '{relative_path}'")
        return toml_key, content
    except Exception as e:
        log.error(f"Falha ao processar o arquivo '{file_path}': {e}")
        return None, None


def build_nested_dict(flat_data: List[Tuple[str, str]]) -> Dict[str, Any]:
    """
    Converte uma lista de chaves planas em um dicionário aninhado.

    Args:
        flat_data (List[Tuple[str, str]]): Lista de tuplas (chave_plana, conteúdo).

    Returns:
        Dict[str, Any]: Um dicionário aninhado representando a estrutura do projeto.
    """
    nested_dict = {}
    for key, content in flat_data:
        parts = key.split('.')
        d = nested_dict
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        # Adiciona o conteúdo sob uma subchave 'content' para estrutura clara no TOML
        d[parts[-1]] = {'content': content}
    return nested_dict


def main():
    """
    Função principal que orquestra a varredura, processamento e salvamento
    do arquivo de contexto.
    """
    log.info("Iniciando a geração do arquivo de contexto para LLM...")

    all_data: List[Tuple[str, str]] = []

    # Processa as pastas recursivamente
    for folder_name in FOLDERS_TO_PROCESS:
        folder_path = PROJECT_ROOT / folder_name
        if not folder_path.is_dir():
            log.warning(f"Pasta '{folder_name}' não encontrada. Pulando.")
            continue
        
        log.info(f"Varrrendo a pasta '{folder_name}'...")
        for item in sorted(folder_path.rglob('*')):
            # Ignora o diretório __pycache__ e seu conteúdo.
            if "__pycache__" in item.parts:
                continue
            
            # **AJUSTE PRINCIPAL**: Processa todos os arquivos, incluindo __init__.py
            if item.is_file():
                key, content = process_file(item, PROJECT_ROOT)
                if key and content:
                    all_data.append((key, content))

    # Processa os arquivos individuais da raiz
    log.info("Processando arquivos da raiz do projeto...")
    for file_name in FILES_TO_PROCESS:
        file_path = PROJECT_ROOT / file_name
        if not file_path.is_file():
            log.warning(f"Arquivo '{file_name}' não encontrado. Pulando.")
            continue
        key, content = process_file(file_path, PROJECT_ROOT)
        if key and content:
            all_data.append((key, content))

    if not all_data:
        log.error("Nenhum arquivo foi processado. O arquivo de contexto não será gerado.")
        return

    log.info("Construindo o dicionário de contexto aninhado...")
    context_dict = build_nested_dict(all_data)
    
    log.info("Gerando a string TOML...")
    toml_string = toml.dumps(context_dict)
    
    output_path = PROJECT_ROOT / OUTPUT_FILENAME
    
    log.info(f"Salvando o contexto consolidado em '{output_path}'...")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(toml_string)
        log.info(f"Arquivo de contexto para LLM gerado com sucesso! ({len(all_data)} arquivos processados)")
    except Exception as e:
        log.critical(f"Falha ao salvar o arquivo de contexto: {e}", exc_info=True)


if __name__ == '__main__':
    main()
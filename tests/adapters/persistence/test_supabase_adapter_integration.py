# tests/adapters/persistence/test_supabase_adapter_integration.py

import pytest
import os
from uuid import uuid4
from supabase import create_client
from dotenv import load_dotenv, dotenv_values 
from pathlib import Path

# --- Carregamento e Verificação de Configuração de Teste (MUITO IMPORTANTE) ---

# CORREÇÃO: O caminho raiz precisa subir 4 níveis para chegar a /instagram_automation
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROD_ENV_PATH = ROOT_DIR / ".env"
TEST_ENV_PATH = ROOT_DIR / ".env.test"

# 2. Lê os valores dos arquivos .env como dicionários, SEM modificar o ambiente global
prod_config = dotenv_values(PROD_ENV_PATH) if PROD_ENV_PATH.exists() else {}
test_config = dotenv_values(TEST_ENV_PATH) if TEST_ENV_PATH.exists() else {}
print(f"DEBUG: Conteúdo lido do .env.test: {test_config}") 

PROD_URL = prod_config.get("SUPABASE_URL")
TEST_URL = test_config.get("SUPABASE_URL")

# 3. Faz a verificação de segurança ANTES de carregar qualquer coisa no ambiente
assert TEST_URL, "SUPABASE_URL não foi definida no arquivo .env.test"
assert PROD_URL, "SUPABASE_URL não foi definida no arquivo .env principal"
assert TEST_URL != PROD_URL, "ERRO CRÍTICO: A URL do Supabase nos arquivos .env e .env.test são idênticas. Use um projeto separado para testes."

# 4. APENAS AGORA, carrega as variáveis de teste no ambiente para que a aplicação as use
load_dotenv(dotenv_path=TEST_ENV_PATH, override=True)


# --- Início dos Testes ---

# Importa o config APÓS o ambiente de teste ter sido carregado e verificado
from src.config import SUPABASE_URL, SUPABASE_KEY
from src.adapters.persistence import SupabasePostRepository
from src.core.domain import Post, PostStatus, PostType

# Marca todos os testes neste arquivo como 'integration'
pytestmark = pytest.mark.integration

@pytest.fixture(scope="module")
def post_repository(): # <-- MUDANÇA AQUI: nome da fixture
    """Cria uma instância do repositório de posts conectado a um DB de teste."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return SupabasePostRepository(client) # <-- MUDANÇA AQUI

@pytest.mark.asyncio
async def test_save_and_find_post(post_repository: SupabasePostRepository):
    """
    Verifica se podemos salvar um post e depois encontrá-lo pelo ID.
    Este teste executa operações REAIS no banco de dados de teste.
    """
    # Arrange
    new_post = Post(
        theme="Integration Test Theme",
        text_content="Conteúdo do teste de integração.",
        status=PostStatus.DRAFT,
        post_type=PostType.SINGLE_IMAGE
    )
    post_id = uuid4()
    new_post.id = post_id

    # Act: Salva o post
    await post_repository.save(new_post)

    # Act: Busca o post
    found_post = await post_repository.find_by_id(post_id)

    # Assert
    assert found_post is not None
    assert found_post.id == post_id
    assert found_post.theme == "Integration Test Theme"

    # Cleanup
    try:
        post_repository._client.table("posts").delete().eq("id", str(post_id)).execute()
    except Exception as e:
        print(f"AVISO: Falha ao limpar o post de teste {post_id}. Erro: {e}")
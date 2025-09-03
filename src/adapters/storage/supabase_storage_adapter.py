# src/adapters/storage/supabase_storage_adapter.py

"""
Módulo do Adaptador de Armazenamento para o Supabase Storage.

Este arquivo contém a implementação concreta da `StoragePort` utilizando o
serviço de armazenamento de objetos do Supabase.
"""

import logging
from supabase import Client

from src.ports.storage import StoragePort

logger = logging.getLogger(__name__)


class SupabaseStorageAdapter(StoragePort):
    """
    Adaptador que implementa a `StoragePort` para interagir com o Supabase Storage.

    Esta classe encapsula a lógica de fazer upload de arquivos de mídia para um
    bucket específico no Supabase e de recuperar a URL pública desses arquivos.
    """

    def __init__(self, supabase_client: Client, bucket_name: str):
        """
        Inicializa o adaptador com o cliente Supabase e o nome do bucket.

        Args:
            supabase_client (Client): Uma instância do cliente Supabase já
                                      configurada e autenticada.
            bucket_name (str): O nome do bucket no Supabase Storage onde as
                               mídias serão armazenadas.
        """
        self._client = supabase_client
        self._bucket_name = bucket_name
        logger.info(
            f"SupabaseStorageAdapter inicializado para o bucket '{self._bucket_name}'."
        )

    async def upload(
        self, file_content: bytes, file_name: str, content_type: str
    ) -> str:
        """
        Faz o upload de um conteúdo de arquivo binário para o bucket no Supabase.

        Args:
            file_content (bytes): Os dados binários do arquivo a ser enviado.
            file_name (str): O nome (path) do arquivo no bucket.
            content_type (str): O MIME type do arquivo (ex: 'image/png').

        Returns:
            str: A URL pública e acessível do arquivo recém-carregado.

        Raises:
            Exception: Relança qualquer exceção que ocorra durante a interação
                       com a API do Supabase, indicando uma falha no upload.
        """
        logger.info(
            f"Iniciando upload do arquivo '{file_name}' ({len(file_content)} bytes) "
            f"para o bucket '{self._bucket_name}'."
        )
        try:
            # Seleciona o bucket de armazenamento
            storage_bucket = self._client.storage.from_(self._bucket_name)

            # Faz o upload do arquivo, especificando o content type
            storage_bucket.upload(
                path=file_name,
                file=file_content,
                file_options={"contentType": content_type},
            )
            logger.debug(f"Upload do arquivo '{file_name}' para o Supabase concluído.")

            # Obtém a URL pública do arquivo recém-enviado
            public_url = storage_bucket.get_public_url(path=file_name)
            logger.info(f"Arquivo '{file_name}' enviado com sucesso. "
                        f"URL pública: {public_url}")

            return public_url

        except Exception as e:
            logger.error(
                f"Falha ao fazer upload do arquivo '{file_name}' para o bucket "
                f"'{self._bucket_name}'. Erro: {e}",
                exc_info=True,
            )
            # Relança a exceção para que a camada de aplicação (caso de uso)
            # possa tratar a falha.
            raise
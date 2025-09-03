# src/ports/storage.py

"""
Módulo da Porta de Armazenamento.

Este arquivo define a porta (interface abstrata) para a funcionalidade de
armazenamento e recuperação de arquivos de mídia (objetos binários).
O propósito desta porta é desacoplar o núcleo da aplicação (core) dos detalhes
de implementação de qualquer serviço de armazenamento de objetos específico,
como Amazon S3, Google Cloud Storage, Supabase Storage ou um sistema de
arquivos local.

O caso de uso de criação de post dependerá desta abstração para persistir
as mídias geradas (imagens, vídeos) e obter uma URL pública para elas.
"""

from abc import ABC, abstractmethod


class StoragePort(ABC):
    """
    Interface abstrata (Porta) para um serviço de armazenamento de objetos.

    Define o contrato que os adaptadores de armazenamento de arquivos devem
    seguir. Um adaptador concreto (ex: `SupabaseStorageAdapter`) implementará
    este contrato usando o SDK ou API do provedor de armazenamento alvo.
    """

    @abstractmethod
    async def upload(
        self, file_content: bytes, file_name: str, content_type: str
    ) -> str:
        """
        Faz o upload de um conteúdo de arquivo binário para o serviço de armazenamento.

        A implementação concreta deste método deve lidar com a autenticação no
        serviço de armazenamento, o upload do `file_content` para um local
        específico (geralmente um "bucket") com o `file_name` fornecido, e
        garantir que o `content_type` correto seja definido para o objeto.

        Args:
            file_content (bytes): Os dados binários brutos do arquivo a ser
                                  enviado.
            file_name (str): O nome desejado para o arquivo no serviço de
                             armazenamento. Recomenda-se que seja um nome
                             único para evitar colisões (ex: usando um UUID).
            content_type (str): O MIME type do arquivo (ex: 'image/jpeg',
                                'video/mp4'). É crucial para que o arquivo
                                seja servido e interpretado corretamente
                                pelos navegadores e outras aplicações.

        Returns:
            str: A URL pública e permanentemente acessível do arquivo que
                 acabou de ser carregado. Esta URL será armazenada na
                 entidade `Media` no nosso domínio.

        Raises:
            Exception: Implementações concretas podem levantar exceções
                       específicas em caso de falha. Exemplos incluem:
                       - `AuthenticationError`: Se as credenciais para o
                         serviço de armazenamento forem inválidas.
                       - `PermissionError`: Se a conta não tiver permissão
                         para escrever no bucket/local de destino.
                       - `StorageError`: Para erros genéricos de upload.
                       O caso de uso chamador deve estar preparado para tratar
                       essas falhas.
        """
        raise NotImplementedError
# src/adapters/media/google_image_adapter.py

"""
Módulo do Adaptador do Google Imagen 4.

Este arquivo contém a implementação concreta da `MediaGeneratorPort` para a
geração de imagens, utilizando a API do Google Imagen 4 através do SDK
`google.genai`, conforme especificado pela FONTE ÚNICA DA VERDADE.
"""

import logging
import threading
import time

# Importação segura do SDK do Google, conforme FONTE ÚNICA DA VERDADE
try:
    import google.genai as genai_sdk
    from google.genai import client as genai_client
    from google.genai import types as genai_types
    _GENAI_SDK_AVAILABLE = True
except ImportError:
    _GENAI_SDK_AVAILABLE = False
    genai_sdk = None
    genai_client = None
    genai_types = None

from src.ports.media_generator import MediaGeneratorPort

logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    """Exceção customizada para erros relacionados à geração de imagens."""
    pass


class GoogleImageAdapter(MediaGeneratorPort):
    """
    Adaptador que implementa a `MediaGeneratorPort` para o Google Imagen 4.
    """

    _last_request_time: float = 0
    _lock = threading.Lock()

    def __init__(
        self,
        api_key: str,
        model_name: str = "models/imagen-4.0-generate-preview-06-06", # Conforme FONTE ÚNICA DA VERDADE
        api_min_interval_seconds: float = 2.0, # Rate limit seguro para imagem
        aspect_ratio: str = "1:1" # Padrão quadrado para Instagram
    ):
        """
        Inicializa o adaptador do Imagen 4.

        Args:
            api_key (str): A chave de API para autenticação.
            model_name (str): O nome do modelo Imagen a ser usado.
            api_min_interval_seconds (float): Intervalo mínimo entre chamadas.
            aspect_ratio (str): A proporção da imagem a ser gerada (ex: "1:1", "16:9").

        Raises:
            ImportError: Se o SDK `google.genai` não estiver instalado.
            ValueError: Se a chave de API não for fornecida.
            ImageGenerationError: Se a inicialização do cliente falhar.
        """
        if not _GENAI_SDK_AVAILABLE:
            raise ImportError("SDK 'google.genai' não encontrado. Instale com 'pip install google-genai'.")
        if not api_key:
            raise ValueError("A chave de API do Google (api_key) não pode ser nula.")

        self.model_name = model_name
        self.api_min_interval_seconds = api_min_interval_seconds
        self.aspect_ratio = aspect_ratio
        self._genai_types = genai_types

        try:
            # Inicialização do cliente conforme a FONTE ÚNICA DA VERDADE
            self._client: genai_client.Client = genai_sdk.Client(api_key=api_key)
            logger.info(f"Cliente google.genai.Client (para Imagen) inicializado com sucesso para o modelo '{self.model_name}'.")
        except Exception as e:
            logger.critical(f"Falha ao inicializar google.genai.Client: {e}", exc_info=True)
            raise ImageGenerationError(f"Falha na inicialização do cliente Google: {e}") from e

    def _rate_limit(self):
        """Garante um intervalo mínimo entre as chamadas à API."""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.api_min_interval_seconds:
                sleep_time = self.api_min_interval_seconds - elapsed
                logger.debug(f"Imagen 4 Rate Limit: Aguardando {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            self._last_request_time = time.time()

    async def generate_image(self, prompt: str) -> bytes:
        """
        Gera uma imagem a partir de um prompt textual usando o Imagen 4.

        Args:
            prompt (str): O texto descritivo para criar a imagem.

        Returns:
            bytes: Os dados binários da imagem gerada.

        Raises:
            ImageGenerationError: Se a geração da imagem falhar.
        """
        self._rate_limit()
        logger.info(f"Gerando imagem com Imagen 4 para o prompt: '{prompt[:80]}...'")
        
        try:
            # Construção da configuração conforme FONTE ÚNICA DA VERDADE
            image_generation_config = self._genai_types.GenerateImagesConfig(
                number_of_images=1, 
                aspect_ratio=self.aspect_ratio
            )
            
            # Chamada à API conforme FONTE ÚNICA DA VERDADE
            # NOTA: síncrona, idealmente executada em um thread pool em ambiente asyncio.
            response = self._client.models.generate_images(
                model=self.model_name, 
                prompt=prompt, 
                config=image_generation_config
            )
            
            # Validação da resposta conforme FONTE ÚNICA DA VERDADE
            if response and hasattr(response, 'generated_images') and response.generated_images:
                first_image = response.generated_images[0]
                if hasattr(first_image, 'image') and hasattr(first_image.image, 'image_bytes'):
                    logger.info("Imagem gerada com sucesso pelo Imagen 4.")
                    return first_image.image.image_bytes
            
            # Lógica de erro detalhada
            error_details = "Nenhuma imagem retornada."
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                error_details = f"Prompt bloqueado. Razão: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}"
            
            logger.error(f"Falha na geração com Imagen 4: {error_details}")
            raise ImageGenerationError(f"Falha na geração com Imagen 4: {error_details}")

        except Exception as e:
            logger.error(f"Erro inesperado ao chamar Imagen 4 com prompt '{prompt[:80]}...': {type(e).__name__} - {e}", exc_info=True)
            raise ImageGenerationError(f"Erro ao chamar API do Imagen 4: {e}") from e

    async def generate_video(self, prompt: str) -> bytes:
        """
        Gera um vídeo a partir de um prompt textual. (Não implementado)

        Raises:
            NotImplementedError: Este adaptador foca na geração de imagens.
        """
        logger.warning("A geração de vídeo não é suportada por este adaptador (GoogleImageAdapter).")
        raise NotImplementedError("Este adaptador é específico para a geração de imagens com o Imagen 4.")
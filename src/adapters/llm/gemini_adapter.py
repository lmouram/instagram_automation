# src/adapters/llm/gemini_adapter.py

"""
Módulo do Adaptador do Google Gemini.

Este arquivo contém a implementação concreta da `ContentGeneratorPort` utilizando
a API do Google Gemini. Ele encapsula toda a lógica de comunicação, incluindo
autenticação, formatação de prompt, chamadas à API, rate limiting e tratamento
de erros, seguindo estritamente as diretrizes do SDK `google.genai`.
"""

import json
import logging
import threading
import time

# Importação segura do SDK do Gemini, conforme a FONTE ÚNICA DA VERDADE
try:
    import google.genai as genai_sdk
    from google.genai import client as genai_client
    from google.genai import types as genai_types
    _GEMINI_SDK_AVAILABLE = True
except ImportError:
    _GEMINI_SDK_AVAILABLE = False
    genai_sdk = None
    genai_client = None
    genai_types = None

from src.ports.content_generator import ContentGeneratorPort

logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Exceção customizada para erros relacionados à API do Gemini."""
    pass


class GeminiAdapter(ContentGeneratorPort):
    """
    Adaptador que implementa a `ContentGeneratorPort` para o Google Gemini.
    Esta implementação é baseada no novo SDK `google.genai`.
    """

    _last_request_time: float = 0
    _lock = threading.Lock()

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-pro", # Conforme FONTE ÚNICA DA VERDADE
        api_min_interval_seconds: float = 1.0,
        max_retries: int = 3,
        delay_seconds: int = 5
    ):
        """
        Inicializa o adaptador do Gemini.

        Args:
            api_key (str): A chave de API para autenticação.
            model_name (str): O nome do modelo Gemini a ser usado.
            api_min_interval_seconds (float): Intervalo mínimo entre chamadas.
            max_retries (int): Número máximo de tentativas em caso de falha.
            delay_seconds (int): Delay inicial entre tentativas.

        Raises:
            ImportError: Se o SDK `google.genai` não estiver instalado.
            ValueError: Se a chave de API não for fornecida.
            GeminiAPIError: Se a inicialização do cliente falhar.
        """
        if not _GEMINI_SDK_AVAILABLE:
            raise ImportError("SDK 'google.genai' não encontrado. Instale com 'pip install google-genai'.")
        if not api_key:
            raise ValueError("A chave de API do Gemini (api_key) não pode ser nula.")

        self.model_name = model_name
        self.api_min_interval_seconds = api_min_interval_seconds
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds
        self._genai_types = genai_types

        try:
            # Inicialização do cliente conforme a FONTE ÚNICA DA VERDADE
            self._client: genai_client.Client = genai_sdk.Client(api_key=api_key)
            logger.info(f"Cliente google.genai.Client inicializado com sucesso para o modelo '{self.model_name}'.")
        except Exception as e:
            logger.critical(f"Falha ao inicializar google.genai.Client: {e}", exc_info=True)
            raise GeminiAPIError(f"Falha na inicialização do cliente Gemini: {e}") from e

    def _rate_limit(self):
        """Garante um intervalo mínimo entre as chamadas à API."""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.api_min_interval_seconds:
                sleep_time = self.api_min_interval_seconds - elapsed
                logger.debug(f"Gemini Rate Limit: Aguardando {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            self._last_request_time = time.time()

    def _build_prompt(self, theme: str) -> str:
        """Cria um prompt detalhado para gerar uma legenda de Instagram."""
        return (
            "Aja como um especialista em mídias sociais criando um post para o Instagram.\n"
            "**Tarefa:** Crie uma legenda envolvente e informativa.\n"
            "**Tema:** {theme}\n"
            "**Requisitos:**\n"
            "- O tom deve ser inspirador e positivo.\n"
            "- A legenda deve ter entre 2 a 4 parágrafos curtos.\n"
            "- Inclua de 2 a 4 emojis relevantes ao longo do texto.\n"
            "- Finalize com uma seção contendo de 5 a 7 hashtags relevantes e populares sobre o tema.\n\n"
            "**Legenda Gerada:**"
        ).format(theme=theme)

    async def generate_text_for_post(self, theme: str) -> str:
        """
        Gera um conteúdo textual para uma postagem com base em um tema.

        Args:
            theme (str): O tópico sobre o qual o conteúdo deve ser gerado.

        Returns:
            str: O conteúdo textual gerado.

        Raises:
            GeminiAPIError: Se a geração de texto falhar após todas as retentativas.
        """
        self._rate_limit()
        prompt = self._build_prompt(theme)
        logger.info(f"Gerando texto com Gemini para o tema: '{theme}'")
        logger.debug(f"Prompt completo enviado ao Gemini:\n{prompt}")

        # Construção de `contents` conforme FONTE ÚNICA DA VERDADE
        contents = [self._genai_types.Part.from_text(text=prompt)]
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # NOTA: A chamada `generate_content` é síncrona. Em um ambiente de
                # produção asyncio, esta chamada deveria ser executada em um thread
                # separado para não bloquear o event loop, por exemplo, com
                # `await asyncio.to_thread(...)`.
                response = self._client.models.generate_content(
                    model=f"models/{self.model_name}", # O novo SDK pode exigir o prefixo "models/"
                    contents=contents,
                    config=None # Simplificado para nosso caso de uso
                )

                # Lógica de validação de resposta, baseada fielmente na FONTE ÚNICA DA VERDADE
                if response.text:
                    logger.info(f"Texto gerado com sucesso para o tema '{theme}' na tentativa {attempt + 1}.")
                    return response.text
                
                # Diagnóstico de resposta vazia/bloqueada
                candidate = response.candidates[0]
                finish_reason_enum = getattr(candidate, 'finish_reason', 'UNKNOWN')
                finish_reason = finish_reason_enum.name if hasattr(finish_reason_enum, 'name') else str(finish_reason_enum)

                block_reason_enum = getattr(getattr(response, 'prompt_feedback', None), 'block_reason', 'N/A')
                block_reason = block_reason_enum.name if hasattr(block_reason_enum, 'name') else str(block_reason_enum)
                
                error_detail = (
                    f"EMPTY_RESPONSE_FROM_API: Resposta sem conteúdo de texto. "
                    f"Finish Reason: '{finish_reason}'. "
                    f"Block Reason: '{block_reason}'."
                )
                last_exception = GeminiAPIError(error_detail)
                logger.warning(f"Gemini (Tentativa {attempt + 1}): {error_detail}. Retentando...")

            except Exception as e:
                last_exception = e
                logger.error(
                    f"Gemini (Tentativa {attempt + 1}): Falha na chamada da API: {type(e).__name__} - {e}",
                    exc_info=False
                )
            
            if attempt < self.max_retries - 1:
                sleep_time = self.delay_seconds * (2 ** attempt)
                logger.info(f"Aguardando {sleep_time}s para a próxima tentativa...")
                time.sleep(sleep_time)

        error_msg = (
            f"Falha na geração de texto com Gemini para o tema '{theme}' "
            f"após {self.max_retries} tentativas. Último erro: {last_exception}"
        )
        logger.error(error_msg)
        raise GeminiAPIError(error_msg) from last_exception
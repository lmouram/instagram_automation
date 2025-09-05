# src/adapters/llm/gemini_adapter.py

"""
Módulo do Adaptador do Google Gemini.

Este arquivo contém a implementação concreta da `ContentGeneratorPort`. Ele atua
como um "motor" genérico, recebendo um `LLMContract` da camada de aplicação e
traduzindo-o para uma chamada de API específica do Google Gemini.

Ele não possui conhecimento sobre a lógica de negócio (prompts ou schemas).
"""

import json
import logging
import re
import threading
import time
from typing import Any, Dict, Optional

from pydantic import ValidationError

# Importação segura do SDK do Gemini
try:
    import google.genai as genai_sdk
    from google.genai import client as genai_client
    from google.genai import types as genai_types
    _GEMINI_SDK_AVAILABLE = True
except ImportError:
    # ... (código de fallback) ...
    _GEMINI_SDK_AVAILABLE = False


# Importações da nossa arquitetura
from src.core.application.contracts import LLMContract
from src.ports.content_generator import ContentGeneratorPort

logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Exceção para erros na API do Gemini."""
    pass

class ParsingError(Exception):
    """Exceção para falhas ao parsear a resposta do LLM."""
    pass

class ValidationError(Exception):
    """Exceção para falhas de validação do schema da resposta."""
    pass


class GeminiAdapter(ContentGeneratorPort):
    """
    Adaptador que implementa a `ContentGeneratorPort` para o Google Gemini.
    Atua como um executor genérico de `LLMContract`.
    """

    _last_request_time: float = 0
    _lock = threading.Lock()

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-pro", # NOVO MODELO PRINCIPAL (NOVO SDK)
        repair_model_name: str = "gemini-2.5-flash", # NOVO MODELO SECUNDÁRIO (NOVO SDK)
        api_min_interval_seconds: float = 1.0,
        max_retries: int = 3,
        delay_seconds: int = 5
    ):
        if not _GEMINI_SDK_AVAILABLE: raise ImportError("SDK 'google.genai' não encontrado.")
        if not api_key: raise ValueError("A chave de API do Gemini não pode ser nula.")
        self.model_name = model_name
        self.repair_model_name = repair_model_name
        self.api_min_interval_seconds = api_min_interval_seconds
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds
        self._genai_types = genai_types
        try:
            self._client: genai_client.Client = genai_sdk.Client(api_key=api_key)
            logger.info(f"Cliente google.genai.Client inicializado para o modelo '{self.model_name}'.")
        except Exception as e:
            raise GeminiAPIError(f"Falha na inicialização do cliente Gemini: {e}") from e


    def _rate_limit(self):
        # ... (código do _rate_limit permanece o mesmo) ...
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.api_min_interval_seconds:
                sleep_time = self.api_min_interval_seconds - elapsed
                time.sleep(sleep_time)
            self._last_request_time = time.time()


    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        # ... (código do _extract_json_from_text permanece o mesmo) ...
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if not match: match = re.search(r'(\{.*?\})', text, re.DOTALL)
        if match:
            try: return json.loads(match.group(1))
            except json.JSONDecodeError: return None
        return None


    # --- NOVO MÉTODO DE REPARO ---
    async def _repair_json(self, broken_text: str, prompt_name: str) -> Optional[str]:
        """
        Tenta corrigir uma string de JSON malformada usando um modelo de IA mais rápido.
        """
        logger.warning(
            f"A resposta para o prompt '{prompt_name}' não era um JSON válido. "
            f"Tentando reparar com o modelo '{self.repair_model_name}'."
        )
        
        repair_prompt = f"""# Tarefa
        Corrija o seguinte texto para que ele se torne um objeto JSON perfeitamente válido. Remova quaisquer comentários, texto introdutório ou final. Sua resposta deve ser APENAS o JSON corrigido.

        # Texto Quebrado
        {broken_text}
        """
        try:
            repair_contents = [self._genai_types.Part.from_text(text=repair_prompt)]
            
            # --- MELHORIA AQUI ---
            # Usa response_schema para forçar uma saída JSON ainda mais confiável.
            repair_config_dict = {"response_mime_type": "application/json"}
            if target_schema:
                repair_config_dict["response_schema"] = target_schema
            
            repair_config = self._genai_types.GenerateContentConfig(**repair_config_dict)
            
            response = self._client.models.generate_content(
                model=self.repair_model_name,
                contents=repair_contents,
                config=repair_config
            )
            logger.info("Tentativa de reparo de JSON concluída com sucesso.")
            return response.text
        except Exception as e:
            logger.error(f"A chamada de reparo de JSON falhou: {e}", exc_info=False)
            return None


    async def generate(self, contract: LLMContract) -> Dict[str, Any]:
        """
        Executa uma chamada genérica ao LLM do Google com base em um contrato,
        incluindo uma etapa de auto-reparo para respostas JSON.
        """
        self._rate_limit()

        try:
            prompt = contract.prompt_template.format(**contract.input_variables)
        except KeyError as e:
            raise GeminiAPIError(f"Variável de input ausente no contrato: {e}")

        logger.info(
            f"Executando contrato de prompt '{contract.prompt_name}' v{contract.prompt_version} "
            f"com o modelo '{self.model_name}'."
        )

        config_dict = {}
        
        # --- LÓGICA DE CONFIGURAÇÃO CORRIGIDA ---
        if contract.tools:
            if "web_search" in contract.tools:
                config_dict["tools"] = [self._genai_types.Tool(google_search=self._genai_types.GoogleSearch())]
            # IMPORTANTE: Se houver tools, não podemos usar response_mime_type
            if contract.response_format == "json":
                logger.debug("O contrato solicita JSON e ferramentas. A API do Gemini não suporta ambos. Priorizando ferramentas e parse manual.")
        elif contract.response_format == "json":
            config_dict["response_mime_type"] = "application/json"
            if contract.output_schema:
                config_dict["response_schema"] = contract.output_schema

        config_dict.update(contract.vendor_overrides)
        
        config = self._genai_types.GenerateContentConfig(**config_dict) if config_dict else None
        contents = [self._genai_types.Part.from_text(text=prompt)]

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # --- CORREÇÕES AQUI ---
                response = self._client.models.generate_content(
                    model=self.model_name, # 1. Removido o prefixo "models/"
                    contents=contents,
                    config=config # 2. Nome do argumento corrigido para 'config'
                )
                
                if not response.text:
                    error_detail = f"Resposta bloqueada. Razão: '{getattr(getattr(response, 'prompt_feedback', None), 'block_reason', 'Desconhecido').name}'"
                    raise GeminiAPIError(error_detail)

                if contract.response_format == "json":
                    # Tenta usar o parser embutido do SDK se um schema foi fornecido E NENHUMA FERRAMENTA FOI USADA
                    if contract.output_schema and not contract.tools:
                        try:
                            # FONTE DA VERDADE: usa getattr para segurança
                            parsed_obj = getattr(response, 'parsed', None)
                            if parsed_obj:
                                logger.info("Resposta JSON parseada pelo SDK com sucesso.")
                                return parsed_obj.model_dump()
                        except Exception as e:
                             logger.warning(f"Falha ao usar o parser JSON do SDK: {e}. Recorrendo ao parse manual.")

                    # Fallback para extração manual e reparo
                    json_data = self._extract_json_from_text(response.text)
                    if not json_data:
                        repaired_text = await self._repair_json(response.text, contract.prompt_name, contract.output_schema)
                        if repaired_text: json_data = self._extract_json_from_text(repaired_text)
                    
                    if not json_data:
                        raise ParsingError(f"Resposta não continha JSON válido, mesmo após reparo.")
                    
                    if contract.output_schema:
                        try:
                            validated_obj = contract.output_schema.model_validate(json_data)
                            return validated_obj.model_dump()
                        except PydanticValidationError as e:
                            raise ValidationError(f"JSON falhou na validação do schema: {e}") from e
                    
                    return json_data
                else:
                    return {"text_content": response.text}

            except (GeminiAPIError, ParsingError, ValidationError) as e:
                last_exception = e
                logger.warning(f"Gemini (Tentativa {attempt + 1}/{self.max_retries}): {e}")
            except Exception as e:
                last_exception = e
                logger.error(f"Gemini (Tentativa {attempt + 1}/{self.max_retries}): Falha na API: {e}", exc_info=False)
            
            if attempt < self.max_retries - 1:
                time.sleep(self.delay_seconds * (2 ** attempt))

        error_msg = f"Falha ao executar contrato '{contract.prompt_name}' v{contract.prompt_version} após {self.max_retries} tentativas. Último erro: {last_exception}"
        logger.error(error_msg)
        raise GeminiAPIError(error_msg) from last_exception
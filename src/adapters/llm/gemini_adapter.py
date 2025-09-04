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
import re
import threading
import time
from typing import List, Optional
from pydantic import BaseModel, Field

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

# --- Pydantic Schemas para Respostas Estruturadas ---

class DossierSchema(BaseModel):
    """
    Schema para a resposta JSON esperada ao gerar um dossiê.
    Define a estrutura que o Gemini deve retornar.
    """
    dossie: str = Field(
        ..., 
        description="O dossiê completo e bem-organizado em formato Markdown."
    )
    search_queries_used: List[str] = Field(
        ..., 
        description="A lista de queries de busca usadas para a investigação."
    )

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

    def _build_instagram_post_prompt(self, theme: str) -> str:
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

    # --- NOVO MÉTODO DE PROMPT (da FONTE ÚNICA DA VERDADE) ---
    def _build_dossier_prompt(self, theme: str) -> str:
        """
        Cria um prompt para guiar o LLM a realizar uma pesquisa investigativa
        e gerar um dossiê detalhado sobre um tema, com a ferramenta de busca ativada.
        """
        return f"""
    # Missão
    Você é um Jornalista Investigativo e Estrategista de Pesquisa. Sua especialidade é desconstruir um tema, conduzir uma investigação profunda usando a ferramenta de busca e, em seguida, sintetizar as descobertas em um dossiê completo e bem fundamentado.

    # Tema para Investigação
    "{theme}"

    # Tarefa Principal: Processo de Investigação em 3 Etapas
    Sua tarefa é gerar um dossiê de pesquisa (`dossie`) e a lista de queries usadas (`search_queries_used`). Para isso, você DEVE seguir rigorosamente as três etapas abaixo.

    ## Etapa 1: Análise e Desconstrução do Tema
    Primeiro, analise o tema fornecido e identifique a **PERGUNTA CENTRAL** ou a **AFIRMAÇÃO PRINCIPAL** a ser investigada. Desconstrua o tema em seus componentes essenciais para guiar sua pesquisa.

    1.  **Sujeito Principal:** Quem ou o que é o foco principal? (Ex: uma tecnologia, uma pessoa, um conceito, um evento).
    2.  **Contexto/Ação:** Qual é o contexto, a ação ou a relevância do sujeito? (Ex: seu impacto na indústria, sua história, como funciona).
    3.  **Escopo:** Qual é a delimitação da investigação? (Ex: focado em um país, em um período de tempo, em uma aplicação específica).

    Essa análise inicial é o núcleo da sua investigação.

    ## Etapa 2: Planejamento da Estratégia de Pesquisa
    Com base na sua análise, você tem autonomia para definir o melhor caminho de pesquisa. Seu objetivo é decidir quais informações são cruciais para entender completamente o tema.

    Para isso, você deve:
    1.  **Identificar Ângulos de Investigação:** Pense em quais áreas precisam de aprofundamento. Exemplos:
        -   Definição e Histórico do [Sujeito].
        -   Como o [Sujeito] funciona (Mecanismos, Detalhes Técnicos).
        -   Aplicações Práticas e Casos de Uso.
        -   Impacto, Vantagens e Desvantagens.
        -   Principais Atores (Empresas, Pesquisadores, Instituições).
        -   Estado da Arte e Tendências Futuras.
        -   Dados, Estatísticas ou Estudos Relevantes.
    2.  **Criar as Queries de Busca:** Com base nos seus ângulos de investigação, formule as queries de busca específicas que você usaria para encontrar essas informações. Essas queries devem ser listadas no campo `search_queries_used` da sua resposta final.

    ## Etapa 3: Execução da Pesquisa e Criação do Dossiê
    Execute seu plano de pesquisa usando a ferramenta de busca. Colete informações de fontes confiáveis.

    Sintetize todas as suas descobertas em um dossiê detalhado e bem organizado no campo `dossie`. O dossiê deve ser formatado em **Markdown** e incluir, no mínimo, as seguintes seções:
    -   **Resumo Executivo:** Um parágrafo inicial que resume os pontos mais importantes da sua investigação.
    -   **Contexto e Definição:** O que é o tema e qual seu histórico relevante.
    -   **Análise Aprofundada:** O corpo principal da pesquisa, dividido em subtópicos claros (ex: "Como Funciona", "Aplicações Principais", "Impacto no Mercado").
    -   **Atores Chave:** Lista e descrição das principais entidades envolvidas.
    -   **Conclusão e Perspectivas Futuras:** Um resumo das implicações e o que esperar para o futuro.

    # Formato da Saída (JSON Obrigatório)
    Sua resposta DEVE ser um único objeto JSON válido, sem nenhum texto antes ou depois. O exemplo abaixo mostra o formato exato e a qualidade do conteúdo esperado.

    ```json
    {{
    "dossie": "dossie completo em markdown",
    "search_queries_used": ["query 1", "query 2"]
    }}
    ```"""

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
        prompt = self._build_instagram_post_prompt(theme)
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

    # --- NOVO MÉTODO PRIVADO (da FONTE ÚNICA DA VERDADE) ---
    def _extract_json_from_text(self, text: str) -> Optional[dict]:
        """
        Extrai um bloco de JSON de uma string de texto usando expressões regulares.
        """
        # Procura por um bloco de código JSON ```json ... ```
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if not match:
            # Se não encontrar, procura por qualquer objeto JSON { ... }
            match = re.search(r'(\{.*?\})', text, re.DOTALL)
        
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.error("Falha ao fazer o parse do JSON extraído do texto.", exc_info=True)
                return None
        return None

    # --- NOVO MÉTODO PRINCIPAL ---
    async def generate_dossier(self, theme: str) -> str:
        """
        Gera um dossiê sobre um tema, utilizando a ferramenta de busca do Google.

        Args:
            theme (str): O tema a ser pesquisado.

        Returns:
            str: O dossiê em formato Markdown.

        Raises:
            GeminiAPIError: Se a geração falhar após todas as retentativas.
        """
        self._rate_limit()
        prompt = self._build_dossier_prompt(theme)
        logger.info(f"Gerando dossiê com pesquisa para o tema: '{theme}'")
        
        contents = [self._genai_types.Part.from_text(text=prompt)]
        
        # Configuração da chamada, conforme FONTE ÚNICA DA VERDADE
        tools = [self._genai_types.Tool(google_search=self._genai_types.GoogleSearch())]
        generation_config_obj = self._genai_types.GenerateContentConfig(
            tools=tools,
        )

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # NOTA: Chamada síncrona, idealmente em thread pool em ambiente asyncio
                response = self._client.models.generate_content(
                    model=f"models/{self.model_name}",
                    contents=contents,
                    config=generation_config_obj
                )

                # --- LÓGICA DE PARSING MODIFICADA ---
                if response.text:
                    # Extrai o JSON do texto de resposta
                    json_data = self._extract_json_from_text(response.text)
                    
                    if json_data:
                        # Valida o JSON com o nosso schema Pydantic
                        parsed_data = DossierSchema.model_validate(json_data)
                        
                        logger.info(f"Dossiê gerado e parseado com sucesso para o tema '{theme}' na tentativa {attempt + 1}.")
                        return parsed_data.dossie # <-- MUDANÇA: 'dossie' em vez de 'context_summary_markdown'
                    else:
                        last_exception = GeminiAPIError(f"A resposta do Gemini foi recebida, mas não continha um JSON válido. Resposta: {response.text[:200]}...")
                        logger.warning(f"Gemini (Tentativa {attempt + 1}): {last_exception}")
                else:
                    # Lógica de diagnóstico de bloqueio
                    error_detail = "Resposta do Gemini vazia."
                    if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                        error_detail = f"Resposta do Gemini bloqueada. Razão: '{response.prompt_feedback.block_reason.name}'"
                    last_exception = GeminiAPIError(error_detail)
                    logger.warning(f"Gemini (Tentativa {attempt + 1}): {error_detail}. Retentando...")


            except Exception as e:
                last_exception = e
                logger.error(f"Gemini (Tentativa {attempt + 1}): Falha na API: {type(e).__name__} - {e}", exc_info=False)
            
            if attempt < self.max_retries - 1:
                sleep_time = self.delay_seconds * (2 ** attempt)
                time.sleep(sleep_time)

        error_msg = f"Falha na geração do dossiê para '{theme}' após {self.max_retries} tentativas. Último erro: {last_exception}"
        logger.error(error_msg)
        raise GeminiAPIError(error_msg) from last_exception
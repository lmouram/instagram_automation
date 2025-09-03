# src/utils/resilience.py

"""
Módulo de Utilitários de Resiliência.

Este módulo fornece um conjunto de decoradores para aumentar a robustez
dos adaptadores que interagem com serviços externos. Ele encapsula lógicas
de retentativa (retry) e limitação de taxa (rate limiting), permitindo que
sejam aplicadas de forma declarativa e limpa.

Dependências externas: `tenacity`, `ratelimit`.
Certifique-se de que estão listadas nas dependências do projeto.
"""

import logging
from functools import wraps
from typing import Callable

from ratelimit import limits, RateLimitException
from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


def _log_on_retry(retry_state):
    """Função de callback para logar informações antes de uma nova tentativa."""
    logger.warning(
        f"Tentativa {retry_state.attempt_number} falhou. "
        f"Aguardando {retry_state.next_action.sleep:.2f}s antes da próxima. "
        f"Causa: {retry_state.outcome.exception()}"
    )


def retry_async_run(max_attempts: int = 3):
    """
    Decorador de retentativa para funções assíncronas.

    Aplica uma estratégia de retentativa com backoff exponencial. Se a função
    decorada falhar, ela será executada novamente até atingir o número máximo
    de tentativas.

    Exemplo de uso:
    ```python
    @retry_async_run(max_attempts=5)
    async def my_unreliable_api_call():
        # ... código que pode falhar
    ```

    Args:
        max_attempts (int): O número total de tentativas a serem feitas.
                            Padrão é 3.

    Returns:
        Callable: O decorador configurado.
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retryer = AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=2, max=30),
                before_sleep=_log_on_retry,
                reraise=True,  # Re-levanta a exceção original após a última falha
            )
            try:
                return await retryer.call(func, *args, **kwargs)
            except RetryError as e:
                # O `reraise=True` já faz isso, mas adicionamos um log final
                # para maior clareza sobre o esgotamento das tentativas.
                logger.error(
                    f"Função '{func.__name__}' falhou após {max_attempts} tentativas."
                )
                raise e.last_attempt.result()

        return wrapper

    return decorator


def rate_limit_async(calls: int, period: int):
    """
    Decorador de limitação de taxa para funções assíncronas.

    Garante que a função decorada não seja chamada mais do que um número
    específico de vezes (`calls`) dentro de um determinado período de tempo
    em segundos (`period`).

    Exemplo de uso:
    ```python
    # Limita a 60 chamadas por minuto (60 segundos)
    @rate_limit_async(calls=60, period=60)
    async def my_rate_limited_function():
        # ... código que chama uma API
    ```

    Args:
        calls (int): O número máximo de chamadas permitidas.
        period (int): O período de tempo em segundos.

    Returns:
        Callable: O decorador configurado.
    """

    def decorator(func: Callable):
        # A biblioteca `ratelimit` aplica o decorador diretamente
        # e lida com funções `async` de forma transparente.
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Criamos uma função síncrona interna para o decorador `limits`
                # e a executamos de forma assíncrona. Isso garante que o `sleep`
                # do ratelimit não bloqueie o event loop se ele for usado.
                # No entanto, a implementação do `ratelimit` já é inteligente
                # o suficiente para usar asyncio.sleep se estiver em um loop.
                # Esta é uma forma mais simples e direta.
                @limits(calls=calls, period=period)
                def check_limit():
                    pass # Só verifica o limite
                
                check_limit()
                return await func(*args, **kwargs)

            except RateLimitException as e:
                logger.warning(
                    f"Rate limit atingido para a função '{func.__name__}'. "
                    f"Aguardando para a próxima janela. Detalhes: {e}"
                )
                # A exceção é capturada, mas podemos querer relançá-la
                # ou esperar e tentar novamente. Por padrão, a biblioteca
                # já faz o sleep, então capturar a exceção é mais para log.
                # Se quisermos parar a execução, podemos relançar a exceção.
                raise
        
        # A biblioteca `ratelimit` é mais simples, vamos usar a forma direta
        # que já é compatível com asyncio.
        return limits(calls=calls, period=period)(func)


    return decorator
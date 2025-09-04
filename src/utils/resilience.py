# src/utils/resilience.py

"""
Módulo de Utilitários de Resiliência.

Este módulo fornece um conjunto de ferramentas para aumentar a robustez da
aplicação. Ele encapsula:
- Decoradores para retentativa (retry) e limitação de taxa (rate limiting),
  ideais para serem aplicadas nos adaptadores.
- Funções para cálculo de estratégias de backoff, úteis para os orquestradores
  de workflow.

Dependências externas: `tenacity`, `ratelimit`.
Certifique-se de que estão listadas nas dependências do projeto.
"""

import logging
import random # <-- Adicionar import
from datetime import datetime, timedelta, timezone # <-- Adicionar imports
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


# --- Funções de Cálculo de Backoff (Para Orquestradores) ---

def get_next_retry_at(
    attempt: int, base_seconds: float = 2.0, max_seconds: float = 300.0
) -> datetime:
    """
    Calcula o próximo timestamp de retentativa com backoff exponencial e jitter.

    Esta função é ideal para a lógica de reagendamento de workflows, determinando
    QUANDO uma próxima tentativa deve ocorrer.

    Args:
        attempt (int): O número da tentativa atual (começando em 0 ou 1).
        base_seconds (float): O tempo de espera base para a primeira retentativa.
        max_seconds (float): O tempo máximo de espera, para evitar esperas muito longas.

    Returns:
        datetime: Um objeto datetime timezone-aware (UTC) indicando o momento
                  da próxima tentativa.
    """
    # Calcula o tempo de espera exponencial
    expo_wait = base_seconds * (2 ** max(0, attempt))
    
    # Limita o tempo de espera ao valor máximo (cap)
    wait_time = min(expo_wait, max_seconds)
    
    # Adiciona "jitter" (variação aleatória) para evitar que múltiplos workers
    # tentem novamente ao mesmo tempo (problema de "thundering herd").
    jitter = random.uniform(0, wait_time * 0.1)  # 0-10% de jitter
    
    total_wait_seconds = wait_time + jitter
    
    return datetime.now(timezone.utc) + timedelta(seconds=total_wait_seconds)


# --- Decoradores de Resiliência (Para Adaptadores) ---

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
    ... (o resto do decorador permanece o mesmo) ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retryer = AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=2, max=30),
                before_sleep=_log_on_retry,
                reraise=True,
            )
            try:
                return await retryer.call(func, *args, **kwargs)
            except RetryError as e:
                logger.error(
                    f"Função '{func.__name__}' falhou após {max_attempts} tentativas."
                )
                raise e.last_attempt.result()
        return wrapper
    return decorator


def rate_limit_async(calls: int, period: int):
    """
    Decorador de limitação de taxa para funções assíncronas.
    ... (o resto do decorador permanece o mesmo) ...
    """
    def decorator(func: Callable):
        return limits(calls=calls, period=period)(func)
    return decorator
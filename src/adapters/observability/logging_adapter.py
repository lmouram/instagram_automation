# src/adapters/observability/logging_adapter.py

"""
Módulo do Adaptador de Observabilidade baseado em Logging.

Este arquivo contém a implementação concreta da `ObservabilityPort` que utiliza
o sistema de logging padrão do Python como backend. É a implementação inicial
e mais simples de observabilidade para o projeto.
"""

import logging
from typing import Any, Dict, Optional

from src.ports.observability import ObservabilityPort


class LoggingObservabilityAdapter(ObservabilityPort):
    """
    Implementação da `ObservabilityPort` que traduz eventos, métricas e
    relatórios de saúde em mensagens de log estruturadas.

    Esta classe não configura o logger; ela recebe uma instância de logger já
    configurada, desacoplando o adaptador da configuração global de logging.
    Isso adere ao Princípio da Inversão de Dependência.
    """

    def __init__(self, logger: logging.Logger):
        """
        Inicializa o adaptador com uma instância de logger.

        Args:
            logger (logging.Logger): Uma instância de logger já configurada
                                     (ex: obtida de um módulo central de
                                     configuração de log).
        """
        self._logger = logger
        self._logger.info("LoggingObservabilityAdapter inicializado.")

    async def log_event(
        self, event_name: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra um evento de negócio como uma mensagem de log no nível INFO.

        Args:
            event_name (str): O nome do evento, ex: 'POST_APPROVED'.
            details (Optional[Dict[str, Any]]): Dados contextuais do evento.
        """
        details_str = (
            " - " + " ".join([f"{k}={v}" for k, v in details.items()])
            if details
            else ""
        )
        self._logger.info(f"[EVENT] {event_name}{details_str}")

    async def increment_metric(
        self,
        metric_name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Registra uma métrica como uma mensagem de log no nível DEBUG.

        Métricas são logadas em um nível mais baixo para evitar poluir os logs
        principais, mas ainda assim estarem disponíveis para análise detalhada.

        Args:
            metric_name (str): O nome da métrica, ex: 'posts_published_total'.
            value (float): O valor a ser incrementado.
            tags (Optional[Dict[str, str]]): Tags para segmentação.
        """
        tags_str = f" tags={tags}" if tags else ""
        self._logger.debug(f"[METRIC] {metric_name} - value={value}{tags_str}")

    async def report_health(
        self, service_name: str, is_healthy: bool, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Relata o estado de saúde de um serviço, usando níveis de log diferentes
        para sucesso e falha.

        Args:
            service_name (str): O nome do serviço verificado.
            is_healthy (bool): O estado de saúde do serviço.
            details (Optional[Dict[str, Any]]): Detalhes adicionais,
                                                 especialmente em caso de falha.
        """
        details_str = (
            " - " + " ".join([f"{k}={v}" for k, v in details.items()])
            if details
            else ""
        )
        if is_healthy:
            self._logger.info(f"[HEALTH] {service_name} - status=HEALTHY{details_str}")
        else:
            self._logger.warning(f"[HEALTH] {service_name} - status=UNHEALTHY{details_str}")
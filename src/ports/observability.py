# src/ports/observability.py

"""
Módulo da Porta de Observabilidade.

Este arquivo define a porta (interface abstrata) para as funcionalidades de
observabilidade do sistema, incluindo o registro de eventos de negócio, a
coleta de métricas e o relato de status de saúde.

O propósito desta porta é desacouplar o núcleo da aplicação (core) dos
detalhes de implementação de qualquer ferramenta ou plataforma de monitoramento
específica (ex: Prometheus, Datadog, Sentry, ou um simples logger).
Isso permite que a aplicação seja instrumentada de forma consistente,
enquanto a forma como os dados de observabilidade são coletados e
visualizados pode evoluir independentemente.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ObservabilityPort(ABC):
    """
    Interface abstrata (Porta) para um serviço de observabilidade.

    Define o contrato que os adaptadores de monitoramento e logging devem seguir.
    Os casos de uso e outros componentes do core utilizarão esta porta para
    relatar informações importantes sobre a execução do sistema.
    """

    @abstractmethod
    async def log_event(
        self, event_name: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra um evento de negócio significativo.

        Diferente de um log de debug, um evento de negócio representa uma
        ocorrência importante no domínio (ex: 'post_approved',
        'publication_failed').

        Args:
            event_name (str): O nome do evento, que deve ser único e descritivo.
                              Ex: 'USER_LOGIN_SUCCESS', 'PAYMENT_PROCESSED'.
            details (Optional[Dict[str, Any]]): Um dicionário com dados
                                                 contextuais sobre o evento.
                                                 Ex: {'post_id': '...', 'user': '...'}.
        """
        raise NotImplementedError

    @abstractmethod
    async def increment_metric(
        self,
        metric_name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Incrementa o valor de uma métrica numérica (contador).

        Métricas são essenciais para dashboards, monitoramento de performance e
        criação de alertas (ex: 'número de posts publicados por hora').

        Args:
            metric_name (str): O nome da métrica. Ex: 'posts_published_total'.
            value (float): O valor a ser adicionado à métrica. Padrão é 1.0.
            tags (Optional[Dict[str, str]]): Um dicionário de tags (ou labels)
                                             para segmentar a métrica.
                                             Ex: {'status': 'success', 'type': 'carousel'}.
        """
        raise NotImplementedError

    @abstractmethod
    async def report_health(
        self, service_name: str, is_healthy: bool, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Relata o estado de saúde de um componente ou dependência externa.

        Utilizado para implementar health checks. Permite que o sistema reporte
        se suas dependências (banco de dados, APIs externas) estão operacionais.

        Args:
            service_name (str): O nome do serviço ou componente sendo verificado.
                                Ex: 'DatabaseConnection', 'GeminiAPI'.
            is_healthy (bool): True se o serviço está saudável, False caso contrário.
            details (Optional[Dict[str, Any]]): Informações adicionais, como
                                                 mensagens de erro ou latência.
        """
        raise NotImplementedError
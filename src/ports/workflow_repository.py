# src/ports/workflow_repository.py

"""
Módulo da Porta do Repositório de Workflows.

Este arquivo define a porta (interface abstrata) para a persistência e
recuperação de entidades `WorkflowRun`. Esta porta é a fronteira entre os
orquestradores de workflow (na camada de aplicação) e a infraestrutura de
armazenamento de estado.

Qualquer adaptador que deseje fornecer funcionalidade de persistência de
estado de workflow (seja em arquivos JSON, banco de dados, etc.) deve
implementar esta interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.domain import WorkflowRun


class WorkflowRepositoryPort(ABC):
    """
    Interface abstrata (Porta) para um repositório de execuções de workflow.

    Define o contrato que os adaptadores de persistência de estado devem seguir
    para gerenciar o ciclo de vida dos objetos `WorkflowRun`.
    """

    @abstractmethod
    async def create(self, run: WorkflowRun) -> None:
        """
        Persiste uma nova execução de workflow pela primeira vez.

        Args:
            run (WorkflowRun): A entidade `WorkflowRun` a ser criada.

        Raises:
            Exception: Pode levantar uma exceção específica do adaptador
                       em caso de falha na persistência (ex: erro de I/O,
                       violação de constraint).
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, run_id: str, workflow_name: str) -> Optional[WorkflowRun]:
        """
        Recupera uma única execução de workflow pelo seu identificador único.

        Args:
            run_id (str): O ID da execução do workflow a ser encontrada.
            workflow_name (str): O nome do workflow ao qual o run_id pertence.
        
        ...
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, run: WorkflowRun) -> None:
        """
        Atualiza o estado de uma execução de workflow existente.

        Implementações deste método devem, idealmente, incluir um mecanismo de
        controle de concorrência otimista (ex: verificando um campo de versão)
        para prevenir "lost updates" em ambientes com múltiplos workers.

        Args:
            run (WorkflowRun): A entidade `WorkflowRun` com seu estado atualizado.

        Raises:
            ConcurrencyError: (Recomendado) Se uma condição de corrida for
                              detectada durante a atualização.
            Exception: Para outros erros de persistência.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_ready_for_execution(
        self, workflow_name: str, limit: int
    ) -> List[WorkflowRun]:
        """
        Busca por execuções de workflow que estão prontas para serem processadas.

        A lógica de "pronto" geralmente inclui:
        - Status `PENDING`.
        - Status `FAILED_RETRYABLE` e cujo `retry_at` está no passado.

        Args:
            workflow_name (str): O nome do workflow a ser buscado (ex: "generate_dossier").
            limit (int): O número máximo de execuções a serem retornadas.

        Returns:
            List[WorkflowRun]: Uma lista de execuções de workflow prontas para
                               serem processadas, geralmente ordenadas pela data
                               de criação ou prioridade.
        """
        raise NotImplementedError
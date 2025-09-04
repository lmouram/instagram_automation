# src/ports/__init__.py

"""
Pacote de Portas (Interfaces / Contratos).

Este pacote é uma peça fundamental da Arquitetura Hexagonal. Ele define as
fronteiras do núcleo da aplicação através de interfaces abstratas (Portas).
Cada porta é um contrato que especifica um conjunto de funcionalidades que o
núcleo (core) precisa para interagir com o mundo exterior, sem se acoplar a
nenhuma tecnologia específica.

O papel desta camada é a aplicação direta do **Princípio da Inversão de
Dependência (DIP)** do SOLID:
- O `core/application` (casos de uso) depende destas abstrações (`ports`).
- A camada de `adapters` implementa estas abstrações.

Dessa forma, o fluxo de dependência é:
`Adapters -> Ports <- Core`

Isso significa que o núcleo da aplicação não sabe nada sobre bancos de dados,
APIs de IA, ou sistemas de arquivos. Ele apenas sabe que existe um "contrato"
que pode ser usado para, por exemplo, "salvar um post" ou "gerar um texto".

Todo o código neste pacote deve ser composto por classes base abstratas
(usando `abc.ABC`) e métodos abstratos (`@abstractmethod`), sem conter
nenhuma lógica de implementação.
"""

# Re-exporta todas as portas para criar uma API pública e conveniente
# para o pacote. Isso permite que outros módulos importem as portas
# diretamente de `src.ports` em vez dos arquivos específicos.

from .audit_repository import AuditEventRepositoryPort
from .content_generator import ContentGeneratorPort
from .media_generator import MediaGeneratorPort
from .observability import ObservabilityPort
from .post_repository import PostRepositoryPort
from .social_publisher import SocialMediaPublisherPort
from .storage import StoragePort
from .workflow_repository import WorkflowRepositoryPort
from .state_repository import StateRepositoryPort

__all__ = [
    "AuditEventRepositoryPort",
    "ContentGeneratorPort",
    "MediaGeneratorPort",
    "ObservabilityPort",
    "PostRepositoryPort",
    "SocialMediaPublisherPort",
    "StoragePort",
    "WorkflowRepositoryPort", # <-- Adicionado
    "StateRepositoryPort", # <-- Adicionado
]
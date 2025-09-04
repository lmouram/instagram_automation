# src/core/application/use_cases/__init__.py

"""
Pacote de Casos de Uso.

Este pacote contém os casos de uso atômicos da aplicação. Cada módulo aqui
representa uma única capacidade de negócio, orquestrando entidades de domínio
e utilizando portas para interagir com a infraestrutura.

Eles são os blocos de construção que podem ser compostos pelos orquestradores
para criar processos de negócio mais complexos.
"""

from .approve_post import approve_post_use_case
from .create_dossier import create_dossier_use_case
from .create_post import create_post_use_case
from .publish_post_immediately import publish_post_immediately_use_case
from .publish_scheduled_posts import publish_scheduled_posts_use_case

__all__ = [
    "approve_post_use_case",
    "create_dossier_use_case",
    "create_post_use_case",
    "publish_post_immediately_use_case",
    "publish_scheduled_posts_use_case",
]
# src/core/domain/__init__.py

"""
Pacote de Domínio.

Este pacote representa o coração da aplicação, o centro da Arquitetura
Hexagonal. Ele contém toda a lógica de negócio, as regras e as estruturas
de dados que são independentes de qualquer tecnologia externa.

O código aqui é "puro" e não tem conhecimento sobre bancos de dados,
interfaces de usuário, APIs externas ou qualquer outra preocupação de
infraestrutura.

Principais componentes desta camada:
- **Entidades (`entities.py`):** Objetos que representam os conceitos
  fundamentais do negócio (ex: Post, Media). Eles encapsulam o estado
  e podem conter métodos que aplicam regras de negócio a esse estado.
- **Enums (`enums.py`):** Conjuntos definidos de valores que representam
  estados ou tipos importantes para o domínio (ex: PostStatus), garantindo
  consistência e prevenindo erros.
- **Value Objects (se necessário):** Objetos que representam valores
  descritivos sem identidade própria (ex: um objeto de Cor, Endereço).

Este pacote não deve ter nenhuma dependência externa, exceto a biblioteca
padrão do Python. Ele é a parte mais estável e protegida da aplicação.
"""

# Re-exporta as entidades e enums para criar uma API pública e conveniente
# para a camada de domínio. Isso permite importações mais limpas, como:
# from src.core.domain import Post, PostStatus

from .entities import AuditEvent, Media, Post
from .enums import MediaType, PostStatus, PostType

__all__ = [
    "Post",
    "Media",
    "AuditEvent",
    "PostStatus",
    "PostType",
    "MediaType",
]
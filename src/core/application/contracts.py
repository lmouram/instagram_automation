# src/core/application/contracts.py

"""
Módulo de Contratos da Camada de Aplicação.

Este arquivo define as estruturas de dados (Data Transfer Objects - DTOs) que
servem como contratos entre diferentes partes da camada de aplicação e entre
a camada de aplicação e as portas.

Esses contratos garantem uma comunicação clara e desacoplada.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel


@dataclass
class LLMContract:
    """
    Encapsula a especificação completa e agnóstica a fornecedor para uma
    chamada a um Large Language Model (LLM).

    Esta estrutura é criada pela camada de aplicação (geralmente por uma fábrica
    de prompts) e consumida por um `ContentGeneratorAdapter`, que a traduz
    para uma chamada de API específica do provedor.
    """
    # --- Metadados para Governança e Rastreabilidade ---
    prompt_name: str
    """O nome único do prompt (ex: "copywriting", "dossier")."""
    
    prompt_version: str
    """A versão semântica do prompt (ex: "1.0", "1.1.2")."""

    # --- Conteúdo e Template ---
    prompt_template: str
    """O template de texto do prompt, com placeholders no estilo .format() (ex: {dossier})."""
    
    input_variables: Dict[str, Any] = field(default_factory=dict)
    """Um dicionário com as variáveis a serem inseridas no `prompt_template`."""

    # --- Capacidades e Formato de Resposta ---
    tools: List[str] = field(default_factory=list)
    """
    Uma lista de capacidades genéricas que o LLM deve utilizar.
    O adaptador é responsável por traduzir estes nomes genéricos para as
    ferramentas específicas do provedor.
    Exemplo: ["web_search"]
    """

    response_format: Optional[str] = "json"
    """
    O formato esperado da resposta. Pode ser "json" ou "text".
    Se "json", o adaptador deve tentar parsear e validar a resposta.
    """

    output_schema: Optional[Type[BaseModel]] = None
    """
    Se `response_format` for "json", este campo DEVE conter o schema Pydantic
    usado para validar a resposta do LLM.
    """
    
    # --- Configurações Específicas do Provedor (Escape Hatch) ---
    vendor_overrides: Dict[str, Any] = field(default_factory=dict)
    """
    Um dicionário para passar parâmetros específicos do provedor que não são
    abstraídos pelo contrato.
    Ex: {"temperature": 0.5, "top_p": 0.9}
    """
"""
Pacote de Prompt para Geração de Componentes de Prompt de Imagem.

Este arquivo __init__.py serve como a fachada pública para o pacote
`image_prompt_components`. Ele expõe os artefatos essenciais da versão mais
recente (ou de versões específicas), permitindo que o `Prompt Registry` e
outras partes da aplicação os importem de um local centralizado e estável.
"""

# Importa os componentes principais do módulo da versão 1.0.
from .v1_0 import get_contract, ImagePromptComponentsOutput

# Define explicitamente a API pública deste pacote.
# Apenas 'get_contract' e 'ImagePromptComponentsOutput' serão importáveis
# quando um cliente fizer 'from src.core.application.prompts.image_prompt_components import *'.
__all__ = [
    "get_contract",
    "ImagePromptComponentsOutput"
]
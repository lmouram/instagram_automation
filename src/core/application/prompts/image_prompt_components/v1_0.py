"""
Módulo de Prompt para Geração de Componentes de Prompt de Imagem.

Versão: 1.0

Este arquivo encapsula a "receita" de negócio para a tarefa de usar um LLM
para gerar componentes estruturados que, juntos, formarão um prompt eficaz
para um modelo de geração de imagem (como Imagen 4 ou DALL-E).

A lógica aqui é agnóstica ao modelo de imagem final; ela apenas foca em
traduzir um conceito de negócio (baseado em dossiê e copy) em um conceito
visual estruturado.
"""

from pydantic import BaseModel, Field

from src.core.application.contracts import LLMContract


# 1. Schema de Saída: Define a estrutura de dados que esperamos do LLM.
class ImagePromptComponentsOutput(BaseModel):
    """
    Schema Pydantic para a resposta JSON esperada contendo os componentes
    do prompt de imagem. Cada campo representa um aspecto fundamental do prompt
    que será construído.
    """
    subject: str = Field(
        ...,
        description=(
            "O sujeito ou elemento principal da imagem, descrito de forma clara "
            "e concisa. Deve ser a representação visual central da ideia do post."
        )
    )
    context_background: str = Field(
        ...,
        description=(
            "Descrição do cenário, ambiente ou fundo onde o sujeito está inserido. "
            "Deve complementar o sujeito e ajudar a contar a história."
        )
    )
    style: str = Field(
        ...,
        description=(
            "O estilo artístico da imagem. Ex: 'Photorealistic', 'Conceptual art', "
            "'Stylized 3D render', 'Clean vector illustration'."
        )
    )
    lighting: str = Field(
        ...,
        description=(
            "Descrição detalhada da iluminação da cena. Ex: 'Cinematic lighting', "
            "'Soft, diffuse light', 'Dramatic, high-contrast lighting'."
        )
    )
    camera_details: str = Field(
        ...,
        description=(
            "Detalhes da câmera, ângulo e composição. Ex: 'Macro view, shallow depth "
            "of field, object slightly off-center', 'Wide angle shot'."
        )
    )
    quality_modifiers: str = Field(
        ...,
        description=(
            "Modificadores que influenciam a qualidade e o detalhe da imagem final. "
            "Ex: '4K, high detail, trending on ArtStation, sophisticated'."
        )
    )


# 2. Fábrica de Contrato: Constrói a especificação completa da chamada ao LLM.
def get_contract(dossier: str, copy_title: str, copy_description: str) -> LLMContract:
    """
    Retorna o contrato (`LLMContract`) completo para gerar os componentes do prompt de imagem.

    Esta função recebe o contexto de negócio (dossiê e a copy já criada) e o
    traduz em uma requisição estruturada para o LLM.

    Args:
        dossier (str): O dossiê de pesquisa completo que serve como base
                       informativa.
        copy_title (str): O título do post, que captura o gancho principal.
        copy_description (str): A descrição (legenda) do post, que desenvolve a ideia.

    Returns:
        LLMContract: O objeto de contrato pronto para ser executado por um
                     `ContentGeneratorAdapter`.
    """
    prompt_template = """
# Missão
Você é um Diretor de Arte e Artista Visual especializado em traduzir conceitos complexos em prompts de imagem impactantes para modelos de IA generativa. Sua tarefa é criar os componentes de um prompt de imagem com base em um dossiê e na copy de um post.

# Contexto para Análise
A seguir estão as informações que você deve usar para extrair a essência visual da mensagem.

## Dossiê de Pesquisa (O "Quê"):
---
{dossier}
---

## Copy do Post (O "Como" e o "Porquê"):
- Título: "{copy_title}"
- Descrição: "{copy_description}"

# Tarefa Principal
Analise o Dossiê e a Copy para destilar a **ESSÊNCIA VISUAL** do post. Com base nessa essência, gere os componentes para o prompt da imagem de fundo. A imagem deve complementar o texto, não apenas repeti-lo.

## Diretrizes CRUCIAIS de Direção de Arte:
1.  **Foco na Essência:** A imagem deve ser uma **metáfora visual** ou representação conceitual da ideia principal. Evite ser literal demais. Pense "o que esta informação *parece* ou *se sente*?".
2.  **Previsão de Espaço para Texto:** O design deve, obrigatoriamente, prever espaço para texto ser sobreposto. Use técnicas como "negative space", "object slightly off-center", "shallow depth of field com bokeh background". A composição deve guiar o olho, mas deixar áreas mais limpas.
3.  **Coerência Tonal e Emocional:** O estilo, as cores e a iluminação devem ser consistentes com o tom da copy. Se a copy é sobre um avanço esperançoso, a imagem deve refletir isso. Se é sobre um alerta, o tom deve ser mais sóbrio.

# Formato de Saída (JSON Obrigatório)
Sua resposta DEVE ser um único objeto JSON válido, sem nenhum texto antes ou depois, seguindo o schema definido.
"""

    return LLMContract(
        prompt_name="image_prompt_components",
        prompt_version="1.0",
        prompt_template=prompt_template,
        output_schema=ImagePromptComponentsOutput,
        input_variables={
            "dossier": dossier,
            "copy_title": copy_title,
            "copy_description": copy_description
        }
    )
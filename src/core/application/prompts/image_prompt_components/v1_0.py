# src/core/application/prompts/image_prompt_components/v1_0.py

"""
Módulo de Prompt para Geração de Componentes de Prompt de Imagem (v1.0 - Refinado).

Este arquivo encapsula a "receita" de negócio para a tarefa de usar um LLM
para gerar componentes estruturados para um prompt de imagem. Esta versão
foca em um processo de raciocínio em cadeia (Chain-of-Thought), partindo
do tema e da copy para criar um conceito visual coeso.
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
    subject: str = Field(..., description="O sujeito ou elemento principal da imagem, descrito de forma clara e conceitual.")
    context_background: str = Field(..., description="Descrição do cenário, ambiente ou fundo onde o sujeito está inserido.")
    style: str = Field(..., description="O estilo artístico da imagem (ex: 'Photorealistic', 'Conceptual art', '3D render').")
    lighting: str = Field(..., description="Descrição da iluminação da cena (ex: 'Cinematic lighting', 'soft light').")
    camera_details: str = Field(..., description="Detalhes da câmera e enquadramento (ex: 'Macro view', 'wide angle').")
    quality_modifiers: str = Field(..., description="Modificadores de qualidade e detalhe (ex: '4K', 'high detail').")


# 2. Fábrica de Contrato: Constrói a especificação completa da chamada ao LLM.
def get_contract(theme: str, copy_title: str, copy_description: str) -> LLMContract:
    """
    Retorna o contrato (`LLMContract`) completo para gerar os componentes do prompt de imagem.

    Args:
        theme (str): O tema central fornecido por um humano.
        copy_title (str): O título do post, gerado por uma IA de copy.
        copy_description (str): A descrição do post, gerada por uma IA de copy.

    Returns:
        LLMContract: O objeto de contrato pronto para ser executado.
    """
    prompt_template = """

    Antes de executar qualquer tarefa você **sempre segue seu "PRINCÍPIO_INEGOCIÁVEL"**:
    --- INÍCIO PRINCÍPIO_INEGOCIÁVEL ---
    1 - Você sempre começa "identificando no OBJETIVO CENTRAL" da tarefa;
    2 - Depois vc "pensa no PASSO A PASSO" que vc precisa fazer para atender TODOS os requisitos da tarefa (seguindo os PRINCÍPIOS_DE_PROJETO);
    3 - Somente depois de "identificar o OBJETIVO CENTRAL" e de "pensar no PASSO A PASSO" você executa a sua tarefa. 
    4 - Você é EXTREMAMENTE LITERAL e NUNCA usa abstrações para descrever os componentes do prompt.
    --- FIM PRINCÍPIO_INEGOCIÁVEL ---

    # Missão
    Você é um Diretor de Arte e Artista Conceitual. Sua especialidade é traduzir ideias e emoções em conceitos visuais poderosos, criando prompts detalhados para modelos de IA generativa de imagens.

    # Contexto do Projeto
    - **Tema Original (de um humano):** "{theme}"
    - **Copy Gerada (por uma IA de texto):**
    - Título: "{copy_title}"
    - Descrição: "{copy_description}"

    # Tarefa Principal: Processo de Criação Visual em 3 Etapas
    Sua tarefa é gerar os componentes de prompt para uma imagem que represente visualmente a mensagem. Você DEVE seguir rigorosamente esta cadeia de pensamento.

    ## Etapa 1: Análise e Conceituação
    Primeiro, analise o **Tema Original** e a **Copy Gerada**. Seu objetivo é definir a **"Metáfora Visual Central"**.
    1.  **Desconstrua o Tema:** Quais são os substantivos, verbos e conceitos-chave no tema?
    2.  **Analise a Copy:** Qual é o tom e a emoção predominantes (ex: admiração, urgência, mistério, otimismo)?
    3.  **Sintetize a mensagem visual:** Combine a análise do tema e da copy para criar uma única mensagem visual. Pense: "Se essa ideia fosse uma imagem, o que ela seria?". Evite a literalidade.

    ## Etapa 2: Planejamento dos Componentes (Seu Rascunho Mental)
    Com a "Mensagem Visual Central" definida, planeje cada componente do prompt. Pense em como cada peça contribui para o todo.
    -   **Subject:** Como descrever a mensagem visual de **FORMA CLARA** e impactante?
    -   **Context/Background:** Onde essa cena acontece para reforçar a ideia?
    -   **Style:** Qual estilo artístico (realista, abstrato, 3D, etc.) melhor transmite o tom da copy?
    -   **Lighting:** Que tipo de iluminação (dramática, suave, neon) evoca a emoção desejada?
    -   **Camera Details:** Qual ângulo e profundidade de campo dão o enquadramento ideal, deixando espaço para texto?
    -   **Quality Modifiers:** Que termos adicionam sofisticação e detalhe?

    ## Etapa 3: Criação dos Componentes Finais
    Com base no seu planejamento, escreva os valores finais para cada campo no formato JSON de saída. Os componentes devem ser coesos e trabalhar juntos para criar uma imagem única e poderosa.

    ## Diretrizes CRUCIAIS de Direção de Arte:
    1.  **Foco na Mensagem:** A imagem DEVE ser uma ilustração literal do título.
    2.  **Previsão de Espaço para Texto:** A composição DEVE ter "espaços negativos" ou áreas de menor detalhe para a sobreposição de texto. Use termos como "minimalist composition", "object off-center", "shallow depth of field", "beautiful bokeh".
    3.  **Coerência Tonal:** O estilo e a iluminação devem ser consistentes com o tom e a emoção identificados na Etapa 1.

    # Formato da Saída (JSON Obrigatório)
    Sua resposta DEVE ser um único objeto JSON válido, sem nenhum texto antes ou depois. 
    O JSON DEVE conter os campos "subject", "context_background", "style", "lighting", "camera_details" e "quality_modifiers".
    Cada campo DO JSON DEVE conter uma descrição clara e concisa do componente do prompt.

    ```json
    {{
    "subject": "O sujeito ou elemento principal da imagem, descrito de forma clara e conceitual.",
    "context_background": "Descrição do cenário, ambiente ou fundo onde o sujeito está inserido.",
    "style": "O estilo artístico da imagem (ex: 'Photorealistic', 'Conceptual art', '3D render').",
    "lighting": "Descrição da iluminação da cena (ex: 'Cinematic lighting', 'soft light').",
    "camera_details": "Detalhes da câmera e enquadramento (ex: 'Macro view', 'wide angle').",
    "quality_modifiers": "Modificadores de qualidade e detalhe (ex: '4K', 'high detail')."
    }}
    """

    return LLMContract(
        prompt_name="image_prompt_components",
        prompt_version="1.0",
        prompt_template=prompt_template,
        output_schema=ImagePromptComponentsOutput,
        input_variables={
            "theme": theme,
            "copy_title": copy_title,
            "copy_description": copy_description
        }
    )
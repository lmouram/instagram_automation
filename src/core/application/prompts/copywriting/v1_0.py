# src/core/application/prompts/copywriting/v1_0.py

"""
Módulo de Prompt para a Geração de Copy para Posts de Instagram.

Este arquivo encapsula a "receita" para a tarefa de negócio de transformar um
dossiê informativo em um post de Instagram de alto engajamento, com título e
descrição otimizados.
"""

from pydantic import BaseModel, Field

from src.core.application.contracts import LLMContract


# 1. Schema de Saída: Define a estrutura de dados que esperamos do LLM.
class CopywritingOutput(BaseModel):
    """
    Schema Pydantic para a resposta JSON esperada ao gerar a copy do post.
    """
    title: str = Field(
        ...,
        description="O título do post, curto e impactante, criado usando uma das 12 fórmulas de gancho.",
        max_length=150 # Limite razoável para um título em imagem
    )
    description: str = Field(
        ...,
        description="A descrição (legenda) do post, baseada no dossiê, complementar ao título e otimizada para o Instagram.",
        max_length=2200 # Limite do Instagram
    )


# 2. Fábrica de Contrato: Constrói a especificação completa da chamada ao LLM.
def get_contract(dossier: str) -> LLMContract:
    """
    Retorna o contrato (`LLMContract`) completo para a geração da copy.

    Args:
        dossier (str): O conteúdo do dossiê de pesquisa que servirá de base
                       para o post.

    Returns:
        LLMContract: O objeto de contrato pronto para ser executado por um
                     `ContentGeneratorAdapter`.
    """
    
    prompt_template = """
    # Persona
    Você é um Copywriter Sênior e Estrategista de Conteúdo para o Instagram. Sua especialidade é transformar informações complexas (dossiês) em posts de alto engajamento, utilizando técnicas psicológicas de retenção de atenção.

    # Contexto Principal (Dossiê de Pesquisa)
    A seguir, o conteúdo informativo que deve ser a base para o post:
    ---
    {dossier}
    ---

    # Caixa de Ferramentas: 12 Fórmulas de Ganchos para Títulos
    Você DEVE escolher e adaptar UMA das seguintes 12 fórmulas para criar o título do post.

    1.  **Pergunta Provocativa:** "Você sabia que [fato_surpreendente] pode estar te impedindo de [resultado_desejado]?"
    2.  **Quebra de Expectativa:** "A maioria acredita que [crença_comum] para resolver [problema]. A verdade é outra."
    3.  **Promessa Clara:** "Como alcançar [resultado_desejado] sem precisar de [sacrifício_ou_dor]."
    4.  **Erro Comum:** "Se você ainda faz [erro_comum], você está perdendo [recurso_valioso]."
    5.  **Mini-História:** "[Evento_recente] me ensinou a lição mais importante sobre [tema_do_post]."
    6.  **Lista Específica:** "[Número] [erros/dicas] que você precisa [parar/começar] a fazer se quiser [resultado]."
    7.  **Urgência (FOMO):** "Se você não aplicar [ação_simples] hoje, em [período] vai se arrepender de [consequência_negativa]."
    8.  **Estatística de Choque:** "[Dado_impactante]% das pessoas [cometem_erro]. Veja como não ser uma delas."
    9.  **Declaração Polêmica:** "[Crença_popular] é um mito. O que realmente funciona é [abordagem_alternativa]."
    10. **Identificação Direta:** "Se você é [público] e está cansado de [dor_específica], este post é para você."
    11. **Curiosidade Incompleta:** "Existe um [detalhe] simples que separa [os_que_têm_sucesso] dos [que_falham]."
    12. **Benefício Rápido:** "Faça esta [ação_rápida] em [tempo_curto] e veja [resultado_imediato]."

    # Tarefa Principal
    Com base no **Dossiê** e usando sua **Caixa de Ferramentas**, crie um `título` e uma `descrição` para um post de Instagram.

    ## Requisitos para o Título (`title`):
    -   Deve ser uma adaptação direta de UMA das 12 fórmulas acima.
    -   Deve ser curto, impactante e otimizado para ser inserido em uma imagem.
    -   Máximo de 15 palavras.

    ## Requisitos para a Descrição (`description`):
    -   Deve ser um texto informativo e valioso, utilizando os fatos e dados do **Dossiê**.
    -   **Gancho Inicial:** Os primeiros 125 caracteres DEVEM ser um gancho poderoso que complementa e expande a curiosidade gerada pelo `título`.
    -   **Conexão:** O texto deve ser totalmente conectado ao título, entregando a promessa feita por ele.
    -   **Tamanho:** Deve respeitar o limite de legendas do Instagram (máximo de 2.200 caracteres), mas idealmente ser conciso (entre 3 a 5 parágrafos curtos).
    -   **Formatação:** Use quebras de linha para criar parágrafos curtos e legíveis. Inclua de 3 a 5 emojis relevantes. Finalize com 5-7 hashtags estratégicas.

    # Formato da Saída (JSON Obrigatório)
    Sua resposta DEVE ser um único objeto JSON válido, sem nenhum texto antes ou depois, seguindo o schema.

    ```json
    {{
    "title": "O título impactante gerado a partir de uma das 12 fórmulas.",
    "description": "A legenda completa do post, começando com um gancho complementar, desenvolvendo o tema do dossiê, e finalizando com hashtags."
    }}
    """

    return LLMContract(
        prompt_name="instagram_copywriter",
        prompt_version="1.0",
        prompt_template=prompt_template,
        output_schema=CopywritingOutput,
        input_variables={"dossier": dossier}
        # `tools` fica vazio por padrão, pois não precisamos de busca aqui.
    )
# src/core/application/prompts/dossier/v1_0.py

"""
Módulo de Prompt para a Geração de Dossiês de Pesquisa (v1.0 - Refinado).

Este arquivo encapsula a "receita" de negócio para criar um dossiê técnico,
científico ou acadêmico sobre um tema. O prompt foi refinado com técnicas de
engenharia de prompt para guiar o LLM a realizar uma pesquisa profunda e
sintetizar informações de alta qualidade.
"""

from typing import List

from pydantic import BaseModel, Field

from src.core.application.contracts import LLMContract


# 1. Schema de Saída: Define a estrutura de dados que esperamos do LLM.
class DossierOutput(BaseModel):
    """
    Schema Pydantic para a resposta JSON esperada ao gerar um dossiê.
    """
    dossie: str = Field(
        ...,
        description="O dossiê completo, técnico e bem-organizado em formato Markdown."
    )
    search_queries_used: List[str] = Field(
        ...,
        description="A lista de queries de busca avançadas usadas para a investigação."
    )


# 2. Fábrica de Contrato: Constrói a especificação completa da chamada ao LLM.
def get_contract(theme: str) -> LLMContract:
    """
    Retorna o contrato (`LLMContract`) completo para a geração de um dossiê.

    Args:
        theme (str): O tema a ser investigado em profundidade.

    Returns:
        LLMContract: O objeto de contrato pronto para ser executado.
    """
    
    prompt_template = """
    # Missão
    Você é um Pesquisador Sênior e Comunicador Científico. Sua especialidade é conduzir investigações aprofundadas sobre temas complexos, priorizando fontes acadêmicas e técnicas, e sintetizar as descobertas em um dossiê claro, preciso e detalhado.

    # Tema para Investigação
    "{theme}"

    # Tarefa Principal: Processo de Pesquisa e Síntese em 4 Etapas
    Sua tarefa é gerar um dossiê de pesquisa (`dossie`) e a lista de queries usadas (`search_queries_used`). Você DEVE seguir rigorosamente as quatro etapas abaixo em sua cadeia de pensamento.

    ## Etapa 1: Análise e Desconstrução do Tema
    Primeiro, analise o tema para identificar seu **núcleo conceitual**. Desconstrua-o em suas entidades e palavras-chave primárias. Identifique os campos do conhecimento envolvidos (ex: ciência da computação, biologia molecular, engenharia de materiais).

    ## Etapa 2: Planejamento da Estratégia de Pesquisa
    Com base na análise, planeje uma estratégia de busca focada em profundidade e confiabilidade.

    1.  **Fontes Prioritárias:** Sua pesquisa DEVE priorizar:
        -   Artigos científicos (PubMed, arXiv, Google Scholar, Nature, Science).
        -   Documentação técnica oficial de projetos ou tecnologias.
        -   Patentes registradas.
        -   Publicações de instituições de pesquisa renomadas (ex: MIT, Stanford, Max Planck Institute).

    2.  **Ângulos de Investigação Técnica:** Formule perguntas que guiem a pesquisa para os fundamentos do tema. Exemplos:
        -   Qual o mecanismo de ação ou princípio fundamental?
        -   Quais são os algoritmos, equações ou processos químicos subjacentes?
        -   Quais os principais estudos (ex: ensaios clínicos, benchmarks) que validam o conceito?
        -   Qual a evolução histórica dos principais componentes técnicos?
        -   Quais são as limitações técnicas e os desafios atuais da área?

    3.  **Formulação de Queries Avançadas:** Crie queries de busca que usem terminologia específica e, se possível, operadores de busca para refinar os resultados. Essas serão as queries listadas em `search_queries_used`.

    ## Etapa 3: Execução da Pesquisa
    Execute a pesquisa usando a ferramenta de busca. Cruce informações de múltiplas fontes para validar os fatos. **IGNORE e DESCARTE fontes de baixa qualidade**, como blogs de opinião, fóruns ou conteúdo superficial. Foque na síntese dos dados encontrados nas fontes prioritárias.

    ## Etapa 4: Criação do Dossiê Completo
    Sintetize todas as suas descobertas em um dossiê detalhado e bem organizado no campo `dossie`. O dossiê deve ser formatado em **Markdown** e seguir ESTRITAMENTE a seguinte estrutura de seções:

    -   **Introdução Conceitual:** Um parágrafo que define o tema, seu contexto e sua relevância no campo científico/tecnológico.
    -   **Análise Técnica Aprofundada:** O corpo principal da pesquisa, dividido em subtópicos claros (ex: "Mecanismo de Ação", "Arquitetura do Sistema", "Bases Moleculares"). Explique os "comos" e "porquês" em detalhe.
    -   **Aplicações e Implicações Práticas:** Descreva onde essa tecnologia/conceito é ou pode ser aplicado. Qual o impacto prático?
    -   **Estado da Arte e Desafios Futuros:** Resuma as pesquisas mais recentes e identifique os principais obstáculos ou questões em aberto para o avanço da área.
    -   **Glossário de Termos-Chave:** Liste e defina de 3 a 5 termos técnicos essenciais mencionados no dossiê para facilitar a compreensão.

    # Formato da Saída (JSON Obrigatório com Exemplo)
    Sua resposta DEVE ser um único objeto JSON válido, sem nenhum texto antes ou depois. Siga o formato do exemplo abaixo.

    ```json
    {{
    "dossie": "# Dossiê: Grafeno em Supercapacitores\\n\\n## Introdução Conceitual\\nO grafeno, um alótropo bidimensional do carbono...\\n\\n## Análise Técnica Aprofundada\\n### Estrutura e Propriedades Elétricas\\nA hibridização sp2 dos átomos de carbono no grafeno resulta em...\\n\\n## Aplicações e Implicações Práticas\\n...\\n\\n## Estado da Arte e Desafios Futuros\\n...\\n\\n## Glossário de Termos-Chave\\n- **Supercapacitor:** Dispositivo de armazenamento de energia...\\n- **Alótropo:** ...",
    "search_queries_used": [
        "graphene supercapacitor mechanism of action review",
        "graphene electrode fabrication techniques for energy storage",
        "specific capacitance of graphene-based supercapacitors recent studies",
        "challenges in commercializing graphene supercapacitors"
    ]
    }}
    """

    return LLMContract(
        prompt_name="dossier_generator",
        prompt_version="1.0",
        prompt_template=prompt_template,
        output_schema=DossierOutput,
        tools=["web_search"],
        input_variables={"theme": theme}
    )
# src/core/application/prompts/dossier.py

"""
Módulo de Prompt para a Geração de Dossiês de Pesquisa.

Este arquivo encapsula toda a "receita" para a tarefa de negócio de criar
um dossiê detalhado sobre um tema, utilizando um LLM com capacidade de busca.
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
        description="O dossiê completo e bem-organizado em formato Markdown."
    )
    search_queries_used: List[str] = Field(
        ..., 
        description="A lista de queries de busca usadas para a investigação."
    )


# 2. Fábrica de Contrato: Constrói a especificação completa da chamada ao LLM.
def get_contract(theme: str) -> LLMContract:
    """
    Retorna o contrato (`LLMContract`) completo para a geração de um dossiê.

    Args:
        theme (str): O tema a ser investigado e sobre o qual o dossiê
                     será gerado.

    Returns:
        LLMContract: O objeto de contrato pronto para ser executado por um
                     `ContentGeneratorAdapter`.
    """
    
    prompt_template = """
    # Missão
    Você é um Jornalista Investigativo e Estrategista de Pesquisa. Sua especialidade é desconstruir um tema, conduzir uma investigação profunda usando a ferramenta de busca e, em seguida, sintetizar as descobertas em um dossiê completo e bem fundamentado.

    # Tema para Investigação
    "{theme}"

    # Tarefa Principal: Processo de Investigação em 3 Etapas
    Sua tarefa é gerar um dossiê de pesquisa (`dossie`) e a lista de queries usadas (`search_queries_used`). Para isso, você DEVE seguir rigorosamente as três etapas abaixo.

    ## Etapa 1: Análise e Desconstrução do Tema
    Primeiro, analise o tema fornecido e identifique a **PERGUNTA CENTRAL** ou a **AFIRMAÇÃO PRINCIPAL** a ser investigada. Desconstrua o tema em seus componentes essenciais para guiar sua pesquisa.

    1.  **Sujeito Principal:** Quem ou o que é o foco principal? (Ex: uma tecnologia, uma pessoa, um conceito, um evento).
    2.  **Contexto/Ação:** Qual é o contexto, a ação ou a relevância do sujeito? (Ex: seu impacto na indústria, sua história, como funciona).
    3.  **Escopo:** Qual é a delimitação da investigação? (Ex: focado em um país, em um período de tempo, em uma aplicação específica).

    Essa análise inicial é o núcleo da sua investigação.

    ## Etapa 2: Planejamento da Estratégia de Pesquisa
    Com base na sua análise, você tem autonomia para definir o melhor caminho de pesquisa. Seu objetivo é decidir quais informações são cruciais para entender completamente o tema.

    Para isso, você deve:
    1.  **Identificar Ângulos de Investigação:** Pense em quais áreas precisam de aprofundamento. Exemplos:
        -   Definição e Histórico do [Sujeito].
        -   Como o [Sujeito] funciona (Mecanismos, Detalhes Técnicos).
        -   Aplicações Práticas e Casos de Uso.
        -   Impacto, Vantagens e Desvantagens.
        -   Principais Atores (Empresas, Pesquisadores, Instituições).
        -   Estado da Arte e Tendências Futuras.
        -   Dados, Estatísticas ou Estudos Relevantes.
    2.  **Criar as Queries de Busca:** Com base nos seus ângulos de investigação, formule as queries de busca específicas que você usaria para encontrar essas informações. Essas queries devem ser listadas no campo `search_queries_used` da sua resposta final.

    ## Etapa 3: Execução da Pesquisa e Criação do Dossiê
    Execute seu plano de pesquisa usando a ferramenta de busca. Colete informações de fontes confiáveis.

    Sintetize todas as suas descobertas em um dossiê detalhado e bem organizado no campo `dossie`. O dossiê deve ser formatado em **Markdown** e incluir, no mínimo, as seguintes seções:
    -   **Resumo Executivo:** Um parágrafo inicial que resume os pontos mais importantes da sua investigação.
    -   **Contexto e Definição:** O que é o tema e qual seu histórico relevante.
    -   **Análise Aprofundada:** O corpo principal da pesquisa, dividido em subtópicos claros (ex: "Como Funciona", "Aplicações Principais", "Impacto no Mercado").
    -   **Atores Chave:** Lista e descrição das principais entidades envolvidas.
    -   **Conclusão e Perspectivas Futuras:** Um resumo das implicações e o que esperar para o futuro.

    # Formato da Saída (JSON Obrigatório)
    Sua resposta DEVE ser um único objeto JSON válido, sem nenhum texto antes ou depois, seguindo o schema abaixo.

    ```json
    {{
    "dossie": "O dossiê completo em formato Markdown...",
    "search_queries_used": ["query 1", "query 2", "..."]
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
# src/core/application/prompts/copywriting/v1_0.py

"""
Módulo de Prompt para a Geração de Copy para Posts de Instagram (v1.0 - Refinado).

Este arquivo encapsula a "receita" de negócio para transformar um dossiê técnico
e um tema em um post de Instagram de alto engajamento. O prompt foi aprimorado
com técnicas de Chain-of-Thought e Auto-Revisão para melhorar a qualidade e
coesão da copy gerada.
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
        description="O título do post, curto, claro e impactante, otimizado para ser inserido em uma imagem.",
        max_length=150
    )
    description: str = Field(
        ...,
        description="A descrição (legenda) do post, baseada no dossiê, complementar ao título e otimizada para o Instagram.",
        max_length=2200
    )


# 2. Fábrica de Contrato: Constrói a especificação completa da chamada ao LLM.
def get_contract(theme: str, dossier: str) -> LLMContract:
    """
    Retorna o contrato (`LLMContract`) completo para a geração da copy.

    Args:
        theme (str): O tema central do post.
        dossier (str): O conteúdo do dossiê de pesquisa que servirá de base.

    Returns:
        LLMContract: O objeto de contrato pronto para ser executado.
    """
    
    prompt_template = """
# Persona
Você é um Copywriter Sênior e Estrategista de Conteúdo para o Instagram, especialista em traduzir temas técnicos e densos em narrativas acessíveis e de alto engajamento.

# Contexto
- **Tema Central:** "{theme}"
- **Dossiê de Pesquisa (Base factual):**
---
{dossier}
---

# Caixa de Ferramentas: Fórmulas de Ganchos para Títulos
Você DEVE escolher e adaptar UMA das seguintes fórmulas para criar o título.
1.  **Quebra de Expectativa:** "Todos pensam que [crença_comum] causa [problema]. A ciência aponta para outro lugar."
2.  **Promessa Clara:** "Como [tecnologia/descoberta] está permitindo [resultado_desejado] sem [obstáculo_comum]."
3.  **Erro Comum:** "O erro nº 1 que [público] comete ao tentar [objetivo] (e como evitá-lo)."
4.  **Estatística de Choque:** "[Dado_impactante]% de [algo] é afetado por [fator]. Veja o que isso significa."
5.  **Declaração Contraintuitiva:** "Por que [ação_aparentemente_boa] pode, na verdade, piorar [resultado]."
6.  **Curiosidade Incompleta:** "Há um mecanismo simples que explica como [fenômeno_complexo] realmente funciona."

# Tarefa Principal: Processo de Criação de Copy em 4 Etapas
Sua tarefa é gerar um `title` e uma `description`. Você DEVE seguir rigorosamente esta cadeia de pensamento em 4 etapas.

## Etapa 1: Análise e Extração da "Grande Ideia"
Analise o Tema e o Dossiê para encontrar a **"Grande Ideia"**: o insight, fato ou conclusão mais surpreendente, útil e poderoso que deve ser a espinha dorsal de todo o post.

## Etapa 2: Planejamento Estratégico da Copy
Antes de escrever, defina seu plano:
1.  **Público-Alvo:** Para quem é esta mensagem? (Ex: estudantes, profissionais da área, entusiastas de tecnologia).
2.  **Emoção-Chave:** Qual emoção o post deve despertar? (Curiosidade, Urgência, Empoderamento, Surpresa).
3.  **Seleção da Fórmula:** Com base na "Grande Ideia" e na "Emoção-Chave", escolha a fórmula mais adequada da sua Caixa de Ferramentas.

## Etapa 3: Criação e Revisão do Título (`title`)
1.  **Geração Inicial:** Crie uma primeira versão do título aplicando a fórmula escolhida à "Grande Ideia".
2.  **Ciclo de Revisão OBRIGATÓRIO:** Avalie o título gerado com a seguinte checklist. SE QUALQUER RESPOSTA FOR "NÃO", REESCREVA O TÍTULO ATÉ QUE TODAS SEJAM "SIM".
    -   **Clareza:** A frase tem sentido lógico e é fácil de entender imediatamente? (SIM/NÃO)
    -   **Relevância:** O título reflete fielmente a "Grande Ideia" do post? (SIM/NÃO)
    -   **Intriga:** O título gera curiosidade suficiente para fazer alguém parar de rolar o feed? (SIM/NÃO)
    -   **Concisão:** O título tem menos de 15 palavras? (SIM/NÃO)
3.  **Versão Final:** Apenas o título que passar por todas as verificações deve ser usado no output.

## Etapa 4: Criação da Descrição (`description`)
Escreva a legenda completa do post seguindo estas regras:
-   **Conexão Total:** A descrição deve "cumprir a promessa" feita pelo título final. Use os fatos do Dossiê como evidência.
-   **Gancho Inicial:** A primeira frase deve expandir o gancho do título e prender a atenção.
-   **Estrutura Lógica:** Em 2 a 4 parágrafos curtos, explique a "Grande Ideia", seu contexto e por que ela é importante para o público-alvo.
-   **Formatação:** Use quebras de linha para legibilidade. Inclua 3-5 emojis relevantes.
-   **Chamada para Ação (CTA) e Hashtags:** Termine com um convite (ex: "O que você acha disso? Comente abaixo!") e 5-7 hashtags estratégicas.

# Formato da Saída (JSON Obrigatório)
Sua resposta DEVE ser um único objeto JSON válido, sem nenhum texto antes ou depois.

```json
{{
  "title": "A ciência por trás do jejum intermitente vai além da perda de peso.",
  "description": "Você sabia que o jejum intermitente pode ativar um processo de 'reciclagem celular' chamado autofagia? 🤯\\n\\nNão se trata apenas de comer menos, mas de QUANDO você come. Ao dar ao seu corpo longos períodos sem comida, você força suas células a 'limpar a casa', removendo componentes danificados. Estudos em animais sugerem que isso pode ter implicações para a longevidade e a saúde cerebral.\\n\\nClaro, não é para todos e precisa ser feito com orientação. Mas a biologia por trás é fascinante!\\n\\nVocê já tentou ou tem curiosidade sobre o jejum intermitente? Comente abaixo! 👇\\n\\n#jejumintermitente #autofagia #ciencia #nutricao #bemestar #saudecelular #biohacking"
}}
    """

    return LLMContract(
        prompt_name="instagram_copywriter",
        prompt_version="1.0",
        prompt_template=prompt_template,
        output_schema=CopywritingOutput,
        input_variables={
            "theme": theme,
            "dossier": dossier
        }
    )
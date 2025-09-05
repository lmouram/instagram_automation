# src/ports/content_generator.py

"""
Módulo da Porta do Gerador de Conteúdo.

Este arquivo define a porta (interface abstrata) para a funcionalidade de
geração de conteúdo por um Large Language Model (LLM). O propósito desta
porta é desacoplar o núcleo da aplicação (core) dos detalhes de implementação
de qualquer provedor de IA específico (Gemini, OpenAI, etc.).

Ela opera com base em um `LLMContract`, uma estrutura de dados que descreve
completamente a tarefa a ser executada pelo LLM.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

# Importa o contrato que define a "linguagem" desta porta
from src.core.application.contracts import LLMContract


class ContentGeneratorPort(ABC):
    """
    Interface abstrata (Porta) para um serviço genérico de geração de conteúdo.

    Define um contrato único e flexível para executar tarefas em um LLM.
    Os casos de uso constroem um `LLMContract` especificando *o que* eles
    querem, e o adaptador que implementa esta porta lida com *como* executar
    essa requisição.
    """

    @abstractmethod
    async def generate(self, contract: LLMContract) -> Dict[str, Any]:
        """
        Executa uma chamada genérica a um LLM com base em um contrato.

        A implementação concreta deste método é responsável por:
        1. Renderizar o template do prompt com as variáveis do contrato.
        2. Traduzir as capacidades genéricas (ex: 'web_search') para as
           ferramentas específicas do provedor de IA.
        3. Fazer a chamada à API.
        4. Se o contrato esperar um JSON, parsear e validar a resposta
           contra o `output_schema` fornecido.
        5. Retornar a resposta estruturada como um dicionário.

        Args:
            contract (LLMContract): A especificação completa da tarefa a ser
                                    executada pelo LLM.

        Returns:
            Dict[str, Any]: Um dicionário representando a resposta estruturada
                            e validada do LLM.

        Raises:
            - Exceções de API (ex: APIError): Para falhas na comunicação com
              o serviço externo.
            - Exceções de Parsing (ex: ParsingError): Se a resposta do LLM
              não puder ser parseada para o formato esperado (ex: JSON inválido).
            - Exceções de Validação (ex: ValidationError): Se a resposta
              parseada não corresponder ao `output_schema` do contrato.
        """
        raise NotImplementedError
# src/ports/theme_loader.py

"""
Módulo da Porta do Carregador de Temas.

Este arquivo define a porta (interface abstrata) para a funcionalidade de
carregamento de configurações de temas visuais. O propósito desta porta é
desacoplar o núcleo da aplicação (core) dos detalhes de implementação de
como os temas são armazenados e lidos (ex: de arquivos JSON, de um banco de
dados, de uma API de configuração).

Qualquer adaptador que forneça uma configuração de tema para a aplicação deve
implementar esta interface.
"""

from abc import ABC, abstractmethod

from src.core.application.contracts import ThemeContract


class ThemeLoaderPort(ABC):
    """
    Interface abstrata (Porta) para um serviço de carregamento de temas.

    Define o contrato que os adaptadores de carregamento de temas devem seguir.
    O `core` da aplicação dependerá desta abstração para obter as configurações
    visuais necessárias para renderizar os posts, sem conhecer a fonte de dados
    subjacente.
    """

    @abstractmethod
    def load(self, theme_name: str) -> ThemeContract:
        """

        Carrega a configuração completa de um tema especificado pelo nome.

        A implementação concreta deste método é responsável por localizar a
        configuração do tema (seja em um arquivo, banco de dados, etc.),
        validá-la e construir um objeto `ThemeContract` imutável que pode ser
        usado com segurança pelo restante da aplicação.

        Args:
            theme_name (str): O identificador único do tema a ser carregado
                              (ex: "default", "perfil_medicina_v2").

        Returns:
            ThemeContract: Um DTO contendo todos os caminhos de ativos e
                           parâmetros de configuração para o tema solicitado.

        Raises:
            ThemeNotFoundError: (Recomendado) Se a implementação não conseguir
                                encontrar um tema com o nome fornecido.
            ThemeInvalidError: (Recomendado) Se a configuração do tema
                               encontrada for inválida ou malformada.
        """
        raise NotImplementedError
# src/adapters/ui/__init__.py

"""
Pacote de Adaptadores de Interface de Usuário (UI).

Este pacote é designado para abrigar os "Driving Adapters" (Adaptadores de
Condução) da nossa Arquitetura Hexagonal que são relacionados à interação
com o usuário.

O código contido aqui é responsável por:
1.  Apresentar dados ao usuário.
2.  Coletar inputs do usuário.
3.  Invocar os casos de uso do `core/application` para executar a lógica de negócio.

Exemplos de módulos que podem residir neste pacote:
- Componentes reutilizáveis para a interface Streamlit.
- Helpers de formulário.
- Potencialmente, uma implementação completa de uma API (ex: com Flask ou FastAPI)
  se a aplicação evoluir para ter uma interface programática além da visual.

Este pacote é a "face" da aplicação para o mundo exterior humano, orquestrando
a interação sem conter nenhuma regra de negócio, que permanece isolada no core.
"""

# Este arquivo está intencionalmente quase vazio. Sua presença transforma o
# diretório 'ui' em um pacote Python. Módulos e subpacotes serão adicionados
# aqui conforme a interface do usuário se torna mais complexa.
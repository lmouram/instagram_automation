# scripts/__init__.py

"""
Pacote de Scripts Executáveis.

Este pacote contém scripts autônomos que atuam como "Driving Adapters" para
a aplicação. Eles são pontos de entrada para processos não-interativos, como
tarefas agendadas (cron jobs) ou operações de linha de comando.

Cada script aqui é tipicamente um "Composition Root", responsável por
inicializar as dependências e invocar um ou mais casos de uso do core.
"""
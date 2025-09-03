# streamlit_app.py

"""
Interface de Usuário (UI) da Aplicação - Driving Adapter.

Este script é o ponto de entrada principal para a interação humana com o sistema.
Ele utiliza a biblioteca Streamlit para criar uma interface web simples e funcional.

Responsabilidades deste módulo (como um Driving Adapter):
1.  **Composition Root:** Inicializa todas as dependências concretas (adaptadores)
    e as injeta nos casos de uso.
2.  **Interação com o Usuário:** Apresenta dados e coleta inputs do usuário.
3.  **Orquestração de Casos de Uso:** Invoca as funções de caso de uso do `core`
    para executar a lógica de negócio, sem conter nenhuma regra de negócio própria.
4.  **Feedback ao Usuário:** Exibe mensagens de sucesso, erro e status.
"""

import logging
from datetime import datetime, time, date

import streamlit as st
from supabase import create_client, Client

# Importações do nosso projeto
from src import config, logger
# Casos de Uso (a serem criados ou já existentes)
from src.core.application import (
    approve_post_use_case,
    create_post_use_case,
    publish_post_immediately_use_case
)
from src.core.application.exceptions import UseCaseError
from src.core.domain import PostStatus
# Adaptadores Concretos
from src.adapters.llm.gemini_adapter import GeminiAdapter
from src.adapters.media.google_image_adapter import GoogleImageAdapter
from src.adapters.observability.logging_adapter import LoggingObservabilityAdapter
from src.adapters.persistence.supabase_adapter import SupabaseAdapter
from src.adapters.social.instagram_adapter import InstagramAdapter
from src.adapters.storage.supabase_storage_adapter import SupabaseStorageAdapter

# --- INICIALIZAÇÃO E INJEÇÃO DE DEPENDÊNCIA ---

# Inicializa o logger global para que ele capture logs de todas as partes da app.
app_logger = logger.get_logger(__name__)

@st.cache_resource
def initialize_dependencies():
    """
    Inicializa e retorna todas as dependências concretas (clientes e adaptadores).
    Utiliza o cache do Streamlit para garantir que as conexões sejam criadas apenas uma vez.

    Returns:
        Dict[str, Any]: Um dicionário contendo as instâncias dos adaptadores.
    """
    app_logger.info("Inicializando todas as dependências da aplicação...")
    
    # --- Clientes de API ---
    supabase_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
    # --- Adaptadores ---
    # Observabilidade (usa o logger já configurado)
    observability_adapter = LoggingObservabilityAdapter(logger.get_logger("ObservabilityAdapter"))
    
    # Persistência e Storage
    persistence_adapter = SupabaseAdapter(supabase_client)
    storage_adapter = SupabaseStorageAdapter(supabase_client, config.SUPABASE_STORAGE_BUCKET)
    
    # Geração de Conteúdo
    content_generator_adapter = GeminiAdapter(api_key=config.GEMINI_API_KEY)
    media_generator_adapter = GoogleImageAdapter(api_key=config.GEMINI_API_KEY)

    # Publicação
    social_publisher_adapter = InstagramAdapter(
        account_id=config.INSTAGRAM_ACCOUNT_ID,
        access_token=config.META_ACCESS_TOKEN
    )

    # Agrupa todas as dependências em um dicionário para fácil acesso
    return {
        "observability": observability_adapter,
        "persistence": persistence_adapter,
        "storage": storage_adapter,
        "content_generator": content_generator_adapter,
        "media_generator": media_generator_adapter,
        "social_publisher": social_publisher_adapter,
    }

# Executa a inicialização e armazena as dependências
try:
    deps = initialize_dependencies()
except Exception as e:
    st.error(f"Erro crítico na inicialização das dependências: {e}")
    app_logger.critical("Falha ao inicializar dependências.", exc_info=True)
    st.stop()


# --- CONFIGURAÇÃO DA PÁGINA ---

st.set_page_config(
    page_title="Gerenciador de Conteúdo IA",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Gerenciador de Conteúdo para Instagram")


# --- BARRA LATERAL (AÇÕES DE CRIAÇÃO) ---

with st.sidebar:
    st.header("Criar Conteúdo")
    
    with st.form("create_post_form", border=False):
        theme = st.text_input("Tema do Post", placeholder="Ex: A importância da hidratação")
        submit_create = st.form_submit_button("Gerar Post para Aprovação", use_container_width=True)

    if submit_create and theme:
        with st.spinner("Gerando texto e imagem com IA... Por favor, aguarde."):
            try:
                create_post_use_case(
                    theme=theme,
                    content_generator=deps["content_generator"],
                    media_generator=deps["media_generator"],
                    storage=deps["storage"],
                    post_repository=deps["persistence"],
                    observability=deps["observability"],
                )
                st.success("Post gerado com sucesso! Ele está na fila de aprovação.")
                # st.rerun() não é necessário aqui pois o estado será recarregado na próxima interação
            except UseCaseError as e:
                st.error(f"Erro ao gerar o post: {e}")
                app_logger.error(f"Falha no caso de uso de criação de post para o tema '{theme}'", exc_info=True)


# --- ÁREA PRINCIPAL (FILA DE APROVAÇÃO) ---

st.header("Fila de Aprovação")

try:
    # A UI chama o repositório para listar os posts. Em um caso de uso mais complexo,
    # isso seria encapsulado em um `list_posts_use_case`. Por simplicidade,
    # a chamada direta é aceitável para uma operação de leitura simples.
    pending_posts = deps["persistence"].find_by_status(PostStatus.PENDING_APPROVAL)
    
    if not pending_posts:
        st.info("Não há posts aguardando aprovação no momento.")
    else:
        for post in pending_posts:
            with st.container(border=True):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.subheader(f"Tema: {post.theme}")
                    st.text_area("Texto Gerado", value=post.text_content, height=300, disabled=True)
                
                with col2:
                    if post.media and post.media[0].url:
                        st.image(post.media[0].url, caption="Mídia Gerada")
                
                # Ações de Aprovação / Rejeição
                st.markdown("---")
                action_cols = st.columns(6)
                
                # Botão de Aprovação
                if action_cols[0].button("✅ Aprovar", key=f"approve_{post.id}", use_container_width=True):
                    # Usamos o session_state para marcar qual post está em processo de aprovação
                    st.session_state.approving_post_id = post.id
                
                # Botão de Rejeição (Lógica a ser implementada com um `reject_post_use_case`)
                if action_cols[1].button("❌ Rejeitar", key=f"reject_{post.id}", use_container_width=True, type="secondary"):
                    st.warning("Funcionalidade de rejeição ainda não implementada.")
                    # Aqui chamaria o `reject_post_use_case`

    # Lógica de Agendamento (aparece quando um post é selecionado para aprovação)
    if "approving_post_id" in st.session_state and st.session_state.approving_post_id:
        post_id_to_approve = st.session_state.approving_post_id
        
        with st.form(f"schedule_form_{post_id_to_approve}"):
            st.subheader(f"Agendar Publicação do Post ID: ...{str(post_id_to_approve)[-6:]}")
            
            # Inputs para data e hora do agendamento
            today = date.today()
            now = datetime.now().time()
            col_date, col_time = st.columns(2)
            schedule_date = col_date.date_input("Data da Publicação", value=today, min_value=today)
            schedule_time = col_time.time_input("Hora da Publicação", value=now)
            
            # Botão de confirmação
            confirm_approval = st.form_submit_button("Confirmar e Agendar", type="primary")

            if confirm_approval:
                scheduled_at = datetime.combine(schedule_date, schedule_time)
                with st.spinner("Aprovando e agendando o post..."):
                    try:
                        approve_post_use_case(
                            post_id=post_id_to_approve,
                            scheduled_at=scheduled_at,
                            responsible="user:streamlit_app", # Identificador do aprovador
                            post_repository=deps["persistence"],
                            audit_repository=deps["persistence"],
                            observability=deps["observability"],
                        )
                        st.success(f"Post aprovado e agendado com sucesso para {scheduled_at.strftime('%d/%m/%Y às %H:%M')}!")
                        # Limpa o estado para fechar o formulário de agendamento e força o recarregamento
                        del st.session_state.approving_post_id
                        st.rerun()

                    except UseCaseError as e:
                        st.error(f"Erro ao aprovar o post: {e}")
                        app_logger.error(f"Falha no caso de uso de aprovação para o post ID '{post_id_to_approve}'", exc_info=True)


except Exception as e:
    st.error("Ocorreu um erro inesperado ao carregar a fila de aprovação.")
    app_logger.error("Falha ao carregar a fila de aprovação na UI.", exc_info=True)
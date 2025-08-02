import streamlit as st
from database import listar_vagas_por_usuario, deletar_vaga

import os

# Configuração da página
st.set_page_config(
    page_title="Gerenciar Vagas",
    page_icon="✂️",
    layout="wide"
)

# CSS para remover botões padrão
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Menu Lateral
with st.sidebar:
    st.title("📋 Menu")
    st.markdown("---")
    st.page_link("pages/1_home.py", label="🏠 Página Inicial", use_container_width=True)
    st.page_link("pages/2_cadastrar_vaga.py", label="➕ Cadastrar Vaga", use_container_width=True)
    st.page_link("pages/3_gerenciar_vagas.py", label="✂️ Gerenciar Vagas", use_container_width=True)
    st.page_link("pages/4_enviar_curriculos.py", label="📤 Enviar Currículo", use_container_width=True)
    st.page_link("pages/5_gerenciar_curriculos.py", label="✂️ Gerenciar Currículos", use_container_width=True)
    st.page_link("pages/6_analises_ia.py", label="🧠 Análises com IA", use_container_width=True)
    st.markdown("---")
    if st.session_state.get('authentication_status'):
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.clear()
            st.switch_page("0_login.py")
    st.caption("Versão 1.0 | © 2025")

st.logo(image = "imagens/BeAI.svg", icon_image = "imagens/captal_lambda_branco.png")

###################################################################

# Título da página
st.title("✂️ Gerenciar Vagas Cadastradas")

# Verifica se o usuário está logado
if not st.session_state.get('authentication_status'):
    st.switch_page("0_login.py")

# Lista as vagas do usuário logado
vagas = listar_vagas_por_usuario(st.session_state.get('user_id'))

if not vagas:
    st.warning("Ainda não há vagas cadastradas!")
else:
    # Mostra as vagas em uma tabela interativa
    for vaga in vagas:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### {vaga[1]}")  # Nome da vaga
                st.markdown("**Empresa:**")
                st.caption(vaga[2])

                st.markdown("**Cadastrada em:**")
                st.caption(vaga[6])

                st.markdown("**Atividades:**")
                st.caption(vaga[3])

                st.markdown("**Requisitos:**")
                st.caption(vaga[4])

                st.markdown("**Diferenciais:**")
                st.caption(vaga[5])

            with col2:
                # st.markdown("### Ações")
                if st.button("🗑️ Excluir", key=f"del_{vaga[0]}", use_container_width=True):
                    deletar_vaga(vaga[0])
                    st.success(f"Vaga {vaga[1]} excluída com sucesso!")
                    st.rerun()
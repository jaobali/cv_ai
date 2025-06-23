import streamlit as st
from PIL import Image
from database import contar_vagas_ativas_por_usuario, contar_curriculos_por_usuario

# Configuração da página
st.set_page_config(
    page_title="Analisador de Currículos IA",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="auto"
)


# INJEÇÃO DE CSS PARA REMOVER OS BOTÕES PADRÃO
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)


# --- MENU LATERAL ---
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

st.logo(image = "imagens/captal_lambda_branco.png", icon_image = "imagens/captal_lambda_branco.png")

#########################################################


cols = st.columns([1,2,1])
with cols[1]:
    st.image(image = "imagens/BeAI.svg", use_container_width=True)

st.markdown("")

# Card de boas-vindas
with st.container(border=True):
    st.markdown("""
    <div style='text-align: center;'>
        <h1 style='color: #467db1;'>Bem-vindo ao Analisador de Currículos com IA</h1>
        <p style='font-size: 16px; color: #acacac;'>
            Transforme seu processo de recrutamento com nossa análise inteligente de currículos
        </p>
    </div>
    """, unsafe_allow_html=True)

# Get user ID from session state
user_id = st.session_state.get('user_id')

if user_id:
    # Get real counts from database
    vagas_count = contar_vagas_ativas_por_usuario(user_id)
    curriculos_count = contar_curriculos_por_usuario(user_id)

    # Custom CSS for the stats cards
    st.markdown("""
    <style>
    .stats-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .stats-card:hover {
        transform: translateY(-5px);
    }
    .stats-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #56aa8a;
        margin: 10px 0;
    }
    .stats-label {
        font-size: 1.1rem;
        color: #CFCFCF;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create two columns for the stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{vagas_count}</div>
            <div class="stats-label">Vagas Ativas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{curriculos_count}</div>
            <div class="stats-label">Currículos</div>
        </div>
        """, unsafe_allow_html=True)

    # Add a small gap
    st.markdown("<br>", unsafe_allow_html=True)

import streamlit as st
from database import (
    verificar_usuario,
    alterar_senha_usuario,
    salvar_sessao_usuario,
    carregar_sessao_usuario,
    limpar_sessao_usuario
)
import time
import json
# import extra_streamlit_components as stx  # Comentado pois não está funcionando

import os
import socket

# Função para obter IP do usuário
def get_user_ip():
    """Obtém um identificador único para o dispositivo do usuário"""
    # Estratégia 1: Tenta obter IP via Streamlit Cloud
    if hasattr(st, 'query_params'):
        try:
            params = st.query_params
            if hasattr(params, 'get') and params.get("_stcore"):
                return f"streamlit_{params['_stcore'][0]}"
        except:
            pass
    
    # Estratégia 2: Para desenvolvimento local, usa informações específicas
    import socket
    import time
    import os
    
    # Obtém informações do sistema de forma mais robusta
    try:
        hostname = socket.gethostname()
        if not hostname or hostname == "localhost":
            hostname = "DESKTOP-LOCAL"
    except Exception as e:
        print(f"Erro ao obter hostname: {e}")
        hostname = "DESKTOP-LOCAL"
    
    try:
        username = os.getenv('USERNAME', os.getenv('USER', 'unknown'))
        if not username or username == "unknown":
            username = "Usuario"
    except Exception as e:
        print(f"Erro ao obter username: {e}")
        username = "Usuario"
    
    timestamp = int(time.time() / 300)  # Muda a cada 5 minutos
    
    # Cria identificador único baseado no ambiente
    device_id = f"local_{hostname}_{username}_{timestamp}"
    print(f"Gerado device_id: {device_id}")
    return device_id

# Função para debug - mostra qual estratégia está sendo usada
def debug_user_ip():
    """Função para debug - mostra como o IP está sendo gerado"""
    # Testa cada estratégia
    if hasattr(st, 'query_params'):
        try:
            params = st.query_params
            if hasattr(params, 'get') and params.get("_stcore"):
                return f"streamlit_{params['_stcore'][0]}", "Streamlit Cloud"
        except:
            pass
    
    # Para desenvolvimento local
    import socket
    import time
    import os
    
    try:
        hostname = socket.gethostname()
        if not hostname or hostname == "localhost":
            hostname = "DESKTOP-LOCAL"
    except Exception as e:
        print(f"Erro ao obter hostname no debug: {e}")
        hostname = "DESKTOP-LOCAL"
    
    try:
        username = os.getenv('USERNAME', os.getenv('USER', 'Usuario'))
        if not username or username == "unknown":
            username = "Usuario"
    except Exception as e:
        print(f"Erro ao obter username no debug: {e}")
        username = "Usuario"
    
    timestamp = int(time.time() / 300)
    
    device_id = f"local_{hostname}_{username}_{timestamp}"
    print(f"Debug - Gerado device_id: {device_id}")
    return device_id, "Local Environment"

# Função para salvar dados do usuário no banco de dados
def save_user_session(user_data):
    try:
        user_ip = get_user_ip()
        salvar_sessao_usuario(user_data, user_ip)
        # st.success(f"Dados salvos para usuário: {user_data['username']}")
    except Exception as e:
        st.error(f"Erro ao salvar dados: {str(e)}")

# Função para verificar e carregar dados salvos
def load_user_session():
    try:
        user_ip = get_user_ip()
        data = carregar_sessao_usuario(user_ip)
        if data:
            # st.info(f"Dados encontrados para usuário: {data['username']}")
            return data
        else:
            # st.info("Nenhum dado salvo encontrado")
            pass
    except Exception as e:
        st.error(f"Erro ao carregar dados salvos: {str(e)}")
    return None

# Configuração da página
st.set_page_config(
    page_title="Login and Register",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)


st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    .small-font { font-size: 0.9rem !important; }
    
    /* Estilos personalizados para o botão */
    div[data-testid="stButton"] > button {
        width: 50%;
        height: 3.5rem;
        font-size: 1.2rem;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background-color: #56aa8a;
        color: #1E1E1E;
        border: none;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stButton"] > button:hover {
        background-color: #56aa8a;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    div[data-testid="stButton"] > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Inicializa o estado da sessão
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# Verifica se há dados salvos
if not st.session_state['authentication_status']:
    saved_data = load_user_session()
    if saved_data and saved_data.get('username'):
        st.session_state['authentication_status'] = True
        st.session_state['username'] = saved_data['username']
        st.session_state['role'] = saved_data['role']
        st.session_state['user_id'] = saved_data['user_id']

if st.session_state['authentication_status']:
    st.title(f"Bem-vindo, {st.session_state['username']}!")
    st.write(f"Nivel de acesso: {st.session_state['role']}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.page_link("pages/1_home.py", label="➡️ Ir para a Página Inicial")
    with col4:
        if st.button("Logout"):
            # Remove os dados salvos ao fazer logout
            user_ip = get_user_ip()
            limpar_sessao_usuario(st.session_state.get('user_id'), user_ip)
            st.session_state['authentication_status'] = None
            st.session_state['username'] = None
            st.session_state['role'] = None
            st.session_state['user_id'] = None
            st.rerun()
else:
    tab1, tab2 = st.tabs(["Login", "Alterar Senha"])

    with tab1:
        st.title("Login")
        # Carrega dados salvos para usar como valor padrão
        saved_data = load_user_session()
        default_username = saved_data.get('username', "") if saved_data else ""
        
        username = st.text_input("Usuário", value=default_username)
        password = st.text_input("Senha", type="password")
        remember_me = st.checkbox("Lembrar-me por 7 dias")
        
        # Usando um container para o botão para melhor controle
        login_container = st.container()
        with login_container:
            if st.button("Entrar", use_container_width=True):
                user = verificar_usuario(username, password)
                if user:
                    st.session_state['authentication_status'] = True
                    st.session_state['username'] = user['username']
                    st.session_state['role'] = user['role']
                    st.session_state['user_id'] = user['id']
                    
                    # Se "Lembrar-me" estiver marcado, salva os dados
                    if remember_me:
                        save_user_session(user)
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")

    with tab2:
        with st.form("password_form", enter_to_submit=False):
            st.title("Alterar Senha")
            # Carrega dados salvos para usar como valor padrão

            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            new_password = st.text_input("Nova senha", type="password")
            if st.form_submit_button("Alterar Senha"):
                if alterar_senha_usuario(email, new_password):
                    st.success("Senha alterada com sucesso!")
                else:
                    st.error("Erro ao alterar senha")

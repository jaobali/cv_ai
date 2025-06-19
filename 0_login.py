import streamlit as st
from database import (
    verificar_usuario,
    criar_usuario
)
import time
import json
from datetime import datetime, timedelta
import extra_streamlit_components as stx

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

# Inicializa o gerenciador de cookies
cookie_manager = stx.CookieManager()

# Função para salvar dados do usuário em cookie
def save_user_cookie(user_data):
    cookie_data = {
        'user_id': user_data['id'],
        'username': user_data['username'],
        'role': user_data['role'],
        'expires': (datetime.now() + timedelta(days=7)).isoformat()
    }
    cookie_manager.set('user_data', json.dumps(cookie_data), expires_at=datetime.now() + timedelta(days=7))

# Função para verificar e carregar dados do cookie
def load_user_cookie():
    try:
        cookie_data = cookie_manager.get('user_data')
        if cookie_data:
            data = json.loads(cookie_data)
            expires = datetime.fromisoformat(data['expires'])
            if datetime.now() < expires:
                return data
    except:
        pass
    return None

# Inicializa o estado da sessão
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# Verifica se há dados salvos no cookie
if not st.session_state['authentication_status']:
    cookie_data = load_user_cookie()
    if cookie_data:
        st.session_state['authentication_status'] = True
        st.session_state['username'] = cookie_data['username']
        st.session_state['role'] = cookie_data['role']
        st.session_state['user_id'] = cookie_data['user_id']

st.write(st.secrets["DB_HOST"])

if st.session_state['authentication_status']:
    st.title(f"Bem-vindo, {st.session_state['username']}!")
    st.write(f"Nivel de acesso: {st.session_state['role']}")
    st.write('---')

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.page_link("pages/1_home.py", label="➡️ Ir para a Página Inicial")
    with col4:
        if st.button("Logout"):
            st.session_state['authentication_status'] = None
            st.session_state['username'] = None
            st.session_state['role'] = None
            st.session_state['user_id'] = None
            # Remove o cookie ao fazer logout
            cookie_manager.delete('user_data')
            st.rerun()
else:
    tab1, tab2 = st.tabs(["Login", "Registro"])

    with tab1:
        st.title("Login")
        username = st.text_input("Usuário")
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
                    
                    # Se "Lembrar-me" estiver marcado, salva os dados no cookie
                    if remember_me:
                        save_user_cookie(user)
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")

    with tab2:
        with st.form("register_form", enter_to_submit=False):
            st.title("Registro")
            new_username = st.text_input("Novo usuário")
            new_email = st.text_input("Email")
            new_password = st.text_input("Nova senha", type="password")
            confirm_password = st.text_input("Confirmar senha", type="password")
            submit = st.form_submit_button("Registrar")
            if submit:
                if new_password != confirm_password:
                    st.error("As senhas não coincidem")
                else:
                    if criar_usuario(new_username, new_password, new_email):
                        st.success("Usuário registrado com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Nome de usuário ou email já existente")

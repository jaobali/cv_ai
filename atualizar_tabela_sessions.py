import psycopg2
from dotenv import load_dotenv
import os
import streamlit as st

def get_connection():
    try:
        # Se st.secrets existir e tiver DB_HOST → Streamlit Cloud
        if st.secrets.get("DB_HOST"):
            return psycopg2.connect(
                host=st.secrets["DB_HOST"],
                port=int(st.secrets["DB_PORT"]),
                dbname=st.secrets["DB_NAME"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASSWORD"],
                sslmode='require'
            )
    except Exception:
        # Se der qualquer erro ao acessar st.secrets → Continua e tenta .env
        pass

    # Ambiente local
    load_dotenv()
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode='require'
    )

def atualizar_tabela_sessions():
    """Atualiza a tabela user_sessions para incluir o campo user_ip"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Verifica se a coluna user_ip já existe
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'user_sessions' AND column_name = 'user_ip'
        """)
        
        if not cursor.fetchone():
            # Adiciona a coluna user_ip se ela não existir
            cursor.execute("""
            ALTER TABLE user_sessions 
            ADD COLUMN user_ip TEXT DEFAULT 'unknown_ip'
            """)
            print("✅ Coluna user_ip adicionada com sucesso!")
        else:
            print("ℹ️ Coluna user_ip já existe!")
        
        # Limpa sessões antigas que não têm IP
        cursor.execute("""
        DELETE FROM user_sessions 
        WHERE user_ip IS NULL OR user_ip = 'unknown_ip'
        """)
        
        conn.commit()
        print("✅ Tabela user_sessions atualizada com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao atualizar tabela: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    atualizar_tabela_sessions() 
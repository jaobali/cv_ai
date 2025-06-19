import psycopg2
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do .env
load_dotenv()

# Pegar as informações do .env
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

try:
    # Conectar ao banco
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    print("✅ Conexão com o Supabase (PostgreSQL) bem-sucedida!")

    # Teste simples: Listar tabelas existentes
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tabelas = cursor.fetchall()

    print("📋 Tabelas no banco Supabase:")
    for tabela in tabelas:
        print(f"- {tabela[0]}")

    cursor.close()
    conn.close()

except Exception as e:
    print("❌ Erro ao conectar ao Supabase:")
    print(e)

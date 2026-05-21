import os
import sys
import psycopg2
from dotenv import load_dotenv

# Carrega o .env local
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or "neon.tech" not in DATABASE_URL:
    print("[Error] DATABASE_URL invalido ou nao aponta para o Neon no .env!")
    sys.exit(1)

print("Conectando ao Neon PostgreSQL...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("Iniciando limpeza de dados pesados no Neon...")
    
    # 1. Trunca o conteúdo de código-fonte completo (que pesa centenas de MB) mas mantém a estrutura das tarefas
    print("Limpando colunas de código-fonte pesado (mantendo as tarefas)...")
    cursor.execute("UPDATE erp_scan_tasks SET source_code = NULL;")
    cursor.execute("UPDATE qa_tasks SET requirements_file_content = NULL;")
    
    # 2. Se preferir zerar completamente as tarefas antigas para liberar espaço físico no banco:
    print("Esvaziando tabelas de tarefas antigas...")
    cursor.execute("TRUNCATE TABLE erp_scan_tasks RESTART IDENTITY CASCADE;")
    cursor.execute("TRUNCATE TABLE qa_tasks RESTART IDENTITY CASCADE;")
    
    # 3. Libera o espaço em disco com VACUUM
    print("Executando VACUUM para consolidar espaco livre no Neon...")
    try:
        cursor.execute("VACUUM FULL;")
    except Exception as e:
        # VACUUM FULL pode requerer privilégios adicionais ou não rodar dentro de transações de alguns pools,
        # se falhar, apenas rodamos o VACUUM normal
        cursor.execute("VACUUM;")
        
    print("Banco de dados do Neon limpo com sucesso! Cota de transferencia e armazenamento liberada.")
    
except Exception as e:
    print(f"Erro ao conectar ou limpar o Neon: {e}")
    print("\nDICA DE SEGURANCA: Se o Neon bloquear o acesso externo devido a cota estourada, siga este passo:")
    print("1. Acesse o console web: https://console.neon.tech/")
    print("2. Abra o 'SQL Editor' no seu projeto.")
    print("3. Execute os seguintes comandos la diretamente (o painel web ignora limites de rede externos):")
    print("   TRUNCATE TABLE erp_scan_tasks RESTART IDENTITY CASCADE;")
    print("   TRUNCATE TABLE qa_tasks RESTART IDENTITY CASCADE;")
    print("   VACUUM FULL;")
finally:
    if 'conn' in locals() and conn:
        conn.close()

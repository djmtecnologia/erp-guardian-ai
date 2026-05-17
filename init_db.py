import os
from sqlalchemy import create_engine
from models import Base
from dotenv import load_dotenv

load_dotenv()

def init_database():
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url or "placeholder" in database_url or "SUA_URL" in database_url:
        print("❌ ERRO: DATABASE_URL não configurada no arquivo .env")
        return

    try:
        print(f"🔄 Conectando ao banco de dados Neon...")
        # Criar o engine
        engine = create_engine(database_url)
        
        print("🏗️ Criando tabelas (ERPMapping, AgentExecution, RiskAnalysis)...")
        # Criar as tabelas baseadas nos modelos definidos em backend/models.py
        Base.metadata.create_all(engine)
        
        print("✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")

if __name__ == "__main__":
    init_database()

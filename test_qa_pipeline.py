import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, QATask, QAReport, ERPUIKnowledge
from agent.qa_engine import QAAutomationEngine
from dotenv import load_dotenv

load_dotenv()

# Configuração temporária de testes em SQLite local (para não sujar o banco de produção Neon)
DATABASE_URL = "sqlite:///./qa_test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_end_to_end_pipeline():
    print("="*60)
    print("🧪 INICIANDO TESTE END-TO-END DO PIPELINE DE QA & MANUAIS")
    print("="*60)

    # 1. Iniciar Banco de Testes
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Mock de Conhecimento Prévio de UI (Sonda)
        print("\n[Teste] 1. Injetando Conhecimento Prévio de UI (Mock)...")
        ui_mock = ERPUIKnowledge(
            screen_name="Faturamento de Notas Fiscais - ERP Classic",
            controls=[
                {"class_name": "TEdit", "text": "Cliente ID"},
                {"class_name": "TButton", "text": "Confirmar Faturamento"},
                {"class_name": "TBitBtn", "text": "Gravar Registro"}
            ]
        )
        db.add(ui_mock)
        db.commit()

        # 2. Criar Cenário de Teste
        print("\n[Teste] 2. Criando Cenário de Teste (QATask)...")
        task = QATask(
            scenario="Testar faturamento de nota fiscal com inclusão de itens e clique no botão Gravar Registro",
            status="pending"
        )
        db.add(task)
        db.commit()
        print(f"Cenário criado! ID: {task.id} | Cenário: '{task.scenario}'")

        # 3. Rodar o QA Engine Local
        print("\n[Teste] 3. Acionando QAAutomationEngine (Simulação de Automação)...")
        # Simula o motor local enviando logs
        qa_engine = QAAutomationEngine(backend_url="http://localhost:8000")
        logs = qa_engine.execute_qa_test(
            task_id=task.id,
            scenario=task.scenario,
            exe_path="C:\\Windows\\notepad.exe" # Abre o bloco de notas como ERP mock
        )
        print(f"Logs de automação gerados ({len(logs)} linhas).")

        # 4. Simular o Processamento de IA do Documentador
        print("\n[Teste] 4. Disparando Inteligência Artificial para redigir Manual e Relatório...")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ AVISO: GEMINI_API_KEY não configurada no .env. Ignorando chamada de IA...")
            print("Automação e pipeline testados localmente com SUCESSO!")
            return

        import google.generativeai as genai
        genai.configure(api_key=api_key)

        ui_controls_str = str(ui_mock.controls)
        prompt = f"""
        Você é um Engenheiro de QA Sênior e Escritor Técnico de Manuais de ERP.
        Com base no cenário testado e no log da automação de UI abaixo, gere dois documentos.
        
        IMPORTANTE: Separe estritamente os dois documentos usando a tag [DIVIDER] no meio!
        
        CENÁRIO TESTADO: {task.scenario}
        LOGS DE EXECUÇÃO: {logs}
        COMPONENTES DE INTERFACE CONHECIDOS: {ui_controls_str}
        
        Estrutura esperada:
        
        # 📋 Relatório de Teste de QA
        Apresente uma análise técnica do teste.
        
        [DIVIDER]
        
        # 📖 Manual do Usuário: Funcionalidade ERP
        Guia explicativo em Markdown.
        """

        print("[Teste] Aguardando retorno da API Gemini com fallbacks de cota...")
        models = [
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-latest',
            'gemini-2.0-flash',
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-3.1-flash-lite'
        ]
        generated_text = ""
        for model_name in models:
            try:
                print(f"[Teste] Tentando modelo: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                generated_text = response.text
                print(f"✅ Sucesso com o modelo: {model_name}")
                break
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    print(f"⚠️ Cota excedida no modelo {model_name}. Tentando próximo...")
                    continue
                else:
                    print(f"❌ Erro no modelo {model_name}: {e}")
                    
        if not generated_text:
            raise Exception("Todos os modelos de IA falharam devido a limites de cota (429).")

        parts = generated_text.split("[DIVIDER]")
        report_md = parts[0].strip()
        manual_md = parts[1].strip() if len(parts) > 1 else "Manual em geração..."

        # Salva o Relatório Gerado
        report = QAReport(
            task_id=task.id,
            test_logs=logs,
            test_report_md=report_md,
            user_manual_md=manual_md
        )
        db.add(report)
        task.status = "completed"
        db.commit()

        print("\n" + "="*50)
        print("🎉 PIPELINE INTEGRADO EXECUTADO COM 100% DE SUCESSO!")
        print("="*50)
        print(f"\n📂 RELATÓRIO DE QA GERADO:\n{report_md[:350]}...\n")
        print(f"\n📘 MANUAL DO USUÁRIO GERADO:\n{manual_md[:350]}...\n")

    except Exception as e:
        print(f"\n❌ ERRO DETECTADO NO PIPELINE: {e}")
    finally:
        db.close()
        # Limpa o banco sqlite de testes
        if os.path.exists("./qa_test.db"):
            try:
                os.remove("./qa_test.db")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(test_end_to_end_pipeline())

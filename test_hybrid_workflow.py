import asyncio
import os
from workflow_engine.engine import HybridWorkflow
from agents.delphi_review_agent.agent import DelphiReviewAgent
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY", "SUA_API_KEY")

# --- FUNÇÕES DETERMINÍSTICAS (Repetitivas e Confiáveis) ---

def verify_file_access(context: dict):
    """Tarefa repetitiva: validar se os arquivos necessários existem."""
    file_path = context.get("file_path", "")
    if os.path.exists(file_path):
        return f"Arquivo {file_path} verificado e acessível."
    else:
        raise FileNotFoundError(f"Arquivo {file_path} não encontrado.")

def check_sql_syntax(context: dict):
    """Tarefa repetitiva: busca palavras proibidas em SQL (ex: DROP)."""
    sql_content = context.get("sql_code", "")
    forbidden = ["DROP TABLE", "DELETE FROM"] # Simplificação determinística
    for term in forbidden:
        if term in sql_content.upper():
            return f"AVISO: Termo de risco '{term}' detectado via análise estática."
    return "Sintaxe SQL básica validada (análise estática)."

def prepare_delivery(context: dict):
    """Tarefa repetitiva: preparar log de entrega."""
    return "Estrutura de entrega preparada na pasta /dist."

# --- EXECUÇÃO DO WORKFLOW HÍBRIDO ---

async def test_hybrid():
    # 1. Configurar o Agente de IA (Dinâmico)
    review_agent = DelphiReviewAgent(api_key=API_KEY)

    # 2. Criar o Workflow Híbrido
    workflow = HybridWorkflow("commit-validation-pipeline")

    # Adicionando os passos
    workflow.add_deterministic_step("verify-access", verify_file_access) \
            .add_deterministic_step("static-sql-check", check_sql_syntax) \
            .add_agent_step(review_agent) \
            .add_deterministic_step("prepare-delivery", prepare_delivery)

    # 3. Executar o Workflow
    print("\n" + "="*60)
    print("INICIANDO WORKFLOW HÍBRIDO (ESTÁTICO + AGENTES IA)")
    print("="*60)

    contexto_inicial = {
        "file_path": "./agent/samples/UGeradorPedido.pas",
        "file_name": "UGeradorPedido.pas",
        "code": "unit UTest; implementation procedure T.Exec; begin end; end.",
        "sql_code": "SELECT * FROM PEDIDOS WHERE ID = 1"
    }

    final_context = await workflow.run(contexto_inicial)

    print("\n" + "="*60)
    print("RESUMO DA EXECUÇÃO")
    print("="*60)
    
    for report in final_context["execution_history"]:
        status_icon = "✅" if report.status.value == "completed" else "❌"
        type_info = " [IA]" if "model" in report.metadata else "[REPETITIVA]"
        print(f"{status_icon} {report.agent_id:<20} {type_info:<15}")

    # Exibe o relatório da IA especificamente
    ia_report = next(r for r in final_context["execution_history"] if r.agent_id == "delphi-review-agent")
    
    if ia_report.status.value == "completed" and ia_report.findings:
        print(f"\nFeedback da IA (Dinâmico):\n{ia_report.findings[0].get('content', 'Sem detalhes.')}")
    elif ia_report.status.value == "failed":
        error_msg = ia_report.findings[0].get("error", "Erro desconhecido")
        print(f"\n❌ A IA falhou com o erro: {error_msg}")
        print("Dica: Verifique se sua GEMINI_API_KEY no arquivo .env é válida.")

if __name__ == "__main__":
    asyncio.run(test_hybrid())

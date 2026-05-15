import asyncio
import os
from orchestrator.engine import OrchestrationEngine
from agents.documentation_agent.agent import DocumentationAgent
from agents.delphi_review_agent.agent import DelphiReviewAgent
from dotenv import load_dotenv

# Carrega API Key do arquivo .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY", "SUA_API_KEY_AQUI")

async def main():
    engine = OrchestrationEngine()

    # 1. Instanciar e Registrar Agentes
    doc_agent = DocumentationAgent(api_key=API_KEY)
    review_agent = DelphiReviewAgent(api_key=API_KEY)

    engine.register_agent(doc_agent)
    engine.register_agent(review_agent)

    print("\n" + "="*50)
    print("TESTE 1: DOCUMENTATION AGENT (Standalone)")
    print("="*50)
    
    # Contexto para mapear a pasta de samples
    doc_context = {"project_path": "./agent/samples"}
    doc_report = await engine.run_standalone("documentation-agent", doc_context)
    
    for find in doc_report.findings:
        print(f"\nArquivo: {find['file']}")
        print(f"Resumo: {find['summary'][:200]}...")

    print("\n" + "="*50)
    print("TESTE 2: CODE REVIEW AGENT (Standalone)")
    print("="*50)
    
    # Código sample para revisão
    with open("./agent/samples/UGeradorPedido.pas", "r") as f:
        code_content = f.read()
        
    review_context = {
        "file_name": "UGeradorPedido.pas",
        "code": code_content
    }
    review_report = await engine.run_standalone("delphi-review-agent", review_context)
    
    print(f"\nReview Findings:\n{review_report.findings[0]['review']}")

    print("\n" + "="*50)
    print("TESTE 3: PIPELINE EXECUTION (Doc -> Review)")
    print("="*50)
    
    # No pipeline, poderíamos usar o Doc Agent para mapear e depois o Review Agent para revisar o que foi mapeado
    pipeline_results = await engine.run_pipeline(
        ["documentation-agent", "delphi-review-agent"],
        {"project_path": "./agent/samples", "file_name": "UGeradorPedido.pas", "code": code_content}
    )
    
    print(f"\nPipeline concluído com {len(pipeline_results)} relatórios.")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import argparse
import os
from dotenv import load_dotenv

# Configurar path para importar módulos do projeto
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.support_agent.agent import SupportResolutionAgent

async def main():
    parser = argparse.ArgumentParser(description="ERP Guardian AI - Resolvedor de Chamados")
    parser.add_argument("--desc", required=True, help="Descrição do problema relatado pelo usuário (Coloque entre aspas)")
    parser.add_argument("--files", nargs='+', default=[], help="Caminho dos arquivos (Evidências PNG/JPG, Códigos PAS/SQL)")
    
    args = parser.parse_args()
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Erro: GEMINI_API_KEY não encontrada no .env")
        return

    print("\n========================================================")
    print("🚑 ERP GUARDIAN AI - ANÁLISE DE CHAMADO DE SUPORTE")
    print("========================================================")
    print(f"Problema: {args.desc}")
    print(f"Arquivos Anexados: {len(args.files)}")
    print("--------------------------------------------------------")

    agent = SupportResolutionAgent(api_key=api_key)
    
    context = {
        "description": args.desc,
        "files": args.files
    }
    
    print("Iniciando análise com a Inteligência Artificial (Isso pode levar alguns segundos)...\n")
    report = await agent.execute(context)
    
    if report.status.value == "completed":
        print("\n✅ RESOLUÇÃO PROPOSTA:")
        print("========================================================")
        # O agente retorna uma lista com o dicionário
        print(report.findings[0].get("content", ""))
        print("========================================================")
    else:
        print("\n❌ FALHA NA ANÁLISE.")
        print(report.findings)

if __name__ == "__main__":
    asyncio.run(main())

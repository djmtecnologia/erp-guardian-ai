import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Erro: GEMINI_API_KEY não encontrada no .env")
else:
    genai.configure(api_key=api_key)
    try:
        print("🔍 Listando TODOS os modelos disponíveis (Texto e Embedding)...")
        for m in genai.list_models():
            methods = m.supported_generation_methods
            type_info = ""
            if 'embedContent' in methods:
                type_info = "[EMBEDDING]"
            elif 'generateContent' in methods:
                type_info = "[TEXTO]"
            
            if type_info:
                print(f"✅ {type_info} {m.name}")
    except Exception as e:
        print(f"❌ Erro ao listar modelos: {e}")

"""
Módulo de Embeddings Semânticos para o ERP Guardian AI.
Usa o modelo text-embedding-004 do Google Gemini para gerar vetores de embedding
e calcular similaridade cosseno para busca semântica na base de conhecimento.
"""

import os
import math
from typing import List, Optional

# Cache do cliente Gemini para reutilização
_genai_configured = False


def _ensure_genai():
    """Configura o Google Generative AI apenas uma vez."""
    global _genai_configured
    if not _genai_configured:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY não configurada no ambiente.")
        genai.configure(api_key=api_key)
        _genai_configured = True


def generate_embedding(text: str, max_chars: int = 8000) -> Optional[List[float]]:
    """
    Gera um vetor de embedding usando o modelo text-embedding-004 do Gemini.
    
    Args:
        text: Texto para gerar o embedding.
        max_chars: Limite máximo de caracteres enviados ao modelo.
    
    Returns:
        Lista de floats representando o vetor de embedding (768 dimensões),
        ou None se houver falha.
    """
    if not text or not text.strip():
        return None

    try:
        _ensure_genai()
        import google.generativeai as genai

        # Trunca textos muito longos para respeitar limites do modelo
        truncated = text[:max_chars]

        result = genai.embed_content(
            model="models/text-embedding-004",
            content=truncated,
            task_type="RETRIEVAL_DOCUMENT"
        )
        return result['embedding']

    except Exception as e:
        print(f"[Embeddings] ⚠️ Erro ao gerar embedding: {e}")
        return None


def generate_query_embedding(text: str, max_chars: int = 2000) -> Optional[List[float]]:
    """
    Gera embedding otimizado para QUERY (busca), usando task_type RETRIEVAL_QUERY.
    Deve ser usado para o texto do chamado/ticket que será comparado com a base.
    
    Args:
        text: Texto da query (descrição do chamado).
        max_chars: Limite máximo de caracteres.
    
    Returns:
        Lista de floats representando o vetor de embedding.
    """
    if not text or not text.strip():
        return None

    try:
        _ensure_genai()
        import google.generativeai as genai

        truncated = text[:max_chars]

        result = genai.embed_content(
            model="models/text-embedding-004",
            content=truncated,
            task_type="RETRIEVAL_QUERY"
        )
        return result['embedding']

    except Exception as e:
        print(f"[Embeddings] ⚠️ Erro ao gerar query embedding: {e}")
        return None


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calcula a similaridade cosseno entre dois vetores.
    Retorna um valor entre -1.0 e 1.0 (1.0 = idênticos).
    
    Implementação pura em Python (sem dependências numpy).
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def find_relevant_knowledge(query_text: str, knowledge_list, top_k: int = 5, min_score: float = 0.3) -> list:
    """
    Busca semântica: encontra os registros de conhecimento mais relevantes
    para um dado texto de query.
    
    Args:
        query_text: Texto do chamado/cenário para buscar contexto relevante.
        knowledge_list: Lista de objetos ERPUIKnowledge com atributo 'embedding'.
        top_k: Número máximo de resultados a retornar.
        min_score: Score mínimo de similaridade para inclusão (0.0 a 1.0).
    
    Returns:
        Lista dos top-K objetos ERPUIKnowledge mais relevantes,
        ordenados por similaridade decrescente.
        Cada objeto recebe um atributo temporário '_similarity' com o score.
    """
    if not query_text or not knowledge_list:
        return []

    # Gera embedding da query
    query_embedding = generate_query_embedding(query_text)
    if not query_embedding:
        print("[Embeddings] ⚠️ Falha ao gerar embedding da query. Usando fallback (primeiros registros).")
        # Fallback: retorna os primeiros top_k registros que têm business_rules
        fallback = [k for k in knowledge_list if k.business_rules][:top_k]
        for k in fallback:
            k._similarity = 0.0
        return fallback

    # Calcula similaridade com cada registro
    scored = []
    for k in knowledge_list:
        if not k.embedding or not k.business_rules:
            continue
        
        score = cosine_similarity(query_embedding, k.embedding)
        if score >= min_score:
            k._similarity = score
            scored.append((score, k))

    # Ordena por score decrescente e retorna top-K
    scored.sort(key=lambda x: x[0], reverse=True)
    
    results = [k for _, k in scored[:top_k]]
    
    if results:
        print(f"[Embeddings] 🎯 {len(results)} registros relevantes encontrados (scores: {[f'{s:.3f}' for s, _ in scored[:top_k]]})")
    else:
        print("[Embeddings] ℹ️ Nenhum registro com similaridade suficiente encontrado.")
    
    return results

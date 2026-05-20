from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
import shutil
from sqlalchemy.orm import Session
from typing import List
import os
import sys
import base64

# Adiciona o caminho para encontrar os modelos na raiz se necessário
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ERPMapping, AgentExecution, Base, ERPScanTask, ERPUIKnowledge, QATask, QAReport, SupportTask, LocalConfig

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ERP Guardian AI - API")

from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    )

# DB Setup
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Auto-cria TODAS as tabelas no Neon na inicialização da API
# Operação idempotente: ignora tabelas que já existem (checkfirst=True)
@app.on_event("startup")
def auto_create_tables():
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("[Startup] ✅ Todas as tabelas verificadas/criadas no banco Neon.")
        
        # Migração segura de colunas: garante que qa_tasks e erp_scan_tasks tenham as novas colunas
        with engine.connect() as conn:
            from sqlalchemy import text
            # qa_tasks
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS exe_path TEXT;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS username VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS password VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS requirements_file_name VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS requirements_file_content TEXT;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS db_object_name VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS db_tns VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS db_user VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS db_password VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS exe_version VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS gef_grupo VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS gef_empresa VARCHAR;"))
            conn.execute(text("ALTER TABLE qa_tasks ADD COLUMN IF NOT EXISTS gef_filial VARCHAR;"))
            
            # erp_scan_tasks
            conn.execute(text("ALTER TABLE erp_scan_tasks ADD COLUMN IF NOT EXISTS exe_version VARCHAR;"))
            conn.execute(text("ALTER TABLE erp_scan_tasks ADD COLUMN IF NOT EXISTS gef_grupo VARCHAR;"))
            conn.execute(text("ALTER TABLE erp_scan_tasks ADD COLUMN IF NOT EXISTS gef_empresa VARCHAR;"))
            conn.execute(text("ALTER TABLE erp_scan_tasks ADD COLUMN IF NOT EXISTS gef_filial VARCHAR;"))
            conn.execute(text("ALTER TABLE erp_scan_tasks ADD COLUMN IF NOT EXISTS source_code TEXT;"))
            
            # erp_ui_knowledge
            conn.execute(text("ALTER TABLE erp_ui_knowledge ADD COLUMN IF NOT EXISTS source_code TEXT;"))
            conn.execute(text("ALTER TABLE erp_ui_knowledge ADD COLUMN IF NOT EXISTS business_rules TEXT;"))
            
            conn.commit()
            print("[Startup] 🧬 Migração de colunas adicionais para qa_tasks, erp_scan_tasks e erp_ui_knowledge concluída com sucesso.")
    except Exception as e:
        print(f"[Startup] ⚠️ Erro ao criar/atualizar tabelas: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api")
def read_root():
    return {"status": "ERP Guardian AI API is online"}

@app.get("/api/mappings")
def get_mappings(db: Session = Depends(get_db)):
    return db.query(ERPMapping).order_by(ERPMapping.updated_at.desc()).all()

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_files = db.query(ERPMapping).count()
    total_executions = db.query(AgentExecution).count()
    return {
        "total_files": total_files,
        "total_executions": total_executions,
        "health_score": 85
    }

@app.post("/api/telemetria")
def post_telemetria(data: dict, db: Session = Depends(get_db)):
    execution = AgentExecution(
        agent_id=data.get("agent_id", "unknown"),
        status=data.get("status", "completed"),
        context=data.get("context", {}),
        report=data.get("report", {})
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return {"status": "success", "id": execution.id}
import base64

@app.post("/api/support/tnsnames")
def save_tnsnames(data: dict, db: Session = Depends(get_db)):
    tns_names = data.get("tns_names", [])
    config = db.query(LocalConfig).filter(LocalConfig.key == "tns_names").first()
    if not config:
        config = LocalConfig(key="tns_names", value=tns_names)
        db.add(config)
    else:
        config.value = tns_names
    db.commit()
    return {"status": "success"}

@app.get("/api/support/tnsnames")
def get_tnsnames(db: Session = Depends(get_db)):
    config = db.query(LocalConfig).filter(LocalConfig.key == "tns_names").first()
    if config:
        return {"tns_names": config.value}
    return {"tns_names": ["XE"]}

@app.post("/api/support")
async def solve_support_ticket(
    description: str = Form(...),
    files: List[UploadFile] = File(...),
    oracle_user: str = Form(None),
    oracle_password: str = Form(None),
    oracle_tns: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # Processamento seguro dos arquivos anexados para JSON (codificando Base64 se for binário)
        processed_files = []
        for file in files:
            content = await file.read()
            if not file.filename:
                continue
            ext = file.filename.lower().split('.')[-1]
            if ext in ['png', 'jpg', 'jpeg', 'webp']:
                encoded = base64.b64encode(content).decode('utf-8')
                processed_files.append({
                    "filename": file.filename,
                    "content": encoded,
                    "is_binary": True
                })
            else:
                try:
                    text_content = content.decode('utf-8', errors='ignore')
                except Exception:
                    text_content = content.decode('latin-1', errors='ignore')
                processed_files.append({
                    "filename": file.filename,
                    "content": text_content,
                    "is_binary": False
                })
                
        # Busca todo o conhecimento acumulado e regras aprendidas de código Delphi / Varredura
        knowledge_list = db.query(ERPUIKnowledge).all()
        learned_context_str = ""
        for idx, k in enumerate(knowledge_list):
            if k.business_rules:
                learned_context_str += f"\n--- [CONHECIMENTO COGNITIVO APRENDIDO #{idx+1} (Tela: {k.screen_name})] ---\n{k.business_rules}\n"
        
        full_description = description
        if learned_context_str:
            full_description = f"{description}\n\n[MEMÓRIA COGNITIVA DO ERP ENCONTRADA]:\n{learned_context_str}"
            
        # Enfileira a tarefa para o agente local resolver
        task = SupportTask(
            description=full_description,
            files=processed_files,
            oracle_user=oracle_user,
            oracle_password=oracle_password,
            oracle_tns=oracle_tns,
            status="pending"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return {"status": "queued", "task_id": task.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/support/pending")
def get_pending_support_task(db: Session = Depends(get_db)):
    task = db.query(SupportTask).filter(SupportTask.status == "pending").order_by(SupportTask.created_at.asc()).first()
    if task:
        # Atualiza para running para evitar múltiplos agentes pegando a mesma tarefa
        task.status = "running"
        db.commit()
        return {
            "status": "task_found",
            "task_id": task.id,
            "description": task.description,
            "oracle_user": task.oracle_user,
            "oracle_password": task.oracle_password,
            "oracle_tns": task.oracle_tns,
            "files": task.files
        }
    return {"status": "no_tasks"}

@app.post("/api/support/result")
def post_support_result(data: dict, db: Session = Depends(get_db)):
    task_id = data.get("task_id")
    status = data.get("status")
    solution = data.get("solution")
    
    task = db.query(SupportTask).filter(SupportTask.id == task_id).first()
    if task:
        task.status = status
        task.solution = solution
        db.commit()
        return {"status": "success"}
    return {"status": "error", "message": "Tarefa de suporte não encontrada."}

@app.get("/api/support/status/{task_id}")
def get_support_status(task_id: int, db: Session = Depends(get_db)):
    task = db.query(SupportTask).filter(SupportTask.id == task_id).first()
    if task:
        return {
            "status": task.status,
            "solution": task.solution
        }
    return {"status": "not_found"}

# --- ENDPOINTS DO UI SCANNER (VARREDURA WINDOWS) ---

@app.post("/api/ui-scan/trigger")
def trigger_scan(data: dict, db: Session = Depends(get_db)):
    """Cria uma tarefa de varredura na nuvem para ser capturada pelo Windows."""
    task = ERPScanTask(
        exe_path=data.get("exe_path"),
        username=data.get("username"),
        password=data.get("password"),
        exe_version=data.get("exe_version"),
        gef_grupo=data.get("gef_grupo"),
        gef_empresa=data.get("gef_empresa"),
        gef_filial=data.get("gef_filial"),
        source_code=data.get("source_code"),
        status=data.get("status") or "pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"status": "success", "task_id": task.id}

@app.post("/api/ui-scan/append-code")
def append_scan_code(data: dict, db: Session = Depends(get_db)):
    task_id = data.get("task_id")
    chunk = data.get("chunk") or ""
    task = db.query(ERPScanTask).filter_by(id=task_id).first()
    if task:
        if task.source_code is None:
            task.source_code = chunk
        else:
            task.source_code += chunk
        db.commit()
        return {"status": "success"}
    return {"status": "error", "message": "Tarefa de varredura não encontrada."}

@app.get("/api/ui-scan/pending")
def get_pending_scan(db: Session = Depends(get_db)):
    """O Agente Windows consome esta rota para verificar se há tarefas."""
    task = db.query(ERPScanTask).filter_by(status="pending").first()
    if not task:
        return {"status": "no_tasks"}
    # Marca como running para evitar que dois agentes peguem a mesma tarefa
    task.status = "running"
    db.commit()
    return {
        "status": "task_found",
        "task_id": task.id,
        "exe_path": task.exe_path,
        "username": task.username,
        "password": task.password,
        "exe_version": task.exe_version,
        "gef_grupo": task.gef_grupo,
        "gef_empresa": task.gef_empresa,
        "gef_filial": task.gef_filial
    }

@app.get("/api/ui-scan/status/{task_id}")
def get_scan_status(task_id: int, db: Session = Depends(get_db)):
    """Frontend consulta o status real de uma tarefa de varredura pelo ID."""
    task = db.query(ERPScanTask).filter(ERPScanTask.id == task_id).first()
    if task:
        return {"status": task.status, "task_id": task.id}
    return {"status": "not_found"}

@app.post("/api/ui-scan/update")
def update_scan_status(data: dict, db: Session = Depends(get_db)):
    """Atualiza o status da varredura executada localmente."""
    task = db.query(ERPScanTask).filter_by(id=data.get("task_id")).first()
    if task:
        task.status = data.get("status")
        db.commit()
        return {"status": "updated"}
    raise HTTPException(status_code=404, detail="Tarefa não encontrada")

@app.post("/api/ui-scan/result")
def post_scan_result(data: dict, db: Session = Depends(get_db)):
    """O Agente Windows envia a árvore de telas do ERP mapeada por pywinauto e a IA processa o aprendizado dos fontes."""
    task_id = data.get("task_id")
    screen_name = data.get("screen_name") or "Tela ERP Mapeada"
    controls = data.get("controls")

    source_code = None
    relevant_code = None
    business_rules = None

    # 1. Recupera o código-fonte completo associado à tarefa
    if task_id:
        task = db.query(ERPScanTask).filter_by(id=task_id).first()
        if task and task.source_code:
            source_code = task.source_code

            # -------------------------------------------------------
            # 2. FILTRAGEM INTELIGENTE: extrai apenas os blocos do
            #    arquivo fonte que correspondem ao nome da tela atual.
            #    O código completo fica no banco; o Gemini só recebe
            #    o trecho relevante (até 60.000 chars).
            # -------------------------------------------------------
            import re

            # Normaliza o nome da tela para comparação (remove espaços, maiúsculas)
            screen_slug = re.sub(r'[^a-z0-9]', '', screen_name.lower())

            # Divide o código nas seções por arquivo (cabeçalho inserido pelo frontend)
            # Formato: "--- ARQUIVO FONTE: NomeArquivo.pas ---"
            sections = re.split(r'\n---\s*(?:ARQUIVO FONTE|FONTE DELPHI)(?:\s*\(ZIP\))?:\s*(.+?)\s*---\n', source_code)

            # sections[0] = texto antes do primeiro separador (ignorar)
            # sections[1] = nome do arquivo 1, sections[2] = conteúdo 1, etc.
            matched_sections = []
            fallback_sections = []  # caso sem match exato, pega os primeiros arquivos

            i = 1
            while i < len(sections) - 1:
                file_name = sections[i].strip()
                file_content = sections[i + 1]
                i += 2

                # Normaliza o nome do arquivo para comparação
                file_slug = re.sub(r'[^a-z0-9]', '', file_name.lower())

                # Match: nome do arquivo contém palavras do nome da tela ou vice-versa
                screen_words = [w for w in re.findall(r'[a-z]{3,}', screen_slug) if w not in ('tela', 'form', 'frm', 'unit', 'main')]
                is_match = any(w in file_slug for w in screen_words) or any(w in screen_slug for w in re.findall(r'[a-z]{3,}', file_slug))

                if is_match:
                    matched_sections.append(f"=== {file_name} ===\n{file_content}")
                else:
                    fallback_sections.append(f"=== {file_name} ===\n{file_content[:2000]}")  # preview dos outros

            MAX_CHARS = 60_000

            if matched_sections:
                relevant_code = "\n".join(matched_sections)[:MAX_CHARS]
                print(f"[UI-Scanner] 🎯 {len(matched_sections)} arquivo(s) fonte correspondente(s) à tela '{screen_name}' encontrado(s).")
            else:
                # Sem match direto: envia os primeiros arquivos como contexto geral
                relevant_code = "\n".join(fallback_sections)[:MAX_CHARS]
                print(f"[UI-Scanner] 🔍 Nenhum fonte específico para '{screen_name}'. Usando contexto geral ({len(fallback_sections)} arquivos).")

            print(f"[UI-Scanner] 🧠 Iniciando aprendizado cognitivo ({len(relevant_code):,} chars enviados ao Gemini)...")

            # 3. Chama o Gemini com apenas o trecho relevante
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

                controls_preview = str(controls)[:500] if controls else "Nenhum componente mapeado."

                prompt = f"""Você é o Orquestrador Cognitivo de Engenharia de Software da Fábrica de Canais da Compusoft.
Analise o código-fonte Delphi Pascal (.pas / .dfm) relacionado à tela '{screen_name}' e gere documentação técnica de referência em Markdown, em português brasileiro.

CÓDIGO-FONTE DELPHI RELEVANTE:
{relevant_code}

COMPONENTES VISUAIS MAPEADOS PELO AGENTE WINDOWS:
{controls_preview}

Gere uma síntese técnica contendo:
1. 📝 **Propósito Principal da Tela** — O que o formulário resolve no contexto do ERP.
2. 📈 **Regras de Negócio e Cálculos** — Fórmulas, impostos, rateios, regras de ANTT, arredondamentos.
3. 🛡️ **Validações e Restrições de Fluxo** — Campos obrigatórios, limites, dependências de gravação.
4. 🗄️ **Tabelas e Campos do Banco Relacionados** — Campos SQL/Delphi lidos ou gravados.
5. 🔗 **Integrações e Dependências** — Outras units, procedures ou módulos chamados."""

                models = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash-latest']
                for m in models:
                    try:
                        model = genai.GenerativeModel(m)
                        response = model.generate_content(prompt)
                        business_rules = response.text
                        print(f"[UI-Scanner] ✅ Regras de negócio extraídas via {m} para '{screen_name}'.")
                        break
                    except Exception as e:
                        print(f"[UI-Scanner] Falha no modelo {m}: {e}")
            except Exception as e:
                print(f"[UI-Scanner] Erro geral ao acionar Gemini: {e}")

    # 4. Salva a base de conhecimento enriquecida no Postgres Neon
    knowledge = ERPUIKnowledge(
        screen_name=screen_name,
        controls=controls,
        source_code=relevant_code,   # salva apenas o trecho relevante, não o ZIP inteiro
        business_rules=business_rules
    )
    db.add(knowledge)
    db.commit()
    return {"status": "success", "learned": business_rules is not None}

@app.get("/api/ui-scan/knowledge")
def get_ui_knowledge(db: Session = Depends(get_db)):
    """Carrega toda a base de conhecimento de interface gerada."""
    return db.query(ERPUIKnowledge).order_by(ERPUIKnowledge.created_at.desc()).all()

# --- ENDPOINTS DO WORKFLOW DE QA (TESTES E MANUAIS AUTOMÁTICOS) ---

@app.post("/api/qa/trigger")
def trigger_qa_task(data: dict, db: Session = Depends(get_db)):
    """Dispara um cenário de teste a ser executado pelo Windows."""
    
    def clean_nul(val):
        if isinstance(val, str):
            # Remove qualquer caractere nulo (0x00) que o PostgreSQL rejeita
            return val.replace("\x00", "").replace("\u0000", "")
        return val

    task = QATask(
        scenario=clean_nul(data.get("scenario")),
        exe_path=clean_nul(data.get("exe_path")),
        username=clean_nul(data.get("username")),
        password=clean_nul(data.get("password")),
        requirements_file_name=clean_nul(data.get("requirements_file_name")),
        requirements_file_content=clean_nul(data.get("requirements_file_content")),
        db_object_name=clean_nul(data.get("db_object_name")),
        db_tns=clean_nul(data.get("db_tns")),
        db_user=clean_nul(data.get("db_user")),
        db_password=clean_nul(data.get("db_password")),
        status=clean_nul(data.get("status")) or "pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"status": "success", "task_id": task.id}

@app.post("/api/qa/append-code")
def append_qa_code(data: dict, db: Session = Depends(get_db)):
    task_id = data.get("task_id")
    chunk = data.get("chunk") or ""
    
    def clean_nul(val):
        if isinstance(val, str):
            return val.replace("\x00", "").replace("\u0000", "")
        return val

    chunk = clean_nul(chunk)
    task = db.query(QATask).filter_by(id=task_id).first()
    if task:
        if task.requirements_file_content is None:
            task.requirements_file_content = chunk
        else:
            task.requirements_file_content += chunk
        db.commit()
        return {"status": "success"}
    return {"status": "error", "message": "Tarefa de QA não encontrada."}

@app.get("/api/qa/pending")
def get_pending_qa_task(db: Session = Depends(get_db)):
    """O Agente Windows busca cenários de testes de interface pendentes."""
    task = db.query(QATask).filter_by(status="pending").first()
    if not task:
        return {"status": "no_tasks"}
    task.status = "running"
    db.commit()
    return {
        "status": "task_found",
        "task_id": task.id,
        "scenario": task.scenario,
        "exe_path": task.exe_path,
        "username": task.username,
        "password": task.password,
        "requirements_file_name": task.requirements_file_name,
        "requirements_file_content": task.requirements_file_content,
        "db_object_name": task.db_object_name,
        "db_tns": task.db_tns,
        "db_user": task.db_user,
        "db_password": task.db_password
    }

@app.get("/api/qa/status/{task_id}")
def get_qa_status(task_id: int, db: Session = Depends(get_db)):
    """Frontend consulta o status real de uma tarefa de QA pelo ID."""
    task = db.query(QATask).filter(QATask.id == task_id).first()
    if task:
        return {"status": task.status, "task_id": task.id}
    return {"status": "not_found"}

@app.post("/api/qa/update")
def update_qa_status(data: dict, db: Session = Depends(get_db)):
    """Atualiza o status do teste de QA local."""
    task = db.query(QATask).filter_by(id=data.get("task_id")).first()
    if task:
        task.status = data.get("status")
        db.commit()
        return {"status": "updated"}
    raise HTTPException(status_code=404, detail="Tarefa não encontrada")

@app.post("/api/qa/result")
def post_qa_result(data: dict, db: Session = Depends(get_db)):
    """O Agente Windows envia os logs brutos da execução da automação UI."""
    task_id = data.get("task_id")
    test_logs = data.get("test_logs")
    
    # 1. Salvar resultado temporário ou direto
    # 2. Chamar a IA para gerar os documentos (Pipeline QA -> Documentador)
    task = db.query(QATask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        
    task.status = "completed"
    
    # Busca todo o conhecimento acumulado e regras aprendidas de código Delphi / Varredura
    knowledge_list = db.query(ERPUIKnowledge).all()
    learned_memory_str = ""
    for idx, k in enumerate(knowledge_list):
        if k.business_rules:
            learned_memory_str += f"\n--- [MEMÓRIA COGNITIVA ERP #{idx+1} (Tela: {k.screen_name})] ---\n{k.business_rules}\n"
        if k.controls:
            learned_memory_str += f"[Componentes da Tela {k.screen_name}]:\n{str(k.controls)[:80]}\n"
            
    ui_controls_str = ""
    if knowledge_list:
        ui_controls_str = str(knowledge_list[-1].controls[:40]) if knowledge_list[-1].controls else ""
        
    # Acionar a inteligência para documentação
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Padrão robusto de fallback de modelos
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
        
        prompt = f"""
        Você é o Orquestrador Cognitivo de QA e Auditor de Sistemas Legados ERP (Especialista em Delphi Pascal e Banco de Dados PL/SQL Oracle).
        Sua missão é realizar uma AUDITORIA TRIDIMENSIONAL CRUZADA com base nos insumos abaixo.
        
        IMPORTANTE: Separe estritamente os dois documentos usando a tag [DIVIDER] no meio!
        
        CENÁRIO TESTADO E CÓDIGOS FORNECIDOS:
        {task.scenario}
        
        LOGS DE EXECUÇÃO E CÓDIGOS DO BANCO EXTRAÍDOS:
        {test_logs}
        
        COMPONENTES DE INTERFACE MAPEADOS DO ERP:
        {ui_controls_str}
        
        📚 REGRAS DE NEGÓCIO E CONHECIMENTOS PREVIAMENTE APRENDIDOS (FONTES / BANCO / SCANNER):
        {learned_memory_str}
        
        INSTRUÇÕES CRÍTICAS DE AUDITORIA CRUZADA (DELPHI PASCAL vs PL/SQL ORACLE vs REQUISITOS):
        Se o usuário fornecer o código-fonte do sistema Delphi (arquivos .pas, units Pascal, forms .dfm) no "CENÁRIO TESTADO" ou arquivo anexo, E houver o código de banco Oracle extraído nos "LOGS DE EXECUÇÃO" (marcado por `[DB-AUDIT-FOUND]`), execute uma análise tridimensional de engenharia de software:
        
        1. **Alinhamento Matemático e Arredondamento:**
           - Compare as fórmulas no Delphi Pascal (ex: uso de `RoundTo`, `Trunc`, divisões com `Double`) com o código PL/SQL Oracle (ex: `ROUND()`, `TRUNC()`, tipos `NUMBER`).
           - Identifique vulnerabilidades de "diferença de centavos" em fretes, impostos (como piso mínimo ANTT) ou faturamento, que geram quebras de consistência.
           
        2. **Tratamento e Alinhamento de Exceções:**
           - Verifique se os erros levantados no banco (`RAISE_APPLICATION_ERROR` ou triggers do Oracle) são devidamente capturados por blocos `try..except` no Delphi ou se causarão travamentos de tela ou loops infinitos no ERP.
           
        3. **Consistência de Tamanho e Tipo de Dados (UI vs Banco):**
           - Compare o tamanho máximo dos campos de entrada mapeados na interface (inputs visualizados, `MaxLength` de TEdit) ou variáveis Delphi com o tamanho físico da coluna na tabela do Oracle (DDL). Aponte riscos de estouro de campo ("Value too large for column").
           
        4. **Geração de Patches:**
           - Se encontrar divergências ou bugs lógicos, forneça OBRIGATORIAMENTE duas seções de correção claras:
             - **Patch de Correção Delphi (Pascal):** Código Pascal limpo e corrigido.
             - **Patch de Correção Oracle (PL/SQL):** Código SQL DDL/DML ou trigger PL/SQL corrigido.

        Estrutura esperada do Relatório:
        
        --- INÍCIO DO RELATÓRIO ---
        # 📋 Relatório de Teste de QA e Auditoria Tridimensional
        Apresente uma análise técnica abrangente da execução visual e lógica de dados.
        
        - **Status Geral da Execução** (Aprovado / Falho)
        - **Detalhes do Teste de Interface (Simulação de UI)**
        - **🛡️ Auditoria Lógica Tridimensional (Delphi ↔ PL/SQL ↔ Regras de Negócio)**
          - [Se houver códigos Pascal e PL/SQL, faça a análise cruzada detalhada de arredondamentos, loops de performance e tratamento de exceções. Se houver apenas um deles, faça a auditoria aprofundada dele em relação aos requisitos]
        - **Tabela de Divergências e Inconsistências Detectadas**
        - **🛠️ Patches de Correção Sugeridos (Delphi Pascal & Oracle PL/SQL)**
          - [Forneça blocos de código prontos e otimizados para corrigir os bugs identificados]
        - **Recomendações de Performance e Segurança**
        
        [DIVIDER]
        
        # 📖 Manual do Usuário: Funcionalidade ERP
        Crie um guia passo a passo amigável em Markdown explicando ao usuário final como navegar e executar essa rotina testada.
        --- FIM ---
        """
        
        system_prompt = """
        Você é o Orquestrador Cognitivo de QA e Auditor de Sistemas Legados ERP da Fábrica da Compusoft.
        Você trabalha com Temperatura Zero e determinismo absoluto.
        
        DIRETRIZES DE COMPORTAMENTO DEFENSIVO:
        1. A REGRA DO "NÃO SEI": Se a informação ou os detalhes do sistema, tabelas do banco ou regras não estiverem descritos no contexto fornecido, no código Delphi anexado ou nos logs do banco, responda estritamente: 'Dados insuficientes para conclusão'. Nunca invente tabelas, campos ou regras.
        2. CADEIA DE RACIOCÍNIO (Chain of Thought): Antes de fornecer qualquer veredito de auditoria ou recomendação final, pense passo a passo. Escreva detalhadamente sua justificativa em uma seção preliminar racional.
        3. DELIMITADORES DE VARIÁVEIS: Isole dados brutos e instruções de entrada usando delimitadores como <xml>, ### ou três aspas ("\"\"\"").
        """

        generated_text = ""
        success_flag = False
        
        for m in models:
            try:
                print(f"[QA-Pipeline] Tentando modelo Criador: {m}")
                # Pillar 1 & 5: Defensive System Prompt, Temperature 0.0 for deterministic execution
                model = genai.GenerativeModel(
                    model_name=m,
                    generation_config={"temperature": 0.0, "top_p": 0.95},
                    system_instruction=system_prompt
                )
                
                # Multi-Agent loop with Auto-Retry (Up to 2 correction attempts)
                current_prompt = prompt
                for attempt in range(3):
                    print(f"[QA-Pipeline] Tentativa de geração #{attempt + 1}...")
                    response = model.generate_content(current_prompt)
                    candidate_text = response.text
                    
                    # Pillar 3 & 4: Structured Validation & Critic Agent Cross-Checking
                    if "[DIVIDER]" not in candidate_text:
                        print("[QA-Pipeline] Erro de validação de formato (tag [DIVIDER] ausente). Forçando auto-correção...")
                        current_prompt = f"{prompt}\n\n⚠️ ATENÇÃO: Sua resposta anterior falhou na validação de formato pois você esqueceu de incluir a tag [DIVIDER] dividindo o Relatório de QA e o Manual do Usuário. Reescreva o conteúdo incluindo a tag obrigatoriamente."
                        continue
                        
                    # Agente Avaliador (Critic Agent) com temperatura zero
                    print("[QA-Pipeline] 🛡️ Acionando Agente Avaliador (Critic Agent) para auditoria cruzada...")
                    critic_prompt = f"""
                    Você é o Agente Avaliador Técnico de Sistemas (Critic Agent) de extrema rigidez.
                    Sua missão é revisar o conteúdo gerado por um colega agente em busca de alucinações lógicas, violação da Regra do 'Não Sei', invenções de fatos ou inconsistência com o cenário e requisitos fornecidos.
                    
                    CONTEÚDO ANALISADO:
                    {candidate_text}
                    
                    DADOS DO CENÁRIO ORIGINAL:
                    Cenário: {task.scenario}
                    Logs: {test_logs}
                    Requisitos/Código Delphi: {task.requirements_file_content}
                    
                    Responda estritamente no seguinte formato:
                    STATUS: [APROVADO] ou [REPROVADO]
                    CORREÇÕES: [Se REPROVADO, liste detalhadamente o que o agente inventou, alucinou ou formatou errado. Se APROVADO, deixe em branco]
                    """
                    
                    critic_response = model.generate_content(critic_prompt)
                    critic_result = critic_response.text
                    print(f"[QA-Pipeline] 🛡️ Resultado do Critic Agent:\n{critic_result}")
                    
                    if "STATUS: [REPROVADO]" in critic_result:
                        print("[QA-Pipeline] Geração reprovada pelo Critic Agent! Iniciando auto-correção...")
                        current_prompt = f"{prompt}\n\n⚠️ ATENÇÃO: Sua tentativa anterior foi REPROVADA pelo Agente Avaliador com os seguintes desvios apontados:\n{critic_result}\nPor favor, refaça o trabalho corrigindo todos esses pontos, mantendo ancoragem estrita e sem inventar dados."
                    else:
                        print("[QA-Pipeline] 🎉 Geração aprovada com sucesso pelo Critic Agent!")
                        generated_text = candidate_text
                        success_flag = True
                        break
                
                if success_flag:
                    break
            except Exception as e:
                print(f"[QA-Pipeline] Erro de processamento no modelo {m}: {e}")
                continue
                
        if not generated_text:
            raise Exception("IA falhou no processamento de escrita técnica pós auditoria cruzada.")
            
        parts = generated_text.split("[DIVIDER]")
        report_md = parts[0].strip()
        manual_md = parts[1].strip() if len(parts) > 1 else "Manual em geração..."
        
        qa_report = QAReport(
            task_id=task_id,
            test_logs=test_logs,
            test_report_md=report_md,
            user_manual_md=manual_md
        )
        db.add(qa_report)
        db.commit()
        
    except Exception as e:
        print(f"[QA-Pipeline] Erro na geração automática de documentação: {e}")
        # Cria relatório com erro para não perder logs
        qa_report = QAReport(
            task_id=task_id,
            test_logs=test_logs,
            test_report_md=f"# ❌ Falha na geração da IA\n{str(e)}",
            user_manual_md="Não foi possível gerar o manual do usuário devido a um erro de IA."
        )
        db.add(qa_report)
        db.commit()
        
    return {"status": "success"}

@app.get("/api/qa/reports")
def get_qa_reports(db: Session = Depends(get_db)):
    """Busca a lista de relatórios de QA e manuais gerados."""
    return db.query(QAReport).order_by(QAReport.created_at.desc()).all()

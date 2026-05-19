import os
import re
from typing import Any, Dict, List
from shared.base_agent import BaseAgent, AgentStatus, AgentReport
import google.generativeai as genai

def get_oracle_dsn(tns_name: str, tnsnames_path: str = r"C:\app\client\oracle\product\19.0.0\client_1\network\admin\tnsnames.ora") -> str:
    """Busca e extrai a string de conexão (DSN) correspondente no tnsnames.ora local."""
    if not os.path.exists(tnsnames_path):
        print(f"[SupportAgent] tnsnames.ora não localizado em '{tnsnames_path}'. Usando TNS Name cru.")
        return tns_name
        
    try:
        with open(tnsnames_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Remover comentários
        content = re.sub(r'#.*', '', content)
        
        # Compactar espaços e quebras para facilitar casamento
        lines = [line.strip() for line in content.splitlines()]
        clean_content = "".join([l for l in lines if l])
        
        # Regex de emparelhamento de parênteses aninhados (até 4 níveis)
        matches = re.findall(r'([a-zA-Z0-9_\-\.]+)\s*=\s*(\((?:[^\(\)]*|\((?:[^\(\)]*|\((?:[^\(\)]*|\([^\(\)]*\))*\))*\))*\))', clean_content)
        for key, val in matches:
            if key.upper().strip() == tns_name.upper().strip():
                print(f"[SupportAgent] ✅ TNS '{tns_name}' resolvido no tnsnames.ora com sucesso!")
                return val.strip()
    except Exception as e:
        print(f"[SupportAgent] Erro ao ler/parsear tnsnames.ora: {e}")
        
    return tns_name

class SupportResolutionAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__("support-resolution-agent")
        genai.configure(api_key=api_key)
        self.model_priorities = [
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-latest',
            'gemini-2.0-flash',
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-3.1-flash-lite'
        ]
        self.findings = []

    async def execute(self, context: Dict[str, Any]) -> AgentReport:
        self.status = AgentStatus.RUNNING
        ticket_description = context.get("description", "Nenhuma descrição fornecida.")
        files = context.get("files", []) # Lista de caminhos de arquivos

        # --- CONEXÃO E INTROSPECÇÃO DE BANCO ORACLE ---
        db_context = ""
        oracle_user = context.get("oracle_user")
        oracle_password = context.get("oracle_password")
        oracle_tns = context.get("oracle_tns")

        if oracle_user and oracle_password and oracle_tns:
            print(f"[SupportAgent] 🔌 Conectando ao Banco Oracle em '{oracle_tns}'...")
            try:
                import oracledb
                
                # Inicializa o Client se existir e for necessário (Modo Thick)
                oracle_client_path = r"C:\app\client\oracle\product\19.0.0\client_1"
                try:
                    if os.name == 'nt' and os.path.exists(oracle_client_path):
                        oracledb.init_oracle_client(lib_dir=oracle_client_path)
                        print("[SupportAgent] Oracle Client inicializado em Thick Mode.")
                except Exception as ex:
                    print(f"[SupportAgent] Executando em Thin Mode (oracledb puro): {ex}")
                
                dsn = get_oracle_dsn(oracle_tns)
                conn = oracledb.connect(user=oracle_user, password=oracle_password, dsn=dsn)
                print("[SupportAgent] ✅ Conexão estabelecida com o Banco Oracle!")
                
                cursor = conn.cursor()
                
                # 1. Obter objetos inválidos no schema
                cursor.execute("SELECT object_name, object_type FROM user_objects WHERE status = 'INVALID' AND rownum <= 10")
                invalids = cursor.fetchall()
                invalid_str = "\n".join([f"- {name} ({obj_type})" for name, obj_type in invalids])
                
                # 2. Obter procedures/triggers alterados recentemente
                cursor.execute("""
                    SELECT object_name, object_type, to_char(last_ddl_time, 'YYYY-MM-DD HH24:MI:SS') 
                    FROM user_objects 
                    WHERE object_type IN ('PROCEDURE', 'FUNCTION', 'TRIGGER', 'PACKAGE') 
                    AND rownum <= 5 
                    ORDER BY last_ddl_time DESC
                """)
                recent_objects = cursor.fetchall()
                recent_str = "\n".join([f"- {name} ({obj_type}) - DDL: {t}" for name, obj_type, t in recent_objects])
                
                # 3. Mapear esquemas de tabelas citadas na descrição do chamado
                cursor.execute("SELECT table_name FROM user_tables")
                all_tables = [r[0] for r in cursor.fetchall()]
                
                tables_discovered = []
                desc_upper = ticket_description.upper()
                for table in all_tables:
                    if table in desc_upper:
                        tables_discovered.append(table)
                        
                table_schemas_str = ""
                for table in tables_discovered[:3]: # Limita as 3 primeiras tabelas encontradas para não explodir tokens
                    cursor.execute(f"""
                        SELECT column_name, data_type, data_length, nullable 
                        FROM user_tab_columns 
                        WHERE table_name = '{table}'
                        ORDER BY column_id
                    """)
                    cols = cursor.fetchall()
                    cols_desc = "\n".join([f"  * {col[0]} | {col[1]}({col[2]}) | Nullable: {col[3]}" for col in cols])
                    table_schemas_str += f"\n--- SCHEMA DA TABELA '{table}' ---\n{cols_desc}\n"
                
                cursor.close()
                conn.close()
                
                db_context = f"""
--- 🗄️ DADOS DIAGNÓSTICOS DO BANCO ORACLE ---
[Conectado via TNS: {oracle_tns}]

Objetos Inválidos no Schema:
{invalid_str or 'Nenhum objeto inválido encontrado.'}

Procedimentos e Objetos Modificados Recentemente:
{recent_str or 'Nenhuma alteração recente.'}
{table_schemas_str}
---------------------------------------------
"""
                print("[SupportAgent] ✅ Introspecção e diagnóstico Oracle concluídos com sucesso!")
                
            except Exception as db_err:
                print(f"[SupportAgent] ❌ Falha na conexão/consulta Oracle: {db_err}")
                db_context = f"\n⚠️ [Aviso Banco Oracle]: Tentativa de conexão falhou. Erro: {db_err}\n"

        prompt_parts = [
            f"Você é um Desenvolvedor Sênior de Delphi e Especialista em Suporte Técnico Nível 3.\n",
            f"Temos o seguinte chamado de suporte relatado pelo usuário/cliente:\n",
            f"--- DESCRIÇÃO DO CHAMADO ---\n{ticket_description}\n---------------------------\n\n",
            db_context, # Insere as tabelas e status do Oracle se disponíveis!
            "Sua tarefa é analisar as evidências e o código fornecido, e então apresentar:\n",
            "1. A Causa Raiz provável do problema.\n",
            "2. A Solução Técnica exata (o que precisa ser alterado no código ou no banco).\n",
            "3. Um trecho de código corrigido ou script SQL de correção, se aplicável.\n\n",
            "Abaixo estão os anexos e códigos fornecidos:\n"
        ]

        uploaded_files = []
        try:
            for file_path in files:
                if not os.path.exists(file_path):
                    continue
                
                ext = file_path.lower().split('.')[-1]
                # Imagens para o Gemini
                if ext in ['png', 'jpg', 'jpeg', 'webp']:
                    print(f"[SupportAgent] Fazendo upload da imagem: {file_path}")
                    uploaded_file = genai.upload_file(path=file_path)
                    uploaded_files.append(uploaded_file)
                    prompt_parts.append(uploaded_file)
                    prompt_parts.append(f"Evidência: {os.path.basename(file_path)}\n")
                
                # Códigos ou logs anexos
                elif ext in ['pas', 'dfm', 'sql', 'txt', 'log']:
                    print(f"[SupportAgent] Lendo código-fonte: {file_path}")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        prompt_parts.append(f"--- ARQUIVO: {os.path.basename(file_path)} ---\n{content}\n----------------\n")
            
            # Executa com ciclagem inteligente de modelos de contingência
            generated_text = ""
            for model_name in self.model_priorities:
                try:
                    print(f"[SupportAgent] Analisando com {model_name}...")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt_parts)
                    generated_text = response.text
                    self.findings = [{"type": "support_resolution", "content": generated_text}]
                    self.status = AgentStatus.COMPLETED
                    print(f"✅ Análise concluída com sucesso usando {model_name}!")
                    break
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg:
                        print(f"⚠️ Cota excedida no modelo {model_name}. Tentando contingência...")
                        continue
                    else:
                        print(f"❌ Erro no modelo {model_name}: {e}")
                        break
            
            if self.status != AgentStatus.COMPLETED:
                raise Exception("Todos os modelos de IA falharam (possível limite de cota 429).")

        except Exception as e:
            print(f"[SupportAgent] Erro crítico: {e}")
            self.status = AgentStatus.FAILED
            self.findings = [{"error": str(e)}]
        finally:
            # Garante limpeza na nuvem
            for uf in uploaded_files:
                try:
                    genai.delete_file(uf.name)
                except:
                    pass

        return self.generate_report()

    async def validate(self, result: Any) -> bool:
        return self.status == AgentStatus.COMPLETED

    async def rollback(self) -> bool:
        return True

    def generate_report(self) -> AgentReport:
        return AgentReport(
            agent_id=self.agent_id,
            status=self.status,
            findings=self.findings,
            recommendations=["Valide as modificações estruturais propostas no ambiente de homologação."],
            metadata={"ticket_analyzed": True}
        )

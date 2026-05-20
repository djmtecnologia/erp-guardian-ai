"use client";

import React, { useState, useEffect } from 'react';
import { Eye, ShieldAlert, Cpu, CheckCircle2, ArrowLeft, Play, LayoutGrid, FileText, ClipboardList, BookOpen } from 'lucide-react';
import Link from 'next/link';

export default function QAPipeline() {
  const [scenario, setScenario] = useState("Testar rotina de faturamento de pedido com inserção automática de itens");
  const [exePath, setExePath] = useState("C:\\COMPUSOFT\\PRINCIPAL\\PRINCIPAL.EXE");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [fileName, setFileName] = useState("");
  const [fileContent, setFileContent] = useState("");
  
  // Código-fonte Delphi fornecido pelo usuário para análise cruzada
  const [delphiFileName, setDelphiFileName] = useState("");
  const [delphiSourceCode, setDelphiSourceCode] = useState("");
  
  // Estados para Auditoria de Banco de Dados Oracle
  const [tnsList, setTnsList] = useState<string[]>(["XE"]);
  const [dbObjectName, setDbObjectName] = useState("");
  const [dbTns, setDbTns] = useState("XE");
  const [dbUser, setDbUser] = useState("");
  const [dbPassword, setDbPassword] = useState("");
  const [enableDbAudit, setEnableDbAudit] = useState(false);

  // Estados para Contexto de Versão & GEF do ERP
  const [exeVersion, setExeVersion] = useState("");
  const [gefGrupo, setGefGrupo] = useState("");
  const [gefEmpresa, setGefEmpresa] = useState("");
  const [gefFilial, setGefFilial] = useState("");
  const [enableGef, setEnableGef] = useState(false);
  
  const [status, setStatus] = useState("idle"); // idle, pending, running, completed, failed
  const [loading, setLoading] = useState(false);
  const [reportsList, setReportsList] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [activeTab, setActiveTab] = useState("report"); // report, manual, logs
  const [scanLog, setScanLog] = useState<string[]>([]);

  const fetchReports = async () => {
    try {
      const resp = await fetch('/api/qa/reports');
      const data = await resp.json();
      setReportsList(data);
    } catch (err) {
      console.error("Erro ao buscar relatórios de QA:", err);
    }
  };

  useEffect(() => {
    fetchReports();
    const interval = setInterval(fetchReports, 5000);
    
    // Carrega dinamicamente a lista de perfis TNS Oracle sincronizados localmente do banco
    const fetchTns = async () => {
      try {
        const resp = await fetch('/api/support/tnsnames');
        const data = await resp.json();
        if (data.tns_names && data.tns_names.length > 0) {
          setTnsList(data.tns_names);
          setDbTns(data.tns_names[0]);
        }
      } catch (err) {
        console.error("Erro ao buscar TNS Names:", err);
      }
    };
    fetchTns();

    return () => clearInterval(interval);
  }, []);

  const addLog = (msg: string) => setScanLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    addLog(`📎 Arquivo de requisitos selecionado: ${file.name}`);
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      setFileContent(text);
    };
    reader.readAsText(file);
  };

  const handleStartTest = async (e) => {
    e.preventDefault();
    if (!scenario) return;

    setLoading(true);
    setStatus("pending");
    setScanLog([]);
    addLog("⏳ Enviando cenário e credenciais de teste para a nuvem...");

    try {
      const resp = await fetch('/api/qa/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario,
          exe_path: exePath,
          username,
          password,
          requirements_file_name: fileName || (delphiFileName ? "Delphi_Unit_Cross_Audit" : ""),
          requirements_file_content: delphiSourceCode 
            ? `[REQUISITOS / REGRAS DE NEGÓCIO]:\n${fileContent || 'Regras fornecidas no Cenário Principal.'}\n\n[CÓDIGO FONTE DELPHI PASCAL DO SISTEMA]:\n${delphiSourceCode}`
            : fileContent,
          db_object_name: enableDbAudit ? dbObjectName : "",
          db_tns: enableDbAudit ? dbTns : "",
          db_user: enableDbAudit ? dbUser : "",
          db_password: enableDbAudit ? dbPassword : "",
          exe_version: enableGef ? exeVersion : "",
          gef_grupo: enableGef ? gefGrupo : "",
          gef_empresa: enableGef ? gefEmpresa : "",
          gef_filial: enableGef ? gefFilial : ""
        })
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        addLog(`❌ Erro do Servidor (Status ${resp.status}): ${errData.error || 'Erro desconhecido'}`);
        if (errData.traceback) {
          addLog(`🔍 Diagnóstico da Exception:\n${errData.traceback}`);
        }
        setStatus("failed");
        setLoading(false);
        return;
      }

      const data = await resp.json();
      if (data.status === "success") {
        addLog(`✅ Tarefa de QA criada! ID: ${data.task_id}. Aguardando Agente Windows local...`);
        checkStatus(data.task_id);
      } else {
        addLog(`❌ Erro no retorno: ${JSON.stringify(data)}`);
        setStatus("failed");
        setLoading(false);
      }
    } catch (err: any) {
      addLog(`❌ Falha de comunicação com o servidor: ${err.message || err}`);
      setStatus("failed");
      setLoading(false);
    }
  };

  const checkStatus = (taskId) => {
    let previousStatus = "pending";
    const checkInterval = setInterval(async () => {
      try {
        const resp = await fetch(`/api/qa/status/${taskId}`);
        const data = await resp.json();
        const currentStatus = data.status;
        
        if (currentStatus !== previousStatus) {
          previousStatus = currentStatus;
          if (currentStatus === "running") {
            addLog("🤖 Agente Windows capturou a tarefa de QA! Inicializando FlaUI/pywinauto...");
            setStatus("running");
          } else if (currentStatus === "completed") {
            addLog("🏆 Robô de QA concluiu com SUCESSO! IA gerando relatório e manual...");
            setStatus("completed");
            setLoading(false);
            clearInterval(checkInterval);
            fetchReports();
          } else if (currentStatus === "failed") {
            addLog("❌ O Robô de QA local reportou falha na automação de interface.");
            setStatus("failed");
            setLoading(false);
            clearInterval(checkInterval);
          }
        }
      } catch (err) {
        clearInterval(checkInterval);
        addLog("❌ Erro ao verificar status do robô.");
        setLoading(false);
      }
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-200 p-8 font-sans">
      <header className="mb-8 flex items-center gap-4">
        <Link href="/" className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition">
          <ArrowLeft size={20} className="text-slate-300" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-3">
            <ClipboardList size={32} className="text-blue-400" /> Pipeline de Automação de QA & Manuais
          </h1>
          <p className="text-slate-500">Crie testes funcionais por texto, execute automação de UI local e gere manuais pela IA</p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Painel de Disparo */}
        <div className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl h-fit">
          <h2 className="text-lg font-semibold mb-6 flex items-center gap-2 text-blue-400">
            <Play size={18} /> Novo Cenário de Teste
          </h2>
          <form onSubmit={handleStartTest} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Caminho do Executável (.exe local)</label>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-300 focus:outline-none focus:border-blue-500 transition"
                  value={exePath}
                  onChange={(e) => setExePath(e.target.value)}
                  placeholder="C:\COMPUSOFT\PRINCIPAL\PRINCIPAL.EXE"
                />
                <input 
                  type="file" 
                  id="exe-picker-qa"
                  className="hidden"
                  accept=".exe"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      const name = file.name;
                      setExePath((prev) => {
                        const lastSlash = prev.lastIndexOf("\\");
                        if (lastSlash !== -1) {
                          return prev.substring(0, lastSlash + 1) + name;
                        }
                        return `C:\\COMPUSOFT\\PRINCIPAL\\` + name;
                      });
                    }
                  }}
                />
                <label 
                  htmlFor="exe-picker-qa"
                  className="bg-slate-950 border border-dashed border-slate-800 hover:border-blue-500/50 cursor-pointer rounded-xl px-4 flex items-center justify-center text-xs text-slate-400 hover:text-slate-200 transition font-medium"
                >
                  Procurar...
                </label>
              </div>
              <p className="text-[10px] text-slate-500 mt-1 leading-relaxed">
                💡 <strong>Segurança do Navegador:</strong> O browser oculta a pasta por privacidade. Ao selecionar o arquivo, extraímos o nome exato (`${exePath.split('\\').pop()}`) mantendo a pasta anterior.
              </p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                <span className="text-[9px] text-slate-500 self-center font-semibold uppercase tracking-wide mr-1">Sugestões:</span>
                <button 
                  type="button" 
                  onClick={() => setExePath("C:\\COMPUSOFT\\PRINCIPAL\\PRINCIPAL.EXE")}
                  className="text-[10px] bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-lg px-2.5 py-1 text-slate-300 transition font-medium"
                >
                  Compusoft Principal
                </button>
                <button 
                  type="button" 
                  onClick={() => setExePath("C:\\ERP\\sistema.exe")}
                  className="text-[10px] bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-lg px-2.5 py-1 text-slate-300 transition font-medium"
                >
                  ERP Padrão
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Usuário ERP</label>
                <input 
                  type="text" 
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-300 focus:outline-none focus:border-blue-500 transition"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Senha ERP</label>
                <input 
                  type="password" 
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-300 focus:outline-none focus:border-blue-500 transition"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-2">Descreva a funcionalidade que deseja testar no ERP</label>
              <textarea 
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 focus:outline-none focus:border-blue-500 transition h-32 resize-none"
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                placeholder="Ex: Abrir tela de faturamento, preencher cliente padrão, confirmar emissão da nota fiscal..."
              />
            </div>

            {/* Seção Premium de Inserção de Código-Fonte Delphi Pascal */}
            <div className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-4 space-y-3">
              <label className="block text-xs text-slate-400 font-semibold flex items-center gap-2">
                <Cpu size={14} className="text-blue-400" />
                Código-Fonte do Sistema Delphi (.pas / .dfm)
              </label>
              
              <div className="flex items-center gap-3">
                <input 
                  type="file" 
                  id="delphi-file"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setDelphiFileName(file.name);
                      const reader = new FileReader();
                      reader.onload = (ev) => {
                        if (ev.target?.result) {
                          setDelphiSourceCode(ev.target.result as string);
                        }
                      };
                      reader.readAsText(file);
                    }
                  }}
                  accept=".pas,.dfm,.pascal,.txt"
                />
                <label 
                  htmlFor="delphi-file"
                  className="bg-slate-950 border border-dashed border-slate-800 hover:border-blue-500/50 cursor-pointer rounded-xl p-3 text-xs text-slate-400 hover:text-slate-200 transition flex items-center gap-2 flex-1 justify-center"
                >
                  <Cpu size={16} className="text-blue-400 animate-pulse" />
                  {delphiFileName ? `Código Anexado: ${delphiFileName}` : "Anexar Código Delphi (.pas / .dfm)"}
                </label>
                {delphiFileName && (
                  <button 
                    type="button"
                    onClick={() => {
                      setDelphiFileName("");
                      setDelphiSourceCode("");
                    }}
                    className="p-3 bg-red-950/40 hover:bg-red-900/60 border border-red-800/40 hover:border-red-700 rounded-xl text-xs text-red-400 transition font-medium"
                  >
                    Remover
                  </button>
                )}
              </div>

              <div>
                <textarea 
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-emerald-400 focus:outline-none focus:border-blue-500 transition h-40 resize-y"
                  value={delphiSourceCode}
                  onChange={(e) => setDelphiSourceCode(e.target.value)}
                  placeholder="Ou cole seu código Delphi Pascal aqui para Auditoria Cruzada...
Ex:
procedure TFormFaturamento.ConfirmarPedido;
begin
  if Pedido.Valor > 0 then
    Faturar(Pedido);
end;"
                />
                <div className="flex justify-between items-center text-[10px] text-slate-500 mt-1 px-1">
                  <span>✨ Análise Cruzada: Delphi ↔ Oracle PL/SQL ↔ Regras de Negócio</span>
                  <span>{delphiSourceCode.length} caracteres lidos</span>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-2">Ou anexe um arquivo de requisitos (.txt, .pas, .sql, etc.)</label>
              <div className="flex items-center gap-3">
                <input 
                  type="file" 
                  id="requirements-file"
                  className="hidden"
                  onChange={handleFileChange}
                  accept=".txt,.pas,.sql,.dfm,.json,.pdf,.doc,.docx"
                />
                <label 
                  htmlFor="requirements-file"
                  className="bg-slate-950 border border-dashed border-slate-800 hover:border-blue-500/50 cursor-pointer rounded-xl p-3 text-xs text-slate-400 hover:text-slate-200 transition flex items-center gap-2 flex-1 justify-center"
                >
                  <FileText size={16} className="text-blue-400" />
                  {fileName ? "Alterar Arquivo" : "Selecionar Arquivo de Requisitos"}
                </label>
                {fileName && (
                  <button 
                    type="button"
                    onClick={() => {
                      setFileName("");
                      setFileContent("");
                      addLog("🗑️ Arquivo de requisitos removido.");
                    }}
                    className="p-3 bg-red-950/20 hover:bg-red-950/40 border border-red-900/40 hover:border-red-900 rounded-xl text-xs text-red-400 transition"
                  >
                    Remover
                  </button>
                )}
              </div>
              {fileName && (
                <div className="mt-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-[10px] text-blue-400 flex items-center justify-between">
                  <span>📎 Anexado: <strong>{fileName}</strong></span>
                  <span>{fileContent.length} caracteres lidos</span>
                </div>
              )}
            </div>

            {/* Configurações de Contexto: Versão & GEF do ERP */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu size={15} className="text-blue-400" />
                  <span className="text-xs font-semibold text-slate-300">Definir Versão & GEF (ERP)</span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="sr-only peer"
                    checked={enableGef}
                    onChange={(e) => setEnableGef(e.target.checked)}
                  />
                  <div className="w-9 h-5 bg-slate-850 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-400 after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600 peer-checked:after:bg-white"></div>
                </label>
              </div>

              {enableGef && (
                <div className="space-y-3 pt-2 border-t border-slate-900/60 animate-in fade-in duration-200">
                  <div>
                    <label className="block text-[10px] text-slate-400 mb-1">Versão do Executável desejada</label>
                    <input 
                      type="text"
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500 transition text-slate-100"
                      placeholder="Ex: VERSAO 12"
                      value={exeVersion}
                      onChange={(e) => setExeVersion(e.target.value)}
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-1 text-center">Grupo</label>
                      <input 
                        type="text"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500 transition text-center"
                        placeholder="1"
                        value={gefGrupo}
                        onChange={(e) => setGefGrupo(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-1 text-center">Empresa</label>
                      <input 
                        type="text"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500 transition text-center"
                        placeholder="10"
                        value={gefEmpresa}
                        onChange={(e) => setGefEmpresa(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-1 text-center">Filial</label>
                      <input 
                        type="text"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500 transition text-center"
                        placeholder="01"
                        value={gefFilial}
                        onChange={(e) => setGefFilial(e.target.value)}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Seção Premium de Auditoria de Banco de Dados Oracle */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldAlert size={16} className="text-purple-400" />
                  <span className="text-xs font-semibold text-slate-300">Auditar Lógica do Banco (Oracle)</span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="sr-only peer"
                    checked={enableDbAudit}
                    onChange={(e) => setEnableDbAudit(e.target.checked)}
                  />
                  <div className="w-9 h-5 bg-slate-850 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-400 after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600 peer-checked:after:bg-white"></div>
                </label>
              </div>
              
              {enableDbAudit && (
                <div className="space-y-3 pt-2 border-t border-slate-900/60 animate-in fade-in duration-200">
                  <div>
                    <label className="block text-[10px] text-slate-400 mb-1">Objeto a Auditar (Trigger, Procedure, View ou Tabela)</label>
                    <input 
                      type="text"
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-purple-500 transition uppercase"
                      placeholder="Ex: TRG_PISO_MINIMO_ANTT"
                      value={dbObjectName}
                      onChange={(e) => setDbObjectName(e.target.value)}
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-1">Perfil de Conexão TNS</label>
                      <select
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-purple-500 transition"
                        value={dbTns}
                        onChange={(e) => setDbTns(e.target.value)}
                      >
                        {tnsList.map((tns) => (
                          <option key={tns} value={tns}>{tns}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-1">Usuário do Banco</label>
                      <input 
                        type="text"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-purple-500 transition"
                        placeholder="Ex: SYSTEM"
                        value={dbUser}
                        onChange={(e) => setDbUser(e.target.value)}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-[10px] text-slate-400 mb-1">Senha do Banco</label>
                    <input 
                      type="password"
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 focus:outline-none focus:border-purple-500 transition"
                      placeholder="Senha de acesso ao Oracle"
                      value={dbPassword}
                      onChange={(e) => setDbPassword(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-xl transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Simulando Automação no Windows...
                </>
              ) : (
                <>
                  <Play size={16} /> Disparar Robô de QA
                </>
              )}
            </button>

            {status !== "idle" && (
              <div className="mt-4 p-3 bg-slate-950/60 border border-slate-800 rounded-xl text-xs flex items-center justify-between">
                <span className="text-slate-400 font-medium">Status do Robô:</span>
                <span className={`px-2 py-1 rounded font-semibold uppercase ${
                  status === "completed" ? "bg-emerald-500/10 text-emerald-400" :
                  status === "failed" ? "bg-red-500/10 text-red-400" :
                  status === "running" ? "bg-blue-500/10 text-blue-400" : "bg-yellow-500/10 text-yellow-400"
                }`}>
                  {status}
                </span>
              </div>
            )}

            {/* Log de Progresso em Tempo Real */}
            {scanLog.length > 0 && (
              <div className="mt-3 p-3 bg-black/40 border border-slate-800/60 rounded-xl max-h-40 overflow-y-auto">
                <p className="text-[10px] text-slate-500 font-mono font-semibold mb-2 uppercase tracking-wider">Log de Execução</p>
                {scanLog.map((line, i) => (
                  <p key={i} className="text-[10px] text-slate-400 font-mono leading-5">{line}</p>
                ))}
              </div>
            )}
          </form>
        </div>

        {/* Lista de Relatórios e Manuais */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl">
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <FileText size={20} className="text-slate-500" /> Relatórios e Manuais Disponíveis ({reportsList.length})
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reportsList.map((r, idx) => (
                <div 
                  key={idx} 
                  onClick={() => setSelectedReport(r)}
                  className={`p-4 rounded-xl border border-slate-800 cursor-pointer transition ${
                    selectedReport?.id === r.id ? "bg-blue-500/10 border-blue-500/40" : "bg-slate-950/40 hover:bg-slate-800/20"
                  }`}
                >
                  <div className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                    <CheckCircle2 size={16} className="text-blue-400" /> Relatório #{r.id}
                  </div>
                  <div className="text-xs text-slate-500 mt-2">
                    Mapeado em: {new Date(r.created_at).toLocaleString()}
                  </div>
                  <div className="text-xs text-slate-400 mt-1 truncate">
                    Logs: {r.test_logs?.length || 0} passos de automação.
                  </div>
                </div>
              ))}
              {reportsList.length === 0 && (
                <div className="text-slate-500 text-sm italic col-span-2">Nenhum teste de QA gerado ainda. Dispare o robô acima!</div>
              )}
            </div>
          </div>

          {/* Área de Visualização do Documento */}
          {selectedReport && (
            <div className="bg-slate-900/30 border border-slate-800 rounded-2xl backdrop-blur-xl overflow-hidden flex flex-col">
              {/* Abas */}
              <div className="flex border-b border-slate-800 bg-slate-950/40">
                <button 
                  onClick={() => setActiveTab("report")}
                  className={`px-6 py-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                    activeTab === "report" ? "border-blue-500 text-blue-400 bg-slate-900/20" : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <ClipboardList size={16} /> Relatório de QA
                </button>
                <button 
                  onClick={() => setActiveTab("manual")}
                  className={`px-6 py-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                    activeTab === "manual" ? "border-purple-500 text-purple-400 bg-slate-900/20" : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <BookOpen size={16} /> Manual do Usuário
                </button>
                <button 
                  onClick={() => setActiveTab("logs")}
                  className={`px-6 py-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                    activeTab === "logs" ? "border-slate-500 text-slate-200 bg-slate-900/20" : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Cpu size={16} /> Logs do Sistema
                </button>
              </div>

              {/* Conteúdo da Aba */}
              <div className="p-8 bg-slate-950/80 max-h-[500px] overflow-y-auto min-h-[300px]">
                {activeTab === "report" && (
                  <div className="prose prose-invert max-w-none text-slate-300 text-sm whitespace-pre-wrap leading-relaxed">
                    {selectedReport.test_report_md}
                  </div>
                )}
                {activeTab === "manual" && (
                  <div className="prose prose-invert max-w-none text-slate-300 text-sm whitespace-pre-wrap leading-relaxed">
                    {selectedReport.user_manual_md}
                  </div>
                )}
                {activeTab === "logs" && (
                  <div className="space-y-2 font-mono text-xs text-slate-400">
                    {selectedReport.test_logs?.map((log, i) => (
                      <div key={i} className="p-2 bg-slate-900/40 rounded border border-slate-900/60">
                        {log}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect } from 'react';
import { Eye, ShieldAlert, Cpu, CheckCircle2, ArrowLeft, Play, LayoutGrid } from 'lucide-react';
import Link from 'next/link';

export default function UIScanner() {
  const [exePath, setExePath] = useState("C:\\ERP\\sistema.exe");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("idle"); // idle, pending, running, completed, failed
  const [loading, setLoading] = useState(false);
  const [knowledgeList, setKnowledgeList] = useState([]);
  const [selectedScreen, setSelectedScreen] = useState(null);

  // Busca base de conhecimento gerada
  const fetchKnowledge = async () => {
    try {
      const resp = await fetch('/api/ui-scan/knowledge');
      const data = await resp.json();
      setKnowledgeList(data);
    } catch (err) {
      console.error("Erro ao buscar base de conhecimento UI:", err);
    }
  };

  useEffect(() => {
    fetchKnowledge();
    const interval = setInterval(fetchKnowledge, 5000); // Atualiza a cada 5s
    return () => clearInterval(interval);
  }, []);

  const [scanLog, setScanLog] = useState<string[]>([]);

  const addLog = (msg: string) => setScanLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  const handleStartScan = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus("pending");
    setScanLog([]);
    addLog("⏳ Enviando tarefa para a fila da nuvem...");

    try {
      const resp = await fetch('/api/ui-scan/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exe_path: exePath,
          username: username,
          password: password
        })
      });
      const data = await resp.json();
      if (data.status === "success") {
        addLog(`✅ Tarefa criada! ID: ${data.task_id}. Aguardando o Agente Windows capturar...`);
        checkStatus(data.task_id);
      } else {
        addLog(`❌ Erro ao criar tarefa: ${JSON.stringify(data)}`);
        setStatus("failed");
        setLoading(false);
      }
    } catch (err) {
      addLog("❌ Erro de comunicação com o servidor.");
      setStatus("failed");
      setLoading(false);
    }
  };

  const checkStatus = async (taskId) => {
    let previousStatus = "pending";
    const checkInterval = setInterval(async () => {
      try {
        const resp = await fetch(`/api/ui-scan/status/${taskId}`);
        const data = await resp.json();
        const currentStatus = data.status;

        // Só loga quando o status muda
        if (currentStatus !== previousStatus) {
          previousStatus = currentStatus;
          if (currentStatus === "running") {
            addLog("🤖 Agente Windows capturou a tarefa! Executando pywinauto...");
            setStatus("running");
          } else if (currentStatus === "completed") {
            addLog("🎉 Varredura concluída! Carregando telas mapeadas...");
            setStatus("completed");
            setLoading(false);
            clearInterval(checkInterval);
            fetchKnowledge();
          } else if (currentStatus === "failed") {
            addLog("❌ O Agente reportou falha na varredura. Verifique o log do executável.");
            setStatus("failed");
            setLoading(false);
            clearInterval(checkInterval);
          }
        }
      } catch (err) {
        clearInterval(checkInterval);
        addLog("❌ Erro ao consultar status da tarefa.");
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
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent flex items-center gap-3">
            <Cpu size={32} className="text-emerald-400" /> Sonda UI Scanner (Windows)
          </h1>
          <p className="text-slate-500">Mapeamento de interfaces legado e geração de Base de Conhecimento</p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Formulário de Disparo */}
        <div className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl h-fit">
          <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <Play size={18} className="text-emerald-400" /> Nova Varredura
          </h2>
          <form onSubmit={handleStartScan} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Caminho do Executável (.exe local)</label>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-300 focus:outline-none focus:border-emerald-500 transition"
                  value={exePath}
                  onChange={(e) => setExePath(e.target.value)}
                  placeholder="C:\COMPUSOFT\PRINCIPAL\PRINCIPAL.EXE"
                />
                <input 
                  type="file" 
                  id="exe-picker-scanner"
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
                  htmlFor="exe-picker-scanner"
                  className="bg-slate-950 border border-dashed border-slate-800 hover:border-emerald-500/50 cursor-pointer rounded-xl px-4 flex items-center justify-center text-xs text-slate-400 hover:text-slate-200 transition font-medium"
                >
                  Procurar...
                </label>
              </div>
              <p className="text-[10px] text-slate-500 mt-1 leading-relaxed">
                💡 <strong>Segurança do Navegador:</strong> O browser oculta a pasta por privacidade. Ao selecionar o arquivo, extraímos o nome exato (`${exePath.split('\\').pop()}`) mantendo a pasta anterior.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Usuário ERP</label>
                <input 
                  type="text" 
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-300 focus:outline-none focus:border-emerald-500 transition"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Senha ERP</label>
                <input 
                  type="password" 
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-300 focus:outline-none focus:border-emerald-500 transition"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3 rounded-xl transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Sonda Local Executando...
                </>
              ) : (
                <>
                  <Play size={16} /> Disparar Varredura
                </>
              )}
            </button>

            {status !== "idle" && (
              <div className="mt-4 p-3 bg-slate-950/60 border border-slate-800 rounded-xl text-xs flex items-center justify-between">
                <span className="text-slate-400 font-medium">Status da Sonda:</span>
                <span className={`px-2 py-1 rounded font-semibold uppercase ${
                  status === "completed" ? "bg-emerald-500/10 text-emerald-400" :
                  status === "failed" ? "bg-red-500/10 text-red-400" :
                  status === "running" ? "bg-blue-500/10 text-blue-400" : "bg-yellow-500/10 text-yellow-400"
                }`}>
                  {status}
                </span>
              </div>
            )}

            {/* Log de Execução em Tempo Real */}
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

        {/* Telas Mapeadas */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl">
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <LayoutGrid size={20} className="text-slate-500" /> Telas Conhecidas ({knowledgeList.length})
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {knowledgeList.map((k, idx) => (
                <div 
                  key={idx} 
                  onClick={() => setSelectedScreen(k)}
                  className={`p-4 rounded-xl border border-slate-800 cursor-pointer transition ${
                    selectedScreen?.id === k.id ? "bg-emerald-500/10 border-emerald-500/40" : "bg-slate-950/40 hover:bg-slate-800/20"
                  }`}
                >
                  <div className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                    <Eye size={16} className="text-emerald-400" /> {k.screen_name}
                  </div>
                  <div className="text-xs text-slate-500 mt-2">
                    Mapeado em: {new Date(k.created_at).toLocaleString()}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {k.controls?.length || 0} componentes identificados.
                  </div>
                </div>
              ))}
              {knowledgeList.length === 0 && (
                <div className="text-slate-500 text-sm italic col-span-2">Nenhuma tela mapeada ainda. Dispare a sonda acima!</div>
              )}
            </div>
          </div>

          {/* Detalhes da Tela Selecionada */}
          {selectedScreen && (
            <div className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl">
              <h3 className="text-md font-semibold mb-4 text-emerald-400">Componentes da Tela: {selectedScreen.screen_name}</h3>
              <div className="max-h-80 overflow-y-auto space-y-2 font-mono text-xs">
                {selectedScreen.controls?.map((c, i) => (
                  <div key={i} className="p-2 bg-slate-950/80 rounded border border-slate-900 flex justify-between items-center">
                    <div>
                      <span className="text-emerald-400">{c.class_name}</span>
                      <span className="text-slate-500 mx-2">|</span>
                      <span className="text-slate-200">"{c.text || 'Sem Texto'}"</span>
                    </div>
                    <div className="text-slate-600 text-[10px]">
                      Posição: {c.rectangle}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect } from 'react';
import { Eye, ShieldAlert, Cpu, CheckCircle2, ArrowLeft, Play, LayoutGrid, FileText, ClipboardList, BookOpen } from 'lucide-react';
import Link from 'next/link';

export default function QAPipeline() {
  const [scenario, setScenario] = useState("Testar rotina de faturamento de pedido com inserção automática de itens");
  const [status, setStatus] = useState("idle"); // idle, pending, running, completed, failed
  const [loading, setLoading] = useState(false);
  const [reportsList, setReportsList] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [activeTab, setActiveTab] = useState("report"); // report, manual, logs

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
    return () => clearInterval(interval);
  }, []);

  const handleStartTest = async (e) => {
    e.preventDefault();
    if (!scenario) return;

    setLoading(true);
    setStatus("pending");

    try {
      const resp = await fetch('/api/qa/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario })
      });
      const data = await resp.json();
      
      if (data.status === "success") {
        checkStatus(data.task_id);
      } else {
        setStatus("failed");
        setLoading(false);
      }
    } catch (err) {
      setStatus("failed");
      setLoading(false);
    }
  };

  const checkStatus = (taskId) => {
    const checkInterval = setInterval(async () => {
      try {
        const resp = await fetch('/api/qa/pending');
        const data = await resp.json();
        
        // Se não há tarefas pendentes, o agente local já executou e concluiu o pipeline
        if (data.status === "no_tasks") {
          setStatus("completed");
          setLoading(false);
          clearInterval(checkInterval);
          fetchReports();
        }
      } catch (err) {
        clearInterval(checkInterval);
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
              <label className="block text-xs text-slate-400 mb-2">Descreva a funcionalidade que deseja testar no ERP</label>
              <textarea 
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 focus:outline-none focus:border-blue-500 transition h-36 resize-none"
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                placeholder="Ex: Abrir tela de faturamento, preencher cliente padrão, confirmar emissão da nota fiscal..."
              />
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
                <span className="text-slate-400 font-medium">Status do Fluxo:</span>
                <span className={`px-2 py-1 rounded font-semibold uppercase ${
                  status === "completed" ? "bg-emerald-500/10 text-emerald-400" :
                  status === "failed" ? "bg-red-500/10 text-red-400" :
                  status === "running" ? "bg-blue-500/10 text-blue-400" : "bg-yellow-500/10 text-yellow-400"
                }`}>
                  {status}
                </span>
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

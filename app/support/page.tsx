"use client";

import React, { useState } from 'react';
import { Shield, Upload, FileText, Bot, AlertCircle, CheckCircle2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function SupportTicket() {
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [solution, setSolution] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!description || files.length === 0) {
      setError("Por favor, preencha a descrição e anexe pelo menos um arquivo.");
      return;
    }

    setLoading(true);
    setError(null);
    setSolution(null);

    const formData = new FormData();
    formData.append("description", description);
    files.forEach(file => {
      formData.append("files", file);
    });

    try {
      const response = await fetch('/api/support', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (data.status === "success") {
        setSolution(data.solution);
      } else {
        setError(data.message || "Erro desconhecido ao analisar o chamado.");
      }
    } catch (err) {
      setError("Falha na comunicação com o servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-200 p-8 font-sans">
      <header className="mb-8 flex items-center gap-4">
        <Link href="/" className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition">
          <ArrowLeft size={20} className="text-slate-300" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-3">
            <Bot size={32} className="text-blue-400" /> Agente de Suporte N3
          </h1>
          <p className="text-slate-500">Resolução automatizada de chamados de clientes via IA</p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Formulário */}
        <div className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl h-fit">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Descrição do Chamado (O que o cliente relatou?)
              </label>
              <textarea 
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-200 focus:outline-none focus:border-blue-500 transition h-32 resize-none"
                placeholder="Ex: O sistema apresenta erro Access Violation ao clicar em Emitir Nota Fiscal..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Evidências e Código-Fonte (.pas, .sql, .png, .jpg)
              </label>
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-800 border-dashed rounded-xl cursor-pointer bg-slate-950/50 hover:bg-slate-800/50 transition">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="w-8 h-8 mb-3 text-slate-500" />
                  <p className="mb-2 text-sm text-slate-400"><span className="font-semibold text-blue-400">Clique para enviar</span> ou arraste arquivos</p>
                  <p className="text-xs text-slate-500">{files.length} arquivo(s) selecionado(s)</p>
                </div>
                <input type="file" multiple className="hidden" onChange={handleFileChange} />
              </label>
            </div>

            {error && (
              <div className="p-4 bg-red-900/20 border border-red-900/50 rounded-xl flex items-center gap-3 text-red-400">
                <AlertCircle size={20} />
                <span className="text-sm">{error}</span>
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 px-4 rounded-xl transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Analisando com Inteligência Artificial...
                </>
              ) : (
                <>
                  <Shield size={20} />
                  Diagnosticar e Resolver
                </>
              )}
            </button>
          </form>
        </div>

        {/* Resultado */}
        <div className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl overflow-hidden flex flex-col">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <CheckCircle2 size={24} className="text-emerald-400" /> Solução Proposta
          </h2>
          
          <div className="flex-1 bg-slate-950 border border-slate-800 rounded-xl p-6 overflow-y-auto min-h-[400px]">
            {solution ? (
              <div className="text-slate-300 text-sm whitespace-pre-wrap leading-relaxed">
                {solution}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-600">
                <Bot size={48} className="mb-4 opacity-20" />
                <p>A solução técnica aparecerá aqui.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

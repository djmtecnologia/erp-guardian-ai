"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Activity, FileText, CheckCircle, AlertTriangle, Search, Terminal } from 'lucide-react';

// Simulação de dados (no cenário real, buscaria da API /stats e /mappings)
const Dashboard = () => {
  const [stats, setStats] = useState({ total_files: 124, executions: 45, health: 92 });
  const [recentFiles, setRecentFiles] = useState([
    { name: 'UGeradorPedido.pas', status: 'Secure', risk: 'Low', time: '2m ago' },
    { name: 'PKG_FATURAMENTO.sql', status: 'Warning', risk: 'Medium', time: '15m ago' },
    { name: 'UFinanceiroSettlement.pas', status: 'Critical', risk: 'High', time: '1h ago' },
  ]);

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-200 p-8 font-sans">
      {/* Header */}
      <header className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            ERP Guardian AI
          </h1>
          <p className="text-slate-500">Autonomous Enterprise Software Factory</p>
        </div>
        <div className="flex gap-4">
          <div className="bg-slate-900/50 border border-slate-800 px-4 py-2 rounded-lg flex items-center gap-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium">Local Agent Online</span>
          </div>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <StatCard icon={<FileText className="text-blue-400" />} label="Arquivos Mapeados" value={stats.total_files} />
        <StatCard icon={<Activity className="text-purple-400" />} label="Análises Realizadas" value={stats.executions} />
        <StatCard icon={<Shield className="text-emerald-400" />} label="ERP Health Score" value={`${stats.health}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Feed */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/30 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Search size={20} className="text-slate-500" /> Monitoramento em Tempo Real
              </h2>
            </div>
            
            <div className="space-y-4">
              {recentFiles.map((file, i) => (
                <FileRow key={i} file={file} />
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar: AI Activity */}
        <div className="space-y-6">
          <div className="bg-slate-900/30 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Terminal size={20} className="text-slate-500" /> Atividade dos Agentes
            </h2>
            <div className="space-y-4 text-sm font-mono text-slate-400">
              <div className="flex gap-3">
                <span className="text-blue-500">[DOC]</span>
                <span>Mapeando UFinanceiroSettlement.pas...</span>
              </div>
              <div className="flex gap-3">
                <span className="text-emerald-500">[REV]</span>
                <span>Análise de Memory Leak concluída.</span>
              </div>
              <div className="flex gap-3">
                <span className="text-amber-500">[RISK]</span>
                <span>Risco detectado no fluxo de Notas Fiscais.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ icon, label, value }) => (
  <div className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl">
    <div className="flex items-center gap-4 mb-2">
      <div className="p-2 bg-slate-800/50 rounded-lg">{icon}</div>
      <span className="text-slate-500 text-sm font-medium">{label}</span>
    </div>
    <div className="text-3xl font-bold">{value}</div>
  </div>
);

const FileRow = ({ file }) => (
  <div className="flex items-center justify-between p-4 bg-slate-800/20 border border-slate-800/50 rounded-xl hover:bg-slate-800/40 transition-all cursor-pointer">
    <div className="flex items-center gap-4">
      <div className={`p-2 rounded-lg ${
        file.status === 'Secure' ? 'bg-emerald-500/10' : 
        file.status === 'Warning' ? 'bg-amber-500/10' : 'bg-rose-500/10'
      }`}>
        {file.status === 'Secure' ? <CheckCircle size={18} className="text-emerald-500" /> : 
         file.status === 'Warning' ? <AlertTriangle size={18} className="text-amber-500" /> : 
         <Shield size={18} className="text-rose-500" />}
      </div>
      <div>
        <div className="font-medium text-slate-200">{file.name}</div>
        <div className="text-xs text-slate-500">{file.time}</div>
      </div>
    </div>
    <div className="flex items-center gap-6">
      <div className="text-right">
        <div className="text-xs text-slate-500 uppercase">Risco</div>
        <div className={`text-sm font-bold ${
          file.risk === 'Low' ? 'text-emerald-400' : 
          file.risk === 'Medium' ? 'text-amber-400' : 'text-rose-400'
        }`}>{file.risk}</div>
      </div>
    </div>
  </div>
);

export default Dashboard;

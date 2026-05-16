"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Activity, FileText, CheckCircle, AlertTriangle, Search, Terminal, Bot } from 'lucide-react';
import Link from 'next/link';

const Dashboard = () => {
  const [stats, setStats] = useState({ total_files: 0, executions: 0, health: 0 });
  const [recentFiles, setRecentFiles] = useState([]);

  // Busca dados reais da API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsResp = await fetch('/api/stats');
        const statsData = await statsResp.json();
        setStats(statsData);

        const mappingsResp = await fetch('/api/mappings');
        const mappingsData = await mappingsResp.json();
        setRecentFiles(mappingsData.slice(0, 5));
      } catch (error) {
        console.error("Erro ao buscar dados:", error);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 10000); // Atualiza a cada 10s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-200 p-8 font-sans">
      <header className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            ERP Guardian AI
          </h1>
          <p className="text-slate-500">Autonomous Enterprise Software Factory</p>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/support" className="bg-blue-600/20 text-blue-400 border border-blue-600/50 hover:bg-blue-600 hover:text-white px-4 py-2 rounded-lg flex items-center gap-2 transition font-medium text-sm">
            <Bot size={16} /> Resolver Chamado (N3)
          </Link>
          <div className="bg-slate-900/50 border border-slate-800 px-4 py-2 rounded-lg flex items-center gap-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium">System Online</span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <StatCard icon={<FileText className="text-blue-400" />} label="Arquivos Mapeados" value={stats.total_files} />
        <StatCard icon={<Activity className="text-purple-400" />} label="Análises Realizadas" value={stats.total_executions} />
        <StatCard icon={<Shield className="text-emerald-400" />} label="ERP Health Score" value={`${stats.health_score}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/30 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Search size={20} className="text-slate-500" /> Mapeamentos Recentes
            </h2>
            <div className="space-y-4">
              {recentFiles.map((file, i) => (
                <FileRow key={i} file={file} />
              ))}
              {recentFiles.length === 0 && <p className="text-slate-500 italic">Nenhum mapeamento encontrado ainda...</p>}
            </div>
          </div>
        </div>

        <div className="bg-slate-900/30 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl h-fit">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <Terminal size={20} className="text-slate-500" /> Atividade Cloud
          </h2>
          <div className="space-y-4 text-sm font-mono text-slate-400">
            <div className="flex gap-3 text-emerald-500">
              <span>●</span>
              <span>API Serverless Pronta</span>
            </div>
            <div className="flex gap-3 text-blue-500">
              <span>●</span>
              <span>Conexão Neon Ativa</span>
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
  <div className="flex items-center justify-between p-4 bg-slate-800/20 border border-slate-800/50 rounded-xl">
    <div className="flex items-center gap-4">
      <div className="p-2 bg-emerald-500/10 rounded-lg">
        <CheckCircle size={18} className="text-emerald-500" />
      </div>
      <div>
        <div className="font-medium text-slate-200">{file.module_name}</div>
        <div className="text-xs text-slate-500">{file.file_path}</div>
      </div>
    </div>
  </div>
);

export default Dashboard;

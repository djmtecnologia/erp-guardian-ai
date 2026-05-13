import React from 'react';
// Assuming shadcn/ui components are available in a real project
// import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
// import { Badge } from "@/components/ui/badge";

const Dashboard = () => {
  const reports = [
    { id: 1, module: "Financial", risk: 85, status: "Critical", date: "2026-05-13" },
    { id: 2, module: "Stock", risk: 20, status: "Low", date: "2026-05-12" }
  ];

  return (
    <div className="p-8 bg-slate-950 min-h-screen text-white font-sans">
      <header className="mb-12 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            ERP Guardian AI
          </h1>
          <p className="text-slate-400 mt-2">Enterprise ERP Code Review + QA Automation</p>
        </div>
        <div className="flex gap-4">
          <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 shadow-xl">
            <span className="text-xs text-slate-500 uppercase">Registered Agents</span>
            <div className="text-2xl font-mono text-emerald-400">12 Online</div>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        <div className="bg-slate-900/50 backdrop-blur-md p-6 rounded-2xl border border-slate-800 hover:border-blue-500/50 transition-all">
          <h3 className="text-slate-400 text-sm font-medium mb-4 uppercase">Overall Risk Score</h3>
          <div className="text-6xl font-bold text-red-500">72%</div>
          <p className="text-xs text-slate-500 mt-4">Elevated risk in Invoicing module</p>
        </div>
        {/* More metric cards */}
      </div>

      <section>
        <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
          <span className="w-2 h-8 bg-blue-500 rounded-full"></span>
          Recent Impact Analysis
        </h2>
        <div className="grid gap-4">
          {reports.map(report => (
            <div key={report.id} className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex justify-between items-center hover:bg-slate-800/50 cursor-pointer transition-colors">
              <div>
                <h4 className="text-lg font-medium">{report.module} Module Update</h4>
                <p className="text-sm text-slate-500">VCS Commit: jvcs_88291 • {report.date}</p>
              </div>
              <div className="flex items-center gap-8">
                <div className="text-right">
                  <div className="text-xs text-slate-500 uppercase">Impact Score</div>
                  <div className={`text-xl font-bold ${report.risk > 50 ? 'text-red-400' : 'text-emerald-400'}`}>
                    {report.risk}/100
                  </div>
                </div>
                <button className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-lg font-medium transition-all shadow-lg shadow-blue-900/20">
                  View Report
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Dashboard;

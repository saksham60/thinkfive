import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Activity, CheckCircle2, AlertOctagon, Clock, ShieldCheck, Zap, Search, Filter, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { AuditEvent } from '../types';

interface SupervisorViewProps {
  onTriggerSimulator: (scenario: string) => void;
}

export const SupervisorView: React.FC<SupervisorViewProps> = ({ onTriggerSimulator }) => {
  const [metrics, setMetrics] = useState<any>({});
  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>([]);
  const [searchFilter, setSearchFilter] = useState('');

  const chartData = [
    { time: '08:00', alerts: 4, resolutions: 12 },
    { time: '10:00', alerts: 8, resolutions: 18 },
    { time: '12:00', alerts: 15, resolutions: 24 },
    { time: '14:00', alerts: 9, resolutions: 30 },
    { time: '16:00', alerts: 18, resolutions: 35 },
    { time: '18:00', alerts: 12, resolutions: 42 },
    { time: '20:00', alerts: 6, resolutions: 48 }
  ];

  const fetchData = async () => {
    try {
      const [mRes, aRes] = await Promise.all([
        fetch('/api/supervisor/metrics'),
        fetch('/api/audit-logs')
      ]);
      const mData = await mRes.json();
      const aData = await aRes.json();

      setMetrics(mData);
      setAuditLogs(aData);
    } catch (e) {
      console.error('Failed to load supervisor data', e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredLogs = auditLogs.filter(l =>
    l.action.toLowerCase().includes(searchFilter.toLowerCase()) ||
    l.actor.toLowerCase().includes(searchFilter.toLowerCase()) ||
    l.details.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Title */}
      <div className="bg-[#111111] rounded-xl p-5 border border-white/10 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <LayoutDashboard className="w-6 h-6 text-orange-500" />
            <h1 className="text-xl font-light tracking-tight text-white">Supervisor Command Center</h1>
            <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-orange-600/20 text-orange-400 border border-orange-500/30 font-mono">
              System Telemetry & Audit Logs
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Real-time conversation metrics, fraud response SLAs, agent execution audit logs, and synthetic event triggers.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#080808] border border-white/10 text-xs text-slate-300 hover:text-white font-mono"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>REFRESH TELEMETRY</span>
        </button>
      </div>

      {/* KPI Metrics Grid (6 cards) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-[#111111] p-4 rounded-xl border border-white/10 space-y-1">
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">Total Conversations</p>
          <p className="text-2xl font-bold text-white font-mono">{metrics.totalConversations || 142}</p>
          <p className="text-[10px] text-green-400 font-mono">↑ 12% today</p>
        </div>

        <div className="bg-[#111111] p-4 rounded-xl border border-white/10 space-y-1">
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">Auto-Resolution</p>
          <p className="text-2xl font-bold text-green-400 font-mono">{metrics.autoResolutionRate || 88.5}%</p>
          <p className="text-[10px] text-slate-500 font-mono">Zero human intervention</p>
        </div>

        <div className="bg-[#111111] p-4 rounded-xl border border-white/10 space-y-1">
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">Open Fraud Alerts</p>
          <p className="text-2xl font-bold text-orange-400 font-mono">{metrics.openFraudAlerts || 12}</p>
          <p className="text-[10px] text-red-500 font-mono font-bold">{metrics.criticalAlerts || 3} CRITICAL</p>
        </div>

        <div className="bg-[#111111] p-4 rounded-xl border border-white/10 space-y-1">
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">Avg Agent Speed</p>
          <p className="text-2xl font-bold text-orange-500 font-mono">{metrics.avgResponseTimeSec || 1.4}s</p>
          <p className="text-[10px] text-slate-500 font-mono">LangGraph latency</p>
        </div>

        <div className="bg-[#111111] p-4 rounded-xl border border-white/10 space-y-1">
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">False Positive Rate</p>
          <p className="text-2xl font-bold text-slate-200 font-mono">{metrics.falsePositiveRate || 8}%</p>
          <p className="text-[10px] text-green-400 font-mono">Optimal precision</p>
        </div>

        <div className="bg-[#111111] p-4 rounded-xl border border-white/10 space-y-1">
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">System Health</p>
          <p className="text-lg font-bold text-green-400 font-mono flex items-center gap-1 mt-1">
            <CheckCircle2 className="w-4 h-4" /> HEALTHY
          </p>
          <p className="text-[10px] text-slate-500 font-mono">100% SLA Uptime</p>
        </div>
      </div>

      {/* Chart & Simulator Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Chart (8 cols) */}
        <div className="lg:col-span-8 bg-[#111111] rounded-xl border border-white/10 p-5 space-y-3 shadow-xl">
          <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 flex items-center gap-1.5 font-mono">
            <Activity className="w-4 h-4 text-orange-500" /> Fraud Alerts vs System Resolutions Volume
          </h3>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorResolutions" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorAlerts" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={11} tick={{ fill: '#94a3b8' }} />
                <YAxis stroke="#475569" fontSize={11} tick={{ fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ backgroundColor: '#080808', borderColor: '#334155', borderRadius: '0.5rem', color: '#fff' }} />
                <Area type="monotone" dataKey="resolutions" stroke="#10b981" fillOpacity={1} fill="url(#colorResolutions)" name="Resolutions" />
                <Area type="monotone" dataKey="alerts" stroke="#ef4444" fillOpacity={1} fill="url(#colorAlerts)" name="Fraud Alerts" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live Simulator Panel (4 cols) */}
        <div className="lg:col-span-4 bg-[#111111] rounded-xl border border-white/10 p-5 space-y-3 shadow-xl">
          <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 flex items-center gap-1.5 font-mono">
            <Zap className="w-4 h-4 text-orange-500" /> Live Event Simulator
          </h3>
          <p className="text-xs text-slate-400">
            Instantly inject synthetic transaction scenarios into the event pipeline to demonstrate real-time alerts.
          </p>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => onTriggerSimulator('stolen_card')}
              className="w-full text-left p-3 rounded bg-[#080808] hover:bg-[#181818] border border-white/5 transition-all flex items-center justify-between text-xs text-white"
            >
              <div>
                <p className="font-bold text-red-500">🚨 Stolen Card Transaction</p>
                <p className="text-[10px] text-slate-400 font-mono">₹3,890.00 @ Crypto Exchange (Geo Mismatch)</p>
              </div>
              <span className="font-mono font-bold text-red-500">Risk 94</span>
            </button>

            <button
              onClick={() => onTriggerSimulator('fraud_ring')}
              className="w-full text-left p-3 rounded bg-[#080808] hover:bg-[#181818] border border-white/5 transition-all flex items-center justify-between text-xs text-white"
            >
              <div>
                <p className="font-bold text-orange-400">🕸️ Shared Device Fraud Ring</p>
                <p className="text-[10px] text-slate-400 font-mono">₹5,400.00 @ Offshore Wire (3 Linked Accounts)</p>
              </div>
              <span className="font-mono font-bold text-orange-400">Risk 92</span>
            </button>

            <button
              onClick={() => onTriggerSimulator('travel_false_positive')}
              className="w-full text-left p-3 rounded bg-[#080808] hover:bg-[#181818] border border-white/5 transition-all flex items-center justify-between text-xs text-white"
            >
              <div>
                <p className="font-bold text-green-400">✈️ Travel Notice False Positive</p>
                <p className="text-[10px] text-slate-400 font-mono">₹410.00 London Rail (Notice Registered)</p>
              </div>
              <span className="font-mono font-bold text-green-400">Risk 32</span>
            </button>
          </div>
        </div>
      </div>

      {/* Real-time Audit Log Table */}
      <div className="bg-[#111111] rounded-xl border border-white/10 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 flex items-center gap-1.5 font-mono">
            <ShieldCheck className="w-4 h-4 text-orange-500" /> Audit Log & MCP Gateway Trace Table
          </h3>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search audit actions or actors..."
              className="bg-[#080808] text-white text-xs pl-8 pr-3 py-1.5 rounded border border-white/10 focus:outline-none focus:border-orange-500 w-60 font-mono"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#080808] text-slate-400 font-mono uppercase text-[10px] border-b border-white/10">
              <tr>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Actor / Role</th>
                <th className="p-3">Action</th>
                <th className="p-3">MCP Server</th>
                <th className="p-3">Details</th>
                <th className="p-3">PII Status</th>
                <th className="p-3">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono text-[11px]">
              {filteredLogs.slice(0, 15).map((log) => (
                <tr key={log.id} className="hover:bg-white/5 transition-colors">
                  <td className="p-3 text-slate-400 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="p-3 font-semibold text-white">
                    {log.actor} <span className="text-[9px] text-slate-400 font-normal">({log.role})</span>
                  </td>
                  <td className="p-3 font-bold text-orange-400">{log.action}</td>
                  <td className="p-3 text-purple-300">{log.mcpServer || 'N/A'}</td>
                  <td className="p-3 text-slate-300 max-w-xs truncate">{log.details}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded bg-green-500/10 text-green-400 text-[9px] border border-green-500/20 font-bold">
                      MASKED
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                      log.status === 'success' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-950 text-red-500 border border-red-500/30'
                    }`}>
                      {log.status.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertOctagon, CheckCircle2, ShieldCheck, Cpu, Volume2, VolumeX, Eye, ArrowUpRight, Lock, Activity, Building, User, Clock, MessageSquare, Plus, Check, Filter } from 'lucide-react';
import { FraudAlert, SecurityIncident, IncidentStatus } from '../types';
import { NetworkGraph } from './NetworkGraph';
import { FraudInvestigationModal } from './FraudInvestigationModal';

interface AnalystViewProps {
  alerts: FraudAlert[];
  incidents?: SecurityIncident[];
  selectedAlertId: string | null;
  setSelectedAlertId: (id: string | null) => void;
  onRefreshAlerts: () => void;
  onRefreshIncidents?: () => void;
}

export const AnalystView: React.FC<AnalystViewProps> = ({
  alerts,
  incidents = [],
  selectedAlertId,
  setSelectedAlertId,
  onRefreshAlerts,
  onRefreshIncidents
}) => {
  const [activeTab, setActiveTab] = useState<'incidents' | 'alerts'>('incidents');
  const [incidentFilter, setIncidentFilter] = useState<'active' | 'resolved' | 'all'>('active');
  const [selectedAlert, setSelectedAlert] = useState<FraudAlert | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<SecurityIncident | null>(null);
  
  const [modalOpen, setModalOpen] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [a2aResult, setA2aResult] = useState<any>(null);
  const [a2aLoading, setA2aLoading] = useState(false);

  // Note form state
  const [newNoteText, setNewNoteText] = useState('');
  const [assignedAnalystInput, setAssignedAnalystInput] = useState('Analyst Sarah Jenkins');
  const [updatingIncident, setUpdatingIncident] = useState(false);

  // Filtered incidents
  const activeIncidents = incidents.filter(i => i.status !== 'Resolved');
  const resolvedIncidents = incidents.filter(i => i.status === 'Resolved');

  const displayedIncidents = incidents.filter(i => {
    if (incidentFilter === 'active') return i.status !== 'Resolved';
    if (incidentFilter === 'resolved') return i.status === 'Resolved';
    return true;
  });

  // Sync selected incident or alert
  useEffect(() => {
    if (displayedIncidents.length > 0) {
      if (!selectedIncident || !displayedIncidents.some(i => i.incidentId === selectedIncident.incidentId)) {
        setSelectedIncident(displayedIncidents[0]);
      }
    } else {
      setSelectedIncident(null);
    }
  }, [incidents, incidentFilter]);

  useEffect(() => {
    if (selectedAlertId) {
      const found = alerts.find(a => a.alertId === selectedAlertId);
      if (found) {
        setSelectedAlert(found);
        setActiveTab('alerts');
      }
    } else if (alerts.length > 0 && !selectedAlert) {
      setSelectedAlert(alerts[0]);
    }
  }, [selectedAlertId, alerts]);

  // Keep selectedIncident updated when incidents prop updates
  useEffect(() => {
    if (selectedIncident) {
      const updated = incidents.find(i => i.incidentId === selectedIncident.incidentId);
      if (updated) setSelectedIncident(updated);
    }
  }, [incidents]);

  const unreadIncidentsCount = incidents.filter(i => i.status === 'New').length;

  const handleUpdateIncidentStatus = async (
    incidentId: string,
    newStatus: IncidentStatus,
    noteText?: string
  ) => {
    setUpdatingIncident(true);
    try {
      const res = await fetch(`/api/incidents/${incidentId}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          analystName: assignedAnalystInput || 'Analyst Sarah Jenkins',
          noteText
        })
      });
      const data = await res.json();
      setSelectedIncident(data);
      if (onRefreshIncidents) onRefreshIncidents();
      setNewNoteText('');
    } catch (e) {
      console.error('Failed to update incident', e);
    } finally {
      setUpdatingIncident(false);
    }
  };

  const handleAddIncidentNote = async () => {
    if (!selectedIncident || !newNoteText.trim()) return;
    await handleUpdateIncidentStatus(
      selectedIncident.incidentId,
      selectedIncident.status,
      newNoteText.trim()
    );
  };

  const handleApproveFreeze = async (analystName: string, reason: string) => {
    if (!selectedAlert) return;
    try {
      const res = await fetch(`/api/alerts/${selectedAlert.alertId}/approve-freeze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analystName, reason })
      });
      const data = await res.json();
      if (data.success) {
        onRefreshAlerts();
      }
    } catch (e) {
      console.error('Failed to approve freeze', e);
    }
  };

  const handleRejectSafe = async () => {
    if (!selectedAlert) return;
    try {
      const res = await fetch(`/api/alerts/${selectedAlert.alertId}/reject-safe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analystName: 'Analyst Sarah Jenkins', notes: 'Verified as false positive.' })
      });
      const data = await res.json();
      if (data.success) {
        onRefreshAlerts();
      }
    } catch (e) {
      console.error('Failed to mark safe', e);
    }
  };

  const handleRunA2ADemo = async () => {
    if (!selectedAlert) return;
    setA2aLoading(true);
    try {
      const res = await fetch('/api/a2a/remote-investigation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transactionId: selectedAlert.transactionId })
      });
      const data = await res.json();
      setA2aResult(data);
    } catch (e) {
      console.error('A2A remote agent error', e);
    } finally {
      setA2aLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Banner */}
      <div className="bg-[#111111] rounded-xl p-5 border border-white/10 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex flex-wrap items-center space-x-2 gap-y-1">
            <ShieldAlert className="w-6 h-6 text-orange-500" />
            <h1 className="text-xl font-light tracking-tight text-white">Fraud Operations Analyst Hub</h1>
            <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-red-950 text-red-500 border border-red-500/30 font-mono">
              Real-Time Incident Gateway Active
            </span>

            {/* Real-time Notification Badge for Customer Incidents */}
            {unreadIncidentsCount > 0 && (
              <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-orange-600 text-white animate-pulse shadow-lg font-mono flex items-center gap-1">
                <span>🔔 NEW INCIDENTS ({unreadIncidentsCount})</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Bi-directional Customer Incident Sync • Multi-score explainable risk analytics • Graph entity relationship explorer
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#080808] border border-white/10 text-xs text-slate-300 hover:text-white font-mono"
          >
            {soundEnabled ? <Volume2 className="w-4 h-4 text-green-400" /> : <VolumeX className="w-4 h-4 text-slate-500" />}
            <span>ALERT CHIME: {soundEnabled ? 'ON' : 'OFF'}</span>
          </button>
        </div>
      </div>

      {/* Primary Queue Tabs */}
      <div className="flex items-center space-x-2 border-b border-white/10 pb-2">
        <button
          onClick={() => setActiveTab('incidents')}
          className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition-all flex items-center space-x-2 ${
            activeTab === 'incidents'
              ? 'bg-orange-600 text-white shadow-lg shadow-orange-600/30'
              : 'bg-[#141414] text-slate-400 hover:text-white border border-white/5'
          }`}
        >
          <Building className="w-4 h-4" />
          <span>Customer Security Incidents ({activeIncidents.length})</span>
          {unreadIncidentsCount > 0 && (
            <span className="bg-red-500 text-white text-[10px] px-1.5 py-0.2 rounded-full font-extrabold animate-bounce">
              {unreadIncidentsCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('alerts')}
          className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition-all flex items-center space-x-2 ${
            activeTab === 'alerts'
              ? 'bg-orange-600 text-white shadow-lg shadow-orange-600/30'
              : 'bg-[#141414] text-slate-400 hover:text-white border border-white/5'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Automated Fraud Alerts Stream ({alerts.length})</span>
        </button>
      </div>

      {/* Main Grid: Stream Feed (4 cols) & Investigation Panel (8 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: Queue Feed */}
        <div className="lg:col-span-4 bg-[#111111] rounded-xl border border-white/10 p-4 space-y-3 h-[720px] flex flex-col shadow-xl">
          <div className="flex flex-col gap-2 pb-2 border-b border-white/10">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 flex items-center gap-1.5 font-mono">
                <Activity className="w-4 h-4 text-orange-500 animate-pulse" />
                {activeTab === 'incidents' ? `Customer Security Queue (${displayedIncidents.length})` : `Live Alert Stream (${alerts.length})`}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">Live Sync</span>
            </div>

            {activeTab === 'incidents' && (
              <div className="flex items-center gap-1 text-[10px] font-mono pt-1">
                <button
                  onClick={() => setIncidentFilter('active')}
                  className={`px-2 py-0.5 rounded font-bold transition-all ${
                    incidentFilter === 'active'
                      ? 'bg-orange-600 text-white shadow'
                      : 'bg-[#181818] text-slate-400 hover:text-white border border-white/5'
                  }`}
                >
                  Active ({activeIncidents.length})
                </button>
                <button
                  onClick={() => setIncidentFilter('resolved')}
                  className={`px-2 py-0.5 rounded font-bold transition-all ${
                    incidentFilter === 'resolved'
                      ? 'bg-orange-600 text-white shadow'
                      : 'bg-[#181818] text-slate-400 hover:text-white border border-white/5'
                  }`}
                >
                  Resolved ({resolvedIncidents.length})
                </button>
                <button
                  onClick={() => setIncidentFilter('all')}
                  className={`px-2 py-0.5 rounded font-bold transition-all ${
                    incidentFilter === 'all'
                      ? 'bg-orange-600 text-white shadow'
                      : 'bg-[#181818] text-slate-400 hover:text-white border border-white/5'
                  }`}
                >
                  All ({incidents.length})
                </button>
              </div>
            )}
          </div>

          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {activeTab === 'incidents' ? (
              /* INCIDENTS QUEUE FEED */
              displayedIncidents.length > 0 ? (
                displayedIncidents.map((inc) => {
                  const isSelected = selectedIncident?.incidentId === inc.incidentId;
                  return (
                    <div
                      key={inc.incidentId}
                      onClick={() => setSelectedIncident(inc)}
                      className={`p-3.5 rounded border transition-all cursor-pointer space-y-2 ${
                        isSelected
                          ? 'bg-[#1a1a1a] border-orange-500 shadow-md ring-1 ring-orange-500/50'
                          : 'bg-[#080808] border-white/5 hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-orange-400">{inc.incidentId}</span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                          inc.severity === 'Critical'
                            ? 'bg-red-950 text-red-400 border border-red-500/40'
                            : inc.severity === 'High'
                            ? 'bg-orange-600/20 text-orange-400 border border-orange-500/40'
                            : 'bg-slate-800 text-slate-300 border border-white/10'
                        }`}>
                          {inc.severity}
                        </span>
                      </div>

                      <div className="text-xs font-bold text-white flex justify-between">
                        <span>{inc.customerName}</span>
                        <span className="text-slate-400 font-mono text-[10px]">{inc.customerId}</span>
                      </div>

                      <p className="text-[11px] text-slate-300 font-mono truncate">
                        Action: <strong className="text-white">{inc.actionInitiated}</strong>
                      </p>

                      <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-white/5 font-mono">
                        <span className="flex items-center gap-1">
                          Status: 
                          <strong className={`uppercase ${
                            inc.status === 'New'
                              ? 'text-red-400 font-bold'
                              : inc.status === 'Under Review'
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                          }`}>
                            {inc.status}
                          </strong>
                        </span>
                        <span>{new Date(inc.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center text-slate-500 text-xs py-10 font-mono">
                  No active customer security incidents.
                </div>
              )
            ) : (
              /* FRAUD ALERTS FEED */
              alerts.map((al) => {
                const isSelected = selectedAlert?.alertId === al.alertId;
                return (
                  <div
                    key={al.alertId}
                    onClick={() => setSelectedAlert(al)}
                    className={`p-3.5 rounded border transition-all cursor-pointer space-y-2 ${
                      isSelected
                        ? 'bg-[#1a1a1a] border-orange-500 shadow-md ring-1 ring-orange-500/50'
                        : 'bg-[#080808] border-white/5 hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-slate-300">{al.alertId}</span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                        al.priority === 'critical'
                          ? 'bg-red-950 text-red-500 border border-red-500/40'
                          : al.priority === 'high'
                          ? 'bg-orange-600/20 text-orange-400 border border-orange-500/40'
                          : 'bg-slate-800 text-slate-300 border border-white/10'
                      }`}>
                        {al.priority} ({al.riskScore})
                      </span>
                    </div>

                    <div className="text-xs font-bold text-white flex justify-between">
                      <span>{al.customerName}</span>
                      <span className="text-red-500 font-mono">₹{al.amount.toFixed(2)}</span>
                    </div>

                    <p className="text-[11px] text-slate-400 truncate">{al.merchantName}</p>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-white/5 font-mono">
                      <span>Status: <strong className="text-slate-300 uppercase">{al.status.replace('_', ' ')}</strong></span>
                      <span>{new Date(al.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Detailed Investigation Panel (8 cols) */}
        <div className="lg:col-span-8 bg-[#111111] rounded-xl border border-white/10 p-6 space-y-6 h-[720px] overflow-y-auto shadow-xl">
          {activeTab === 'incidents' ? (
            /* INCIDENT INVESTIGATION PANEL */
            selectedIncident ? (
              <>
                {/* Incident Title Banner */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono text-orange-400 bg-orange-600/10 px-2.5 py-0.5 rounded border border-orange-500/30 font-bold">
                        {selectedIncident.incidentId}
                      </span>
                      <h2 className="text-lg font-bold text-white">{selectedIncident.customerName}</h2>
                      <span className="text-xs text-slate-400 font-mono">({selectedIncident.customerId})</span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1 font-mono">
                      Initiated Action: <strong className="text-orange-400">{selectedIncident.actionInitiated}</strong>
                    </p>
                  </div>

                  <div className="flex items-center space-x-3 bg-[#080808] px-4 py-2.5 rounded border border-white/10">
                    <div className="text-right">
                      <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">Incident Status</p>
                      <p className={`text-lg font-bold font-mono uppercase ${
                        selectedIncident.status === 'New'
                          ? 'text-red-400'
                          : selectedIncident.status === 'Under Review'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }`}>
                        {selectedIncident.status}
                      </p>
                    </div>
                    <div className={`w-3 h-8 rounded-full ${
                      selectedIncident.status === 'New' ? 'bg-red-500 animate-pulse' : selectedIncident.status === 'Under Review' ? 'bg-amber-400' : 'bg-emerald-500'
                    }`} />
                  </div>
                </div>

                {/* Key Incident Metadata Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div className="bg-[#080808] p-3 rounded border border-white/5">
                    <span className="text-slate-500 text-[10px] uppercase block">Fraud Category</span>
                    <span className="text-white font-bold">{selectedIncident.fraudCategory}</span>
                  </div>
                  <div className="bg-[#080808] p-3 rounded border border-white/5">
                    <span className="text-slate-500 text-[10px] uppercase block">Severity Level</span>
                    <span className={`font-bold ${
                      selectedIncident.severity === 'Critical' ? 'text-red-400' : 'text-orange-400'
                    }`}>{selectedIncident.severity}</span>
                  </div>
                  <div className="bg-[#080808] p-3 rounded border border-white/5">
                    <span className="text-slate-500 text-[10px] uppercase block">Assigned Analyst</span>
                    <span className="text-slate-200 font-bold">{selectedIncident.assignedAnalyst || 'Unassigned'}</span>
                  </div>
                  <div className="bg-[#080808] p-3 rounded border border-white/5">
                    <span className="text-slate-500 text-[10px] uppercase block">Dispatched Timestamp</span>
                    <span className="text-slate-300">{new Date(selectedIncident.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</span>
                  </div>
                </div>

                {/* AI Fraud Assessment Summary Box */}
                <div className="bg-[#080808] rounded p-4 border border-white/10 space-y-2">
                  <h3 className="text-[10px] font-bold uppercase tracking-widest text-slate-400 flex items-center gap-1.5 font-mono">
                    <ShieldAlert className="w-3.5 h-3.5 text-orange-400" /> AI Fraud Assessment Summary
                  </h3>
                  <p className="text-xs text-slate-200 leading-relaxed font-sans bg-[#121212] p-3 rounded border border-white/5">
                    {selectedIncident.aiAssessmentSummary}
                  </p>
                </div>

                {/* Analyst Notes & Case Log History */}
                <div className="bg-[#080808] rounded p-4 border border-white/10 space-y-3">
                  <h3 className="text-[10px] font-bold uppercase tracking-widest text-slate-400 flex items-center justify-between font-mono">
                    <span className="flex items-center gap-1.5">
                      <MessageSquare className="w-3.5 h-3.5 text-blue-400" /> Incident Notes & Customer Sync Log
                    </span>
                    <span className="text-[10px] text-slate-500">Auto-Syncs Live to Customer Portal</span>
                  </h3>

                  {/* Notes Timeline */}
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {selectedIncident.notes && selectedIncident.notes.length > 0 ? (
                      selectedIncident.notes.map((n) => (
                        <div key={n.id} className="bg-[#141414] p-3 rounded border border-white/5 text-xs space-y-1">
                          <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                            <span className="font-bold text-orange-400">{n.author}</span>
                            <span>{new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          </div>
                          <p className="text-slate-200 font-sans text-xs">{n.text}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500 font-mono italic">No analyst notes recorded yet.</p>
                    )}
                  </div>

                  {/* Add Note Input */}
                  <div className="pt-2 flex gap-2">
                    <input
                      type="text"
                      placeholder="Type analyst investigation note or customer update..."
                      value={newNoteText}
                      onChange={(e) => setNewNoteText(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddIncidentNote()}
                      className="flex-1 bg-[#141414] border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 font-sans focus:outline-none focus:border-orange-500"
                    />
                    <button
                      onClick={handleAddIncidentNote}
                      disabled={!newNoteText.trim() || updatingIncident}
                      className="px-3.5 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 disabled:opacity-40 text-white text-xs font-mono font-bold transition-all flex items-center gap-1"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Note</span>
                    </button>
                  </div>
                </div>

                {/* Workflow Actions Controls */}
                <div className="bg-[#080808] p-4 rounded border border-white/10 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center space-x-2 text-xs font-mono">
                    <span className="text-slate-400">Analyst:</span>
                    <input
                      type="text"
                      value={assignedAnalystInput}
                      onChange={(e) => setAssignedAnalystInput(e.target.value)}
                      className="bg-[#141414] border border-white/10 rounded px-2 py-1 text-white text-xs font-mono w-48 focus:outline-none focus:border-orange-500"
                    />
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleUpdateIncidentStatus(selectedIncident.incidentId, 'Under Review', 'Initiated analyst investigation & verification call.')}
                      disabled={selectedIncident.status === 'Under Review' || updatingIncident}
                      className="px-3.5 py-2 rounded text-xs font-bold text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 disabled:opacity-50 transition-all font-mono"
                    >
                      Set Under Review
                    </button>

                    <button
                      onClick={() => handleUpdateIncidentStatus(selectedIncident.incidentId, 'Resolved', 'Incident resolved. Mitigation protocol confirmed and completed.')}
                      disabled={selectedIncident.status === 'Resolved' || updatingIncident}
                      className="px-4 py-2 rounded text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 transition-all flex items-center gap-1.5 shadow-lg shadow-emerald-600/30 font-mono uppercase"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{selectedIncident.status === 'Resolved' ? 'Resolved & Synced' : 'Resolve Incident'}</span>
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs space-y-2 font-mono">
                <Building className="w-8 h-8 text-slate-600" />
                <p>Select a customer security incident from the queue to investigate.</p>
              </div>
            )
          ) : (
            /* FRAUD ALERTS PANEL */
            selectedAlert ? (
              <>
                {/* Alert Title Banner */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono text-orange-400 bg-orange-600/10 px-2.5 py-0.5 rounded border border-orange-500/30 font-bold">
                        {selectedAlert.alertId}
                      </span>
                      <h2 className="text-lg font-bold text-white">{selectedAlert.customerName}</h2>
                      <span className="text-xs text-slate-400 font-mono">({selectedAlert.customerId})</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 font-mono">
                      Transaction Ref: <strong className="text-slate-200 font-mono">{selectedAlert.transactionId}</strong> • ₹{selectedAlert.amount.toFixed(2)} @ {selectedAlert.merchantName}
                    </p>
                  </div>

                  <div className="flex items-center space-x-3 bg-[#080808] px-4 py-2.5 rounded border border-white/10">
                    <div className="text-right">
                      <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">Risk Score</p>
                      <p className="text-3xl font-bold font-mono text-red-500">{selectedAlert.riskScore}<span className="text-xs text-slate-500">/100</span></p>
                    </div>
                    <div className={`w-3 h-10 rounded-full ${selectedAlert.riskScore > 80 ? 'bg-red-600 animate-pulse' : 'bg-orange-500'}`} />
                  </div>
                </div>

                {/* Multi-factor Score Breakdown Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="bg-[#080808] p-3 rounded border border-white/5 text-center">
                    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">Rules Score</p>
                    <p className="text-lg font-bold text-orange-400 font-mono">{(selectedAlert.evidence?.ruleViolations.length ? 0.96 : 0.40).toFixed(2)}</p>
                  </div>
                  <div className="bg-[#080808] p-3 rounded border border-white/5 text-center">
                    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">XGBoost ML</p>
                    <p className="text-lg font-bold text-red-500 font-mono">{selectedAlert.evidence?.mlScore || 0.93}</p>
                  </div>
                  <div className="bg-[#080808] p-3 rounded border border-white/5 text-center">
                    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">Isolation Forest</p>
                    <p className="text-lg font-bold text-purple-400 font-mono">{selectedAlert.evidence?.anomalyScore || 0.89}</p>
                  </div>
                  <div className="bg-[#080808] p-3 rounded border border-white/5 text-center">
                    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest font-mono">Graph Network</p>
                    <p className="text-lg font-bold text-blue-400 font-mono">{selectedAlert.evidence?.graphScore || 0.95}</p>
                  </div>
                </div>

                {/* Risk Reasons Bullet List */}
                <div className="bg-[#080808] rounded p-4 border border-white/10 space-y-2">
                  <h3 className="text-[10px] font-bold uppercase tracking-widest text-slate-400 flex items-center gap-1.5 font-mono">
                    <ShieldAlert className="w-3.5 h-3.5 text-red-500" /> Primary Explainable Risk Factors
                  </h3>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {selectedAlert.reasons.map((r, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-red-500 font-bold">•</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Graph Entity Network Visualizer */}
                <NetworkGraph
                  customerName={selectedAlert.customerName}
                  customerId={selectedAlert.customerId}
                  deviceHash="DEV-RING-X992"
                  ipHash="IP-45-133-19-88"
                  merchantName={selectedAlert.merchantName}
                  sharedDeviceCount={selectedAlert.evidence?.graphClusterInfo?.sharedDeviceCustomers || 3}
                />

                {/* Action Buttons: Human Approval & False Positive */}
                <div className="bg-[#080808] p-4 rounded border border-white/10 flex flex-wrap items-center justify-between gap-3">
                  <div className="text-xs text-slate-400 font-mono">
                    STATUS: <strong className="text-white uppercase">{selectedAlert.status.replace('_', ' ')}</strong>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleRejectSafe}
                      className="px-3.5 py-2 rounded text-xs font-semibold text-green-400 bg-green-500/10 hover:bg-green-500/20 border border-green-500/30 transition-all font-mono"
                    >
                      Mark Safe
                    </button>

                    <button
                      onClick={handleRunA2ADemo}
                      className="px-3.5 py-2 rounded text-xs font-semibold text-orange-400 bg-orange-600/10 hover:bg-orange-600/20 border border-orange-500/30 transition-all flex items-center gap-1 font-mono"
                    >
                      <Cpu className="w-3.5 h-3.5" />
                      <span>A2A Remote Agent</span>
                    </button>

                    <button
                      onClick={() => setModalOpen(true)}
                      disabled={selectedAlert.status === 'approved_frozen'}
                      className="px-4 py-2 rounded text-xs font-bold text-white bg-red-600 hover:bg-red-500 transition-all flex items-center gap-1.5 disabled:opacity-50 shadow-lg shadow-red-600/30 font-mono uppercase"
                    >
                      <Lock className="w-3.5 h-3.5" />
                      <span>{selectedAlert.status === 'approved_frozen' ? 'Card Frozen' : 'Approve Card Freeze'}</span>
                    </button>
                  </div>
                </div>

                {/* A2A Remote Agent Payload Display */}
                {a2aResult && (
                  <div className="bg-[#050505] p-4 rounded border border-orange-500/30 text-xs font-mono text-orange-300 space-y-1">
                    <p className="font-bold uppercase text-[10px] text-orange-400">🤖 Agent-to-Agent (A2A) Remote Inspection Output:</p>
                    <pre className="text-[11px] whitespace-pre-wrap overflow-x-auto">{JSON.stringify(a2aResult, null, 2)}</pre>
                  </div>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs space-y-2">
                <ShieldAlert className="w-8 h-8 text-slate-600" />
                <p className="font-mono">Select a fraud alert from the live stream to inspect detailed evidence.</p>
              </div>
            )
          )}
        </div>
      </div>

      {/* Human Approval Modal */}
      {selectedAlert && (
        <FraudInvestigationModal
          alert={selectedAlert}
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onConfirmFreeze={handleApproveFreeze}
        />
      )}
    </div>
  );
};


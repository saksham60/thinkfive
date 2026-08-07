import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { CustomerView } from './components/CustomerView';
import { AnalystView } from './components/AnalystView';
import { SupervisorView } from './components/SupervisorView';
import { ArchitectureView } from './components/ArchitectureView';
import { AIAgentsView, AgentId } from './components/AIAgentsView';
import { LoginScreen, AuthRole } from './components/LoginScreen';
import { UserRole, FraudAlert, SecurityIncident } from './types';

const AUTH_STORAGE_KEY = 'sentinel_auth_role';

export default function App() {
  const [authRole, setAuthRole] = useState<AuthRole | null>(() => {
    const saved = localStorage.getItem(AUTH_STORAGE_KEY);
    return (saved === 'customer' || saved === 'admin') ? (saved as AuthRole) : null;
  });

  const [activeTab, setActiveTab] = useState<'customer' | 'analyst' | 'agents' | 'supervisor' | 'architecture'>(() => {
    const savedRole = localStorage.getItem(AUTH_STORAGE_KEY);
    return savedRole === 'admin' ? 'analyst' : 'customer';
  });
  const [selectedAgentId, setSelectedAgentId] = useState<AgentId>('supervisor');
  const [userRole, setUserRole] = useState<UserRole>(() => {
    const savedRole = localStorage.getItem(AUTH_STORAGE_KEY);
    return savedRole === 'admin' ? 'analyst' : 'customer';
  });
  const [alerts, setAlerts] = useState<FraudAlert[]>([]);
  const [incidents, setIncidents] = useState<SecurityIncident[]>([]);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [customerSubTab, setCustomerSubTab] = useState<'concierge' | 'alerts' | 'activity'>('concierge');

  // Enforce Route Protection
  useEffect(() => {
    if (authRole === 'customer' && activeTab !== 'customer') {
      setActiveTab('customer');
      setUserRole('customer');
    } else if (authRole === 'admin' && activeTab === 'customer') {
      setActiveTab('analyst');
      setUserRole('analyst');
    }
  }, [authRole, activeTab]);

  const handleLoginSuccess = (role: AuthRole) => {
    setAuthRole(role);
    localStorage.setItem(AUTH_STORAGE_KEY, role);
    if (role === 'customer') {
      setActiveTab('customer');
      setUserRole('customer');
    } else {
      setActiveTab('analyst');
      setUserRole('analyst');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    setAuthRole(null);
    setActiveTab('customer');
    setUserRole('customer');
  };

  const handleSetActiveTabProtected = (tab: 'customer' | 'analyst' | 'agents' | 'supervisor' | 'architecture') => {
    if (tab === 'customer') {
      setAuthRole('customer');
      setUserRole('customer');
    } else {
      setAuthRole('admin');
      setUserRole('analyst');
    }
    setActiveTab(tab);
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch('/api/alerts');
      const data = await res.json();
      if (Array.isArray(data)) {
        setAlerts(data);
      }
    } catch (e) {
      console.error('Failed to fetch alerts', e);
    }
  };

  const fetchIncidents = async () => {
    try {
      const res = await fetch('/api/incidents');
      const data = await res.json();
      if (Array.isArray(data)) {
        setIncidents(data);
      }
    } catch (e) {
      console.error('Failed to fetch incidents', e);
    }
  };

  useEffect(() => {
    if (!authRole) return;

    fetchAlerts();
    fetchIncidents();

    // Setup WebSockets for real-time fraud alert & incident updates
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'INITIAL_STATE') {
            if (msg.alerts) setAlerts(msg.alerts);
            if (msg.incidents) setIncidents(msg.incidents);
          } else if (msg.type === 'NEW_FRAUD_ALERT' && msg.payload?.alert) {
            setAlerts(prev => [msg.payload.alert, ...prev.filter(a => a.alertId !== msg.payload.alert.alertId)]);
          } else if (msg.type === 'ALERT_UPDATED') {
            fetchAlerts();
          } else if (msg.type === 'NEW_INCIDENT' && msg.payload?.incident) {
            setIncidents(prev => [msg.payload.incident, ...prev.filter(i => i.incidentId !== msg.payload.incident.incidentId)]);
          } else if (msg.type === 'INCIDENT_UPDATED' && msg.payload?.incident) {
            setIncidents(prev => prev.map(i => i.incidentId === msg.payload.incident.incidentId ? msg.payload.incident : i));
            fetchIncidents();
          }
        } catch (err) {
          console.error('WebSocket parse error', err);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
      };
    } catch (e) {
      console.warn('WebSocket connection deferred', e);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [authRole]);

  const handleTriggerSimulator = async (scenario: string) => {
    if (authRole !== 'admin') return; // Event Simulator is Admin only

    try {
      const res = await fetch('/api/simulator/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenarioType: scenario })
      });
      const data = await res.json();
      if (data.result) {
        fetchAlerts();
        if (data.result.alertId) {
          setSelectedAlertId(data.result.alertId);
          if (scenario === 'stolen_card' || scenario === 'fraud_ring') {
            setActiveTab('analyst');
            setUserRole('analyst');
          }
        }
      }
    } catch (e) {
      console.error('Simulator trigger error', e);
    }
  };

  const handleResetSeedData = async () => {
    if (authRole !== 'admin') return;

    try {
      await fetch('/api/seed/reset', { method: 'POST' });
      fetchAlerts();
      alert('Synthetic Database successfully reset to initial demo seed state.');
    } catch (e) {
      console.error('Failed to reset seed data', e);
    }
  };

  const handleReportFraudTransaction = (txnId: string) => {
    // Direct analyst to investigate
    fetchAlerts();
  };

  // Render Login Screen if unauthenticated
  if (!authRole) {
    return <LoginScreen onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-slate-100 font-sans antialiased selection:bg-orange-600 selection:text-white flex flex-col md:flex-row">
      {/* Side Navigation Bar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={handleSetActiveTabProtected}
        customerSubTab={customerSubTab}
        onSelectCustomerSubTab={setCustomerSubTab}
        activeAlertsCount={alerts.filter(a => a.status === 'open').length}
        selectedAgentId={selectedAgentId}
        onSelectAgent={setSelectedAgentId}
        userRole={userRole}
        setUserRole={setUserRole}
        authRole={authRole}
        onLogout={handleLogout}
        wsConnected={wsConnected}
        onTriggerSimulator={handleTriggerSimulator}
        onResetSeedData={handleResetSeedData}
      />

      {/* Primary View Router */}
      <main className="flex-1 min-w-0 pb-12 overflow-y-auto">
        {authRole === 'customer' && activeTab === 'customer' && (
          <CustomerView
            alerts={alerts}
            incidents={incidents}
            onRefreshAlerts={fetchAlerts}
            onRefreshIncidents={fetchIncidents}
            onReportFraudTransaction={handleReportFraudTransaction}
            customerSubTab={customerSubTab}
            onSelectCustomerSubTab={setCustomerSubTab}
          />
        )}

        {authRole === 'admin' && activeTab === 'analyst' && (
          <AnalystView
            alerts={alerts}
            incidents={incidents}
            selectedAlertId={selectedAlertId}
            setSelectedAlertId={setSelectedAlertId}
            onRefreshAlerts={fetchAlerts}
            onRefreshIncidents={fetchIncidents}
          />
        )}

        {authRole === 'admin' && activeTab === 'agents' && (
          <AIAgentsView
            initialAgentId={selectedAgentId}
            onSelectAgent={setSelectedAgentId}
          />
        )}

        {authRole === 'admin' && activeTab === 'supervisor' && (
          <SupervisorView onTriggerSimulator={handleTriggerSimulator} />
        )}

        {authRole === 'admin' && activeTab === 'architecture' && (
          <ArchitectureView />
        )}
      </main>
    </div>
  );
}



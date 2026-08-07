import { useEffect, useState, type FormEvent } from 'react';
import { RefreshCw } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/app/hooks';
import { fetchAlerts } from '@/features/alerts/store/alertsThunks';
import { selectActiveFraudAlerts } from '@/features/alerts/store/alertsSelectors';
import { addCaseNote, fetchCases } from '@/features/cases/store/casesThunks';
import { caseSelectors } from '@/features/cases/store/casesSlice';
import { fetchApprovals, approveAction, rejectAction } from '@/features/approvals/store/approvalsThunks';
import { approvalSelectors } from '@/features/approvals/store/approvalsSlice';
import { EmptyState } from '@/components/EmptyState';

export function AnalystPage() {
  const dispatch = useAppDispatch();
  const alerts = useAppSelector(selectActiveFraudAlerts);
  const cases = useAppSelector(caseSelectors.selectAll);
  const approvals = useAppSelector(approvalSelectors.selectAll).filter((approval) => ['waiting', 'pending'].includes(approval.status));
  const [customerId, setCustomerId] = useState('demo_customer_001');
  const [selectedCase, setSelectedCase] = useState('');
  const [note, setNote] = useState('');

  const refresh = (target = customerId) => {
    void dispatch(fetchAlerts(target));
    void dispatch(fetchCases(target));
    void dispatch(fetchApprovals());
  };
  useEffect(() => { refresh('demo_customer_001'); }, [dispatch]);

  const query = (event: FormEvent) => { event.preventDefault(); refresh(); };
  const saveNote = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedCase || !note.trim()) return;
    await dispatch(addCaseNote({ id: selectedCase, body: note.trim() })).unwrap();
    setNote('');
  };

  return <div className="page"><header><p className="eyebrow">ANALYST WORKSPACE</p><h1>Security queue</h1><p>Investigate backend-authoritative alerts, cases, and approval requests.</p></header>
    <form className="toolbar" onSubmit={query}><label>Customer ID<input value={customerId} onChange={(event) => setCustomerId(event.target.value)} /></label><button><RefreshCw size={16} /> Refresh queue</button></form>
    <div className="columns"><section><h2>Fraud alerts <span>{alerts.length}</span></h2>{alerts.length ? alerts.map((alert) => <article className="list-row" key={alert.id}><div><strong>{alert.title}</strong><p>{alert.description}</p></div><span className={`badge ${alert.severity}`}>{alert.severity} · score {alert.riskScore}</span></article>) : <EmptyState title="Queue is clear" />}
      <h2>Cases <span>{cases.length}</span></h2>{cases.length ? cases.map((record) => <button className={`list-row selectable ${selectedCase === record.id ? 'selected' : ''}`} key={record.id} onClick={() => setSelectedCase(record.id)}><div><strong>{record.title}</strong><p>{record.id}</p></div><span className="badge">{record.status}</span></button>) : <EmptyState title="No cases found" />}
      {selectedCase && <form className="stack-form card" onSubmit={saveNote}><strong>Add investigation note</strong><textarea required value={note} onChange={(event) => setNote(event.target.value)} placeholder="Record evidence or next steps" /><button>Save note</button></form>}
    </section><section><h2>Pending approvals <span>{approvals.length}</span></h2>{approvals.map((approval) => <article className="card" key={approval.id}><strong>{approval.summary}</strong><p>{approval.caseId ? `Case ${approval.caseId}` : `Approval ${approval.id}`}</p><div className="actions"><button onClick={() => void dispatch(approveAction({ id: approval.id }))}>Approve</button><button className="secondary" onClick={() => void dispatch(rejectAction({ id: approval.id }))}>Reject</button></div></article>)}{!approvals.length && <EmptyState title="No approvals waiting" />}</section></div>
  </div>;
}

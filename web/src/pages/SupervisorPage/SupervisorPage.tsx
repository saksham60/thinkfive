import { useEffect, useState, type FormEvent } from 'react';
import { useAppDispatch, useAppSelector } from '@/app/hooks';
import { fetchSupervisorMetrics, fetchSupervisorRuns, runEvaluation, triggerSimulator } from '@/features/supervisor/store/supervisorThunks';
import { humanize } from '@/api/mappers';
import { LoadingState } from '@/components/LoadingState';
import { EmptyState } from '@/components/EmptyState';

export function SupervisorPage() {
  const dispatch = useAppDispatch();
  const { metrics, runs, status, simulatorStatus, evaluationStatus } = useAppSelector((state) => state.supervisor);
  const [customerId, setCustomerId] = useState('demo_customer_001');
  const [amount, setAmount] = useState('1250');
  const [description, setDescription] = useState('Controlled fraud simulation');
  useEffect(() => { void dispatch(fetchSupervisorMetrics()); void dispatch(fetchSupervisorRuns()); }, [dispatch]);
  const simulate = (event: FormEvent) => { event.preventDefault(); void dispatch(triggerSimulator({ customerId, amount: Number(amount), description })); };

  return <div className="page"><header><p className="eyebrow">SUPERVISOR</p><h1>Operations overview</h1><p>Live metrics and controlled test workflows from the backend.</p></header>
    {status === 'loading' ? <LoadingState /> : metrics ? <div className="grid metrics-grid">{Object.entries(metrics.runs).map(([key, value]) => <article className="card" key={key}><small>{humanize(key)}</small><h2>{value}</h2></article>)}<article className="card"><small>Waiting for human</small><h2>{metrics.waitingHitlCount}</h2></article><article className="card"><small>Event types</small><h2>{Object.keys(metrics.eventCounts).length}</h2></article></div> : <EmptyState title="Metrics unavailable" description="The backend has not returned supervisor metrics." />}
    <div className="columns"><section><h2>Recent runs</h2>{runs.length ? runs.map((run) => <article className="list-row" key={run.id}><div><strong>{run.id}</strong><p>{run.customerId || 'System run'}{run.startedAt ? ` · ${run.startedAt}` : ''}</p></div><span className="badge">{run.status}</span></article>) : <EmptyState title="No recent runs" />}</section>
      <section><h2>Simulator</h2><form className="stack-form card" onSubmit={simulate}><label>Customer ID<input value={customerId} onChange={(event) => setCustomerId(event.target.value)} /></label><label>Amount<input required min="0.01" step="0.01" type="number" value={amount} onChange={(event) => setAmount(event.target.value)} /></label><label>Description<input required value={description} onChange={(event) => setDescription(event.target.value)} /></label><button disabled={simulatorStatus === 'loading'}>{simulatorStatus === 'loading' ? 'Creating…' : 'Create synthetic transaction'}</button>{simulatorStatus === 'succeeded' && <p className="success">Transaction created in the configured banking provider.</p>}{simulatorStatus === 'failed' && <p className="form-error">Simulator request failed.</p>}</form>
        <h2>Evaluation</h2><div className="card"><p>Run the backend evaluation suite against current agent behavior.</p><button disabled={evaluationStatus === 'loading'} onClick={() => void dispatch(runEvaluation())}>{evaluationStatus === 'loading' ? 'Running…' : 'Run evaluation'}</button>{evaluationStatus === 'succeeded' && <p className="success">Evaluation complete.</p>}</div>
      </section></div>
  </div>;
}

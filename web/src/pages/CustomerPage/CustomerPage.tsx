import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { Send } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/app/hooks';
import { fetchCustomerDashboard } from '@/features/customer/store/customerThunks';
import { fetchAlerts } from '@/features/alerts/store/alertsThunks';
import { selectActiveFraudAlerts } from '@/features/alerts/store/alertsSelectors';
import { submitChatMessage } from '@/features/chat/store/chatThunks';
import { LoadingState } from '@/components/LoadingState';
import { ErrorState } from '@/components/ErrorState';
import { EmptyState } from '@/components/EmptyState';

const money = (amount: number, currency = 'USD') => {
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(amount); }
  catch { return `${currency} ${amount.toFixed(2)}`; }
};

export function CustomerPage() {
  const dispatch = useAppDispatch();
  const dashboard = useAppSelector((state) => state.customer);
  const alerts = useAppSelector(selectActiveFraudAlerts);
  const chat = useAppSelector((state) => state.chat);
  const [message, setMessage] = useState('');

  useEffect(() => {
    void dispatch(fetchCustomerDashboard());
    void dispatch(fetchAlerts(undefined));
  }, [dispatch]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const content = message.trim();
    if (!content) return;
    setMessage('');
    try {
      await dispatch(submitChatMessage({ message: content, conversationId: chat.conversationId || undefined })).unwrap();
    } catch {
      setMessage(content);
    }
  };

  const retry = () => void dispatch(fetchCustomerDashboard());
  return <Page title="Concierge" subtitle="Your accounts, activity, and security updates">
    {dashboard.status === 'loading' ? <LoadingState /> : dashboard.status === 'failed' ? <ErrorState message={dashboard.error || 'Unable to load dashboard'} onRetry={retry} /> : dashboard.data && <>
      <section className="grid metrics-grid">
        <article className="card"><small>Total balance</small><h2>{money(dashboard.data.totalBalance)}</h2><p>{dashboard.data.profile.displayName}</p></article>
        {dashboard.data.accounts.map((account) => <article className="card" key={account.id}><small>{account.name} · {account.maskedNumber}</small><h2>{money(account.balance, account.currency)}</h2></article>)}
      </section>
      <section><h2>Recent transactions</h2>{dashboard.data.recentTransactions.length ? <div className="data-list">{dashboard.data.recentTransactions.map((transaction) => <article className="list-row" key={transaction.id}><div><strong>{transaction.description}</strong><p>{transaction.category || 'Uncategorized'}{transaction.occurredAt ? ` · ${transaction.occurredAt}` : ''}</p></div><div className="align-right"><strong>{money(transaction.amount, transaction.currency)}</strong>{transaction.pending && <span className="badge">pending</span>}</div></article>)}</div> : <EmptyState title="No recent transactions" />}</section>
    </>}

    <div className="columns customer-lower">
      <section><h2>Security alerts <span>{alerts.length}</span></h2>{alerts.length ? alerts.map((alert) => <article className="list-row" key={alert.id}><div><strong>{alert.title}</strong><p>{alert.description}</p></div><span className={`badge ${alert.severity}`}>{alert.severity} · score {alert.riskScore}</span></article>) : <EmptyState title="No active alerts" description="New security updates will appear here." />}</section>
      <section><h2>Ask ThinkFive</h2><div className="chat-panel" aria-live="polite">{chat.messages.length ? chat.messages.map((item) => <div className={`chat-message ${item.role}`} key={item.id}><small>{item.role}</small><p>{item.content}</p></div>) : <p className="muted">Ask about an account, transaction, alert, or case.</p>}{chat.status === 'loading' && <p className="muted">The agent team is working…</p>}</div><form className="inline-form" onSubmit={submit}><input aria-label="Message" placeholder="How can you help?" value={message} onChange={(event) => setMessage(event.target.value)} /><button aria-label="Send message" disabled={chat.status === 'loading' || !message.trim()}><Send size={17} /></button></form>{chat.error && <p className="form-error">{chat.error}</p>}</section>
    </div>
  </Page>;
}

function Page({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return <div className="page"><header><p className="eyebrow">CUSTOMER</p><h1>{title}</h1><p>{subtitle}</p></header>{children}</div>;
}

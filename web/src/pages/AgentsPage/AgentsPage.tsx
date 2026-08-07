import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/app/hooks';
import { fetchMcpTools } from '@/features/system/store/systemThunks';
import { LoadingState } from '@/components/LoadingState';
import { ErrorState } from '@/components/ErrorState';

const descriptions: Record<string, string> = {
  banking: 'Accounts, transactions, cards, and sandbox operations.',
  fraud: 'Risk assessment, fraud alerts, and monitoring evidence.',
  case: 'Investigations, notes, approvals, and controlled actions.',
};

export function AgentsPage() {
  const dispatch = useAppDispatch();
  const { mcpTools, mcpStatus } = useAppSelector((state) => state.system);
  useEffect(() => { void dispatch(fetchMcpTools()); }, [dispatch]);
  return <div className="page"><header><p className="eyebrow">AGENT OPERATIONS</p><h1>Connected MCP capabilities</h1><p>These tools are discovered from the live backend and executed only by governed agents.</p></header>
    {mcpStatus === 'loading' ? <LoadingState label="Discovering MCP tools" /> : mcpStatus === 'failed' ? <ErrorState message="Unable to load MCP capabilities" onRetry={() => void dispatch(fetchMcpTools())} /> : <div className="grid">{(Object.entries(mcpTools || {}) as Array<[string, string[]]>).map(([service, tools]) => <article className="card agent" key={service}><span>{String(tools.length).padStart(2, '0')} TOOLS</span><h2>{service}</h2><p>{descriptions[service]}</p><div className="tool-list">{tools.map((tool) => <code key={tool}>{tool}</code>)}</div></article>)}</div>}
  </div>;
}

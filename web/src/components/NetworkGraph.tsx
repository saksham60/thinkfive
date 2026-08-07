import React from 'react';

interface NetworkGraphProps {
  customerName: string;
  customerId: string;
  deviceHash: string;
  ipHash: string;
  merchantName: string;
  sharedDeviceCount?: number;
}

export const NetworkGraph: React.FC<NetworkGraphProps> = ({
  customerName,
  customerId,
  deviceHash,
  ipHash,
  merchantName,
  sharedDeviceCount = 3
}) => {
  return (
    <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 relative overflow-hidden">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
          🕸️ Entity Graph Network Analysis
        </span>
        <span className="text-[10px] text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 font-mono">
          Shared Cluster Detected ({sharedDeviceCount} Customers)
        </span>
      </div>

      <svg className="w-full h-48" viewBox="0 0 500 200">
        {/* Connection Lines */}
        <line x1="250" y1="40" x2="120" y2="100" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 2" />
        <line x1="250" y1="40" x2="250" y2="100" stroke="#ef4444" strokeWidth="2.5" />
        <line x1="250" y1="40" x2="380" y2="100" stroke="#3b82f6" strokeWidth="2" />

        <line x1="250" y1="100" x2="180" y2="160" stroke="#ef4444" strokeWidth="2" />
        <line x1="250" y1="100" x2="320" y2="160" stroke="#f59e0b" strokeWidth="2" />

        {/* Center Top: Customer Node */}
        <g transform="translate(250, 40)">
          <circle r="22" fill="#1e293b" stroke="#3b82f6" strokeWidth="3" />
          <text textAnchor="middle" y="4" fill="#ffffff" fontSize="10" fontWeight="bold">Customer</text>
          <text textAnchor="middle" y="32" fill="#94a3b8" fontSize="8" fontFamily="monospace">{customerId}</text>
        </g>

        {/* Middle Left: Account */}
        <g transform="translate(120, 100)">
          <circle r="18" fill="#0f172a" stroke="#10b981" strokeWidth="2" />
          <text textAnchor="middle" y="3" fill="#ffffff" fontSize="9">Account</text>
        </g>

        {/* Middle Center: Device Node (High Risk Red) */}
        <g transform="translate(250, 100)">
          <circle r="22" fill="#450a0a" stroke="#ef4444" strokeWidth="3" className="animate-pulse" />
          <text textAnchor="middle" y="4" fill="#fca5a5" fontSize="9" fontWeight="bold">Shared Device</text>
          <text textAnchor="middle" y="34" fill="#ef4444" fontSize="8" fontFamily="monospace">RING-CLUSTER</text>
        </g>

        {/* Middle Right: Card */}
        <g transform="translate(380, 100)">
          <circle r="18" fill="#0f172a" stroke="#3b82f6" strokeWidth="2" />
          <text textAnchor="middle" y="3" fill="#ffffff" fontSize="9">Card 4832</text>
        </g>

        {/* Bottom Left: IP Address Node */}
        <g transform="translate(180, 160)">
          <circle r="18" fill="#450a0a" stroke="#ef4444" strokeWidth="2" />
          <text textAnchor="middle" y="3" fill="#ffffff" fontSize="8">IP Geo</text>
          <text textAnchor="middle" y="28" fill="#f87171" fontSize="7" fontFamily="monospace">Lagos, NG</text>
        </g>

        {/* Bottom Right: Merchant */}
        <g transform="translate(320, 160)">
          <circle r="18" fill="#1e1b4b" stroke="#6366f1" strokeWidth="2" />
          <text textAnchor="middle" y="3" fill="#ffffff" fontSize="8">Merchant</text>
        </g>
      </svg>
      <p className="text-[10px] text-slate-400 text-center font-mono mt-1">
        Graph Analysis: Shared device fingerprint connects Customer CUST-1001 with 2 other flagged accounts.
      </p>
    </div>
  );
};

import React, { useState } from 'react';
import { User, Shield, Lock, ArrowRight, AlertCircle, Eye, EyeOff, ShieldCheck, CheckCircle2 } from 'lucide-react';

export type AuthRole = 'customer' | 'admin';

interface LoginScreenProps {
  onLoginSuccess: (role: AuthRole) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLoginSuccess }) => {
  const [selectedRole, setSelectedRole] = useState<AuthRole | null>(null);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRoleSelect = (role: AuthRole) => {
    setSelectedRole(role);
    setPassword('');
    setError(null);
  };

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRole) return;

    setError(null);
    setIsSubmitting(true);

    setTimeout(() => {
      let isValid = false;
      if (selectedRole === 'customer' && password === 'customer123') {
        isValid = true;
      } else if (selectedRole === 'admin' && password === 'admin123') {
        isValid = true;
      }

      if (isValid) {
        onLoginSuccess(selectedRole);
      } else {
        setError(`Incorrect password for ${selectedRole === 'customer' ? 'Customer' : 'Admin'} role. Please try again.`);
        setIsSubmitting(false);
      }
    }, 300);
  };

  return (
    <div className="min-h-screen w-full bg-[#070707] text-slate-100 flex items-center justify-center p-4 relative overflow-hidden font-sans selection:bg-orange-600 selection:text-white">
      {/* Background Subtle Cyber Grids & Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(234,88,12,0.08)_0,transparent_65%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center space-y-3 mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-orange-600 rounded-xl font-extrabold text-2xl text-white shadow-xl shadow-orange-600/30 border border-orange-500/50">
            S
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white uppercase font-sans">
              SentinelBank <span className="text-orange-500">AI</span>
            </h1>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Autonomous Fraud Defense & Agent Governance System
            </p>
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-[#111111] border border-white/10 rounded-2xl p-6 md:p-8 shadow-2xl space-y-6 backdrop-blur-md">
          {!selectedRole ? (
            /* STEP 1: Select Role */
            <div className="space-y-5">
              <div className="text-center space-y-1">
                <h2 className="text-lg font-light text-white tracking-tight">System Portal Access</h2>
                <p className="text-xs text-slate-400 font-mono">
                  Select your authorization persona to continue
                </p>
              </div>

              <div className="grid grid-cols-1 gap-3.5 pt-2">
                {/* Customer Role Card */}
                <button
                  type="button"
                  onClick={() => handleRoleSelect('customer')}
                  className="w-full text-left p-4 rounded-xl bg-[#090909] hover:bg-[#161616] border border-white/10 hover:border-orange-500/50 transition-all duration-200 group flex items-center justify-between shadow-md"
                >
                  <div className="flex items-center space-x-3.5">
                    <div className="w-10 h-10 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <User className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm text-white group-hover:text-orange-400 transition-colors">
                          👤 Customer Portal
                        </span>
                        <span className="text-[10px] uppercase font-mono font-bold px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">
                          End-User
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 font-mono mt-0.5">
                        Account details, AI assistant chat, card status & fraud reporting
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-orange-400 group-hover:translate-x-1 transition-all flex-shrink-0" />
                </button>

                {/* Admin Role Card */}
                <button
                  type="button"
                  onClick={() => handleRoleSelect('admin')}
                  className="w-full text-left p-4 rounded-xl bg-[#090909] hover:bg-[#161616] border border-white/10 hover:border-orange-500/50 transition-all duration-200 group flex items-center justify-between shadow-md"
                >
                  <div className="flex items-center space-x-3.5">
                    <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-center group-hover:scale-105 transition-transform">
                      <Shield className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm text-white group-hover:text-orange-400 transition-colors">
                          🛡️ Admin Command Center
                        </span>
                        <span className="text-[10px] uppercase font-mono font-bold px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                          Full Access
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 font-mono mt-0.5">
                        Analyst hub, supervisor telemetry, agent evaluation & simulator
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-orange-400 group-hover:translate-x-1 transition-all flex-shrink-0" />
                </button>
              </div>

              {/* Demo Password Reference Pill */}
              <div className="p-3 rounded-lg bg-[#080808] border border-white/5 text-[11px] font-mono text-slate-400 text-center space-y-1">
                <p className="text-slate-500 uppercase font-bold text-[10px]">Demo Login Credentials</p>
                <div className="flex items-center justify-center space-x-4 text-slate-300">
                  <span>Customer: <code className="text-orange-400 font-bold">customer123</code></span>
                  <span>•</span>
                  <span>Admin: <code className="text-red-400 font-bold">admin123</code></span>
                </div>
              </div>
            </div>
          ) : (
            /* STEP 2: Password Verification Prompt */
            <form onSubmit={handleLoginSubmit} className="space-y-5">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <div className="flex items-center space-x-2">
                  {selectedRole === 'customer' ? (
                    <User className="w-5 h-5 text-orange-400" />
                  ) : (
                    <Shield className="w-5 h-5 text-red-400" />
                  )}
                  <h2 className="text-base font-bold text-white capitalize">
                    {selectedRole === 'customer' ? 'Customer Authentication' : 'Admin Security Access'}
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedRole(null);
                    setError(null);
                  }}
                  className="text-xs text-slate-400 hover:text-white font-mono underline"
                >
                  Change Role
                </button>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-950/80 border border-red-500/40 text-xs text-red-300 flex items-start space-x-2 font-mono animate-fadeIn">
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="block text-xs font-mono font-bold uppercase text-slate-300">
                  Enter Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={`Enter password (${selectedRole === 'customer' ? 'customer123' : 'admin123'})`}
                    required
                    autoFocus
                    className="w-full bg-[#080808] text-white text-sm pl-9 pr-10 py-2.5 rounded-lg border border-white/10 focus:outline-none focus:border-orange-500 font-mono placeholder:text-slate-600 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-[11px] text-slate-500 font-mono">
                  Demo Key: <code className="text-orange-400 font-bold">{selectedRole === 'customer' ? 'customer123' : 'admin123'}</code>
                </p>
              </div>

              <div className="pt-2 flex items-center space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedRole(null);
                    setError(null);
                  }}
                  className="w-1/3 py-2.5 px-3 rounded-lg text-xs font-mono font-bold text-slate-300 bg-[#080808] border border-white/10 hover:text-white transition-colors"
                >
                  BACK
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !password}
                  className="w-2/3 py-2.5 px-4 rounded-lg text-xs font-mono font-bold text-white bg-orange-600 hover:bg-orange-500 shadow-lg shadow-orange-600/30 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 uppercase"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>{isSubmitting ? 'VERIFYING...' : 'LOGIN TO PORTAL'}</span>
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer Legal / Version Note */}
        <p className="text-[11px] text-center text-slate-500 font-mono mt-6">
          SentinelBank AI Security Engine • 256-bit Encrypted Token Authentication
        </p>
      </div>
    </div>
  );
};

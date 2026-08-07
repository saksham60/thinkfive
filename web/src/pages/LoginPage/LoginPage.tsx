import { useState, type FormEvent } from 'react';
import { Navigate } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/app/hooks';
import { login } from '@/features/auth/store/authThunks';

export function LoginPage() {
  const dispatch = useAppDispatch();
  const { user, status, error } = useAppSelector((state) => state.auth);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  if (user) return <Navigate to={user.role === 'customer' ? '/customer' : '/analyst'} replace />;
  const submit = (event: FormEvent) => { event.preventDefault(); void dispatch(login({ email, password })); };
  return <section className="login-card"><ShieldCheck size={40}/><p className="eyebrow">THINKFIVE</p><h1>Fraud operations, coordinated.</h1><p>Sign in with your organization account. Access and roles are assigned by the backend session.</p><form onSubmit={submit}><label>Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="username"/></label><label>Password<input required type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password"/></label>{error && <p className="form-error" role="alert">{error}</p>}<button disabled={status === 'loading'}>{status === 'loading' ? 'Signing in…' : 'Sign in'}</button></form></section>;
}

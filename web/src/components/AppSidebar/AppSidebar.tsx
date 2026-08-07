import { Activity, AlertTriangle, Bot, LayoutDashboard, LogOut, Network, ShieldCheck } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/app/hooks';
import { logout } from '@/features/auth/store/authThunks';
import { ConnectionIndicator } from '../ConnectionIndicator';
import { ThemeToggle } from '../ThemeToggle';

const items = [['/customer','Concierge',Activity],['/analyst','Security queue',AlertTriangle],['/supervisor','Supervisor',LayoutDashboard],['/agents','Agents',Bot],['/architecture','Architecture',Network]] as const;

export function AppSidebar() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((state) => state.auth.user);
  return <aside className="sidebar"><div className="sidebar-top"><div className="brand"><ShieldCheck/><div><strong>ThinkFive</strong><small>Fraud operations</small></div></div><ThemeToggle/></div><nav>{items.map(([to,label,Icon]) => <NavLink key={to} to={to}><Icon size={18}/>{label}</NavLink>)}</nav><footer><ConnectionIndicator/><div className="user"><span>{user?.displayName}</span><small>{user?.role}</small></div><button className="icon-button" aria-label="Sign out" onClick={() => void dispatch(logout())}><LogOut size={18}/></button></footer></aside>;
}

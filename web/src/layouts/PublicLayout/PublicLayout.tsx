import { Outlet } from 'react-router-dom';
import { ThemeToggle } from '@/components/ThemeToggle';

export function PublicLayout() {
  return <main className="public-layout"><div className="public-theme-toggle"><ThemeToggle/></div><Outlet/></main>;
}

import{Outlet}from'react-router-dom';import{AppSidebar}from'@/components/AppSidebar';export function AuthenticatedLayout(){return <div className="app-shell"><AppSidebar/><main><Outlet/></main></div>}

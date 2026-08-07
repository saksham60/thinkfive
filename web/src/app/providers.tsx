import{useEffect,type ReactNode}from'react';import{Provider}from'react-redux';import{store}from'./store';import{restoreSession}from'@/features/auth/store/authThunks';import{useEventStream}from'@/hooks/useEventStream';
function Lifecycle({children}:{children:ReactNode}){useEventStream();useEffect(()=>{const promise=store.dispatch(restoreSession());return()=>promise.abort()},[]);return children}
export function AppProviders({children}:{children:ReactNode}){return <Provider store={store}><Lifecycle>{children}</Lifecycle></Provider>}

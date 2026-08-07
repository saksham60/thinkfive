import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/app/hooks';
import { connectEventStream } from '@/sse/client';
import { dispatchServerEvent } from '@/sse/handlers';
import { connectionChanged } from '@/features/system/store/systemSlice';

export function useEventStream() {
  const dispatch = useAppDispatch();
  const conversationId = useAppSelector((state) => state.chat.conversationId);
  useEffect(() => {
    if (!conversationId) {
      dispatch(connectionChanged('offline'));
      return;
    }
    dispatch(connectionChanged('connecting'));
    let opened = false;
    const stream = connectEventStream(
      conversationId,
      (event) => dispatchServerEvent(dispatch, event),
      () => { opened = true; dispatch(connectionChanged('live')); },
      () => dispatch(connectionChanged(opened ? 'reconnecting' : 'offline')),
    );
    return () => stream.close();
  }, [conversationId, dispatch]);
}

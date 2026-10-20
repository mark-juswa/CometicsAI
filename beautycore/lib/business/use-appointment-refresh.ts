'use client';
import { useEffect, useRef } from 'react';
// Refresh existing appointment reads when returning to the tab; no polling or realtime service.
export function useAppointmentRefresh(refresh: () => void) {
  const latest = useRef(refresh);
  latest.current = refresh;
  useEffect(() => {
    const focus = () => latest.current();
    const visible = () => {
      if (document.visibilityState === 'visible') latest.current();
    };
    window.addEventListener('focus', focus);
    document.addEventListener('visibilitychange', visible);
    return () => {
      window.removeEventListener('focus', focus);
      document.removeEventListener('visibilitychange', visible);
    };
  }, []);
}

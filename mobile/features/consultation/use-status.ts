import { useCallback, useEffect, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { useConsultationSession } from '../../store/consultation-session';
export function useConsultationStatus() {
  const active = useConsultationSession(s => s.active);
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [active]);
  useFocusEffect(useCallback(() => {
    if (active?.phase !== 'unknown') return;
    void useConsultationSession.getState().checkGeneration();
    // Reads only. The store never automatically repeats a GPU POST.
    const timer = setInterval(() => void useConsultationSession.getState().checkGeneration(), 5000);
    return () => clearInterval(timer);
  }, [active?.phase, active?.recommendationId]));
  return active ? Math.max(0, Math.floor((now - active.startedAt) / 1000)) : 0;
}

"use client";
import { useEffect, useRef } from "react";
// Visible pages refresh status changes made by staff or the backend worker.
export function useAppointmentRefresh(refresh: () => void) {
  const latest = useRef(refresh);
  latest.current = refresh;
  useEffect(() => {
    const focus = () => latest.current();
    const visible = () => {
      if (document.visibilityState === "visible") latest.current();
    };
    const timer=setInterval(visible,10000);
    window.addEventListener("focus", focus);
    window.addEventListener("appointments-updated", focus);
    document.addEventListener("visibilitychange", visible);
    return () => {
      clearInterval(timer);
      window.removeEventListener("focus", focus);
      window.removeEventListener("appointments-updated", focus);
      document.removeEventListener("visibilitychange", visible);
    };
  }, []);
}

"use client";
import { useEffect, useRef, useState } from "react";
// Native hash links also support opening an exact appointment in another tab.
export function useBookingTarget(
  rows: { id: string }[],
  onTarget: (id: string) => void,
) {
  const [target, setTarget] = useState(""),
    latest = useRef(onTarget),
    scrolled = useRef("");
  latest.current = onTarget;
  useEffect(() => {
    const select = (id: string) => {
      if (!/^[0-9a-f-]{36}$/i.test(id)) return;
      scrolled.current = "";
      setTarget(id);
      latest.current(id);
    };
    const hash = () => {
      const match = /^#booking-([0-9a-f-]{36})$/i.exec(window.location.hash);
      if (match) select(match[1]);
    };
    const notification = (event: Event) => {
      const id = (event as CustomEvent).detail;
      if (typeof id === "string") select(id);
    };
    hash();
    window.addEventListener("hashchange", hash);
    window.addEventListener("booking-notification-open", notification);
    return () => {
      window.removeEventListener("hashchange", hash);
      window.removeEventListener("booking-notification-open", notification);
    };
  }, []);
  useEffect(() => {
    if (
      !target ||
      scrolled.current === target ||
      !rows.some((row) => row.id === target)
    )
      return;
    const element = document.getElementById("booking-" + target);
    if (!element) return;
    const frame = window.requestAnimationFrame(() => {
      element.scrollIntoView?.({ block: "center" });
      scrolled.current = target;
    });
    return () => window.cancelAnimationFrame(frame);
  }, [target, rows]);
  return target;
}

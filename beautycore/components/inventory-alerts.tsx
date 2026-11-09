"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { businessRequest } from "../lib/business/client";
export function InventoryAlerts() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let active = true;
    const refresh = () => {
      if (document.visibilityState !== "visible") return;
      businessRequest("/api/inventory/summary")
        .then((d) => {
          if (active)
            setCount(
              Number(d.stats.low) +
                Number(d.stats.out) +
                Number(d.stats.expired) +
                Number(d.stats.expiring) +
                (d.servicesAtRisk?.length ?? 0) + (d.shortages?.length ?? 0),
            );
        })
        .catch(() => {});
    };
    refresh();
    const timer = setInterval(refresh, 30000);
    window.addEventListener("inventory-updated", refresh);
    window.addEventListener("focus", refresh);
    return () => {
      active = false;
      clearInterval(timer);
      window.removeEventListener("inventory-updated", refresh);
      window.removeEventListener("focus", refresh);
    };
  }, []);
  return count > 0 ? (
    <aside
      className="mb-5 rounded-lg border border-warning/30 bg-warning/5 p-3 text-sm text-warning"
      aria-label="Inventory attention"
    >
      <Link href="/admin/inventory?attention=1">
        Inventory needs attention: review stock, expiry dates and service
        supplies.
      </Link>
    </aside>
  ) : null;
}

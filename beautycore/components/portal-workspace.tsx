"use client";
import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { ArrowLeft, ArrowRight } from "lucide-react";
export function PortalWorkspace({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`portal-workspace ${className}`}>{children}</div>;
}
export function PortalMetrics({
  items,
}: {
  items: { label: string; value: ReactNode; note?: string; icon: LucideIcon }[];
}) {
  return (
    <div className="portal-metrics">
      {items.map((item) => (
        <div key={item.label} className="portal-metric">
          <div className="portal-metric-icon">
            <item.icon size={18} />
          </div>
          <p>{item.label}</p>
          <strong>{item.value}</strong>
          {item.note && <span>{item.note}</span>}
        </div>
      ))}
    </div>
  );
}
export function PortalPagination({
  page,
  pages,
  total,
  onChange,
}: {
  page: number;
  pages: number;
  total: number;
  onChange: (page: number) => void;
}) {
  return (
    <nav aria-label="Pagination" className="portal-pagination">
      <span>
        {total} results · Page {page} of {pages}
      </span>
      <div>
        <button
          className="portal-button"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          <ArrowLeft size={14} />
          Previous
        </button>
        <button
          className="portal-button"
          disabled={page >= pages}
          onClick={() => onChange(page + 1)}
        >
          Next
          <ArrowRight size={14} />
        </button>
      </div>
    </nav>
  );
}

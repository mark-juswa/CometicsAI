"use client";
import { PortalWorkspace } from "@/components/portal-workspace";

import { useState } from "react";
import { Package, AlertTriangle, Search, Scissors } from "lucide-react";
import { PageHeader, Card } from "@/components/ui";
import { serviceGroups } from "@/lib/services";

export default function StylistServicesPage() {
  const [active, setActive] = useState(serviceGroups[0].id);
  const [query, setQuery] = useState("");
  const group = serviceGroups.find((g) => g.id === active) ?? serviceGroups[0];

  const categories = group.categories
    .map((category) => ({
      ...category,
      items: category.items.filter((item) =>
        item.name.toLowerCase().includes(query.trim().toLowerCase()),
      ),
    }))
    .filter((category) => category.items.length);
  return (
    <PortalWorkspace>
      <header className="portal-hero">
        <div>
          <p className="portal-eyebrow">Your service reference</p>
          <h1>Service Menu</h1>
          <p>
            Explore the salon’s services and reference prices before discussing
            the final quote with your client.
          </p>
        </div>
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-gold/25 bg-gold/5 text-gold">
          <Scissors size={28} />
        </div>
      </header>
      <div className="service-reference-layout">
        <nav className="service-category-nav" aria-label="Service categories">
          <p className="portal-eyebrow">Categories</p>
          {serviceGroups.map((g) => (
            <button
              key={g.id}
              aria-pressed={active === g.id}
              onClick={() => {
                setActive(g.id);
                setQuery("");
              }}
            >
              <span>{g.label}</span>
              <span>
                {g.categories.reduce((sum, c) => sum + c.items.length, 0)}
              </span>
            </button>
          ))}
        </nav>
        <section>
          <div className="portal-panel">
            <div className="portal-panel-heading">
              <div>
                <h2>{group.label}</h2>
                <p>{group.sub}</p>
              </div>
              <span className="portal-pill">
                {categories.reduce((sum, c) => sum + c.items.length, 0)}{" "}
                services
              </span>
            </div>
            <div className="portal-inset">
              <p className="portal-help mb-5">{group.intro}</p>
              <label className="portal-search">
                <Search size={16} />
                <input
                  aria-label="Find a service"
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={"Search " + group.label.toLowerCase()}
                />
              </label>
            </div>
          </div>
          <div className="grid gap-5 xl:grid-cols-2">
            {categories.map((category) => (
              <section key={category.title} className="portal-panel">
                <div className="portal-panel-heading">
                  <h3 className="flex items-center gap-2 text-sm text-gold">
                    <Package size={15} />
                    {category.title}
                  </h3>
                </div>
                <ul className="portal-inset space-y-4">
                  {category.items.map((item) => (
                    <li
                      key={item.name}
                      className="flex items-start justify-between gap-5 border-b border-purple-light/10 pb-4 last:border-0 last:pb-0"
                    >
                      <span className="text-sm leading-relaxed text-secondary">
                        {item.name}
                      </span>
                      <span className="shrink-0 rounded-lg bg-gold/5 px-3 py-1.5 text-sm text-gold">
                        {item.price}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
          {!categories.length && (
            <p
              role="status"
              className="portal-panel portal-inset text-sm text-muted"
            >
              No services match this search in {group.label}.
            </p>
          )}
          <p className="portal-help flex items-start gap-3 rounded-xl border border-gold/20 bg-gold/5 p-5">
            <AlertTriangle size={18} className="shrink-0 text-gold" />
            <span>
              Prices marked <strong className="text-gold">Mula</strong> (from)
              vary with length, thickness, and condition. Confirm the final
              quote before starting the service.
            </span>
          </p>
        </section>
      </div>
    </PortalWorkspace>
  );
}

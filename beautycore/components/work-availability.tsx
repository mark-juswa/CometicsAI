"use client";
import { useEffect, useRef, useState } from "react";
import { businessRequest } from "@/lib/business/client";
type Hours = { day: number; start: string; end: string };
const days = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
];
export function WorkAvailability() {
  const [hours, setHours] = useState<Hours[]>([]),
    [available, setAvailable] = useState(false),
    [ready, setReady] = useState(false),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState("");
  const locked = useRef(false);
  useEffect(() => {
    let active = true;
    businessRequest("/api/stylist/availability")
      .then((d) => {
        if (active) {
          setHours(d.hours);
          setAvailable(d.available);
          setReady(true);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, []);
  async function save(nextAvailable = available) {
    if (locked.current) return;
    locked.current = true;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const d = await businessRequest("/api/stylist/availability", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ available: nextAvailable, hours }),
      });
      setHours(d.hours);
      setAvailable(d.available);
      setMessage(
        d.available
          ? "You are available for new bookings during your working hours."
          : "New bookings are paused. Your existing appointments remain on your schedule.",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save availability.");
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }
  return (
    <section
      className="work-availability-panel mb-6 rounded-2xl border border-purple-light/20 bg-card p-5 sm:p-6"
      aria-labelledby="work-availability-title"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="mb-2 text-[10px] uppercase tracking-[2px] text-gold">
            Booking preferences
          </p>
          <h2 id="work-availability-title" className="font-serif text-2xl">
            Work availability
          </h2>
          <p className="mt-2 max-w-xl text-sm text-muted">
            Working hours use Philippine time. Your schedule and existing
            bookings are checked before a new booking is confirmed.
          </p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={available}
          disabled={!ready || busy}
          onClick={() => void save(!available)}
          className={`inline-flex min-h-11 items-center gap-3 rounded-full border px-4 py-2 text-sm font-medium transition-colors ${available ? "border-success/40 bg-success/10 text-success" : "border-warning/40 bg-warning/10 text-warning"}`}
        >
          <span
            className={`h-3 w-3 rounded-full ${available ? "bg-success" : "bg-warning"}`}
          />
          {busy ? "Saving…" : available ? "Available to Work" : "Not Available"}
        </button>
      </div>
      {ready && (
        <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-purple-light/15 pt-4">
          <span className="mr-2 text-xs text-muted">Your working week</span>
          {days.map((name, day) => (
            <span
              key={day}
              className={`rounded-lg border px-3 py-2 text-xs ${hours.some((entry) => entry.day === day) ? "border-gold/20 bg-gold/5 text-gold" : "border-purple-light/10 text-muted"}`}
            >
              {name.slice(0, 3)}
              <span className="sr-only">
                {hours.some((entry) => entry.day === day)
                  ? " working day"
                  : " day off"}
              </span>
            </span>
          ))}
        </div>
      )}
      <fieldset disabled={!ready || busy}>
        <details className="mt-4 rounded-xl border border-purple-light/15 bg-deep/25 p-4">
          <summary className="cursor-pointer text-sm text-gold">
            Weekly working hours
          </summary>
          <p className="my-3 text-xs text-muted">
            Enable each working day and set its hours. Set a schedule before
            turning availability on.
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            {days.map((name, day) => {
              const entry = hours.find((row) => row.day === day);
              return (
                <div
                  key={day}
                  className="grid grid-cols-2 items-center gap-3 rounded-xl border border-purple-light/15 bg-card p-4 sm:grid-cols-[minmax(100px,1fr)_1fr_1fr]"
                >
                  <label className="col-span-2 flex items-center gap-2 text-sm sm:col-span-1">
                    <input
                      type="checkbox"
                      checked={!!entry}
                      onChange={(e) =>
                        setHours(
                          e.target.checked
                            ? [...hours, { day, start: "09:00", end: "17:00" }]
                            : hours.filter((row) => row.day !== day),
                        )
                      }
                    />
                    {name}
                  </label>
                  {entry ? (
                    <>
                      <label className="text-xs text-muted">
                        From
                        <input
                          aria-label={`${name} start`}
                          type="time"
                          required
                          value={entry.start}
                          onChange={(e) =>
                            setHours(
                              hours.map((row) =>
                                row.day === day
                                  ? { ...row, start: e.target.value }
                                  : row,
                              ),
                            )
                          }
                        />
                      </label>
                      <label className="text-xs text-muted">
                        Until
                        <input
                          aria-label={`${name} end`}
                          type="time"
                          required
                          value={entry.end}
                          onChange={(e) =>
                            setHours(
                              hours.map((row) =>
                                row.day === day
                                  ? { ...row, end: e.target.value }
                                  : row,
                              ),
                            )
                          }
                        />
                      </label>
                    </>
                  ) : (
                    <span className="col-span-2 text-xs text-muted">
                      Day off
                    </span>
                  )}
                </div>
              );
            })}
          </div>
          <button
            type="button"
            className="studio-primary-button mt-4"
            onClick={() => void save()}
          >
            Save working hours
          </button>
        </details>
      </fieldset>
      {!ready && !error && (
        <p role="status" className="mt-3 text-sm text-muted">
          Loading your availability…
        </p>
      )}
      {message && (
        <p role="status" className="mt-3 text-sm text-success">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="mt-3 text-sm text-error">
          {error}
        </p>
      )}
    </section>
  );
}

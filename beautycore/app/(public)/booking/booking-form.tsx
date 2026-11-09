"use client";
import { LookInformation } from "@/components/look-information";
import { featureFromType } from "@/lib/business/look-information";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import {
  businessRequest,
  savedGroup,
  type SavedLook,
} from "@/lib/business/client";
import { salonDay, salonDateTime } from "@/lib/business/dates";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  Calendar,
  Clock,
  User,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
  allServices,
  serviceGroups,
  parsePrice,
  type ServiceGroup,
} from "@/lib/services";

export default function BookingForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading: authLoading } = useAuth();

  const lookId = searchParams.get("look");
  const [look, setLook] = useState<SavedLook | null>(null);
  const [lookLoading, setLookLoading] = useState(!!lookId);
  const [lookError, setLookError] = useState("");
  const preselectedGroup = searchParams.get("service");
  const firstGroup = preselectedGroup
    ? serviceGroups.find((g) => g.id === preselectedGroup) || serviceGroups[0]
    : serviceGroups[0];

  const [catalog, setCatalog] = useState<
    ((typeof allServices)[number] & { id?: string })[]
  >([]);
  const [catalogError, setCatalogError] = useState("");
  useEffect(() => {
    const c = new AbortController();
    businessRequest("/api/services", { signal: c.signal })
      .then((d) => setCatalog(d.services))
      .catch((e) => {
        if (!c.signal.aborted) setCatalogError(e.message);
      });
    return () => c.abort();
  }, []);
  const [group, setGroup] = useState<ServiceGroup>(firstGroup);
  const [serviceName, setServiceName] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [stylistId, setStylistId] = useState("");
  const [notes, setNotes] = useState("");

  const [stylists, setStylists] = useState<Array<{ id: string; name: string }>>(
    [],
  );
  const [stylistsLoading, setStylistsLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [bookingStatus, setBookingStatus] = useState("");
  const [slots, setSlots] = useState<{ time: string; available: boolean }[]>(
      [],
    ),
    [slotsLoading, setSlotsLoading] = useState(false),
    [slotsError, setSlotsError] = useState(""),
    [slotRevision, setSlotRevision] = useState(0),
    [lookRevision, setLookRevision] = useState(0);
  const bookingLock = useRef(false);
  const redirectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (redirectTimer.current) clearTimeout(redirectTimer.current);
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({
      serviceType: group.serviceType,
      serviceName,
    });

    setStylistsLoading(true);
    fetch("/api/stylists?" + params, { signal: controller.signal })
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok)
          throw new Error(
            data.error || "Could not check stylist availability.",
          );
        if (!controller.signal.aborted) {
          const available = data.stylists || [];
          setStylists(available);
          setStylistId((current) =>
            current &&
            !available.some((stylist: { id: string }) => stylist.id === current)
              ? ""
              : current,
          );
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setStylists([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setStylistsLoading(false);
      });
    return () => controller.abort();
  }, [group.serviceType, serviceName]);

  useEffect(() => {
    const controller = new AbortController();
    setSlots([]);
    setSlotsError("");
    if (!date || !serviceName) {
      setSlotsLoading(false);
      return;
    }
    setSlotsLoading(true);
    const params = new URLSearchParams({ date, service: serviceName });
    const selected = catalog.find((s) => s.name === serviceName);
    if (selected?.id) params.set("serviceId", selected.id);
    if (stylistId) params.set("stylist", stylistId);
    businessRequest("/api/appointments/availability?" + params, {
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted) {
          setSlots(data.slots ?? []);
          setTime((current) =>
            current &&
            (data.slots ?? []).some(
              (slot: { time: string; available: boolean }) =>
                slot.time === current && slot.available,
            )
              ? current
              : "",
          );
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setSlotsError(cause.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setSlotsLoading(false);
      });
    return () => controller.abort();
  }, [date, serviceName, stylistId, slotRevision, catalog]);
  useEffect(() => {
    const refresh = () => setSlotRevision((value) => value + 1);
    const timer=setInterval(()=>{if(document.visibilityState==="visible")refresh();},10000);
    window.addEventListener("focus", refresh);
    window.addEventListener("appointments-updated", refresh);
    return () => {
      clearInterval(timer);
      window.removeEventListener("focus", refresh);
      window.removeEventListener("appointments-updated", refresh);
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLook(null);
    setLookError("");
    setLookLoading(!!lookId && !!user);
    if (!lookId || !user) return;
    businessRequest("/api/saved-looks/" + encodeURIComponent(lookId), {
      signal: controller.signal,
    })
      .then((data) => {
        if (controller.signal.aborted) return;
        setLook(data.look);
        const group = serviceGroups.find(
          (g) =>
            g.id ===
            (data.look.bookingService?.groupId ??
              savedGroup(data.look.styleType)),
        );
        if (group) {
          setGroup(group);
          setServiceName(data.look.bookingService?.name ?? "");
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setLookError(cause.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLookLoading(false);
      });
    return () => controller.abort();
  }, [lookId, user?.id, lookRevision]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (bookingLock.current) return;
    setError("");

    if (!user) {
      router.push(
        `/login?redirect=${encodeURIComponent("/booking" + (lookId ? "?look=" + encodeURIComponent(lookId) : ""))}`,
      );
      return;
    }

    if (lookId && (lookLoading || lookError || !look)) {
      setError(
        "Wait for your selected look to load, or retry loading it below.",
      );
      return;
    }
    if (!serviceName) {
      setError("Please choose the salon service for your look.");
      return;
    }
    if (
      slotsLoading ||
      slotsError ||
      !slots.some((slot) => slot.time === time && slot.available)
    ) {
      setError("Choose an available appointment time.");
      return;
    }
    if (!date || !time) {
      setError("Please select a date and time.");
      setLoading(false);
      return;
    }

    const appointmentDate = new Date(salonDateTime(date, time));
    if (appointmentDate.getTime() < Date.now()) {
      setError("Please choose a future date and time.");
      setLoading(false);
      return;
    }

    const selectedService = catalog.find((s) => s.name === serviceName);
    const totalPrice = selectedService
      ? parsePrice(selectedService.price)
      : null;

    bookingLock.current = true;
    setLoading(true);
    try {
      const data = await businessRequest("/api/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lookId: look?.id,
          serviceId: selectedService?.id,
          serviceName,
          serviceType: group.serviceType,
          appointmentDate: appointmentDate.toISOString(),
          stylistId: stylistId || undefined,
          totalPrice,
          notes: notes.trim() || undefined,
        }),
      });

      window.dispatchEvent(new Event("appointments-updated"));
      setBookingStatus(data.appointment?.status || "pending");
      setSuccess(true);
      redirectTimer.current = setTimeout(
        () => router.push("/client/appointments"),
        2000,
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not book your appointment.",
      );
      setSlotRevision((value) => value + 1);
    } finally {
      bookingLock.current = false;
      setLoading(false);
    }
  };

  const serviceOptions = catalog
    .filter((s) => s.groupId === group.id)
    .map((s) => ({ value: s.name, label: `${s.name} — ${s.price}` }));

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 size={24} className="animate-spin text-gold" />
      </div>
    );
  }

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <CheckCircle size={48} className="mx-auto mb-4 text-success" />
          <h2 className="mb-2 font-serif text-3xl text-white">
            {bookingStatus === "confirmed"
              ? "Appointment confirmed"
              : "Booking received"}
          </h2>
          {bookingStatus !== "confirmed" && (
            <p className="mb-3 text-sm text-secondary">
              Your booking is pending a stylist assignment and schedule
              confirmation.
            </p>
          )}
          <p className="text-muted">Redirecting you to your appointments…</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-6 py-12 lg:px-10">
      <div className="mx-auto max-w-2xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="mb-2 font-serif text-4xl text-white">
            Book an Appointment
          </h1>
          <p className="mb-8 text-[14px] text-secondary">
            Pick a service, choose a time, and we&apos;ll see you soon.
          </p>

          {lookId && !user && !authLoading && (
            <p className="business-panel">
              <a
                href={`/login?redirect=${encodeURIComponent(`/booking?look=${encodeURIComponent(lookId)}`)}`}
              >
                Sign in to view your selected look and finish booking.
              </a>
            </p>
          )}
          {lookLoading && <p role="status">Loading your selected look…</p>}
          {lookError && (
            <p role="alert" className="studio-alert">
              {lookError}{" "}
              <button
                type="button"
                className="underline"
                onClick={() => setLookRevision((value) => value + 1)}
              >
                Retry loading look
              </button>
            </p>
          )}
          {look && (
            <section className="business-panel mb-6">
              <h2>Booking with {look.styleName}</h2>
              <LookInformation
                saved
                feature={featureFromType(look.styleType)}
                styleId={look.styleId}
                details={look.lookDetails}
              />
              <div className="relative mt-3 h-56">
                <Image
                  src={look.imageUrl}
                  alt={look.styleName}
                  fill
                  unoptimized
                  className="object-contain"
                />
              </div>
              <p>
                This preview will be available to your assigned stylist. Choose
                the salon service below.
              </p>
            </section>
          )}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 flex items-start gap-2 rounded-sm border border-error/30 bg-error/10 p-4 text-[13px] text-error"
            >
              <AlertCircle size={16} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}

          {catalogError && <p role="alert">{catalogError}</p>}
          <form onSubmit={handleSubmit} className="glass rounded-sm p-6">
            {/* Category */}
            <div className="mb-5">
              <label className="mb-2 block text-[11px] font-medium text-secondary">
                Service Category
              </label>
              <div className="grid gap-2 sm:grid-cols-2">
                {serviceGroups.map((g) => (
                  <button
                    key={g.id}
                    type="button"

                    onClick={() => {
                      setGroup(g);
                      setServiceName("");
                      setTime("");
                      setStylistId("");
                    }}
                    className={`rounded-sm border px-4 py-2.5 text-left text-[13px] transition-colors ${
                      group.id === g.id
                        ? "border-gold/40 bg-gold/10 text-white"
                        : "border-purple-light/15 text-muted hover:border-purple-light/40"
                    }`}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Service */}
            <div className="mb-5">
              <label
                htmlFor="service"
                className="mb-2 block text-[11px] font-medium text-secondary"
              >
                Service
              </label>
              <select
                id="service"
                value={serviceName}
                onChange={(e) => {
                  setServiceName(e.target.value);
                  const selected = catalog.find(
                    (s) => s.name === e.target.value,
                  );
                  const category = serviceGroups.find(
                    (g) => g.id === selected?.groupId,
                  );
                  if (category) setGroup(category);
                  setTime("");
                  setStylistId("");
                }}
                required
                className="w-full rounded-sm border border-purple-light/20 bg-surface/40 px-4 py-2.5 text-[13px] text-white focus:border-purple-light focus:outline-none"
              >
                <option value="">Choose a service</option>
                {serviceOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {serviceName && (
              <p className="mb-5 text-sm text-secondary">
                {catalog.find((s) => s.name === serviceName)?.price}
              </p>
            )}
            {/* Stylist */}
            <div className="mb-5">
              <label
                htmlFor="stylist"
                className="mb-2 block text-[11px] font-medium text-secondary"
              >
                <User size={13} className="mr-1 inline" />
                Preferred Stylist (optional)
              </label>
              <select
                id="stylist"
                value={stylistId}
                onChange={(e) => {
                  setStylistId(e.target.value);
                  setTime("");
                }}
                className="w-full rounded-sm border border-purple-light/20 bg-surface/40 px-4 py-2.5 text-[13px] text-white focus:border-purple-light focus:outline-none"
              >
                <option value="">No preference</option>
                {stylistsLoading && (
                  <option disabled>Checking qualified stylists…</option>
                )}
                {!stylistsLoading && serviceName && stylists.length === 0 && (
                  <option disabled>
                    No qualified stylists available at this time
                  </option>
                )}
                {stylists.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              <p className="mt-2 text-xs text-muted">
                An available stylist confirms your booking automatically.
                Choosing no preference sends a pending request for salon
                assignment.
              </p>
            </div>

            {/* Date */}
            <div className="mb-5 grid gap-4 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="date"
                  className="mb-2 block text-[11px] font-medium text-secondary"
                >
                  <Calendar size={13} className="mr-1 inline" />
                  Date (Philippine time)
                </label>
                <input
                  id="date"
                  type="date"
                  value={date}
                  onChange={(e) => {
                    setDate(e.target.value);
                    setTime("");
                  }}
                  min={salonDay()}
                  required
                  className="w-full rounded-sm border border-purple-light/20 bg-surface/40 px-4 py-2.5 text-[13px] text-white focus:border-purple-light focus:outline-none"
                />
              </div>

              <div>
                <label
                  htmlFor="time"
                  className="mb-2 block text-[11px] font-medium text-secondary"
                >
                  <Clock size={13} className="mr-1 inline" />
                  Time
                </label>
                <select
                  id="time"
                  aria-label="Time"
                  value={time}
                  onChange={(event) => setTime(event.target.value)}
                  required
                  disabled={
                    !date || !serviceName || slotsLoading || !!slotsError
                  }
                  className="w-full rounded-sm border border-purple-light/20 bg-surface/40 px-4 py-2.5 text-[13px] text-white disabled:opacity-50"
                >
                  <option value="">
                    {slotsLoading
                      ? "Checking available times…"
                      : "Choose an available time"}
                  </option>
                  {slots.map((slot) => (
                    <option
                      key={slot.time}
                      value={slot.time}
                      disabled={!slot.available}
                    >
                      {new Date(
                        salonDateTime(date, slot.time),
                      ).toLocaleTimeString("en-PH", {
                        hour: "numeric",
                        minute: "2-digit",
                        timeZone: "Asia/Manila",
                      })}
                      {slot.available ? "" : " · Unavailable"}
                    </option>
                  ))}
                </select>
                <div
                  className="mt-3 flex flex-wrap gap-2"
                  role="group"
                  aria-label="Available appointment times"
                >
                  {slots.map((slot) => (
                    <button
                      key={slot.time}
                      type="button"
                      disabled={!slot.available || slotsLoading}
                      aria-pressed={time === slot.time}
                      onClick={() => setTime(slot.time)}
                      className={
                        time === slot.time
                          ? "rounded border border-gold bg-gold px-3 py-2 text-black"
                          : "rounded border border-purple-light/30 px-3 py-2 text-white disabled:opacity-30"
                      }
                    >
                      {slot.time}
                    </button>
                  ))}
                </div>
                {slotsLoading && <p role="status">Checking available times…</p>}
                <p className="mt-2 text-xs text-muted">
                  Every appointment reserves 1 hour and 30 minutes. Choose a
                  stylist and date to see their available times.
                </p>
                {slotsError && (
                  <p role="alert" className="mt-2 text-xs text-error">
                    {slotsError}{" "}
                    <button
                      type="button"
                      className="underline"
                      onClick={() => setSlotRevision((value) => value + 1)}
                    >
                      Retry available times
                    </button>
                  </p>
                )}
                {date &&
                  serviceName &&
                  !slotsLoading &&
                  !slotsError &&
                  !slots.some((slot) => slot.available) && (
                    <p role="status" className="mt-2 text-xs text-warning">
                      No available times for this date and stylist. Choose
                      another date or stylist.
                    </p>
                  )}
              </div>
            </div>

            {/* Notes */}
            <div className="mb-6">
              <label
                htmlFor="notes"
                className="mb-2 block text-[11px] font-medium text-secondary"
              >
                Special Requests (optional)
              </label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                maxLength={1000}
                className="w-full rounded-sm border border-purple-light/20 bg-surface/40 px-4 py-2.5 text-[13px] text-white placeholder-muted focus:border-purple-light focus:outline-none"
                placeholder="Allergies, preferences, or anything we should know…"
              />
            </div>

            <button
              type="submit"
              disabled={
                loading ||
                slotsLoading ||
                (!!user &&
                  (lookLoading || (!!lookId && (!look || !!lookError))))
              }
              className="flex w-full items-center justify-center gap-2 bg-gold px-6 py-3 text-[11px] font-semibold uppercase tracking-[2px] text-card transition-all hover:bg-gold-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Booking…
                </>
              ) : (
                "Confirm Booking"
              )}
            </button>

            {!user && (
              <p className="mt-4 text-center text-[12px] text-muted">
                You&apos;ll be asked to sign in before confirming.
              </p>
            )}
          </form>
        </motion.div>
      </div>
    </div>
  );
}

function selectedServiceLabel(name: string) {
  const item = allServices.find((s) => s.name === name);
  if (!item) return "";
  return parsePrice(item.price) === null
    ? "Price to be confirmed by the salon."
    : item.price.startsWith("Mula")
      ? `Starting price: ${item.price}. Final amount is confirmed by the salon.`
      : `Catalog price: ${item.price}`;
}

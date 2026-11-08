import { salonDay } from "./dates";
import type { AppointmentStatus } from "../../db/schema";
import type { ServiceRecord } from "./workflow-types";
import type { AppointmentLook } from "../../components/appointment-look";

export interface AdminAppointment extends ServiceRecord {
  id: string;
  stylistId: string | null;
  serviceName: string;
  serviceType: string;
  appointmentDate: string;
  durationMinutes?: number;
  status: AppointmentStatus;
  totalPrice: number | null;
  notes: string | null;
  client: { id: string; name: string; email: string } | null;
  stylist: { id: string; name: string } | null;
  look?: AppointmentLook | null;
}
export type AdminStylistOption = {
  id: string;
  name: string;
  isActive?: boolean;
  workAvailable?: boolean;
  specialties?: string[];
};
export type AppointmentView = "all" | "today" | "upcoming" | "unassigned";
export type AppointmentFilters = {
  view: AppointmentView;
  query: string;
  status: AppointmentStatus | "all";
  from: string;
  to: string;
  stylist: string;
  service: string;
  unpriced: boolean;
  sort: "latest" | "soonest" | "client";
};
export const DEFAULT_APPOINTMENT_FILTERS: AppointmentFilters = {
  view: "all",
  query: "",
  status: "all",
  from: "",
  to: "",
  stylist: "all",
  service: "all",
  unpriced: false,
  sort: "latest",
};
export function activeAppointment(row: AdminAppointment) {
  return row.status === "pending" || row.status === "confirmed";
}
export function appointmentCounts(rows: AdminAppointment[], now = Date.now()) {
  const today = salonDay(new Date(now));
  return {
    today: rows.filter(
      (row) =>
        row.status !== "cancelled" &&
        salonDay(new Date(row.appointmentDate)) === today,
    ).length,
    upcoming: rows.filter(
      (row) => activeAppointment(row) && Date.parse(row.appointmentDate) >= now,
    ).length,
    unassigned: rows.filter((row) => activeAppointment(row) && !row.stylistId)
      .length,
    completed: rows.filter((row) => row.status === "completed").length,
  };
}
export function filterAppointments(
  rows: AdminAppointment[],
  filters: AppointmentFilters,
  now = Date.now(),
) {
  if (filters.from && filters.to && filters.from > filters.to) return [];
  const today = salonDay(new Date(now)),
    query = filters.query.trim().toLowerCase();
  return rows
    .filter((row) => {
      const scheduled = salonDay(new Date(row.appointmentDate));
      if (
        filters.view === "today" &&
        (scheduled !== today || row.status === "cancelled")
      )
        return false;
      if (
        filters.view === "upcoming" &&
        (!activeAppointment(row) || Date.parse(row.appointmentDate) < now)
      )
        return false;
      if (
        filters.view === "unassigned" &&
        (!activeAppointment(row) || !!row.stylistId)
      )
        return false;
      if (filters.status !== "all" && row.status !== filters.status)
        return false;
      if (
        (filters.from && scheduled < filters.from) ||
        (filters.to && scheduled > filters.to)
      )
        return false;
      if (
        filters.stylist !== "all" &&
        (row.stylistId ?? "unassigned") !== filters.stylist
      )
        return false;
      if (filters.service !== "all" && row.serviceType !== filters.service)
        return false;
      if (filters.unpriced && row.totalPrice !== null) return false;
      return (
        !query ||
        `${row.serviceName} ${row.client?.name ?? ""} ${row.client?.email ?? ""} ${row.stylist?.name ?? ""}`
          .toLowerCase()
          .includes(query)
      );
    })
    .sort(
      (a, b) =>
        (filters.sort === "client"
          ? (a.client?.name ?? "").localeCompare(b.client?.name ?? "")
          : filters.sort === "soonest"
            ? Date.parse(a.appointmentDate) - Date.parse(b.appointmentDate)
            : Date.parse(b.appointmentDate) - Date.parse(a.appointmentDate)) ||
        a.id.localeCompare(b.id),
    );
}
export function appointmentTimeInput(date: string) {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Manila",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(date));
}

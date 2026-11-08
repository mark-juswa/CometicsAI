import test from "node:test";
import assert from "node:assert/strict";
import {
  appointmentCounts,
  filterAppointments,
  appointmentTimeInput,
  DEFAULT_APPOINTMENT_FILTERS,
  type AdminAppointment,
} from "../lib/business/appointment-list";
const now = Date.parse("2030-10-17T01:00:00Z");
const row = (
  id: string,
  patch: Partial<AdminAppointment> = {},
): AdminAppointment => ({
  id,
  serviceName: "Gel Manicure",
  serviceType: "nail",
  appointmentDate: "2030-10-17T02:00:00Z",
  status: "pending",
  totalPrice: null,
  notes: null,
  stylistId: null,
  stylist: null,
  client: { id: "client", name: "Maria Cruz", email: "maria@example.invalid" },
  ...patch,
});
test("appointment views and counts use Philippine dates and distinguish closed from active bookings", () => {
  const rows = [
    row("today"),
    row("past", {
      appointmentDate: "2030-10-16T16:30:00Z",
      status: "completed",
    }),
    row("cancelled", { status: "cancelled" }),
    row("future", {
      appointmentDate: "2030-10-18T02:00:00Z",
      stylistId: "staff",
    }),
  ];
  assert.deepEqual(appointmentCounts(rows, now), {
    today: 2,
    upcoming: 2,
    unassigned: 1,
    completed: 1,
  });
  assert.deepEqual(
    filterAppointments(
      rows,
      { ...DEFAULT_APPOINTMENT_FILTERS, view: "today" },
      now,
    ).map((r) => r.id),
    ["today", "past"],
  );
  assert.deepEqual(
    filterAppointments(
      rows,
      { ...DEFAULT_APPOINTMENT_FILTERS, view: "upcoming", sort: "soonest" },
      now,
    ).map((r) => r.id),
    ["today", "future"],
  );
  assert.equal(appointmentTimeInput("2030-10-16T16:30:00Z"), "00:30");
});
test("date ranges are inclusive, invalid ranges are empty, and zero pesos is a confirmed amount", () => {
  const rows = [
    row("unknown"),
    row("free", { totalPrice: 0 }),
    row("other", {
      serviceType: "hair",
      stylistId: "staff",
      stylist: { id: "staff", name: "Lara" },
      appointmentDate: "2030-10-18T15:59:00Z",
    }),
  ];
  assert.deepEqual(
    filterAppointments(
      rows,
      { ...DEFAULT_APPOINTMENT_FILTERS, unpriced: true, service: "nail" },
      now,
    ).map((r) => r.id),
    ["unknown"],
  );
  assert.deepEqual(
    filterAppointments(
      rows,
      {
        ...DEFAULT_APPOINTMENT_FILTERS,
        query: "lara",
        from: "2030-10-18",
        to: "2030-10-18",
      },
      now,
    ).map((r) => r.id),
    ["other"],
  );
  assert.deepEqual(
    filterAppointments(
      rows,
      { ...DEFAULT_APPOINTMENT_FILTERS, from: "2030-10-19", to: "2030-10-18" },
      now,
    ),
    [],
  );
  assert.equal(
    filterAppointments(
      rows,
      {
        ...DEFAULT_APPOINTMENT_FILTERS,
        stylist: "unassigned",
        query: "maria@example.invalid",
      },
      now,
    ).length,
    2,
  );
});

import { allServices, APPOINTMENT_DURATION_MINUTES } from "../services";
import { BusinessError, PRIVATE, day, fail, id } from "./core";
import { salonDateTime, salonDay } from "./dates";
import type { Query } from "./store";

type Hours = { day: number; start: string; end: string };
type Staff = { id: string; hours: Hours[] };
type Reservation = {
  stylistId: string;
  appointmentDate: string;
  durationMinutes: number;
};
const minutes = (time: string) =>
  Number(time.slice(0, 2)) * 60 + Number(time.slice(3));
export function availableBookingSlots(
  date: string,
  staff: Staff[],
  reservations: Reservation[],
  now = new Date(),
) {
  const weekday = new Date(date + "T00:00:00Z").getUTCDay(),
    duration = APPOINTMENT_DURATION_MINUTES;
  const slots: { time: string; available: boolean }[] = [];
  for (let minute = 0; minute + duration <= 1440; minute += 30) {
    const time =
      String(Math.floor(minute / 60)).padStart(2, "0") +
      ":" +
      String(minute % 60).padStart(2, "0");
    const onDuty = staff.filter((person) =>
      person.hours.some(
        (hours) =>
          hours.day === weekday &&
          minute >= minutes(hours.start) &&
          minute + duration <= minutes(hours.end),
      ),
    );
    if (!onDuty.length) continue;
    const start = Date.parse(salonDateTime(date, time)),
      end = start + duration * 60000;
    const available =
      start > now.getTime() &&
      onDuty.some(
        (person) =>
          !reservations.some(
            (row) =>
              row.stylistId === person.id &&
              start <
                Date.parse(row.appointmentDate) +
                  Math.max(row.durationMinutes, duration) * 60000 &&
              Date.parse(row.appointmentDate) < end,
          ),
      );
    slots.push({ time, available });
  }
  return slots;
}
export async function bookingAvailability(
  request: Request,
  deps: { query: Query; now?: () => Date },
) {
  try {
    if (request.method !== "GET") fail("Operation not found.", 404);
    const params = new URL(request.url).searchParams,
      date = day(params.get("date")),
      service = allServices.find((row) => row.name === params.get("service"));
    if (!service) fail("Choose a service from the salon catalog.");
    const stylist = params.get("stylist") ? id(params.get("stylist")) : null,
      now = deps.now?.() ?? new Date();
    if (date < salonDay(now)) fail("Choose today or a future date.");
    const staff = (await deps.query(
      `SELECT u.id,w.hours FROM users u JOIN stylist_work_settings w ON w.stylist_id=u.id WHERE u.role='stylist' AND u.is_active AND w.available AND ($2::uuid IS NULL OR u.id=$2) AND EXISTS(SELECT 1 FROM stylist_specialties s WHERE s.stylist_id=u.id AND s.service_type=$1) ORDER BY u.id`,
      [service!.serviceType, stylist],
    )) as unknown as Staff[];
    const start = salonDateTime(date, "00:00"),
      end = new Date(Date.parse(start) + 86400000).toISOString();
    const reserved = staff.length
      ? await deps.query(
          `SELECT stylist_id AS "stylistId",appointment_date AT TIME ZONE 'UTC' AS "appointmentDate",duration_minutes AS "durationMinutes" FROM appointments WHERE stylist_id=ANY($1::uuid[]) AND status IN ('pending','confirmed') AND appointment_date<($3::timestamptz AT TIME ZONE 'UTC') AND appointment_date+make_interval(mins=>greatest(duration_minutes,90))>($2::timestamptz AT TIME ZONE 'UTC')`,
          [staff.map((row) => row.id), start, end],
        )
      : [];
    return Response.json(
      {
        date,
        stylistId: stylist,
        durationMinutes: APPOINTMENT_DURATION_MINUTES,
        slots: availableBookingSlots(
          date,
          staff,
          reserved.map((row) => ({
            ...row,
            appointmentDate: new Date(
              String(row.appointmentDate),
            ).toISOString(),
          })) as Reservation[],
          now,
        ),
        timeZone: "Asia/Manila",
      },
      { headers: PRIVATE },
    );
  } catch (cause) {
    return Response.json(
      {
        error:
          cause instanceof BusinessError
            ? cause.message
            : "Available times could not be loaded. Please try again.",
      },
      {
        status: cause instanceof BusinessError ? cause.status : 503,
        headers: PRIVATE,
      },
    );
  }
}

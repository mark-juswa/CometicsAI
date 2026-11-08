import { BusinessError, PRIVATE, fail } from "./core";
import type { HistoryDependencies } from "./customer-history";

export type BookingNotification = {
  id: string;
  key: string;
  serviceName: string;
  appointmentDate: string;
  createdAt: string;
  status: "pending" | "confirmed";
  otherName: string | null;
};
export async function bookingNotifications(
  request: Request,
  deps: HistoryDependencies,
) {
  try {
    const actor = await deps.actor();
    if (!actor) fail("Sign in to continue.", 401);
    if (!["client", "stylist"].includes(actor.role))
      fail("Client or stylist access required.", 403);
    if (request.method !== "GET") fail("Operation not found.", 404);
    const rows = await deps.query(
      `SELECT a.id,a.service_name AS "serviceName",a.appointment_date AT TIME ZONE 'UTC' AS "appointmentDate",a.created_at AT TIME ZONE 'UTC' AS "createdAt",a.status,a.stylist_id AS "stylistId",CASE WHEN $2='client' THEN s.name ELSE c.name END AS "otherName",count(*) OVER()::int AS total FROM appointments a LEFT JOIN users c ON c.id=a.client_id LEFT JOIN users s ON s.id=a.stylist_id WHERE (($2='client' AND a.client_id=$1) OR ($2='stylist' AND a.stylist_id=$1)) AND a.status IN ('pending','confirmed') AND (a.appointment_date AT TIME ZONE 'UTC')>=now() ORDER BY a.created_at DESC,a.id DESC LIMIT 20`,
      [actor.id, actor.role],
    );
    return Response.json(
      {
        ownerId: actor.id,
        role: actor.role,
        total: Number(rows[0]?.total ?? 0),
        notifications: rows.map((row) => ({
          ...row,
          total: undefined,
          stylistId: undefined,
          key: [
            row.id,
            row.status,
            row.stylistId ?? "",
            new Date(String(row.appointmentDate)).toISOString(),
          ].join(":"),
        })),
      },
      { headers: PRIVATE },
    );
  } catch (error) {
    return Response.json(
      {
        error:
          error instanceof BusinessError
            ? error.message
            : "Booking notifications could not be loaded.",
      },
      {
        status: error instanceof BusinessError ? error.status : 503,
        headers: PRIVATE,
      },
    );
  }
}

import { day, fail, id, paging } from "./core";
import {
  historyAction,
  privateJson,
  type HistoryDependencies,
} from "./customer-history";

export function stylistServiceHistory(
  request: Request,
  stylistId: string,
  deps: HistoryDependencies,
) {
  return historyAction(request, deps, "admin", async () => {
    if (request.method !== "GET") fail("Operation not found.", 404);
    id(stylistId);
    const params = new URL(request.url).searchParams,
      { page, offset } = paging(params);
    const from = params.has("from") ? day(params.get("from")) : null,
      to = params.has("to") ? day(params.get("to")) : null;
    if (from && to && from > to)
      fail("The end date must be on or after the start date.");
    const [stylist] = await deps.query(
      "SELECT id,name,email,is_active AS \"isActive\" FROM users WHERE id=$1 AND role='stylist'",
      [stylistId],
    );
    if (!stylist) fail("Stylist not found.", 404);
    const filter = `a.stylist_id=$1 AND a.status='completed' AND ($2::date IS NULL OR (a.appointment_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')::date >= $2) AND ($3::date IS NULL OR (a.appointment_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')::date <= $3)`;
    const [summaries, services] = await Promise.all([
      deps.query(
        `SELECT count(*)::int AS completed,coalesce(sum(a.total_price),0)::bigint AS amount,count(*) FILTER(WHERE a.total_price IS NULL)::int AS unpriced,count(DISTINCT a.client_id)::int AS clients,coalesce(sum(a.duration_minutes),0)::int AS minutes FROM appointments a WHERE ${filter}`,
        [stylistId, from, to],
      ),
      deps.query(
        `SELECT a.id,a.service_name AS "serviceName",a.service_type AS "serviceType",a.appointment_date AT TIME ZONE 'UTC' AS "appointmentDate",a.completed_at AS "completedAt",a.duration_minutes AS "durationMinutes",a.total_price AS "totalPrice",c.name AS "clientName",r.rating FROM appointments a LEFT JOIN users c ON c.id=a.client_id LEFT JOIN appointment_reviews r ON r.appointment_id=a.id WHERE ${filter} ORDER BY a.appointment_date DESC,a.id LIMIT 12 OFFSET $4`,
        [stylistId, from, to, offset],
      ),
    ]);
    const summary = summaries[0];
    return privateJson({
      stylist,
      services,
      page,
      pageSize: 12,
      total: Number(summary.completed),
      summary: { ...summary, amount: Number(summary.amount) },
    });
  });
}

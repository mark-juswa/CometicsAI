import type { Query } from "./store";
import {
  revenueWindow,
  type RevenueWindow,
  type RevenueStylist,
  type RevenueReport,
} from "./revenue-periods";

/** Completed services are counted once, without joining product or payment rows. */
export async function loadRevenueReport(
  query: Query,
  window: RevenueWindow,
): Promise<RevenueReport> {
  const month = revenueWindow("month", window.date),
    year = revenueWindow("year", window.date);
  const values = [
    window.from,
    window.to,
    window.previousFrom,
    window.previousTo,
    window.date,
    month.from,
    month.to,
    year.from,
    year.to,
  ];
  const utc = (index: number, next = false) =>
    `(($${index}::date${next ? "+1" : ""})::timestamp AT TIME ZONE 'Asia/Manila') AT TIME ZONE 'UTC'`;
  const bounds = `SELECT ${utc(1)} AS start_at,${utc(2, true)} AS end_at,${utc(3)} AS previous_start,${utc(4, true)} AS previous_end,${utc(5)} AS day_start,${utc(5, true)} AS day_end,${utc(6)} AS month_start,${utc(7, true)} AS month_end,${utc(8)} AS year_start,${utc(9, true)} AS year_end`;
  const [summaryRows, seriesRows, stylistRows] = await Promise.all([
    query(
      `WITH bounds AS (${bounds}) SELECT
   coalesce(sum(a.total_price) FILTER(WHERE a.appointment_date>=b.start_at AND a.appointment_date<b.end_at),0)::bigint AS amount,
   count(*) FILTER(WHERE a.appointment_date>=b.start_at AND a.appointment_date<b.end_at)::int AS completed,
   count(*) FILTER(WHERE a.appointment_date>=b.start_at AND a.appointment_date<b.end_at AND a.total_price IS NULL)::int AS unpriced,
   coalesce(sum(a.total_price) FILTER(WHERE a.appointment_date>=b.previous_start AND a.appointment_date<b.previous_end),0)::bigint AS "previousAmount",
   count(*) FILTER(WHERE a.appointment_date>=b.previous_start AND a.appointment_date<b.previous_end)::int AS "previousCompleted",
   coalesce(sum(a.total_price),0)::bigint AS "allTimeAmount",
   coalesce(sum(a.total_price) FILTER(WHERE a.appointment_date>=b.start_at AND a.appointment_date<b.end_at AND a.stylist_id IS NULL),0)::bigint AS "unassignedAmount"
   FROM appointments a CROSS JOIN bounds b WHERE a.status='completed'`,
      values,
    ),
    query(
      `WITH selected AS (
   SELECT date_trunc($3::text,(appointment_date AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Manila') AS bucket,
    coalesce(sum(total_price),0)::bigint AS amount,count(*)::int AS completed
   FROM appointments WHERE status='completed' AND appointment_date>=${utc(1)} AND appointment_date<${utc(2, true)} GROUP BY 1
  ) SELECT to_char(g.bucket,'YYYY-MM-DD"T"HH24:MI:SS') AS key,
   to_char(g.bucket,CASE $3 WHEN 'hour' THEN 'HH24:MI' WHEN 'month' THEN 'Mon' ELSE 'DD Mon' END) AS label,
   coalesce(s.amount,0)::bigint AS amount,coalesce(s.completed,0)::int AS completed
   FROM generate_series($1::date::timestamp,($2::date+1)::timestamp-$4::interval,$4::interval) g(bucket)
   LEFT JOIN selected s ON s.bucket=g.bucket ORDER BY g.bucket`,
      [window.from, window.to, window.bucket, `1 ${window.bucket}`],
    ),
    query(
      `WITH bounds AS (${bounds}), earnings AS (
   SELECT a.stylist_id,
    coalesce(sum(a.total_price) FILTER(WHERE a.appointment_date>=b.start_at AND a.appointment_date<b.end_at),0)::bigint AS amount,
    count(*) FILTER(WHERE a.appointment_date>=b.start_at AND a.appointment_date<b.end_at)::int AS completed,
    count(*) FILTER(WHERE a.appointment_date>=b.start_at AND a.appointment_date<b.end_at AND a.total_price IS NULL)::int AS unpriced,
    coalesce(sum(a.total_price) FILTER(WHERE a.appointment_date>=b.day_start AND a.appointment_date<b.day_end),0)::bigint AS "dayAmount",
    coalesce(sum(a.total_price) FILTER(WHERE a.appointment_date>=b.month_start AND a.appointment_date<b.month_end),0)::bigint AS "monthAmount",
    coalesce(sum(a.total_price) FILTER(WHERE a.appointment_date>=b.year_start AND a.appointment_date<b.year_end),0)::bigint AS "yearAmount"
   FROM appointments a CROSS JOIN bounds b WHERE a.status='completed' AND a.appointment_date>=least(b.start_at,b.year_start) AND a.appointment_date<greatest(b.end_at,b.year_end) GROUP BY a.stylist_id
  ) SELECT u.id,u.name,u.email,u.is_active AS "isActive",
   EXISTS(SELECT 1 FROM stylist_work_settings w WHERE w.stylist_id=u.id AND w.available) AS "workAvailable",
   coalesce((SELECT json_agg(ss.service_type ORDER BY ss.service_type) FROM stylist_specialties ss WHERE ss.stylist_id=u.id),'[]'::json) AS specialties,
   coalesce(e.amount,0)::bigint AS amount,coalesce(e.completed,0)::int AS completed,coalesce(e.unpriced,0)::int AS unpriced,
   coalesce(e."dayAmount",0)::bigint AS "dayAmount",coalesce(e."monthAmount",0)::bigint AS "monthAmount",coalesce(e."yearAmount",0)::bigint AS "yearAmount"
   FROM users u LEFT JOIN earnings e ON e.stylist_id=u.id WHERE u.role='stylist' ORDER BY coalesce(e.amount,0) DESC,u.name,u.id`,
      values,
    ),
  ]);
  const row = summaryRows[0];
  const summary = {
    amount: Number(row.amount),
    completed: Number(row.completed),
    unpriced: Number(row.unpriced),
    previousAmount: Number(row.previousAmount),
    previousCompleted: Number(row.previousCompleted),
    allTimeAmount: Number(row.allTimeAmount),
    unassignedAmount: Number(row.unassignedAmount),
    changePercent: null as number | null,
  };
  summary.changePercent =
    summary.previousAmount > 0
      ? Math.round(
          ((summary.amount - summary.previousAmount) / summary.previousAmount) *
            1000,
        ) / 10
      : null;
  const stylists = stylistRows.map((row) => ({
    ...row,
    amount: Number(row.amount),
    completed: Number(row.completed),
    unpriced: Number(row.unpriced),
    dayAmount: Number(row.dayAmount),
    monthAmount: Number(row.monthAmount),
    yearAmount: Number(row.yearAmount),
  })) as RevenueStylist[];
  return {
    window,
    summary,
    stylists,
    series: seriesRows.map((row) => ({
      key: String(row.key),
      label: String(row.label),
      amount: Number(row.amount),
      completed: Number(row.completed),
    })),
    timeZone: "Asia/Manila",
    amountBasis: "Recorded completed-service value by scheduled service date",
  };
}

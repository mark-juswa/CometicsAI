import { databaseSql } from "@/db";
import { bookingAvailability } from "@/lib/business/booking-availability";
export const dynamic = "force-dynamic";
export const GET = (request: Request) =>
  bookingAvailability(request, {
    query: (sql, values) => databaseSql.query(sql, values),
  });

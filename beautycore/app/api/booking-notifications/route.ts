import { bookingNotifications } from "@/lib/business/booking-notifications";
import { historyDependencies } from "@/lib/business/history-server";
export const dynamic = "force-dynamic";
export const GET = (request: Request) =>
  bookingNotifications(request, historyDependencies);

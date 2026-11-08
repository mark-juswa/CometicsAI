import { stylistServiceHistory } from "@/lib/business/stylist-history";
import { historyDependencies } from "@/lib/business/history-server";
export const dynamic = "force-dynamic";
export const GET = async (
  request: Request,
  context: { params: Promise<{ id: string }> },
) =>
  stylistServiceHistory(
    request,
    (await context.params).id,
    historyDependencies,
  );

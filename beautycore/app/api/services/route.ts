import { businessDependencies } from "../../../lib/business/server";
export const dynamic = "force-dynamic";
export async function GET() {
  try {
    return Response.json(
      { services: await businessDependencies.store.serviceCatalog() },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return Response.json(
      { error: "Services could not be loaded. Please try again." },
      { status: 503 },
    );
  }
}

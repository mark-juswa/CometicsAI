import { boundedJson, fail } from "./core";
import {
  historyAction,
  privateJson,
  type HistoryDependencies,
} from "./customer-history";
export function workAvailability(request: Request, deps: HistoryDependencies) {
  return historyAction(request, deps, "stylist", async (actor) => {
    if (request.method === "GET") {
      const [settings] = await deps.query(
        "SELECT available,hours FROM stylist_work_settings WHERE stylist_id=$1",
        [actor.id],
      );
      return privateJson(settings ?? { available: false, hours: [] });
    }
    if (request.method !== "PUT") fail("Operation not found.", 404);
    const body = await boundedJson(request);
    if (
      Object.keys(body).some((k) => !["available", "hours"].includes(k)) ||
      typeof body.available !== "boolean" ||
      !Array.isArray(body.hours) ||
      body.hours.length > 7
    )
      fail("Enter a valid availability setting and weekly schedule.");
    const hours = body.hours;
    if (
      hours.some(
        (h) =>
          !h ||
          typeof h !== "object" ||
          Array.isArray(h) ||
          Object.keys(h).some((k) => !["day", "start", "end"].includes(k)) ||
          !Number.isInteger(h.day) ||
          h.day < 0 ||
          h.day > 6 ||
          typeof h.start !== "string" ||
          typeof h.end !== "string" ||
          !/^([01]\d|2[0-3]):[0-5]\d$/.test(h.start) ||
          !/^([01]\d|2[0-3]):[0-5]\d$/.test(h.end) ||
          h.start >= h.end,
      ) ||
      new Set(hours.map((h) => h.day)).size !== hours.length ||
      (body.available && !hours.length)
    )
      fail("Set valid working hours before making yourself available.");
    await deps.query("SELECT beautycore_set_work($1,$2,$3::jsonb)", [
      actor.id,
      body.available,
      JSON.stringify(hours),
    ]);
    return privateJson({ available: body.available, hours });
  });
}

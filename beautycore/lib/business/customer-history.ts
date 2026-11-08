import { createHash } from "node:crypto";
import sharp from "sharp";
import {
  BusinessError,
  PRIVATE,
  MAX_IMAGE,
  boundedJson,
  day,
  fail,
  id,
  mutationOrigin,
  object,
  paging,
  validateLook,
  type Actor,
} from "./core";
import type { Query } from "./store";
import { verifyConsultationHandle } from "../ai/consultation-handle";

export type HistoryDependencies = {
  query: Query;
  actor: () => Promise<Actor | null>;
  publicOrigin?: string;
};
export const privateJson = (data: unknown, status = 200) =>
  Response.json(data, { status, headers: PRIVATE });
export async function historyAction(
  request: Request,
  deps: HistoryDependencies,
  role: Actor["role"],
  action: (actor: Actor) => Promise<Response>,
) {
  try {
    const actor = await deps.actor();
    if (!actor) fail("Sign in to continue.", 401);
    if (actor.role !== role)
      fail(
        `${role === "admin" ? "Administrator" : role === "stylist" ? "Stylist" : "Customer"} access required.`,
        403,
      );
    if (request.method !== "GET") mutationOrigin(request, deps.publicOrigin);
    return await action(actor);
  } catch (error) {
    if (error instanceof BusinessError)
      return privateJson({ error: error.message }, error.status);
    return privateJson(
      { error: "Could not load or save this record. Please try again." },
      503,
    );
  }
}

export function clientHistory(
  request: Request,
  clientId: string,
  deps: HistoryDependencies,
  payment = false,
) {
  return historyAction(request, deps, "admin", async (actor) => {
    id(clientId);
    const [client] = await deps.query(
      `SELECT id,name,email,phone,avatar,is_active AS "isActive",created_at AT TIME ZONE 'UTC' AS "createdAt" FROM users WHERE id=$1 AND role='client'`,
      [clientId],
    );
    if (!client) fail("Client not found.", 404);
    if (payment) {
      if (request.method !== "POST") fail("Operation not found.", 404);
      const body = await boundedJson(request);
      const appointmentId = id(body.appointmentId);
      const requestId = id(body.requestId);
      if (
        Object.keys(body).some(
          (k) =>
            ![
              "appointmentId",
              "requestId",
              "amount",
              "method",
              "reference",
            ].includes(k),
        ) ||
        !Number.isSafeInteger(body.amount) ||
        Number(body.amount) < 1 ||
        Number(body.amount) > 100000000 ||
        !["cash", "card", "bank", "other"].includes(String(body.method)) ||
        (body.reference !== undefined &&
          (typeof body.reference !== "string" || body.reference.length > 160))
      )
        fail("Enter a valid payment amount, method, and reference.");
      try {
        const [row] = await deps.query(
          "SELECT beautycore_record_payment($1,$2,$3,$4,$5,$6,$7) AS id",
          [
            clientId,
            appointmentId,
            actor.id,
            body.amount,
            body.method,
            body.reference ?? "",
            requestId,
          ],
        );
        return privateJson({ payment: row }, 201);
      } catch {
        fail(
          "Payment was not recorded. Check the appointment price, status, and remaining balance.",
          409,
        );
      }
    }
    if (request.method !== "GET") fail("Operation not found.", 404);
    const params = new URL(request.url).searchParams;
    const { page, offset } = paging(params);
    const status = params.get("status") || "all";
    if (
      !["all", "pending", "confirmed", "completed", "cancelled"].includes(
        status,
      )
    )
      fail("Invalid status.");
    const from =
      params.has("from") && params.get("from") ? day(params.get("from")) : null;
    const to =
      params.has("to") && params.get("to") ? day(params.get("to")) : null;
    if (from && to && from > to) fail("Choose a valid date range.");
    const search = (params.get("q") || "").trim().slice(0, 100);
    const where = `a.client_id=$1 AND ($2='all' OR a.status::text=$2) AND ($3::date IS NULL OR ((a.appointment_date AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Manila')::date >= $3) AND ($4::date IS NULL OR ((a.appointment_date AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Manila')::date <= $4) AND ($5='' OR strpos(lower(a.service_name||' '||coalesce(s.name,'')),lower($5))>0)`;
    const values = [clientId, status, from, to, search];
    const [appointments, counts, totals, payments] = await Promise.all([
      deps.query(
        `SELECT a.id,a.service_name AS "serviceName",a.service_type AS "serviceType",a.appointment_date AT TIME ZONE 'UTC' AS "appointmentDate",a.status,a.total_price AS "totalPrice",s.name AS "stylistName",coalesce((SELECT sum(amount) FROM appointment_payments p WHERE p.appointment_id=a.id),0)::bigint AS "paidAmount" FROM appointments a LEFT JOIN users s ON s.id=a.stylist_id WHERE ${where} ORDER BY a.appointment_date DESC,a.id LIMIT 12 OFFSET $6`,
        [...values, offset],
      ),
      deps.query(
        `SELECT count(*)::int AS total FROM appointments a LEFT JOIN users s ON s.id=a.stylist_id WHERE ${where}`,
        values,
      ),
      deps.query(
        `SELECT count(*)::int AS bookings,count(*) FILTER(WHERE status='completed')::int AS completed,coalesce(sum(total_price) FILTER(WHERE status='completed'),0)::bigint AS "completedValue",(SELECT coalesce(sum(p.amount),0)::bigint FROM appointment_payments p JOIN appointments x ON x.id=p.appointment_id WHERE x.client_id=$1) AS "paymentsReceived" FROM appointments WHERE client_id=$1`,
        [clientId],
      ),
      deps.query(
        `SELECT p.id,p.appointment_id AS "appointmentId",p.amount,p.method,p.reference,p.created_at AS "createdAt",a.service_name AS "serviceName",u.name AS "recordedBy" FROM appointment_payments p JOIN appointments a ON a.id=p.appointment_id JOIN users u ON u.id=p.recorded_by WHERE a.client_id=$1 AND a.id IN(SELECT a.id FROM appointments a LEFT JOIN users s ON s.id=a.stylist_id WHERE ${where} ORDER BY a.appointment_date DESC,a.id LIMIT 12 OFFSET $6) ORDER BY p.created_at DESC,p.id`,
        [...values, offset],
      ),
    ]);
    return privateJson({
      client,
      appointments,
      payments,
      summary: totals[0],
      total: Number(counts[0].total),
      page,
      pageSize: 12,
    });
  });
}

export function clientImages(
  request: Request,
  deps: HistoryDependencies,
  imageId?: string,
) {
  return historyAction(request, deps, "client", async (actor) => {
    if (request.method !== "GET") fail("Operation not found.", 404);
    if (imageId) {
      id(imageId);
      const [row] = await deps.query(
        `SELECT image_data FROM client_reference_images WHERE id=$1 AND client_id=$2
         UNION ALL SELECT source_image_url FROM ai_generations WHERE id=$1 AND client_id=$2 AND source_image_url ~ '^data:image/(png|jpeg);base64,' LIMIT 1`,
        [imageId, actor.id],
      );
      if (!row) fail("Image not found.", 404);
      const image = /^data:(image\/(?:png|jpeg));base64,(.+)$/.exec(
        String(row.image_data),
      );
      if (!image) fail("Image is unavailable.", 404);
      return new Response(Buffer.from(image[2], "base64"), {
        headers: {
          ...PRIVATE,
          "Content-Type": image[1],
          "X-Content-Type-Options": "nosniff",
          "Content-Disposition": "inline",
        },
      });
    }
    const params = new URL(request.url).searchParams;
    const { page, offset } = paging(params);
    const kind = params.get("kind") || "all";
    if (!["all", "uploaded", "generated"].includes(kind))
      fail("Invalid image category.");
    const rows = await deps.query(
      `WITH images AS (
      SELECT r.id,'uploaded' AS kind,r.filename AS name,c.feature,r.consultation_id AS "consultationId",r.created_at AS "createdAt",'/api/client-images/'||r.id AS "imageUrl" FROM client_reference_images r JOIN client_consultations c ON c.id=r.consultation_id WHERE r.client_id=$1
      UNION ALL SELECT l.id,'uploaded','Earlier uploaded reference',CASE l.style_type WHEN 'hair' THEN 'hairstyle' WHEN 'nail' THEN 'nails' ELSE 'makeup' END,NULL::uuid,l.created_at AT TIME ZONE 'UTC','/api/client-images/'||l.id FROM (SELECT DISTINCT ON(md5(source_image_url)) id,style_type,created_at FROM ai_generations WHERE client_id=$1 AND source_image_url ~ '^data:image/(png|jpeg);base64,' ORDER BY md5(source_image_url),created_at,id) l
      UNION ALL SELECT g.id,'generated',g.style_name,CASE g.style_type WHEN 'hair' THEN 'hairstyle' WHEN 'nail' THEN 'nails' ELSE 'makeup' END,NULL::uuid,g.saved_at,'/api/saved-looks/'||g.id||'/image' FROM ai_generations g WHERE g.client_id=$1 AND g.saved_at IS NOT NULL AND g.result_hash IS NOT NULL
    ) SELECT *,count(*) OVER()::int AS total FROM images WHERE ($2='all' OR kind=$2) ORDER BY "createdAt" DESC,id LIMIT 12 OFFSET $3`,
      [actor.id, kind, offset],
    );
    return privateJson({
      images: rows,
      page,
      total: Number(rows[0]?.total ?? 0),
    });
  });
}

export function paymentHistory(request: Request, deps: HistoryDependencies) {
  return historyAction(request, deps, "admin", async () => {
    if (request.method !== "GET") fail("Operation not found.", 404);
    const params = new URL(request.url).searchParams,
      { page, offset } = paging(params);
    const search = (params.get("q") || "").trim().slice(0, 100),
      method = params.get("method") || "all";
    if (!["all", "cash", "card", "bank", "other"].includes(method))
      fail("Invalid payment method.");
    const from = params.get("from") ? day(params.get("from")) : null,
      to = params.get("to") ? day(params.get("to")) : null;
    if (from && to && from > to) fail("Choose a valid date range.");
    const base = `FROM appointment_payments p JOIN appointments a ON a.id=p.appointment_id JOIN users c ON c.id=a.client_id LEFT JOIN users s ON s.id=a.stylist_id WHERE ($1='' OR strpos(lower(c.name||' '||a.service_name||' '||coalesce(p.reference,'')),lower($1))>0) AND ($2='all' OR p.method=$2) AND ($3::date IS NULL OR (p.created_at AT TIME ZONE 'Asia/Manila')::date >= $3) AND ($4::date IS NULL OR (p.created_at AT TIME ZONE 'Asia/Manila')::date <= $4)`;
    const values = [search, method, from, to];
    const [payments, summary] = await Promise.all([
      deps.query(
        `SELECT p.id,p.amount,p.method,p.reference,p.created_at AS "createdAt",a.id AS "appointmentId",a.status,a.service_name AS "serviceName",a.appointment_date AT TIME ZONE 'UTC' AS "appointmentDate",a.total_price AS "totalPrice",c.id AS "clientId",c.name AS "clientName",s.name AS "stylistName" ${base} ORDER BY p.created_at DESC,p.id LIMIT 12 OFFSET $5`,
        [...values, offset],
      ),
      deps.query(
        `SELECT count(*)::int AS total,coalesce(sum(p.amount),0)::bigint AS amount ${base}`,
        values,
      ),
    ]);
    return privateJson({
      payments,
      page,
      total: Number(summary[0].total),
      amount: Number(summary[0].amount),
    });
  });
}

export function consultationHistory(
  request: Request,
  deps: HistoryDependencies,
  sessionId?: string,
) {
  return historyAction(request, deps, "client", async (actor) => {
    if (request.method !== "GET") fail("Operation not found.", 404);
    if (!sessionId) {
      const { page, offset } = paging(new URL(request.url).searchParams);
      const rows = await deps.query(
        `SELECT c.id,c.feature,c.created_at AS "createdAt",c.updated_at AS "updatedAt",(SELECT count(*)::int FROM client_reference_images r WHERE r.consultation_id=c.id) AS uploads,(SELECT count(*)::int FROM client_consultation_results r WHERE r.consultation_id=c.id) AS results,count(*) OVER()::int AS total FROM client_consultations c WHERE c.client_id=$1 ORDER BY c.created_at DESC,c.id LIMIT 12 OFFSET $2`,
        [actor.id, offset],
      );
      return privateJson({
        sessions: rows,
        page,
        total: Number(rows[0]?.total ?? 0),
      });
    }
    id(sessionId);
    const [session] = await deps.query(
      `SELECT id,feature,snapshot,created_at AS "createdAt",updated_at AS "updatedAt" FROM client_consultations WHERE id=$1 AND client_id=$2`,
      [sessionId, actor.id],
    );
    if (!session) fail("Consultation not found.", 404);
    const [uploads, results] = await Promise.all([
      deps.query(
        `SELECT id,filename AS name,width,height,created_at AS "createdAt",'/api/client-images/'||id AS "imageUrl" FROM client_reference_images WHERE consultation_id=$1 AND client_id=$2 ORDER BY created_at,id`,
        [sessionId, actor.id],
      ),
      deps.query(
        `SELECT g.id,g.style_name AS name,g.style_type AS "styleType",g.saved_at AS "savedAt",'/api/saved-looks/'||g.id||'/image' AS "imageUrl",r.recommendation_id AS "recommendationId" FROM client_consultation_results r JOIN ai_generations g ON g.id=r.generation_id AND g.client_id=r.client_id WHERE r.consultation_id=$1 AND r.client_id=$2 ORDER BY r.created_at,g.id`,
        [sessionId, actor.id],
      ),
    ]);
    return privateJson({ session, uploads, results });
  });
}

/** Archive at the authenticated application boundary; generation requests/results stay intact. */
export async function archiveConsultationResponse(
  request: Request,
  response: Response,
  parts: string[],
  owner: string,
  query: Query,
  secret: string,
  budget: number,
) {
  if (!response.ok || !(parts[0] === "consultations" || parts[0] === "jobs"))
    return;
  const payload: unknown = await response.clone().json();
  if (!object(payload)) return;
  let session: Record<string, unknown> | undefined;
  let recommendation = parts[2];
  if (parts[0] === "jobs") {
    if (parts[2] !== "result") return;
    [session] = await query(
      `SELECT c.id,c.feature,j.recommendation_id FROM client_consultation_jobs j JOIN client_consultations c ON c.id=j.consultation_id WHERE j.job_id=$1 AND j.client_id=$2`,
      [id(parts[1]), owner],
    );
    if (!session) {
      if (object(payload.generation))
        throw Error("Consultation job archive is missing.");
      return;
    }
    recommendation = String(session.recommendation_id);
  } else {
    const handle =
      typeof payload.handle === "string"
        ? payload.handle
        : request.headers.get("x-ai-consultation-handle");
    if (!handle) return;
    const upstreamId = await verifyConsultationHandle(handle, owner, secret);
    if (!upstreamId) return;
    const key = createHash("sha256").update(upstreamId).digest("hex");
    const state = object(payload.state) ? payload.state : payload;
    const snapshot: Record<string, unknown> = {};
    for (const key of [
      "primary_service",
      "stage",
      "conversation_status",
      "photo",
      "messages",
      "recommendations",
      "generations",
      "selected_recommendation_id",
      "preferences",
    ])
      if (key in state) snapshot[key] = state[key];
    if (
      parts[1] === "recommendations" &&
      Array.isArray(payload.recommendations)
    )
      snapshot.recommendations = payload;
    if (Buffer.byteLength(JSON.stringify(snapshot)) > 262144)
      throw Error("Consultation record is too large.");
    const feature = String(state.primary_service || "");
    if (["hairstyle", "nails", "makeup"].includes(feature)) {
      [session] = await query(
        `INSERT INTO client_consultations(client_id,source_key,feature,snapshot) VALUES($1,$2,$3,$4::jsonb) ON CONFLICT(client_id,source_key) DO UPDATE SET snapshot=client_consultations.snapshot||excluded.snapshot,updated_at=now() RETURNING id,feature`,
        [owner, key, feature, JSON.stringify(snapshot)],
      );
    } else {
      [session] = await query(
        `UPDATE client_consultations SET snapshot=snapshot||$3::jsonb,updated_at=now() WHERE client_id=$1 AND source_key=$2 RETURNING id,feature`,
        [owner, key, JSON.stringify(snapshot)],
      );
    }
    if (!session) throw Error("Consultation archive is missing.");
    if (request.method === "PUT" && parts[1] === "photo") {
      const form = await request.formData();
      const file = form.get("image");
      if (
        !file ||
        typeof file === "string" ||
        file.size < 1 ||
        file.size > MAX_IMAGE
      )
        throw Error("Invalid reference image.");
      const bytes = Buffer.from(await file.arrayBuffer());
      const decoder = sharp(bytes, {
        limitInputPixels: 4096 * 4096,
        failOn: "warning",
      });
      const info = await decoder.metadata();
      if (
        !["png", "jpeg"].includes(info.format || "") ||
        !info.width ||
        !info.height ||
        info.width > 4096 ||
        info.height > 4096 ||
        (info.pages ?? 1) !== 1
      )
        throw Error("Invalid reference image.");
      await decoder.stats();
      const mime = `image/${info.format}`;
      await query(
        "SELECT beautycore_store_reference($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
        [
          owner,
          session.id,
          `data:${mime};base64,${bytes.toString("base64")}`,
          createHash("sha256").update(bytes).digest("hex"),
          bytes.length,
          mime,
          info.width,
          info.height,
          file.name,
          budget,
        ],
      );
    }
  }
  if (payload.job_id && recommendation) {
    await query(
      "INSERT INTO client_consultation_jobs(job_id,client_id,consultation_id,recommendation_id) VALUES($1,$2,$3,$4) ON CONFLICT(job_id) DO NOTHING",
      [id(payload.job_id), owner, session.id, recommendation],
    );
  }
  if (
    object(payload.result) &&
    object(payload.result.image) &&
    object(payload.result.style) &&
    object(payload.generation) &&
    payload.generation.status === "completed"
  ) {
    const look = await validateLook({
      feature: session.feature,
      styleId: payload.result.style.id,
      image: payload.result.image.data_url,
      status: payload.result.status,
      sourceKind: "consultation",
    });
    await query(
      "SELECT beautycore_archive_result($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11)",
      [
        owner,
        session.id,
        recommendation,
        look.styleType,
        look.styleId,
        look.styleName,
        look.imageUrl,
        look.hash,
        look.imageBytes,
        JSON.stringify(look.lookDetails),
        budget,
      ],
    );
  }
}

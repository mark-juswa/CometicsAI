import { featureFromType, resolveLookInformation, type LookDetails } from './look-information';
import type { Actor } from './core';
import { loadRevenueReport } from './revenue-store';
import type { RevenueWindow } from './revenue-periods';
export type Query = (text: string, values?: unknown[]) => Promise<Record<string, unknown>[]>;
export type SavedInput = {
  styleType: string;
  styleId: string;
  styleName: string;
  imageUrl: string;
  hash: string;
  imageBytes: number;
  sourceKind: string;
  lookDetails?: LookDetails | null;
};
export type Settings = {
  enabled: boolean;
  clientLimit: number;
  storageBudget: number;
};
const lookFields = `g.id,g.client_id AS "clientId",g.style_type AS "styleType",g.style_id AS "styleId",g.style_name AS "styleName",g.saved_at AS "savedAt",g.result_hash AS "resultHash",g.image_bytes AS "imageBytes",g.source_kind AS "sourceKind",g.look_details AS "lookDetails",(g.created_at AT TIME ZONE 'UTC') AS "createdAt"`;
export function lookView(row: Record<string, unknown>) {
  return {
    id: row.id,
    styleType: row.styleType,
    styleId: row.styleId,
    styleName: row.styleName,
    lookDetails:
      row.lookDetails ??
      (featureFromType(String(row.styleType))
        ? resolveLookInformation(featureFromType(String(row.styleType))!, String(row.styleId))
        : null),
    savedAt: row.savedAt,
    createdAt: row.createdAt,
    imageUrl: `/api/saved-looks/${row.id}/image`,
  };
}
const appointmentFields = `a.id,(SELECT service_id FROM appointment_services WHERE appointment_id=a.id) AS "serviceId",a.client_id AS "clientId",a.stylist_id AS "stylistId",a.service_name AS "serviceName",a.service_type AS "serviceType",(a.appointment_date AT TIME ZONE 'UTC') AS "appointmentDate",CASE WHEN a.status IN ('pending','confirmed','in_progress') THEN 90 ELSE a.duration_minutes END AS "durationMinutes",(SELECT to_jsonb(t)-'appointment_id' FROM appointment_service_tracking t WHERE t.appointment_id=a.id) AS "tracking",(SELECT coalesce(json_agg(h ORDER BY h.happened_at,h.id),'[]'::json) FROM appointment_activity h WHERE h.appointment_id=a.id) AS "activity",a.status,a.total_price AS "totalPrice",a.notes,a.completed_at AS "completedAt",a.completed_by AS "completedBy",a.ai_generation_id AS "aiGenerationId"`;
const lookJoin = `CASE WHEN g.id IS NULL THEN NULL ELSE json_build_object('id',g.id,'styleType',g.style_type,'styleName',g.style_name,'styleId',g.style_id,'lookDetails',g.look_details,'imageUrl','/api/saved-looks/'||g.id||'/image') END AS look`;
const serviceRecords = `(SELECT json_build_object('rating',r.rating,'comment',r.comment,'createdAt',r.created_at) FROM appointment_reviews r WHERE r.appointment_id=a.id) AS review,
 coalesce((SELECT json_agg(json_build_object('inventoryId',p.inventory_id,'productName',p.product_name,'brand',p.brand,'quantity',p.quantity,'unit',p.unit,'unitCost',CASE WHEN $1='client' THEN NULL ELSE p.unit_cost END) ORDER BY p.created_at,p.id) FROM appointment_product_usage p WHERE p.appointment_id=a.id),'[]'::json) AS products`;
export function createBusinessStore(query: Query) {
  const getLook = async (identity: string, owner: string) =>
    (
      await query(
        `SELECT ${lookFields} FROM ai_generations g WHERE g.id=$1 AND g.client_id=$2 AND g.result_hash IS NOT NULL`,
        [identity, owner],
      )
    )[0];
  const save = async (owner: string, input: SavedInput, settings: Settings) =>
    (
      await query(
        'SELECT * FROM beautycore_save_look_with_details($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb)',
        [
          owner,
          input.styleType,
          input.styleId,
          input.styleName,
          input.imageUrl,
          input.hash,
          input.imageBytes,
          input.sourceKind,
          settings.clientLimit,
          settings.storageBudget,
          input.lookDetails ? JSON.stringify(input.lookDetails) : null,
        ],
      )
    )[0];
  return {
    processNoShows: async () => query('SELECT beautycore_process_no_shows() AS processed'),
    serviceAction: async (identity:string,actor:Actor,action:string,reason:string|null,date:string|null,now?:string) => (await query('SELECT * FROM beautycore_service_action($1,$2,$3,$4,$5::timestamptz,coalesce($6::timestamptz,clock_timestamp()))',[identity,actor.id,action,reason,date,now??null]))[0],
    revenueReport: (window:RevenueWindow) => loadRevenueReport(query,window),
    currentUser: async (identity: string) =>
      (await query('SELECT id,role FROM users WHERE id=$1 AND is_active=true', [identity]))[0] as Actor | undefined,
    isQualifiedStylist: async (identity: string, serviceType: string) =>
      (await query(`SELECT 1 FROM users u JOIN stylist_specialties ss ON ss.stylist_id=u.id WHERE u.id=$1 AND u.role='stylist' AND u.is_active AND ss.service_type=$2`, [identity,serviceType])).length > 0,
    isAvailable: async (identity: string, date: string, durationMinutes: number, excludeId?: string) =>
      (await query(`SELECT 1 WHERE beautycore_work_available($1,$2::timestamptz,$3) AND NOT EXISTS(SELECT 1 FROM appointments a WHERE a.stylist_id=$1 AND a.status IN ('pending','confirmed','in_progress') AND ($4::uuid IS NULL OR a.id<>$4::uuid) AND ($2::timestamptz AT TIME ZONE 'UTC')<CASE WHEN a.status='in_progress' THEN greatest(a.appointment_date+make_interval(mins=>90),(date_trunc('minute',clock_timestamp())+interval '91 minutes') AT TIME ZONE 'UTC') ELSE a.appointment_date+make_interval(mins=>90) END AND a.appointment_date<($2::timestamptz AT TIME ZONE 'UTC')+make_interval(mins=>$3))`, [identity,date,durationMinutes,excludeId ?? null])).length > 0,
    getLook,
    save,
    listLooks: async (
      owner: string,
      type: string | null,
      offset: number,
      from: string | null = null,
      to: string | null = null,
    ) => {
      const values = [owner, type, from, to];
      const where =
        "g.client_id=$1 AND g.saved_at IS NOT NULL AND ($2::text IS NULL OR g.style_type::text=$2) AND ($3::text IS NULL OR g.saved_at>=($3::date::timestamp AT TIME ZONE 'Asia/Manila')) AND ($4::text IS NULL OR g.saved_at<(($4::date+1)::timestamp AT TIME ZONE 'Asia/Manila'))";
      const [rows, counts] = await Promise.all([
        query(
          `SELECT ${lookFields} FROM ai_generations g WHERE ${where} ORDER BY g.saved_at DESC,g.id DESC LIMIT 12 OFFSET $5`,
          [...values, offset],
        ),
        query(`SELECT count(*)::int AS total FROM ai_generations g WHERE ${where}`, values),
      ]);
      return { looks: rows.map(lookView), total: Number(counts[0].total) };
    },
    hideLook: async (identity: string, owner: string) =>
      (
        await query(
          'UPDATE ai_generations SET saved_at=NULL WHERE id=$1 AND client_id=$2 AND result_hash IS NOT NULL RETURNING id',
          [identity, owner],
        )
      )[0],
    ownImage: async (identity: string, owner: string) =>
      (
        await query(
          'SELECT generated_image_url AS image FROM ai_generations WHERE id=$1 AND client_id=$2 AND result_hash IS NOT NULL',
          [identity, owner],
        )
      )[0],
    authorizedImage: async (identity: string, actor: Actor) =>
      (
        await query(
          `SELECT g.generated_image_url AS image FROM ai_generations g WHERE g.id=$1 AND g.result_hash IS NOT NULL AND (g.client_id=$2 OR ($3='admin' AND EXISTS(SELECT 1 FROM appointments a WHERE a.ai_generation_id=g.id)) OR ($3='stylist' AND EXISTS(SELECT 1 FROM appointments a WHERE a.ai_generation_id=g.id AND a.stylist_id=$2)))`,
          [identity, actor.id, actor.role],
        )
      )[0],
    appointments: async (actor: Actor, upcoming: boolean) =>
      query(
        `SELECT ${appointmentFields},json_build_object('id',c.id,'name',c.name,'email',c.email) AS client,CASE WHEN s.id IS NULL THEN NULL ELSE json_build_object('id',s.id,'name',s.name) END AS stylist,${lookJoin},${serviceRecords} FROM appointments a JOIN users c ON c.id=a.client_id LEFT JOIN users s ON s.id=a.stylist_id LEFT JOIN ai_generations g ON g.id=a.ai_generation_id WHERE ($1='admin' OR ($1='client' AND a.client_id=$2) OR ($1='stylist' AND a.stylist_id=$2)) AND (NOT $3::boolean OR a.status='in_progress' OR (a.status IN ('pending','confirmed') AND a.appointment_date >= (now() AT TIME ZONE 'UTC'))) ORDER BY a.appointment_date DESC,a.id`,
        [actor.role, actor.id, upcoming],
      ),
    appointment: async (identity: string, actor: Actor) =>
      (
        await query(
          `SELECT ${appointmentFields},${serviceRecords} FROM appointments a WHERE a.id=$3 AND ($1='admin' OR ($1='client' AND a.client_id=$2) OR ($1='stylist' AND a.stylist_id=$2))`,
          [actor.role, actor.id, identity],
        )
      )[0],
    serviceCatalog: async () => query('SELECT id,name,service_type AS "serviceType",group_id AS "groupId",group_label AS "groupLabel",price,90 AS "durationMinutes" FROM salon_services WHERE active ORDER BY group_id,id'),
    bookingService: async (feature: string, styleId: string) => (await query('SELECT s.id,s.name,s.service_type AS "serviceType",s.group_id AS "groupId",s.price FROM salon_services s JOIN preset_services p ON p.service_id=s.id WHERE p.feature=$1 AND p.style_id=$2 AND s.active',[feature,styleId]))[0],
    createAppointment: async (input: Record<string, unknown>) =>
      (
        await query(
          'SELECT * FROM beautycore_create_service_appointment($1,$2,$3,$4,$5::timestamptz,$6,$7,$8,$9,$10,$11)',
          [input.clientId,input.stylistId,input.serviceName,input.serviceType,input.date,input.durationMinutes,input.price,input.notes,input.lookId,input.serviceId,input.actorId],
        )
      )[0],
    updateAppointment: async (identity: string, actor: Actor, updates: Record<string, unknown>) => {
      const names: Record<string, string> = {
        status: 'status',
        notes: 'notes',
        appointmentDate: 'appointment_date',
        stylistId: 'stylist_id',
        totalPrice: 'total_price',
      };
      const correction =
        actor.role === 'admin' &&
        Object.keys(updates).every((key) => ['totalPrice', 'notes'].includes(key));
      const values: unknown[] = [identity, actor.role, actor.id];
      const fields = Object.entries(updates).map(([key, value]) => {
        values.push(value);
        return `${names[key]}=$${values.length}${key === 'appointmentDate' ? "::timestamptz AT TIME ZONE 'UTC'" : ''}`;
      });
      return (
        await query(
          `WITH actor_context AS MATERIALIZED (SELECT set_config('beautycore.actor_id',($3::uuid)::text,true),set_config('beautycore.lifecycle_action','status_update',true),set_config('beautycore.action_time','',true),set_config('beautycore.action_reason','',true)) UPDATE appointments SET ${fields.join(',')} FROM actor_context WHERE id=$1 AND ($2='admin' OR ($2='client' AND client_id=$3) OR ($2='stylist' AND stylist_id=$3)) AND (status NOT IN ('completed','cancelled','no_show') ${correction ? "OR status='completed'" : ''}) RETURNING id,status,notes,total_price AS "totalPrice",stylist_id AS "stylistId",appointment_date AT TIME ZONE 'UTC' AS "appointmentDate"`,
          values,
        )
      )[0];
    },
    deleteAppointment: async (identity: string) =>
      (
        await query("DELETE FROM appointments WHERE id=$1 AND status<>'completed' RETURNING id", [
          identity,
        ])
      )[0],
    complete: async (identity: string, actor: Actor, products: unknown[]) =>
      (
        await query('SELECT * FROM beautycore_complete_appointment($1,$2,$3,$4::jsonb)', [
          identity,
          actor.id,
          actor.role,
          JSON.stringify(products),
        ])
      )[0],
    review: async (identity: string, actor: Actor, rating: number, comment: string | null) =>
      (
        await query('SELECT * FROM beautycore_review_appointment($1,$2,$3,$4)', [
          identity,
          actor.id,
          rating,
          comment,
        ])
      )[0],
    stylistPerformance: async (from: string, to: string) =>
      query(
        `
      WITH completed AS (
        SELECT id,stylist_id,total_price FROM appointments
        WHERE status='completed'
        AND appointment_date>=($1::date::timestamp AT TIME ZONE 'Asia/Manila') AT TIME ZONE 'UTC'
        AND appointment_date<(($2::date+1)::timestamp AT TIME ZONE 'Asia/Manila') AT TIME ZONE 'UTC'
      ), counts AS (
        SELECT stylist_id,count(*)::int AS completed,
          count(*) FILTER(WHERE total_price IS NULL)::int AS unpriced,
          coalesce(sum(total_price),0)::bigint AS amount FROM completed GROUP BY stylist_id
      ), ratings AS (
        SELECT r.stylist_id,count(*)::int AS reviews,round(avg(r.rating),2) AS rating
        FROM appointment_reviews r JOIN completed a ON a.id=r.appointment_id GROUP BY r.stylist_id
      ) SELECT s.id,s.name,coalesce(c.completed,0)::int AS completed,coalesce(c.unpriced,0)::int AS unpriced,
        coalesce(c.amount,0)::bigint AS amount,coalesce(r.reviews,0)::int AS reviews,r.rating::float8 AS rating
      FROM users s LEFT JOIN counts c ON c.stylist_id=s.id LEFT JOIN ratings r ON r.stylist_id=s.id
      WHERE s.role='stylist' ORDER BY coalesce(c.completed,0) DESC,s.name,s.id`,
        [from, to],
      ),
    daily: async (
      from: string,
      to: string,
      stylist: string | null,
      status: string,
      offset: number,
    ) =>
      (
        await query(
          `WITH filtered AS (
   SELECT a.id,a.service_name AS "serviceName",a.status,a.total_price AS "totalPrice",a.stylist_id AS "stylistId",coalesce(s.name,'Unassigned') AS "stylistName",c.name AS "clientName",a.appointment_date AT TIME ZONE 'UTC' AS "appointmentDate",to_char((a.appointment_date AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Manila','YYYY-MM-DD') AS "serviceDay",a.ai_generation_id AS "lookId"
   FROM appointments a JOIN users c ON c.id=a.client_id LEFT JOIN users s ON s.id=a.stylist_id
   WHERE a.appointment_date >= ($1::date::timestamp AT TIME ZONE 'Asia/Manila') AT TIME ZONE 'UTC'
   AND a.appointment_date < (($2::date+1)::timestamp AT TIME ZONE 'Asia/Manila') AT TIME ZONE 'UTC'
   AND ($3::text IS NULL OR ($3='unassigned' AND a.stylist_id IS NULL) OR a.stylist_id::text=lower($3))
   AND ($4='all' OR a.status::text=$4)
  ), grouped AS (
   SELECT "serviceDay","stylistId","stylistName",count(*)::int AS count,
   count(*) FILTER(WHERE status='completed')::int AS completed,count(*) FILTER(WHERE status='pending')::int AS pending,
   count(*) FILTER(WHERE status='confirmed')::int AS confirmed,count(*) FILTER(WHERE status='cancelled')::int AS cancelled,
   count(*) FILTER(WHERE status='completed' AND "totalPrice" IS NULL)::int AS unpriced,
   coalesce(sum("totalPrice") FILTER(WHERE status='completed'),0)::bigint AS amount
   FROM filtered GROUP BY "serviceDay","stylistId","stylistName"
  ) SELECT coalesce((SELECT json_agg(x ORDER BY x."serviceDay" DESC,x."stylistName") FROM grouped x),'[]'::json) AS summaries,
  coalesce((SELECT json_agg(x) FROM (SELECT * FROM filtered ORDER BY "appointmentDate",id LIMIT 12 OFFSET $5) x),'[]'::json) AS rows,
  (SELECT count(*)::int FROM filtered) AS total,
  coalesce((SELECT sum(amount) FROM grouped),0)::bigint AS amount,
  coalesce((SELECT sum(unpriced) FROM grouped),0)::int AS unpriced`,
          [from, to, stylist, status, offset],
        )
      )[0],
  };
}
export type BusinessStore = ReturnType<typeof createBusinessStore>;

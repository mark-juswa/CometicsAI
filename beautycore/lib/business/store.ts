import { featureFromType, resolveLookInformation, type LookDetails } from './look-information';
import type { Actor } from './core';
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
const appointmentFields = `a.id,a.client_id AS "clientId",a.stylist_id AS "stylistId",a.service_name AS "serviceName",a.service_type AS "serviceType",(a.appointment_date AT TIME ZONE 'UTC') AS "appointmentDate",a.status,a.total_price AS "totalPrice",a.notes,a.ai_generation_id AS "aiGenerationId"`;
const lookJoin = `CASE WHEN g.id IS NULL THEN NULL ELSE json_build_object('id',g.id,'styleType',g.style_type,'styleName',g.style_name,'styleId',g.style_id,'lookDetails',g.look_details,'imageUrl','/api/saved-looks/'||g.id||'/image') END AS look`;
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
    currentUser: async (identity: string) =>
      (await query('SELECT id,role FROM users WHERE id=$1', [identity]))[0] as Actor | undefined,
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
          `SELECT g.generated_image_url AS image FROM ai_generations g WHERE g.id=$1 AND g.result_hash IS NOT NULL AND (g.client_id=$2 OR $3='admin' OR ($3='stylist' AND EXISTS(SELECT 1 FROM appointments a WHERE a.ai_generation_id=g.id AND a.stylist_id=$2)))`,
          [identity, actor.id, actor.role],
        )
      )[0],
    appointments: async (actor: Actor, upcoming: boolean) =>
      query(
        `SELECT ${appointmentFields},json_build_object('id',c.id,'name',c.name,'email',c.email) AS client,CASE WHEN s.id IS NULL THEN NULL ELSE json_build_object('id',s.id,'name',s.name) END AS stylist,${lookJoin} FROM appointments a JOIN users c ON c.id=a.client_id LEFT JOIN users s ON s.id=a.stylist_id LEFT JOIN ai_generations g ON g.id=a.ai_generation_id WHERE ($1='admin' OR ($1='client' AND a.client_id=$2) OR ($1='stylist' AND a.stylist_id=$2)) AND (NOT $3::boolean OR a.appointment_date >= (now() AT TIME ZONE 'UTC')) ORDER BY a.appointment_date DESC,a.id`,
        [actor.role, actor.id, upcoming],
      ),
    appointment: async (identity: string, actor: Actor) =>
      (
        await query(
          `SELECT ${appointmentFields} FROM appointments a WHERE a.id=$1 AND ($2='admin' OR ($2='client' AND a.client_id=$3) OR ($2='stylist' AND a.stylist_id=$3))`,
          [identity, actor.role, actor.id],
        )
      )[0],
    createAppointment: async (input: Record<string, unknown>) =>
      (
        await query(
          `INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,total_price,notes,ai_generation_id) VALUES($1,$2,$3,$4,$5::timestamptz AT TIME ZONE 'UTC',$6,$7,$8) RETURNING id`,
          [
            input.clientId,
            input.stylistId,
            input.serviceName,
            input.serviceType,
            input.date,
            input.price,
            input.notes,
            input.lookId,
          ],
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
      const values: unknown[] = [identity, actor.role, actor.id];
      const fields = Object.entries(updates).map(([key, value]) => {
        values.push(value);
        return `${names[key]}=$${values.length}${key === 'appointmentDate' ? "::timestamptz AT TIME ZONE 'UTC'" : ''}`;
      });
      return (
        await query(
          `UPDATE appointments SET ${fields.join(',')} WHERE id=$1 AND ($2='admin' OR ($2='client' AND client_id=$3) OR ($2='stylist' AND stylist_id=$3)) RETURNING id,status,notes,total_price AS "totalPrice",stylist_id AS "stylistId",appointment_date AT TIME ZONE 'UTC' AS "appointmentDate"`,
          values,
        )
      )[0];
    },
    deleteAppointment: async (identity: string) =>
      (await query('DELETE FROM appointments WHERE id=$1 RETURNING id', [identity]))[0],
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

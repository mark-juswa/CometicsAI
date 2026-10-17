import { allServices, parsePrice } from '../services';
import {
  Actor,
  BusinessError,
  PRIVATE,
  MAX_SAVE_BODY,
  boundedJson,
  day,
  fail,
  featureToType,
  id,
  mutationOrigin,
  paging,
  salonDay,
  validateLook,
} from './core';
import { BusinessStore, Settings, lookView } from './store';
export type Dependencies = {
  actor: () => Promise<Actor | null>;
  store: BusinessStore;
  settings: Settings;
  publicOrigin?: string;
  now?: () => number;
};
const statuses = ['pending', 'confirmed', 'completed', 'cancelled'];
function json(value: unknown, status = 200) {
  return Response.json(value, { status, headers: PRIVATE });
}
async function user(request: Request, deps: Dependencies) {
  const actor = await deps.actor();
  if (!actor) fail('Sign in to continue.', 401);
  if (request.method !== 'GET') mutationOrigin(request, deps.publicOrigin);
  return actor;
}
async function controlled(action: () => Promise<Response>) {
  try {
    return await action();
  } catch (error) {
    if (error instanceof BusinessError) return json({ error: error.message }, error.status);
    return json({ error: 'This feature is temporarily unavailable. Please try again.' }, 503);
  }
}
let savesInFlight = 0;
async function boundedSave(action: () => Promise<Response>) {
  if (savesInFlight >= 2) fail('Other previews are being saved. Please try again shortly.', 429);
  savesInFlight++;
  try {
    return await action();
  } finally {
    savesInFlight--;
  }
}
function enabled(deps: Dependencies) {
  if (!deps.settings.enabled)
    fail('Saved looks are not enabled yet. Your preview is still available to download.', 503);
}
function dateInput(value: unknown, future = false, now = Date.now()): string {
  if (
    typeof value !== 'string' ||
    !/(?:Z|[+-]\d{2}:\d{2})$/.test(value) ||
    !Number.isFinite(Date.parse(value))
  )
    fail('Choose a valid date and time with a timezone.');
  day(value.slice(0, 10));
  if (future && Date.parse(value) <= now) fail('Choose a future date and time.');
  return new Date(value).toISOString();
}
function price(value: unknown) {
  if (value === null) return null;
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0 || value > 100000000)
    fail('Enter a nonnegative whole-peso amount.');
  return value;
}
function notes(value: unknown) {
  if (value === undefined || value === null) return null;
  if (typeof value !== 'string' || value.length > 1000)
    fail('Notes must be no more than 1000 characters.');
  return value.trim() || null;
}
async function saveResult(
  owner: string,
  input: Parameters<BusinessStore['save']>[1],
  deps: Dependencies,
) {
  const result = await deps.store.save(owner, input, deps.settings);
  if (result.outcome === 'client_limit')
    fail(
      `You can keep up to ${deps.settings.clientLimit} saved looks. Remove a saved look before adding another.`,
      409,
    );
  if (result.outcome === 'storage_limit')
    fail('Saved image storage is full. Your preview is still available to download.', 507);
  if (typeof result.look_id !== 'string') fail('The preview was not saved.', 503);
  const row = await deps.store.getLook(result.look_id, owner);
  if (!row) fail('The saved look could not be read.', 503);
  return json({ look: lookView(row) }, result.outcome === 'created' ? 201 : 200);
}
export function savedLooks(
  request: Request,
  identity: string | undefined,
  image: boolean,
  deps: Dependencies,
): Promise<Response> {
  return controlled(async () => {
    const actor = await user(request, deps);
    enabled(deps);
    if (identity) id(identity);
    if (image) {
      if (request.method !== 'GET' || !identity) fail('Operation not found.', 404);
      const row = await deps.store.authorizedImage(identity, actor);
      if (!row || typeof row.image !== 'string') fail('Look not found.', 404);
      const match = /^data:(image\/(?:png|jpeg));base64,([A-Za-z0-9+/]+={0,2})$/.exec(row.image);
      if (!match) fail('Image is unavailable.', 404);
      return new Response(Buffer.from(match[2], 'base64'), {
        headers: {
          ...PRIVATE,
          'Content-Type': match[1],
          'Content-Disposition': 'inline',
          'X-Content-Type-Options': 'nosniff',
          'Cross-Origin-Resource-Policy': 'same-origin',
        },
      });
    }
    if (actor.role !== 'client') fail('Client access is required.', 403);
    if (!identity && request.method === 'GET') {
      const params = new URL(request.url).searchParams;
      const { page, offset } = paging(params);
      const feature = params.get('feature');
      const type = feature ? featureToType(feature) : null;
      const from = params.has('from') ? day(params.get('from')) : null;
      const to = params.has('to') ? day(params.get('to')) : null;
      if (from && to && from > to) fail('The end date must be after the start date.');
      return json({
        ...(await deps.store.listLooks(actor.id, type, offset, from, to)),
        page,
        pageSize: 12,
        clientLimit: deps.settings.clientLimit,
      });
    }
    if (!identity && request.method === 'POST')
      return boundedSave(async () =>
        saveResult(actor.id, await validateLook(await boundedJson(request, MAX_SAVE_BODY)), deps),
      );
    if (!identity) fail('Operation not found.', 404);
    const row = await deps.store.getLook(identity, actor.id);
    if (!row) fail('Look not found.', 404);
    if (request.method === 'GET') {
      if (!row.savedAt) fail('Look is no longer saved.', 404);
      return json({ look: lookView(row) });
    }
    if (request.method === 'PATCH') {
      const body = await boundedJson(request);
      if (Object.keys(body).length !== 1 || typeof body.saved !== 'boolean')
        fail('Choose saved or removed.');
      if (body.saved) {
        const data = await deps.store.ownImage(identity, actor.id);
        if (!data) fail('Look not found.', 404);
        return saveResult(
          actor.id,
          {
            styleType: String(row.styleType),
            styleId: String(row.styleId),
            styleName: String(row.styleName),
            imageUrl: String(data.image),
            hash: String(row.resultHash),
            imageBytes: Number(row.imageBytes),
            sourceKind: String(row.sourceKind),
          },
          deps,
        );
      }
      await deps.store.hideLook(identity, actor.id);
      return json({ removed: true });
    }
    return fail('Operation not found.', 404);
  });
}
export function bookingApi(
  request: Request,
  identity: string | undefined,
  deps: Dependencies,
): Promise<Response> {
  return controlled(async () => {
    const actor = await user(request, deps);
    if (identity) id(identity);
    if (!identity && request.method === 'GET')
      return json({
        appointments: await deps.store.appointments(
          actor,
          new URL(request.url).searchParams.get('upcoming') === 'true',
        ),
      });
    if (!identity && request.method === 'POST') {
      const body = await boundedJson(request);
      const allowed = [
        'serviceName',
        'serviceType',
        'appointmentDate',
        'stylistId',
        'totalPrice',
        'notes',
        'lookId',
        'clientId',
      ];
      if (Object.keys(body).some((k) => !allowed.includes(k))) fail('Unexpected booking field.');
      const service = allServices.find(
        (s) => s.name === body.serviceName && s.serviceType === body.serviceType,
      );
      if (!service) fail('Choose a service from the salon catalog.');
      const owner = actor.role === 'client' ? actor.id : id(body.clientId);
      if (actor.role === 'client' && body.clientId !== undefined && body.clientId !== actor.id)
        fail('You can only book for yourself.', 403);
      const client = await deps.store.currentUser(owner);
      if (!client || client.role !== 'client') fail('Choose a valid client.');
      const date = dateInput(body.appointmentDate, true, deps.now?.());
      const stylist = body.stylistId ? id(body.stylistId) : null;
      if (stylist && (await deps.store.currentUser(stylist))?.role !== 'stylist')
        fail('Choose an available stylist or no preference.');
      const lookId = body.lookId ? id(body.lookId) : null;
      if (lookId) {
        enabled(deps);
        const look = await deps.store.getLook(lookId, owner);
        if (!look || !look.savedAt) fail('Choose one of this client’s saved looks.', 404);
        if (look.styleType !== service.serviceType)
          fail('Choose a service that matches the selected look.');
      }
      const amount =
        actor.role === 'admin' && body.totalPrice !== undefined
          ? price(body.totalPrice)
          : parsePrice(service.price);
      const appointment = await deps.store.createAppointment({
        clientId: owner,
        stylistId: stylist,
        serviceName: service.name,
        serviceType: service.serviceType,
        date,
        price: amount,
        notes: notes(body.notes),
        lookId,
      });
      return json({ appointment }, 201);
    }
    if (!identity) fail('Operation not found.', 404);
    const row = await deps.store.appointment(identity, actor);
    if (!row) fail('Appointment not found.', 404);
    if (request.method === 'GET') return json({ appointment: row });
    if (request.method === 'DELETE') {
      if (actor.role !== 'admin') fail('Admin access is required.', 403);
      await deps.store.deleteAppointment(identity);
      return json({ success: true });
    }
    if (request.method !== 'PATCH') fail('Operation not found.', 404);
    const body = await boundedJson(request);
    const allowed =
      actor.role === 'client'
        ? ['status']
        : actor.role === 'stylist'
          ? ['status', 'notes', 'appointmentDate']
          : ['status', 'notes', 'appointmentDate', 'stylistId', 'totalPrice'];
    if (!Object.keys(body).length || Object.keys(body).some((k) => !allowed.includes(k)))
      fail('These appointment details cannot be changed.', 403);
    const update: Record<string, unknown> = {};
    if (body.status !== undefined) {
      if (typeof body.status !== 'string' || !statuses.includes(body.status))
        fail('Invalid status.');
      if (
        actor.role === 'client' &&
        (body.status !== 'cancelled' || ['completed', 'cancelled'].includes(String(row.status)))
      )
        fail('Only an active booking can be cancelled.', 403);
      update.status = body.status;
    }
    if (body.notes !== undefined) update.notes = notes(body.notes);
    if (body.appointmentDate !== undefined)
      update.appointmentDate = dateInput(body.appointmentDate);
    if (body.totalPrice !== undefined) update.totalPrice = price(body.totalPrice);
    if (body.stylistId !== undefined) {
      const stylist = body.stylistId === null ? null : id(body.stylistId);
      if (stylist && (await deps.store.currentUser(stylist))?.role !== 'stylist')
        fail('Choose a valid stylist.');
      update.stylistId = stylist;
    }
    const result = await deps.store.updateAppointment(identity, actor, update);
    if (!result) fail('Appointment assignment changed. Reload the page.', 409);
    return json({ appointment: result });
  });
}
export function dailyServices(request: Request, deps: Dependencies): Promise<Response> {
  return controlled(async () => {
    const actor = await user(request, deps);
    if (actor.role !== 'admin') fail('Admin access is required.', 403);
    if (request.method !== 'GET') fail('Operation not found.', 404);
    const params = new URL(request.url).searchParams;
    const from = day(params.get('from') ?? salonDay());
    const to = day(params.get('to') ?? from);
    const span = (Date.parse(to) - Date.parse(from)) / 86400000;
    if (span < 0 || span > 30) fail('Choose a date range of up to 31 days.');
    const stylist = params.get('stylist');
    if (stylist && stylist !== 'unassigned') id(stylist);
    const status = params.get('status') ?? 'all';
    if (status !== 'all' && !statuses.includes(status)) fail('Invalid appointment status.');
    const { page, offset } = paging(params);
    const report = await deps.store.daily(from, to, stylist, status, offset);
    return json({
      ...report,
      from,
      to,
      page,
      pageSize: 12,
      timeZone: 'Asia/Manila',
      dateBasis: 'Scheduled service date',
      amountBasis: 'Recorded completed-service amount',
    });
  });
}

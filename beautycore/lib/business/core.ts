import { createHash } from 'node:crypto';
import sharp from 'sharp';
import { publicStyle, snapshotLookInformation } from './look-information';
import type { UserRole } from '../../db/schema';
export type Actor = { id: string; role: UserRole };
export class BusinessError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export const MAX_IMAGE = 8 * 1024 * 1024;
export const MAX_SAVE_BODY = Math.ceil((MAX_IMAGE * 4) / 3) + 16384;
export const PRIVATE = { 'Cache-Control': 'private, no-store' };
export function object(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}
export function fail(message: string, status = 400): never {
  throw new BusinessError(status, message);
}
export function id(value: unknown): string {
  if (typeof value !== 'string' || !UUID.test(value)) fail('Invalid reference.');
  return value;
}
export function mutationOrigin(request: Request, configured?: string) {
  let expected = new URL(request.url).origin;
  if (configured !== undefined) {
    try {
      const u = new URL(configured);
      if (
        u.protocol !== 'https:' ||
        u.username ||
        u.password ||
        u.pathname !== '/' ||
        u.search ||
        u.hash
      )
        fail('Application origin is not configured.', 503);
      expected = u.origin;
    } catch {
      fail('Application origin is not configured.', 503);
    }
  }
  if (request.headers.get('origin') !== expected) fail('Same-origin request required.', 403);
}
export async function boundedJson(
  request: Request,
  limit = 16384,
): Promise<Record<string, unknown>> {
  const declared = request.headers.get('content-length');
  if (declared && (!/^\d+$/.test(declared) || Number(declared) > limit))
    fail('Request is too large.', 413);
  if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json'))
    fail('JSON request required.', 415);
  const reader = request.body?.getReader();
  if (!reader) fail('Request body is required.');
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.length;
      if (size > limit) fail('Request is too large.', 413);
      chunks.push(part.value);
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  try {
    const body: unknown = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    if (!object(body)) fail('Invalid request body.');
    return body;
  } catch (error) {
    if (error instanceof BusinessError) throw error;
    return fail('Invalid JSON request.');
  }
}
export function featureToType(feature: string): 'hair' | 'nail' | 'makeup' {
  if (feature === 'hairstyle') return 'hair';
  if (feature === 'nails') return 'nail';
  if (feature === 'makeup') return 'makeup';
  return fail('Invalid beauty feature.');
}
export function typeToGroup(type: string) {
  return type === 'hair'
    ? 'hair-design'
    : type === 'nail'
      ? 'nail-studio'
      : type === 'makeup'
        ? 'makeup'
        : null;
}
export async function validateLook(body: Record<string, unknown>) {
  if (
    Object.keys(body).some(
      (k) => !['feature', 'styleId', 'image', 'sourceKind', 'status'].includes(k),
    )
  )
    fail('Unexpected saved-look field.');
  const feature = String(body.feature);
  const styleType = featureToType(feature);
  const styleId = typeof body.styleId === 'string' ? body.styleId : '';
  const styleName = publicStyle(feature, styleId)?.name;
  if (!styleName) fail('Choose a supported style.');
  if (body.status !== 'completed') fail('Only a completed preview can be saved.');
  if (body.sourceKind !== 'manual' && body.sourceKind !== 'consultation')
    fail('Invalid preview source.');
  if (typeof body.image !== 'string') fail('A generated image is required.');
  const match = /^data:(image\/(?:png|jpeg));base64,([A-Za-z0-9+/]+={0,2})$/.exec(body.image);
  if (!match || match[2].length > Math.ceil(MAX_IMAGE / 3) * 4)
    fail('Choose a PNG or JPEG preview up to 8 MB.', 413);
  const image = Buffer.from(match[2], 'base64');
  if (!image.length || image.length > MAX_IMAGE || image.toString('base64') !== match[2])
    fail('Invalid or oversized preview image.', 413);
  try {
    const info = await sharp(image, {
      limitInputPixels: 4096 * 4096,
      failOn: 'warning',
    }).metadata();
    if (
      !['png', 'jpeg'].includes(info.format ?? '') ||
      `image/${info.format}` !== match[1] ||
      !info.width ||
      !info.height ||
      info.width > 4096 ||
      info.height > 4096 ||
      (info.pages ?? 1) !== 1
    )
      fail('Use a single PNG or JPEG image up to 4096 pixels per side.');
    // Decode the whole image too: a valid header alone is insufficient.
    await sharp(image, {
      limitInputPixels: 4096 * 4096,
      failOn: 'warning',
    }).stats();
  } catch (error) {
    if (error instanceof BusinessError) throw error;
    fail('The preview image could not be read.');
  }
  return {
    styleType,
    styleId,
    styleName,
    imageUrl: body.image,
    hash: createHash('sha256').update(image).digest('hex'),
    imageBytes: image.length,
    sourceKind: body.sourceKind as 'manual' | 'consultation',
    lookDetails: snapshotLookInformation(feature as 'hairstyle' | 'makeup' | 'nails', styleId),
  };
}
export { SALON_TIMEZONE, salonDay, salonDateTime } from './dates';
import { day as parseDay } from './dates';
export function day(value: unknown): string {
  try {
    return parseDay(value);
  } catch {
    return fail('Invalid date.');
  }
}
export function paging(search: URLSearchParams) {
  const page = Number(search.get('page') ?? '1');
  if (!Number.isSafeInteger(page) || page < 1 || page > 10000) fail('Invalid page.');
  return { page, limit: 12, offset: (page - 1) * 12 };
}

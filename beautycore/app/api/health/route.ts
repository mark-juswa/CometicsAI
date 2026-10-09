export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

// Render liveness; intentionally does not wake Gemini or start inference.
export function GET(): Response {
  return Response.json({ status: 'ok', service: 'beautycore' },
    { headers: { 'Cache-Control': 'no-store' } });
}

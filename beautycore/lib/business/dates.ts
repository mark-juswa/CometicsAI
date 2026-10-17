function invalid(message: string): never {
  throw new Error(message);
}
export const SALON_TIMEZONE = 'Asia/Manila';
export function salonDay(date = new Date()): string {
  const p = new Intl.DateTimeFormat('en-US', {
    timeZone: SALON_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(date);
  return `${p.find((x) => x.type === 'year')!.value}-${p.find((x) => x.type === 'month')!.value}-${p.find((x) => x.type === 'day')!.value}`;
}
export function day(value: unknown): string {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value))
    invalid('Use a date in YYYY-MM-DD format.');
  const d = new Date(value + 'T00:00:00Z');
  if (!Number.isFinite(d.getTime()) || d.toISOString().slice(0, 10) !== value)
    invalid('Invalid date.');
  return value;
}
export function salonDateTime(date: string, time: string): string {
  day(date);
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(time)) invalid('Choose a valid time.');
  return new Date(`${date}T${time}:00+08:00`).toISOString();
}

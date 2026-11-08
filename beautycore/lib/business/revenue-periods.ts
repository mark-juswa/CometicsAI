import { day, salonDay } from "./dates";
export const REVENUE_PERIODS = ["day", "week", "month", "year"] as const;
export type RevenuePeriod = (typeof REVENUE_PERIODS)[number];
export type RevenueWindow = {
  period: RevenuePeriod;
  date: string;
  from: string;
  to: string;
  previousFrom: string;
  previousTo: string;
  label: string;
  bucket: "hour" | "day" | "month";
};
const iso = (date: Date) => date.toISOString().slice(0, 10);
const shiftDays = (value: string, count: number) => {
  const date = new Date(value + "T00:00:00Z");
  date.setUTCDate(date.getUTCDate() + count);
  return iso(date);
};
export function revenueWindow(
  period: unknown,
  date = salonDay(),
): RevenueWindow {
  if (
    typeof period !== "string" ||
    !REVENUE_PERIODS.includes(period as RevenuePeriod)
  )
    throw Error("Choose day, week, month, or year.");
  day(date);
  if (Number(date.slice(0, 4)) < 1900 || Number(date.slice(0, 4)) > 2200)
    throw Error("Choose a date between 1900 and 2200.");
  const start = new Date(date + "T00:00:00Z");
  if (period === "week")
    start.setUTCDate(start.getUTCDate() - ((start.getUTCDay() + 6) % 7));
  if (period === "month") start.setUTCDate(1);
  if (period === "year") {
    start.setUTCMonth(0, 1);
  }
  const next = new Date(start),
    previous = new Date(start);
  if (period === "day") {
    next.setUTCDate(next.getUTCDate() + 1);
    previous.setUTCDate(previous.getUTCDate() - 1);
  }
  if (period === "week") {
    next.setUTCDate(next.getUTCDate() + 7);
    previous.setUTCDate(previous.getUTCDate() - 7);
  }
  if (period === "month") {
    next.setUTCMonth(next.getUTCMonth() + 1);
    previous.setUTCMonth(previous.getUTCMonth() - 1);
  }
  if (period === "year") {
    next.setUTCFullYear(next.getUTCFullYear() + 1);
    previous.setUTCFullYear(previous.getUTCFullYear() - 1);
  }
  const from = iso(start),
    to = shiftDays(iso(next), -1);
  const format = (value: string, options: Intl.DateTimeFormatOptions) =>
    new Intl.DateTimeFormat("en-PH", { timeZone: "UTC", ...options }).format(
      new Date(value + "T00:00:00Z"),
    );
  const label =
    period === "year"
      ? from.slice(0, 4)
      : period === "month"
        ? format(from, { month: "long", year: "numeric" })
        : period === "day"
          ? format(from, { month: "short", day: "numeric", year: "numeric" })
          : `${format(from, { month: "short", day: "numeric" })} – ${format(to, { month: "short", day: "numeric", year: "numeric" })}`;
  return {
    period: period as RevenuePeriod,
    date,
    from,
    to,
    previousFrom: iso(previous),
    previousTo: shiftDays(from, -1),
    label,
    bucket: period === "day" ? "hour" : period === "year" ? "month" : "day",
  };
}
export type RevenueStylist = {
  id: string;
  name: string;
  email: string;
  isActive: boolean;
  workAvailable: boolean;
  specialties: string[];
  amount: number;
  completed: number;
  unpriced: number;
  dayAmount: number;
  monthAmount: number;
  yearAmount: number;
};
export type RevenueBucket = {
  key: string;
  label: string;
  amount: number;
  completed: number;
};
export type RevenueReport = {
  window: RevenueWindow;
  summary: {
    amount: number;
    completed: number;
    unpriced: number;
    previousAmount: number;
    previousCompleted: number;
    allTimeAmount: number;
    unassignedAmount: number;
    changePercent: number | null;
  };
  series: RevenueBucket[];
  stylists: RevenueStylist[];
  timeZone: string;
  amountBasis: string;
};

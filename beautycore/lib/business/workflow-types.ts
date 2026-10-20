export type ProductUsage = {
  inventoryId?: string | null;
  productName: string;
  brand: string | null;
  quantity: number | null;
  unit: string | null;
  unitCost: number | null;
};
export type AppointmentReview = { rating: number; comment: string | null; createdAt: string };
export type ServiceRecord = {
  completedAt?: string | null;
  review?: AppointmentReview | null;
  products?: ProductUsage[];
};
export const PRODUCT_UNITS = [
  'ml',
  'l',
  'g',
  'kg',
  'piece',
  'pair',
  'bottle',
  'pack',
  'set',
  'application',
] as const;

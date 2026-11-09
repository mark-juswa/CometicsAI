export type ProductUsage = {
  consumeStock?: boolean;
  adjustmentReason?: string|null;
  inventoryId?: string | null;
  productName: string;
  brand: string | null;
  quantity: number | null;
  unit: string | null;
  unitCost: number | null;
};
export type AppointmentReview = { rating: number; comment: string | null; createdAt: string };
export type ServiceRecord = {
  inventoryConsumption?:{productName:string;unit:string;requestedQuantity:number;deductedQuantity:number;netQuantity:number;shortage:number;equipment:boolean}[];
  tracking?: {arrived_at?:string|null;started_at?:string|null;ended_at?:string|null;no_show_at?:string|null;release_at?:string|null;last_actor?:string|null}|null;
  activity?: {id:string;action:string;status:string;actor_id?:string|null;source:string;happened_at:string;explanation?:string|null}[];

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
  'tube',
  'pack',
  'set',
  'application',
] as const;

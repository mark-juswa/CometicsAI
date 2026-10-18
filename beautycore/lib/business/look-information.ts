import styles from './style-catalog.json';
import { allServices, parsePrice } from '../services';
import type { FeatureId } from '../ai/browser-client';

export type ServiceEstimate = {
  serviceName: string;
  amount: number | null;
  priceLabel: string;
  kind: 'fixed' | 'from' | 'per_nail' | 'quote';
};
export type LookDetails = {
  version: 1;
  feature: FeatureId;
  styleId: string;
  description: string;
  currency: 'PHP';
  options: ServiceEstimate[];
  quoteRequired: boolean;
  note: string;
  catalogVersion: string;
  capturedAt: string | null;
};
const type = { hairstyle: 'hair', makeup: 'makeup', nails: 'nail' } as const;
export function featureFromType(value: string): FeatureId | null {
  return value === 'hair'
    ? 'hairstyle'
    : value === 'nail'
      ? 'nails'
      : value === 'makeup'
        ? 'makeup'
        : null;
}
export function publicStyle(feature: string, styleId: string) {
  if (!Object.hasOwn(styles, feature)) return null;
  const rows = styles[feature as FeatureId] as Record<
    string,
    { name: string; description: string; services: string[] }
  >;
  return Object.hasOwn(rows, styleId) ? rows[styleId] : null;
}
function fingerprint(value: unknown) {
  let hash = 2166136261;
  for (const ch of JSON.stringify(value)) hash = Math.imul(hash ^ ch.charCodeAt(0), 16777619);
  return (hash >>> 0).toString(16);
}
export function resolveLookInformation(feature: FeatureId, styleId: string): LookDetails | null {
  const style = publicStyle(feature, styleId);
  if (!style) return null;
  const options: ServiceEstimate[] = style.services.flatMap((name) => {
    const service = allServices.find((s) => s.name === name && s.serviceType === type[feature]);
    if (!service) return [];
    const amount = parsePrice(service.price);
    return [
      {
        serviceName: service.name,
        amount,
        priceLabel: service.price,
        kind:
          amount === null
            ? 'quote'
            : service.name.includes('(per nail)')
              ? 'per_nail'
              : service.price.startsWith('Mula')
                ? 'from'
                : 'fixed',
      },
    ];
  });
  const quoteRequired = options.length === 0 || options.every((option) => option.kind === 'quote');
  const note =
    feature === 'nails'
      ? 'Choose the manicure service when booking. Nail art is priced per nail; ask the salon whether an additional charge applies.'
      : 'These are service options, not a fixed price for this style. Choose the applicable service when booking; the salon confirms the final price.';
  return {
    version: 1,
    feature,
    styleId,
    description: style.description,
    currency: 'PHP',
    options,
    quoteRequired,
    note,
    catalogVersion: 'look-info-1-' + fingerprint({ description: style.description, options }),
    capturedAt: null,
  };
}
export function snapshotLookInformation(feature: FeatureId, styleId: string): LookDetails | null {
  const details = resolveLookInformation(feature, styleId);
  return details ? { ...details, capturedAt: new Date().toISOString() } : null;
}

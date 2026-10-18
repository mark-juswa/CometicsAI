import { resolveLookInformation, type LookDetails } from '../lib/business/look-information';
import type { FeatureId } from '../lib/ai/browser-client';

export function LookInformation({
  feature,
  styleId,
  details,
  fallbackDescription,
  saved = false,
}: {
  feature: FeatureId | null;
  styleId: string;
  details?: LookDetails | null;
  fallbackDescription?: string;
  saved?: boolean;
}) {
  const info = details ?? (feature ? resolveLookInformation(feature, styleId) : null);
  return (
    <section className="look-information" aria-label="Look description and estimated cost">
      <p className="look-description">
        {info?.description ||
          fallbackDescription ||
          'Discuss this style and the required service with the salon.'}
      </p>
      <p className="look-estimate-label">
        Estimated cost{saved && info?.capturedAt ? ' when saved' : ''}
      </p>
      {(!info || info.quoteRequired) && <p>Price to be confirmed by the salon.</p>}
      {!!info?.options.length && (
        <ul>
          {info.options.map((option) => (
            <li key={option.serviceName}>
              <span>{option.serviceName}</span>
              <strong>
                {option.amount === null
                  ? 'Price to be confirmed'
                  : option.priceLabel.replace(/^Mula /, 'From ')}
              </strong>
            </li>
          ))}
        </ul>
      )}
      {saved && !info?.capturedAt && (
        <p className="look-estimate-note">
          Current service estimate; the original estimate was not recorded.
        </p>
      )}
      <p className="look-estimate-note">
        {info?.note ||
          'The salon confirms availability and the final price when you choose a service.'}
      </p>
    </section>
  );
}

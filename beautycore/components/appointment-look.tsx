'use client';
import Image from 'next/image';
import { LookInformation } from './look-information';
import { featureFromType, type LookDetails } from '../lib/business/look-information';
import { useRef } from 'react';
export type AppointmentLook = {
  id: string;
  styleName: string;
  styleType: string;
  styleId?: string;
  lookDetails?: LookDetails | null;
  imageUrl: string;
};
export function AppointmentLookPreview({ look }: { look: AppointmentLook | null | undefined }) {
  const ref = useRef<HTMLDialogElement>(null);
  if (!look) return null;
  return (
    <div className="booking-look-reference">
      <button
        type="button"
        onClick={() => ref.current?.showModal()}
        className="flex items-center gap-3 text-left"
      >
        <Image
          src={look.imageUrl}
          alt={`Requested ${look.styleName}`}
          width={80}
          height={80}
          unoptimized
          className="h-20 w-20 rounded object-contain"
        />
        <span>
          <strong className="block">{look.styleName}</strong>
          <span className="text-sm text-secondary">View requested look</span>
        </span>
      </button>
      <dialog
        aria-label={`Requested ${look.styleName}`}
        ref={ref}
        className="studio-result-dialog"
        onClick={(e) => {
          if (e.target === ref.current) ref.current.close();
        }}
      >
        <div className="studio-result-content">
          <div className="studio-result-header">
            <h2>{look.styleName}</h2>
            <button
              type="button"
              className="studio-secondary-button"
              onClick={() => ref.current?.close()}
            >
              Close preview
            </button>
          </div>
          <div className="relative h-[65vh]">
            <Image
              src={look.imageUrl}
              alt={`Client-selected ${look.styleName}`}
              fill
              unoptimized
              className="object-contain"
            />
          </div>
          <LookInformation
            saved
            feature={featureFromType(look.styleType)}
            styleId={look.styleId ?? ''}
            details={look.lookDetails}
          />
          <p className="studio-result-note">
            Client-selected reference for this appointment. Confirm the final service with the
            client.
          </p>
        </div>
      </dialog>
    </div>
  );
}

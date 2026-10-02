# Mobile studio design

Source: existing `beautycore/app/ai-studio.css`, `beautycore/components/ai-studio.tsx` and original Hair, Makeup, Nails and Consultation screens. Supervisor direction is CONFIRMED.

The studio is dark purple with gold accents, serif editorial headings and simple sans-serif controls. Preserve the Andrea's wordmark, numbered panels, gold selected borders, style monograms and nail swatches. Native tokens live in `constants/theme.ts`. Georgia on Apple/web and the native serif family on Android preserve the web heading hierarchy without bundling proprietary fonts. Native system sans maps the web Segoe UI/Arial fallback.

Build mandate: service selection, then a single-column studio with hero, photo panel, catalog panel and explicit preview action. Original and mock result are stacked on phones. Navigation uses Expo Router and Android back. Consultation preserves Service, Direction, Your Looks labels but stops at the service overview in this slice. A connectivity screen exposes explicit checks and a readable error.

All cards fit the available width, long names wrap, controls are at least 44 points tall, and content scrolls inside safe areas. Keep loading, empty, error and mock states distinct. Catalogs are real API data; mock preview is the unchanged local photo and must say so. No invented transformation or recommendation.

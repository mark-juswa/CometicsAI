# Mobile studio design

Source: existing `beautycore/app/ai-studio.css`, `beautycore/components/ai-studio.tsx` and original Hair, Makeup, Nails and Consultation screens. Supervisor direction is CONFIRMED.

The studio is dark purple with gold accents, serif editorial headings and simple sans-serif controls. Preserve the Andrea's wordmark, numbered panels, gold selected borders, style monograms and nail swatches. Native tokens live in `constants/theme.ts`. Georgia on Apple/web and the native serif family on Android preserve the web heading hierarchy without bundling proprietary fonts. Native system sans maps the web Segoe UI/Arial fallback.

Build mandate for MOBILE-02A: Home gives AI Beauty Consultation the dominant gold bordered card and primary CTA. Custom Hair, Makeup and Nails use smaller image cards with bundled copies of the actual BeautyCore service images. The normal header gear opens Settings, where connection status and explicit recheck now live. No diagnostics belong on Home.

Studios share Photo, Style and Review stages, one at a time, under a compact progress strip. Each stage scrolls above the safe area action bar. Photo selection, preview, replace and remove stay in Photo; real catalogs and selected gold borders stay in Style; final photo/style summary stays in Review. Native header and Android Back move to the previous stage while preserving work. Compact image frames adapt to screen height. No full size desktop hero or repeated numbered panels should push workflow actions below the fold.

Results are a dedicated route with Original/Result comparison controls, selected style, explicit unchanged mock labeling and disabled Save/Share placeholders. Try Another Style preserves the photo; Start Over clears only the current studio. Consultation has local Service, Direction and Your Looks stages using the web's real preference vocabulary. Its pending recommendations panel is honest, with a brief review and custom studio photo handoff. No invented conversation, recommendation or generated look.

All cards fit the available width, long names wrap, controls are at least 44 points tall, and content scrolls inside safe areas. Keep loading, empty, error and mock states distinct. Catalogs are real API data; mock preview is the unchanged local photo and must say so. No invented transformation or recommendation.

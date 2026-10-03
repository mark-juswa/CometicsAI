# Mobile Consultation UI refinement — 2026-10-03

**Scope:** Presentation and local stage flow only. The Supervisor asked for the current mobile Consultation to feel like the finished BeautyCore web page in the supplied Service and Direction screenshots, with fewer visible controls. The actual web route and `beautycore/app/ai-studio.css` were inspected as the product source. No backend, BeautyCore adapter, Gemini, Kaggle, catalog, generation, authentication, or model source changed.

The former mobile Service stage combined service and photo selection. Direction then exposed Occasion, Vibe, Maintenance and other preference controls before the first conversation turn. Your Looks displayed three full recommendation cards with repeated actions. On a phone, the visible decisions competed for attention.

The revised Service stage presents the three purple/gold illustrated service cards, one Continue action, and a quiet Custom link. Direction now owns the photo and one open-ended description. Optional structured preferences are collapsed by default; if opened, they still use the same preference mapper. The first description goes through the existing create → photo → preferences → text turn sequence on one Start action. Subsequent Gemini questions remain free text with contextual quick replies. Your Looks displays three compact backend-provided look selectors and one featured recommendation with one generation action. The completed result retains Original/Generated Result and Select; the duplicate footer Back button was removed because the native header already handles Back. Custom still transfers the local photo to the service Style step.

## Visual evidence

- [Before: Direction at 390 px](mobile-02c-assets/direction-fixture-390.png) and [before: Your Looks at 390 px](mobile-02c-assets/looks-fixture-390.png) are preserved from the prior fixture run.
- [After: Service 390 px](mobile-consultation-ux-assets/service-after-390.png), [Direction before photo 390 px](mobile-consultation-ux-assets/direction-empty-after-390.png), [Direction with photo 390 px](mobile-consultation-ux-assets/direction-ready-after-390.png), [conversation 390 px](mobile-consultation-ux-assets/conversation-after-390.png), [Your Looks 390 px](mobile-consultation-ux-assets/looks-after-390.png), and [second look selected 390 px](mobile-consultation-ux-assets/look-two-after-390.png).
- Narrow-width captures: [Service](mobile-consultation-ux-assets/service-after-320.png), [Direction](mobile-consultation-ux-assets/direction-empty-after-320.png), [Your Looks](mobile-consultation-ux-assets/looks-after-320.png). Content scrolls within the screen; the bottom primary action remains visible.

## Verification

- TypeScript, Expo lint and 37 mobile tests passed.
- Expo Doctor passed 21/21. Android and web exports passed.
- [Intercepted browser fixture](mobile-consultation-ux-assets/ui-check.cjs) passed Service choices, gallery cancel/choose/replace/remove, first nonempty text turn exactly once, three validated recommendation records, look switching and Custom photo handoff. Viewports 320/360/390/430 had no horizontal overflow and visible primary actions. No page errors, empty Gemini turns or generation POST occurred. [Fixture report](mobile-consultation-ux-assets/ui-checks.json).
- [Bundle scan](mobile-consultation-ux-assets/bundle-scan.json) found zero private-value matches in 57 Android/web bundle files for 13 private values.
- Supervisor manually reloaded Expo Go and answered “Looks good” to the Consultation UI checklist covering Service, Direction, keyboard, Back, bottom action and the optional Your Looks look-switching check. This is user-reported native feedback; no remote phone taps, navigation or capture were performed. No new GPU run was requested.

The previously verified MOBILE-02C real Android Hair Consultation result and Select remain historical evidence. This UI-only pass does not re-claim live generation acceptance or close the separately deferred standalone Makeup/Nails gates.

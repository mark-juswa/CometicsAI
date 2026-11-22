# 0021. Consultation chat layout

**Date**: 2026-11-16
**Status**: DONE (website release67979a1 VERIFIED Live; live AI provider acceptance NEEDS VERIFICATION)
**Decision**: CONFIRMED. The Supervisor approves prototype v3 for implementation, preserving existing brand styling and functionality, and keeping the conversation visible beside the recommended looks.
**Planning progress**: DONE
**Implementation progress**: DONE locally
**Evidence**: VERIFIED component/API regressions, local browser workflows, responsive screenshots and production compilation. See [implementation evidence](../experiments/consultation-chat-ui-20261116.md). Physical mobile keyboard and live provider/release checks remain NEEDS VERIFICATION.

## Summary

Present consultation as one chat workspace with a compact header, prominent progress steps, readable conversation and a composer near the bottom. Keep the existing client navigation, purple and gold palette, typography and business controls. Let the user describe a direction first, then prompt for a photo in the composer. Reveal the photo and recommended looks panel only when recommendations are ready. Preserve the existing application contracts and request and recovery rules.

## Context

The reference shows a narrow navigation rail, one large rounded workspace, small controls along the top, a centered welcome and a wide composer near the bottom. Generous open space makes conversation the main activity. The screenshot depicts a welcome state, so message, result and mobile arrangements must be derived from BeautyCore's existing requirements rather than treated as visible reference details.

The unchanged supplied image is preserved at `artifacts/consultation-ui-plan-20261115/reference.png`.

BeautyCore currently presents Service, Direction and Your Looks as three separate sections. Direction contains the conversation or structured preference form beside a photo panel. Your Looks replaces that section with generated previews and selection actions. The large studio hero, progress strip and section introductions consume space that could support the conversation.

The client portal already provides the navigation rail and mobile navigation drawer. The shared studio shell adds its own branding, feature navigation and hero. A consultation layout should integrate with the portal while retaining guest navigation, existing utility links and consistent styling across the site.

### Source baseline and preservation inventory

Inspection covered the working checkout and stored client refs. The working checkout is `codex/look-details-performance`, HEAD `63fc8512cb9f6c93c7e3e07d4d50a71cbf2e086a`, with substantial unrelated local work. Its consultation source is older than the client enhancements.

The stored `origin/codex/beautycore-enhancements` ref is `23b2555a7e3b86acd2458ebeb865b782b37f0308`. It descends from the stored generation recovery branch `ba077964e87b7f6b5b481ecc55d4dc6f7083a408`. Its consultation already uses shared state and refs, checks manual generation activity, and includes camera capture and a reference image picker. The reference picker supplies the consultation source photo through `acceptFile`; it is not a new image sent to the conversational model.

Before implementation, establish the latest intended client source and preserve its features. These observations concern locally stored refs, not a fresh remote fetch or an observation of the deployed site. Do not reconstruct the new screen from the older root component and thereby discard newer behavior.

Inspected areas include `components/consultation.tsx`, `components/ai-studio.tsx`, `components/ClientSidebar.tsx`, `components/Sidebar.tsx`, `app/client/layout.tsx`, both consultation route wrappers, `app/globals.css`, `app/ai-studio.css`, `lib/ai/studio-consultation-api.ts`, existing guest UI tests and related specs 0003, 0004, 0013 and 0020. Paths are relative to `beautycore/` unless stated otherwise. Earlier specs contain historical descriptions; actual source controls the preservation inventory.

## Requirements

As a client, you can discuss a look, inspect the recommendations and act on a preview within a consistent workspace. As a guest, you retain the same trial allowance, temporary result notices and account restrictions.

The Supervisor supplied the design source, brand constraints and functional boundary. Existing data, providers, authorization and APIs are inherited. No new schema, provider, dependency or conversational capability is proposed. The following acceptance criteria translate those instructions into checks for implementation.

1. **AC-1**: The workspace follows the reference hierarchy of navigation, compact header, central conversation and bottom composer, using existing BeautyCore colors, type styles, buttons, icons and border treatments.
2. **AC-2**: The user can describe their intended look before uploading a photo. Preserve that first description as a local draft. Confirm a primary service when the request is ambiguous, prompt for the appropriate portrait or hand photo inside the composer, and require valid photo preparation before starting the existing server consultation. JPG and PNG validation, the 8 MB limit, camera behavior, reference picker eligibility and photo change effects remain intact.
3. **AC-3**: Actual assistant and user messages, suggested replies, the 500 character reply limit, Enter to send, Shift and Enter for a new line, pending feedback and opening question recovery remain available. Existing guards prevent duplicate submissions. Sending becomes unavailable when the consultation reaches its current recommendation boundary.
4. **AC-4**: The conversation remains visible when three recommendations become available. Clients can inspect all three looks, initiate the existing sequential generation flow, switch the featured result and use existing description, estimate, complement, selection, download, Save Look, Book Selected Look and Custom actions.
5. **AC-5**: Busy, partial failure and uncertain status states keep their existing action restrictions. Opening a panel, changing viewport or switching a visual tab sends no generation request. Uncertain status uses the existing status read and never an automatic replacement generation request.
6. **AC-6**: Shared consultation state, account isolation, navigation recovery, generation coordination and trial restoration retain the behavior present in the chosen implementation baseline. Responsive layout changes do not remount a second consultation owner.
7. **AC-7**: The guest version still offers three text recommendations and one chosen generation allowance, with existing notices, limit dialog and signup or login actions. Member saving, booking and additional generation are not exposed through visual rearrangement.
8. **AC-8**: The structured preference mode remains usable when the configured provider is deterministic. Its occasion, vibe, service preference, avoids and notes fields keep their current values and limits.
9. **AC-9**: The layout works at 1440, 1024, 768 and 390 CSS pixels, plus a 320 pixel overflow check. The composer remains reachable with a mobile keyboard, focus stays visible, controls have accessible names, dialogs manage focus, and the conversation does not force scrolling away from older messages.
10. **AC-10**: Consultation styling does not alter the dashboard, Hair, Makeup or Nails studios. Existing API, model, database, quota and booking rules remain outside the implementation diff.

## Options considered

### Improve spacing in the existing steps

This keeps the smallest markup change and most existing layout. It would still replace the conversation when entering results and only partly achieve the requested chatbot experience.

### Recompose the existing presentation

Keep one consultation owner and rearrange its visual sections into a chat workspace with a details rail. This fits the chosen reference and allows direct reuse of handlers. It requires careful responsive layout, focus and scroll verification.

### Build a separate chatbot feature

A separate component could be styled freely. Recreating the workflow would duplicate session, guest and recovery behavior and expand the risk beyond the requested presentation change.

## Decision

Recommend recomposing the existing presentation. The main consultation component continues to own the existing state and actions. Any extracted view components receive values and callbacks from that owner. UI expansion and collapse state stays separate from consultation progress.

Use the existing Next.js, React, CSS and icon stack. Prefer a consultation specific stylesheet and an optional visual variant on `StudioShell` whose default preserves all other studios. Preserve the client layout provider, sidebar and notifications. The runner up is spacing improvements within the existing steps, but that cannot keep the conversation and looks visible together.

## Rationale

The application already has the needed capabilities. Most risk comes from losing state, changing action availability or affecting shared styling during rearrangement. Reusing the existing owner and handlers limits the change to presentation while allowing a substantial layout improvement.

## Feature design

### Confirmed prototype refinements

The Supervisor's browser comments on15November2026 supersede the earlier preparation presentation. Remove the top prototype label and restart control. Make all three progress steps larger, with a clear active step and completed state. Hide the photo and looks panel initially. Accept an initial description, prompt for the photo inside the chat and place attachment controls in the composer. Reveal the results panel when recommendations are ready, keeping the transcript visible.

Subsequent typography feedback confirms retaining the serif headings and gold display text while replacing Arial in the conversation and controls. The revised prototype uses Inter, already configured by the actual application, with readable message sizing and spacing. Progress uses a lighter strip with numbered markers and active underlines, labeled Your direction, Consultation and Your looks, rather than three bordered cards. This replaces the earlier boxed step presentation while preserving the same stages and state transitions.

The approved isolated prototype establishes the presentation. The application now implements it using actual existing UI actions and API adapters. The initial description stays local until the existing photo and session preparation is complete. No conversational API call is sent before the photo prerequisite.

### Reference interpretation

| Reference element | BeautyCore adaptation |
| --- | --- |
| Left navigation rail | Keep the existing client sidebar, active state, account footer and mobile drawer. Guest navigation remains appropriate to the public trial. |
| Large rounded main canvas | One consultation workspace inside the current portal content area. |
| Small top toolbar | Consultation title, selected service, current mode label, compact progress and existing help or history links where available. Provider mode is information, not a model switch. |
| Centered welcome and emblem | A restrained existing brand icon with a short welcome and existing service choices. It contracts after the conversation starts. |
| Large bottom composer | The existing reply field and send handler, with suggested replies immediately above and the photo attachment control nearby. |
| Secondary controls | Photo attachment belongs in the composer during preparation. Show the read only source photo and look details in the secondary panel only after recommendations exist. |

The screenshot's black and silver palette, cryptocurrency content, subscription card, model selector and microphone do not define BeautyCore requirements. The requested transfer is its layout hierarchy.

### Brand and consistency

Use the inspected existing values: deep background `#0f0520`, card `#1a0a2e`, surface `#2d1054`, primary purple `#7b2fa0`, light purple `#b040d8`, gold `#f0a800`, gold hover `#f5c040`, white primary text and secondary `#e0c8f0`. Preserve established muted text tokens in the relevant surface, including the studio's existing higher contrast muted value. Use the existing serif display treatment, sans serif controls, rounded portal controls and Lucide icons. Do not change global tokens to imitate the reference.

Keep the dashboard sidebar width and content alignment. Scope the compact studio hero and reduced decorative artwork to consultation. All navigation destinations currently available remain reachable without adding a second sidebar inside the workspace.

### Desktop arrangement

The existing portal sidebar sits outside the consultation workspace. Initially the main area is one centered chat column with no details panel. After recommendations are ready, show the arrangement below:

```text
Compact title   Selected service   Mode   Progress   Existing links

Conversation area                         Details panel
  Welcome or actual conversation            Your photo
  Assistant and client messages             Attachment options
  Pending and error feedback                Three looks when ready
                                           Featured preview
Suggested replies                          Existing result actions
Reply field and send action
```

The chat uses the flexible main column, with a readable message width around 680 to 760 pixels. The details panel targets about 300 to 360 pixels when available space allows both columns. Those dimensions are initial layout targets, not new global design tokens. Use available content width rather than viewport width alone, since the portal sidebar consumes space.

The main workspace uses the available viewport height after the existing portal header and page spacing. The transcript can scroll inside the chat column. The composer remains in the column's normal grid layout or sticky region so it does not overlap messages, dialogs or the details panel. A long conversation must remain readable and selectable.

### Existing workflow inside the new layout

| Existing capability | New visual location | Preserved source or action |
| --- | --- | --- |
| Choose one service | Welcome choices and a compact selected service summary | `SERVICES`, `service`, `changeService`, existing Continue transition |
| Upload or replace photo | Attachment prompt and thumbnail inside the composer | Existing input ref, `onFileChange`, `acceptFile`, drop handling and eligibility |
| Camera or existing source picker | Photo controls in the same preparation area | Existing `CameraCapture` and `ReferenceImagePicker`, with the baseline's guards |
| Begin consultation | Explicit Continue consultation after valid preparation | Existing session and photo preparation, followed by submission of the retained initial description through the existing turn contract |
| Conversation and suggested replies | Main transcript and composer | `chatMessages`, `chatInput`, `quickReplies`, `replyToConsultant`, GET-only `checkConversation` recovery |
| Structured provider mode | Guided preference content in the main column | Existing preference fields, `preferences`, `start` |
| Recommendation readiness | A system status and the enabled looks panel | `conversationReady`, `cards`, existing progress transition |
| Generate previews | Primary action in the looks panel | Existing `generateLooks`; three member looks remain sequential, guest generates the chosen one |
| Inspect a look | Three compact selectors and a featured preview | `activeLookId`, `switchLook`, `activeCard`, `StudioPhoto`, `LookInformation` |
| Result actions and handoff | Beneath the featured preview and selected look summary | `select`, download link, `SavedLookActions`, existing `customLink` |
| Failures and recovery | Status adjacent to the affected message or look | Existing errors, `retry`, `checkStatus`, `continuePending` and their guards |
| Guest limits | Visible trial status and the existing dialog | `GuestTrialIndicator`, `GuestTrialLimitDialog`, `trialFeedback` |

Retain preparation, conversation and looks as distinct stages. During preparation, show welcome choices and an enabled composer for the initial description. Capture that text locally and prompt for a primary service if needed. Then show the photo prompt and file controls inside the composer, with a local thumbnail after attachment. An explicit Continue consultation action performs the existing server preparation before any actual conversational turn. During Your Looks, retain the transcript as visible context, reveal the looks panel and replace the editable composer with a clear recommendation ready status. This layout does not enable further conversation after the current API flow has finished.

Production preserves the initial description and sends it once as the first nonempty turn through the existing interface after session creation and photo upload succeed. Inspected `begin_turn` permits this without a separate empty opening turn, so no endpoint or backend change is required. On an uncertain turn, persist the pending text and preceding user message count, then reconcile through GET state. Only a canonical user message at that position confirms receipt. An unchanged or unavailable state remains uncertain and blocks further turn POSTs; a status check never replays a message. Failed photo preparation reuses the same existing handle through an explicit preparation action and does not send a turn until upload succeeds.

Implementation uses a synchronous tab-scoped sessionStorage journal for only the initial local description and one pending turn. It is scoped to account and signed consultation identity, holds no photo or canonical conversation history, and is written before sending a turn. If the write fails, the UI sends no turn. Renewed guest JWTs match by issuer, audience, subject and consultation identity only for local draft recovery; the server still authorizes every request using the current signed handle. The central account cleanup removes this journal, and an account lifetime counter rejects late writes after logout, including after route departure. The existing shared member IndexedDB/photo store is retained. Session creation and recommendation generation contracts remain unchanged.

Restoring a member consultation locks edits and generation until the canonical state and existing result details have been read. Completed previews are rendered safely while image detail loads. Expired access, including the adapter's specific 403 response, permits an explicit fresh consultation. Generic authorization failures are not treated as expiry. Before a handle is created, service choices remain available to correct an inferred service without discarding the direction.

Service and photo mutation controls retain their existing allowed stages. Showing the photo in results does not introduce a new reset action. Selecting a suggested reply continues to populate the existing reply field rather than automatically sending it. Choosing a look continues to change the active preview without generating it. Selecting a completed recommendation remains separate from saving or booking it.

### Booking handoff

Follow up source inspection confirms that Book Selected Look saves the completed result first if it has not already been saved, then opens the existing `/booking?look=...` page. Save Look alone keeps it in My Saved Looks without creating an appointment. The proposed panel retains these exact actions.

The newer client booking form loads that saved preview, associates it with the matching service category, and asks for the specific salon service, preferred stylist if wanted, date, an available time and optional notes. Booking submission remains on this separate form. The resulting status is displayed as confirmed or pending according to the existing response; opening the form is not a completed appointment. The preview remains attached for the assigned stylist. These observations describe the stored client enhancements source, not a new live booking verification.

### Mobile and accessibility

At narrower available widths, stack the chat and details content. Use a labeled Your photo or Your looks disclosure to control page length. When results are ready, expose the selected look and generation action clearly, while the conversation remains available above. The existing mobile portal menu remains the only portal navigation drawer.

Use dynamic viewport sizing with a fallback and bottom safe area padding. Test the actual software keyboard and a short landscape viewport. Avoid hardcoded bottom offsets based on desktop screenshots. For message updates, keep the current live log semantics and loading announcements. Only follow the newest message automatically when the reader is already near the bottom or has just submitted; otherwise offer a reachable latest message control. Preserve focus when views collapse and provide labels for every icon action. Honor reduced motion.

### Data and interface boundaries

The server data model and API surface remain unchanged. `service`, photo state, preferences, messages, consultation handle, recommendation cards, result payloads and selected recommendation ID remain in their existing owner or shared provider. Local preparation adds the initial description from the composer, its pending submission state and attachment panel visibility. It must not become a second source of server consultation truth. Existing shared recovery must retain the pending description without resubmitting it automatically.

`createStudioConsultationApi` remains responsible for the existing authenticated or guest API prefix and signed handles. Its create, upload, preference, turn, recommend, generate, status and select operations retain their current contracts. Result labels and estimates come from existing recommendation or `LookInformation` sources. Trial availability comes from server trial state. Generated image content comes from the existing result payload. The redesign does not create message history, infer prices, copy a session into local storage or send the photo to the text conversation provider.

### Verification scenarios

| Scenario | Expected observation | Criteria |
| --- | --- | --- |
| Member service, photo, chat and recommendation journey | Existing request order and payloads; three sequential generation submissions after explicit action | AC-2, AC-3, AC-4 |
| Deterministic provider | Every existing preference input and action remains usable | AC-8 |
| Guest available, reserved, spent or unresolved | Existing quota and recovery messages; only the chosen generation is submitted | AC-5, AC-7 |
| Timeout, partial failure or unknown result | Completed siblings persist; eligible manual retry and status read remain distinct; no automatic replacement POST | AC-5 |
| Navigation and refresh in the selected baseline | Shared state and handle recovery persist; no new generation is sent by visual recovery | AC-6 |
| Camera, source picker and file replacement | Current eligibility, validation, reset effects and photo privacy remain intact | AC-2, AC-7 |
| Preview selection, download, save, booking and Custom | Same underlying IDs, payloads and destinations as the baseline | AC-4, AC-10 |
| Responsive, keyboard and long conversation | No horizontal overflow, hidden composer, inaccessible action or duplicate live log | AC-1, AC-9 |
| Dashboard and all manual studios | Shared styling and behavior remain unchanged | AC-10 |

## Build plan

Use one complete user journey first, followed by failure and guest verification. This ordering is a presentation adaptation of an end to end build, with existing APIs retained throughout.

1. Establish the current client source and capture the existing member, guest and deterministic request traces with controlled responses. Inventory camera, picker, help, history, recovery and business actions before touching markup. Satisfies AC-2 through AC-8 and AC-10.
2. Add the consultation specific shell and scoped styles. Preserve the existing portal layout and make any shared shell option default to its current appearance. Satisfies AC-1 and AC-10.
3. Recompose service preparation, photo controls, transcript and composer around the existing owner and callbacks. Complete the member journey through recommendation readiness. Satisfies AC-2, AC-3 and AC-8.
4. Place the three look selectors, featured result and current business actions in the details panel while keeping the transcript visible. Carry forward all current status and guest restrictions. Satisfies AC-4 through AC-7.
5. Verify responsive stacking, software keyboard behavior, scroll position, dialog focus and keyboard operation. Satisfies AC-1 and AC-9.
6. Run the relevant existing client, guest, generation recovery, camera and business checks from the chosen baseline. Add targeted integration coverage for the new layout where existing coverage cannot establish request parity. Run TypeScript and the production build. Perform browser verification with controlled API responses before considering a separate live rehearsal. Satisfies AC-1 through AC-10.

No model generation, training or cloud deployment is needed to verify the layout. If an existing baseline failure is found, record it separately rather than silently expanding this presentation task.

## Consequences

The conversation becomes the main focus and remains available while choosing a look. Existing dashboard styling stays consistent. A scoped component change can be rolled back by reverting its UI commit without a data migration.

The details panel can narrow the chat on medium screens, so it must collapse according to actual available space. Keeping the transcript visible requires deliberate scrolling and focus behavior. A rigid copy of the screenshot would not accommodate these existing product controls; the adaptation preserves its hierarchy while allowing the photo and results to occupy appropriate space.

## Follow-up

The approved v3 presentation is implemented on `codex/consultation-chat-ui`, based on client enhancements `23b2555a7e3b86acd2458ebeb865b782b37f0308`. Independent code review is complete with final verdict Approve. Local tests and controlled browser evidence establish application behavior, not live AI service availability or model quality. Physical software keyboard and real device camera checks remain NEEDS VERIFICATION. No production release, cloud setting, database migration or GPU generation is part of this implementation.

## 22 November 2026 approved v4 implementation override

CONFIRMED: Supervisor approves [v4](../../artifacts/consultation-ui-prototype-20261122/consultation-chat-v4.html) and requests implementation and deployment. The earlier side panel, desktop rail diagram and mobile collapse arrangement in this spec are DEPRECATED. Recommendations, generated images, existing service/complement details, Select, Download, Save, Book, Retry, Check status, Continue and applicable guest/Custom controls now belong inside the existing transcript. Keep one consultation owner and stable selected recommendation identity. Reuse the actual SavedLookActions and /booking?look= handoff; booking remains a separate form and explicit submission. The ready status links back to the inline recommendations. Auto-follow starts new results at their heading without taking older-message readers away. No API, model, quota, auth, persistence or booking rule changes.

All other functional acceptance criteria remain in force; AC-4's side panel placement and AC-9's stacking refer to this inline arrangement. Current implementation is DONE locally with VERIFIEDregressions/build/browser evidence and independent review Approve. Production deployment remains IN PROGRESS pending the manual Render action and live checks. [Release evidence and limits](../experiments/consultation-inline-results-release-20261122.md).

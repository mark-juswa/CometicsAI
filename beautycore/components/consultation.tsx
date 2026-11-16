"use client";
import {
  GenerationContext,
  useConsultationState,
  useConsultationRef,
  useManualGenerationBusy,
} from "@/components/generation-provider";
import { LookInformation } from "@/components/look-information";
import {
  GuestTrialIndicator,
  GuestTrialLimitDialog,
  type TrialFeedbackState,
} from "@/components/guest-trial-feedback";
import {
  ArrowUp,
  Check,
  ChevronRight,
  ImagePlus,
  LockKeyhole,
  Paperclip,
  Scissors,
  Sparkles,
  WandSparkles,
  Hand,
} from "lucide-react";

import Link from "next/link";
import { SavedLookActions } from "@/components/saved-look-actions";
import {
  type ChangeEvent,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { StudioPhoto } from "@/components/ai-studio";
import {
  clearConsultationPreparation,
  consultationPreparationEpoch,
  expiredConsultationAccess,
  readConsultationPreparation,
  writeConsultationPreparation,
  consultationTurnRecorded,
  inferConsultationService,
  type PendingConsultationTurn,
} from "@/lib/ai/consultation-preparation";
import type { FeatureId, GenerateResponse } from "@/lib/ai/studio-api";
import {
  createStudioConsultationApi,
  type GenerationDetail,
  type Preferences,
  type Recommendation,
} from "@/lib/ai/studio-consultation-api";
import {
  readTrialSession,
  type GuestTrialStatus,
} from "@/lib/ai/guest-trial-client";
import { rememberCustomPhoto } from "@/lib/ai/studio-photo-handoff";
import { ReferenceImagePicker } from "@/components/reference-image-picker";
import { CameraCapture } from "@/components/camera-capture";

type CardStatus = "pending" | "generating" | "completed" | "failed" | "unknown";
type Card = {
  recommendation: Recommendation;
  status: CardStatus;
  result: GenerateResponse | null;
  error: string;
  canRetry: boolean;
};
type Phase = "setup" | "preparing" | "generating" | "ready" | "attention";
type Step = 1 | 2 | 3;

const SERVICES: {
  id: FeatureId;
  label: string;
  detail: string;
  href: string;
}[] = [
  {
    id: "hairstyle",
    label: "Hairstyle",
    detail: "A cut or shape for your next look",
    href: "/client/hair-studio",
  },
  {
    id: "makeup",
    label: "Makeup",
    detail: "A finish for your portrait",
    href: "/client/makeup-studio",
  },
  {
    id: "nails",
    label: "Nails",
    detail: "A polished hand look",
    href: "/client/nail-studio",
  },
];
const MAX_BYTES = 8 * 1024 * 1024;
const wait = (milliseconds: number) =>
  new Promise((resolve) => setTimeout(resolve, milliseconds));

export default function Consultation({ trial = false }: { trial?: boolean }) {
  const store = useContext(GenerationContext);
  const draftOwner = trial ? "guest" : store?.owner || "local";
  const manualBusy = useManualGenerationBusy();
  const api = useMemo(
    () => createStudioConsultationApi(trial ? "/api/ai-trial/" : "/api/ai/"),
    [trial],
  );
  const {
    createConsultation,
    generateRecommendation,
    getConsultationMode,
    getGenerationDetail,
    recommendConsultation,
    sendConsultationTurn,
    selectRecommendation,
    updateConsultation,
    uploadConsultationPhoto,
  } = api;
  const [trialStatus, setTrialStatus] =
    useConsultationState<GuestTrialStatus | null>("trialStatus", null, trial);
  const [trialLoading, setTrialLoading] = useConsultationState(
    "trialLoading",
    trial,
    trial,
  );
  const [trialLimitOpen, setTrialLimitOpen] = useConsultationState(
    "trialLimitOpen",
    false,
    trial,
  );
  const trialUsedAnnounced = useRef(false);
  async function refreshTrial() {
    const state = await readTrialSession();
    setTrialStatus(state);
    return state;
  }
  const [service, setService] = useConsultationState<FeatureId | null>(
    "service",
    null,
    trial,
  );
  const [step, setStep] = useConsultationState<Step>("step", 1, trial);
  const [activeLookId, setActiveLookId] = useConsultationState(
    "activeLookId",
    "",
    trial,
  );
  const [showMorePreferences, setShowMorePreferences] = useConsultationState(
    "showMorePreferences",
    false,
    trial,
  );
  const [dragging, setDragging] = useConsultationState(
    "dragging",
    false,
    trial,
  );
  const [file, setFile] = useConsultationState<File | null>(
    "file",
    null,
    trial,
  );
  const [preview, setPreview] = useConsultationState("preview", "", trial);
  const previewRef = useConsultationRef("previewRef", preview, trial);
  const inputRef = useRef<HTMLInputElement>(null);
  const running = useConsultationRef("running", false, trial);
  const selecting = useConsultationRef("selecting", false, trial);
  const [selectionBusy, setSelectionBusy] = useConsultationState(
    "selectionBusy",
    false,
    trial,
  );
  const [occasion, setOccasion] = useConsultationState("occasion", "", trial);
  const [vibe, setVibe] = useConsultationState("vibe", "", trial);
  const [avoids, setAvoids] = useConsultationState("avoids", "", trial);
  const [notes, setNotes] = useConsultationState("notes", "", trial);
  const [servicePreference, setServicePreference] = useConsultationState(
    "servicePreference",
    "",
    trial,
  );
  const [providerMode, setProviderMode] = useConsultationState<
    "loading" | "deterministic" | "gemini"
  >("providerMode", "loading", trial);
  const [chatInput, setChatInput] = useConsultationState(
    "chatInput",
    "",
    trial,
  );
  const [chatMessages, setChatMessages] = useConsultationState<
    { role: "user" | "assistant"; content: string }[]
  >("chatMessages", [], trial);
  const [conversationReady, setConversationReady] = useConsultationState(
    "conversationReady",
    false,
    trial,
  );
  const [phase, setPhase] = useConsultationState<Phase>(
    "phase",
    "setup",
    trial,
  );
  const [consultationId, setConsultationId] = useConsultationState(
    "consultationId",
    "",
    trial,
  );
  const [cards, setCards] = useConsultationState<Card[]>("cards", [], trial);
  const [selectedId, setSelectedId] = useConsultationState(
    "selectedId",
    "",
    trial,
  );
  const [error, setError] = useConsultationState("error", "", trial);
  const [initialIntent, setInitialIntent] = useConsultationState(
    "initialIntent",
    "",
    trial,
  );
  const [pendingTurn, setPendingTurn] =
    useConsultationState<PendingConsultationTurn | null>(
      "pendingTurn",
      null,
      trial,
    );
  const [photoUploaded, setPhotoUploaded] = useConsultationState(
    "photoUploaded",
    false,
    trial,
  );
  const [sessionUnavailable, setSessionUnavailable] = useConsultationState(
    "sessionUnavailable",
    false,
    trial,
  );
  const [attachmentOpen, setAttachmentOpen] = useState(
    step === 2 && !consultationId,
  );
  const [looksOpen, setLooksOpen] = useState(true);
  const [restoring, setRestoring] = useState(
    !trial && !!consultationId && !running.current,
  );
  const restoringRef = useRef(restoring);
  const transcript = useRef<HTMLDivElement>(null);
  const replyInput = useRef<HTMLTextAreaElement>(null);
  const photoButton = useRef<HTMLButtonElement>(null);
  const continueButton = useRef<HTMLButtonElement>(null);
  const resultsPanel = useRef<HTMLElement>(null);
  const following = useRef(true);
  const [showLatest, setShowLatest] = useState(false);
  const draftEpoch = useRef(consultationPreparationEpoch(draftOwner));
  const refocusReply = useRef(false);

  function journal(
    id: string,
    pending: PendingConsultationTurn | null,
    intent = initialIntent,
  ) {
    return writeConsultationPreparation(
      draftOwner,
      {
        handle: id,
        initialIntent: intent,
        pendingTurn: pending,
      },
      draftEpoch.current,
    );
  }

  function restorePreparation(id: string) {
    const draft = readConsultationPreparation(draftOwner, id);
    if (draft) {
      setInitialIntent(draft.initialIntent);
      if (
        trial ||
        !store ||
        !Object.hasOwn(store.getSnapshot().consultation, "notes")
      )
        setNotes(draft.initialIntent);
      setPendingTurn(draft.pendingTurn);
    }
    return draft?.pendingTurn || pendingTurn;
  }

  function confirmTurn(id: string) {
    setPendingTurn(null);
    setChatInput("");
    journal(id, null);
  }

  function preparationFailed(cause: unknown) {
    if (expiredConsultationAccess(cause)) setSessionUnavailable(true);
    setError(
      cause instanceof Error
        ? cause.message
        : "The consultation could not be prepared. Your description is kept here.",
    );
    setPhase("setup");
  }

  useEffect(() => {
    if (following.current && transcript.current)
      transcript.current.scrollTop = transcript.current.scrollHeight;
    else if (chatMessages.length) setShowLatest(true);
  }, [chatMessages, initialIntent, phase]);

  useEffect(() => {
    if (refocusReply.current && !pendingTurn && phase !== "preparing") {
      refocusReply.current = false;
      if (!conversationReady) replyInput.current?.focus();
    }
  }, [pendingTurn, phase, conversationReady]);

  useEffect(() => {
    if (initialIntent && service && !consultationId && !pendingTurn) {
      if (file) continueButton.current?.focus();
      else photoButton.current?.focus();
    }
  }, [initialIntent, service, file, consultationId, pendingTurn]);

  useEffect(
    () => () => {
      if (trial && previewRef.current) URL.revokeObjectURL(previewRef.current);
    },
    [],
  );

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        if (!trial && consultationId && !running.current) {
          restoringRef.current = true;
          setRestoring(true);
          const pending = restorePreparation(consultationId);
          try {
            const existing = await api.getConsultation(consultationId);
            if (!active) return;
            setService(existing.primary_service);
            setChatMessages(existing.messages);
            setPhotoUploaded(!!existing.photo);
            if (pending && consultationTurnRecorded(existing.messages, pending))
              confirmTurn(consultationId);
            setSelectedId(existing.selected_recommendation_id || "");
            setConversationReady(!!existing.recommendations);
            const rows = (existing.recommendations?.recommendations || []).map(
              (recommendation) => {
                const cached = cards.find(
                  (card) => card.recommendation.id === recommendation.id,
                );
                const status = existing.generations.find(
                  (item) => item.recommendation_id === recommendation.id,
                );
                return {
                  recommendation,
                  status: (status?.status === "generating"
                    ? "unknown"
                    : status?.status || "pending") as CardStatus,
                  result: cached?.result || null,
                  error: "",
                  canRetry: status?.status === "failed",
                };
              },
            );
            setCards(rows);
            if (rows.length) {
              setStep(3);
              setActiveLookId(
                (current) => current || rows[0].recommendation.id,
              );
            } else setStep(2);
            setPhase(
              rows.some(
                (row) => row.status === "unknown" || row.status === "pending",
              )
                ? "attention"
                : "ready",
            );
            for (const row of rows) {
              if (!active) return;
              if (
                (row.status === "completed" && !row.result) ||
                row.status === "unknown"
              ) {
                try {
                  const detail = await api.getGenerationDetail(
                    consultationId,
                    row.recommendation.id,
                  );
                  if (active) applyDetail(row.recommendation.id, detail);
                } catch {
                  if (active)
                    patchCard(row.recommendation.id, {
                      status: "unknown",
                      error:
                        "The existing preview could not be recovered. No replacement was sent.",
                      canRetry: false,
                    });
                }
              }
            }
          } catch (cause) {
            if (active) {
              if (expiredConsultationAccess(cause)) setSessionUnavailable(true);
              setError(
                "Your previous consultation is unavailable or expired. No replacement generation was sent.",
              );
              setPhase("attention");
            }
          } finally {
            if (active) {
              restoringRef.current = false;
              setRestoring(false);
            }
          }
        }
        if (trial) {
          const status = await readTrialSession("POST");
          if (!active) return;
          setTrialStatus(status);
          if (status.handle) {
            setConsultationId(status.handle);
            const pending = restorePreparation(status.handle);
            try {
              const existing = await api.getConsultation(status.handle);
              if (!active) return;
              setService(existing.primary_service);
              setConsultationId(existing.id);
              setChatMessages(existing.messages);
              setConversationReady(!!existing.recommendations);
              setPhotoUploaded(!!existing.photo);
              if (
                pending &&
                consultationTurnRecorded(existing.messages, pending)
              )
                confirmTurn(status.handle);
              const restored = (
                existing.recommendations?.recommendations ?? []
              ).map((recommendation) => ({
                recommendation,
                status: (recommendation.id === status.recommendation_id &&
                status.state !== "available"
                  ? "unknown"
                  : "pending") as CardStatus,
                result: null,
                error: "",
                canRetry: false,
              }));
              setCards(restored);
              if (restored.length) {
                setStep(3);
                setActiveLookId(
                  status.recommendation_id || restored[0].recommendation.id,
                );
              } else setStep(2);
              if (status.recommendation_id && status.state !== "available") {
                try {
                  const detail = await api.getGenerationDetail(
                    existing.id,
                    status.recommendation_id,
                  );
                  if (active) {
                    applyDetail(status.recommendation_id, detail);
                    setPhase("ready");
                  }
                } catch {
                  if (active)
                    setError(
                      "The trial result is unavailable or unresolved. No replacement generation was sent.",
                    );
                }
              }
            } catch (cause) {
              if (active) {
                preparationFailed(cause);
                setError(
                  "Your temporary consultation is unavailable. Your trial allowance has not been reset.",
                );
              }
            }
          }
        }
        const mode = await api.getConsultationMode();
        if (active) setProviderMode(mode.provider);
      } catch (cause) {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : "Consultation is unavailable.",
          );
      } finally {
        if (active) setTrialLoading(false);
      }
    }
    void initialize();
    return () => {
      active = false;
    };
  }, [api, trial]);

  function acceptFile(chosen?: File) {
    if (
      !chosen ||
      restoringRef.current ||
      running.current ||
      pendingTurn ||
      phase === "generating" ||
      (trial &&
        (trialLoading ||
          trialStatus?.state !== "available" ||
          trialStatus?.preparation_locked))
    )
      return;
    if (
      !["image/jpeg", "image/png"].includes(chosen.type) ||
      chosen.size < 1 ||
      chosen.size > MAX_BYTES
    ) {
      setError("Choose a JPG or PNG image up to 8 MB.");
      return;
    }
    if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    previewRef.current = URL.createObjectURL(chosen);
    setPreview(previewRef.current);
    setFile(chosen);
    const replacing =
      !!consultationId && (photoUploaded || chatMessages.length > 0);
    if (replacing) {
      clearConsultationPreparation(draftOwner);
      setInitialIntent("");
    }
    setPhotoUploaded(false);
    setSessionUnavailable(false);
    setAttachmentOpen(true);
    setCards([]);
    setSelectedId("");
    setActiveLookId("");
    setPhase("setup");
    if (replacing) {
      setConsultationId("");
      setChatMessages([]);
      setChatInput("");
    }
    setConversationReady(false);
    setError("");
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    acceptFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function changeService(next: FeatureId) {
    if (
      restoringRef.current ||
      running.current ||
      consultationId ||
      pendingTurn
    )
      return;
    if (trial && trialStatus && trialStatus.state !== "available") {
      setTrialLimitOpen(true);
      return;
    }
    setService(next);
    setPhotoUploaded(false);
    setSessionUnavailable(false);
    setServicePreference("");
    setCards([]);
    setSelectedId("");
    setActiveLookId("");
    setPhase("setup");
    setConsultationId("");
    setChatMessages([]);
    setConversationReady(false);
    setError("");
  }

  function preferences(): Preferences {
    const shared: Preferences = {
      occasion: occasion.trim() || undefined,
      vibe: vibe.trim() || undefined,
      avoids: avoids
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean)
        .slice(0, 5),
      notes: notes.trim() || undefined,
    };
    if (service === "hairstyle" && servicePreference)
      shared.hair_maintenance = servicePreference as "low" | "medium" | "high";
    if (service === "makeup" && servicePreference)
      shared.makeup_intensity = servicePreference as
        "natural" | "soft" | "bold";
    if (service === "nails" && servicePreference)
      shared.nail_finish = servicePreference as
        "glossy" | "matte" | "ombre" | "french";
    return shared;
  }

  function patchCard(id: string, change: Partial<Card>) {
    setCards((old) =>
      old.map((card) =>
        card.recommendation.id === id ? { ...card, ...change } : card,
      ),
    );
  }

  function applyDetail(id: string, detail: GenerationDetail): boolean {
    if (
      "archive_warning" in detail &&
      typeof detail.archive_warning === "string"
    )
      setError(detail.archive_warning);
    if (detail.generation.status === "completed" && detail.result) {
      patchCard(id, {
        status: "completed",
        result: detail.result,
        error: "",
        canRetry: false,
      });
      setActiveLookId((current) => current || id);
      return true;
    }
    if (detail.generation.status === "failed") {
      patchCard(id, {
        status: "failed",
        error: detail.generation.error || "This look could not be generated.",
        canRetry: !trial,
      });
      return true;
    }
    return false;
  }

  async function generateOne(
    id: string,
    recommendationId: string,
  ): Promise<boolean> {
    patchCard(recommendationId, {
      status: "generating",
      error: "",
      canRetry: false,
    });
    try {
      const detail = await generateRecommendation(id, recommendationId);
      if (applyDetail(recommendationId, detail)) return true;
      throw new Error(
        "The generation response did not contain a completed result.",
      );
    } catch (cause) {
      // This is a status read, never a second generation request. A lost HTTP
      // response can leave the original GPU request active.
      try {
        let detail = await getGenerationDetail(id, recommendationId);
        for (
          let checks = 0;
          detail.generation.status === "generating" && checks < 120;
          checks++
        ) {
          await wait(5000);
          detail = await getGenerationDetail(id, recommendationId);
        }
        if (applyDetail(recommendationId, detail)) return true;
        if (detail.generation.status === "pending") {
          patchCard(recommendationId, {
            status: "failed",
            error:
              cause instanceof Error
                ? cause.message
                : "This look is unavailable.",
            canRetry: false,
          });
          return true;
        }
      } catch {
        // Keep the state uncertain; do not send another generation POST.
      }
      patchCard(recommendationId, {
        status: "unknown",
        error:
          "Generation status is uncertain. Check status before continuing.",
        canRetry: false,
      });
      return false;
    }
  }

  async function generatePending(id: string, rows: Recommendation[]) {
    setPhase("generating");
    for (const row of rows) {
      if (!(await generateOne(id, row.id))) {
        setPhase("attention");
        return;
      }
    }
    setPhase("ready");
  }

  async function start() {
    if (
      (!file && !photoUploaded) ||
      !service ||
      restoringRef.current ||
      running.current ||
      pendingTurn ||
      sessionUnavailable
    )
      return;
    running.current = true;
    setError("");
    setCards([]);
    setSelectedId("");
    setPhase("preparing");
    try {
      let id = consultationId;
      if (!id) {
        const created = await createConsultation(service);
        id = created.id;
        setConsultationId(id);
      }
      if (!journal(id, null))
        throw new Error(
          "Your browser could not keep your preparation draft. Allow session storage before continuing.",
        );
      if (!photoUploaded && file) {
        await uploadConsultationPhoto(id, file);
        setPhotoUploaded(true);
      }
      await updateConsultation(id, preferences());
      const set = await recommendConsultation(id);
      setCards(
        set.recommendations.map((recommendation) => ({
          recommendation,
          status: "pending",
          result: null,
          error: "",
          canRetry: false,
        })),
      );
      setActiveLookId(set.recommendations[0].id);
      setConversationReady(true);
      setStep(3);
      setPhase("setup");
    } catch (cause) {
      preparationFailed(cause);
    } finally {
      running.current = false;
    }
  }

  function applyConversation(
    state: Awaited<ReturnType<typeof api.getConsultation>>,
  ) {
    setChatMessages(state.messages);
    setPhotoUploaded(!!state.photo);
    setConversationReady(!!state.recommendations);
    if (state.recommendations) {
      setCards(
        state.recommendations.recommendations.map((recommendation) => ({
          recommendation,
          status: "pending",
          result: null,
          error: "",
          canRetry: false,
        })),
      );
      setActiveLookId(state.recommendations.recommendations[0].id);
      setStep(3);
    } else setStep(2);
  }

  async function reconcileTurn(id: string, pending: PendingConsultationTurn) {
    try {
      const state = await api.getConsultation(id);
      applyConversation(state);
      if (consultationTurnRecorded(state.messages, pending)) {
        confirmTurn(id);
        setError("");
        setPhase("setup");
        return;
      }
      setError(
        "Your message has not been confirmed yet. Check conversation status before continuing. No replacement message was sent.",
      );
    } catch (cause) {
      if (expiredConsultationAccess(cause)) setSessionUnavailable(true);
      setError(
        "Your conversation could not be checked. Your message is kept here and has not been sent again.",
      );
    }
    setPhase("attention");
  }

  async function submitTurn(id: string, text: string) {
    const pending = {
      text,
      userCount: chatMessages.filter((message) => message.role === "user")
        .length,
    };
    if (!journal(id, pending)) {
      setError(
        "Your browser could not keep a safe recovery draft. No message was sent. Allow session storage before continuing.",
      );
      setPhase("setup");
      return;
    }
    // Persist before the POST. Navigation/refresh can reconcile this exact position with GET only.
    refocusReply.current = true;
    setPendingTurn(pending);
    try {
      const turn = await sendConsultationTurn(id, text);
      if (!consultationTurnRecorded(turn.state.messages, pending)) {
        await reconcileTurn(id, pending);
        return;
      }
      applyConversation(turn.state);
      confirmTurn(id);
      setPhase("setup");
    } catch {
      await reconcileTurn(id, pending);
    }
  }

  async function beginConversation() {
    if (
      (!file && !photoUploaded) ||
      !service ||
      !initialIntent ||
      running.current ||
      pendingTurn ||
      sessionUnavailable ||
      providerMode !== "gemini" ||
      busy
    )
      return;
    running.current = true;
    following.current = true;
    setError("");
    setPhase("preparing");
    try {
      let id = consultationId;
      if (!id) {
        const created = await createConsultation(service);
        id = created.id;
        setConsultationId(id);
      }
      if (!journal(id, null))
        throw new Error(
          "Your browser could not keep your preparation draft. Allow session storage before continuing.",
        );
      if (!photoUploaded && file) {
        await uploadConsultationPhoto(id, file);
        setPhotoUploaded(true);
      }
      setAttachmentOpen(false);
      await submitTurn(id, initialIntent);
    } catch (cause) {
      preparationFailed(cause);
    } finally {
      running.current = false;
    }
  }

  async function checkConversation() {
    if (
      !consultationId ||
      !pendingTurn ||
      restoringRef.current ||
      running.current
    )
      return;
    running.current = true;
    setPhase("preparing");
    try {
      await reconcileTurn(consultationId, pendingTurn);
    } finally {
      running.current = false;
    }
  }

  async function replyToConsultant() {
    const text = chatInput.trim();
    if (
      !text ||
      text.length > 500 ||
      running.current ||
      pendingTurn ||
      busy ||
      conversationReady ||
      sessionUnavailable
    )
      return;
    following.current = true;
    if (!consultationId || !photoUploaded || !chatMessages.length) {
      setInitialIntent(text);
      setNotes(text);
      setChatInput("");
      setStep(2);
      if (!service) setService(inferConsultationService(text));
      if (consultationId) journal(consultationId, null, text);
      setAttachmentOpen(true);
      setError("");
      return;
    }
    if (providerMode !== "gemini") return;
    running.current = true;
    setError("");
    setPhase("preparing");
    try {
      await submitTurn(consultationId, text);
    } finally {
      running.current = false;
    }
  }

  function startNewConsultation() {
    if (
      restoringRef.current ||
      running.current ||
      phase === "generating" ||
      (trial &&
        (trialStatus?.state !== "available" || trialStatus?.preparation_locked))
    )
      return;
    clearConsultationPreparation(draftOwner);
    setConsultationId("");
    setInitialIntent("");
    setPendingTurn(null);
    setPhotoUploaded(false);
    setChatMessages([]);
    setChatInput("");
    setConversationReady(false);
    setCards([]);
    setSelectedId("");
    setActiveLookId("");
    setSessionUnavailable(false);
    setPhase("setup");
    setError("");
    setStep(1);
    requestAnimationFrame(() => replyInput.current?.focus());
  }

  async function retry(card: Card) {
    if (restoringRef.current || manualBusy || pendingTurn || sessionUnavailable)
      return;
    if (trial || !consultationId || !card.canRetry || running.current) return;
    running.current = true;
    setPhase("generating");
    try {
      const settled = await generateOne(consultationId, card.recommendation.id);
      setPhase(
        settled &&
          !cards.some(
            (item) => item.status === "pending" || item.status === "unknown",
          )
          ? "ready"
          : "attention",
      );
    } finally {
      running.current = false;
    }
  }

  async function checkStatus(card: Card) {
    if (!consultationId || restoringRef.current || running.current) return;
    try {
      const detail = await getGenerationDetail(
        consultationId,
        card.recommendation.id,
      );
      if (applyDetail(card.recommendation.id, detail)) setPhase("attention");
      else
        patchCard(card.recommendation.id, {
          status: "unknown",
          error: "Still processing or status unavailable. Check again shortly.",
        });
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not check generation status.",
      );
    }
  }

  async function continuePending() {
    if (restoringRef.current || manualBusy || pendingTurn || sessionUnavailable)
      return;
    if (
      trial ||
      !consultationId ||
      running.current ||
      cards.some((card) => card.status === "unknown")
    )
      return;
    running.current = true;
    try {
      await generatePending(
        consultationId,
        cards
          .filter((card) => card.status === "pending")
          .map((card) => card.recommendation),
      );
    } finally {
      running.current = false;
    }
  }

  async function generateLooks() {
    if (restoringRef.current || manualBusy || pendingTurn || sessionUnavailable)
      return;
    if (!consultationId || running.current || cards.length !== 3) return;
    if (trial) {
      const chosen = cards.find(
        (card) => card.recommendation.id === activeLookId,
      );
      if (
        !chosen ||
        chosen.status !== "pending" ||
        trialStatus?.state !== "available" ||
        trialStatus.preparation_locked
      )
        return;
      running.current = true;
      setPhase("generating");
      setTrialStatus((old) => (old ? { ...old, state: "reserved" } : old));
      try {
        await generateOne(consultationId, chosen.recommendation.id);
      } finally {
        setPhase("ready");
        running.current = false;
        try {
          const status = await refreshTrial();
          if (status.state === "available")
            setCards((old) =>
              old.map((card) =>
                card.recommendation.id === chosen.recommendation.id
                  ? { ...card, status: "pending", canRetry: false }
                  : card,
              ),
            );
        } catch {
          /* Retain local lock until server status is known. */
        }
      }
      return;
    }
    if (cards.some((card) => card.status !== "pending")) return;
    running.current = true;
    try {
      await generatePending(
        consultationId,
        cards.map((card) => card.recommendation),
      );
    } finally {
      running.current = false;
    }
  }

  async function select(card: Card) {
    if (
      !consultationId ||
      restoringRef.current ||
      !card.result ||
      card.status !== "completed" ||
      selecting.current
    )
      return;
    selecting.current = true;
    setSelectionBusy(true);
    try {
      const state = await selectRecommendation(
        consultationId,
        card.recommendation.id,
      );
      setSelectedId(state.selected_recommendation_id || "");
      setError("");
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Selection could not be saved.",
      );
    } finally {
      selecting.current = false;
      setSelectionBusy(false);
    }
  }

  const serviceInfo = SERVICES.find((item) => item.id === service);
  const busy =
    restoring ||
    phase === "preparing" ||
    phase === "generating" ||
    trialLoading ||
    (trial &&
      (trialStatus?.state !== "available" ||
        !!trialStatus?.preparation_locked));
  const selected = cards.find((card) => card.recommendation.id === selectedId);
  const activeCard =
    cards.find((card) => card.recommendation.id === activeLookId) || cards[0];
  const activeIndex = cards.findIndex(
    (card) => card.recommendation.id === activeCard?.recommendation.id,
  );
  const hasTrialPreview = cards.some((card) => !!card.result);
  const trialFeedback: TrialFeedbackState = trialLoading
    ? "checking"
    : phase === "generating" ||
        cards.some((card) => card.status === "generating")
      ? "processing"
      : !trialStatus || trialStatus.preparation_locked
        ? "unresolved"
        : trialStatus.state === "available"
          ? "available"
          : hasTrialPreview ||
              (trialStatus.state === "spent" &&
                !cards.some((card) => card.status === "unknown"))
            ? "used"
            : "unresolved";
  useEffect(() => {
    if (!trial) return;
    if (trialFeedback === "available") {
      trialUsedAnnounced.current = false;
      setTrialLimitOpen(false);
    }
    if (trialFeedback === "used" && !trialUsedAnnounced.current) {
      trialUsedAnnounced.current = true;
      setTrialLimitOpen(true);
    }
  }, [trial, trialFeedback]);
  function cardLabel(card: Card) {
    if (card.status !== "pending") return card.status;
    if (!trial) return "Up next";
    return trialFeedback === "available"
      ? "Choose to preview"
      : trialFeedback === "used"
        ? "Account required"
        : "Not generated";
  }
  function switchLook(card: Card) {
    setActiveLookId(card.recommendation.id);
    if (
      trial &&
      card.status === "pending" &&
      (trialFeedback === "used" || trialFeedback === "unresolved")
    )
      setTrialLimitOpen(true);
  }
  const pendingPreviewMessage = !trial
    ? "Your preview is up next"
    : trialFeedback === "available"
      ? "Choose this look for your free preview"
      : trialFeedback === "used"
        ? "Sign up to preview this look"
        : trialFeedback === "processing"
          ? "Your one trial preview is already in progress"
          : "Check your current trial request";
  const lastQuestion =
    [...chatMessages].reverse().find((item) => item.role === "assistant")
      ?.content || "";
  const quickReplies = /maintenance|easy to maintain/i.test(lastQuestion)
    ? ["Easy to maintain", "Some styling is fine", "No preference"]
    : /intensity|natural|soft|bold/i.test(lastQuestion)
      ? ["Natural and subtle", "Soft and polished", "Bold and expressive"]
      : /color|finish/i.test(lastQuestion)
        ? ["Dark and glossy", "Soft and natural", "No preference"]
        : /occasion|getting ready|event/i.test(lastQuestion)
          ? ["Everyday", "Special event", "Graduation"]
          : [];
  const customLink = !trial && serviceInfo && (
    <Link
      className="consult-custom-link"
      href={serviceInfo.href}
      onClick={() => {
        if (file) rememberCustomPhoto(serviceInfo.id, file);
      }}
    >
      Prefer to choose yourself?{" "}
      <strong>
        Custom {serviceInfo.label} <span aria-hidden="true">↗</span>
      </strong>
    </Link>
  );

  const ready = conversationReady && cards.length === 3;
  const started =
    !!initialIntent || !!consultationId || chatMessages.length > 0;
  const currentStage = ready ? 3 : consultationId && photoUploaded ? 2 : 1;
  const preparation =
    (!consultationId || !photoUploaded || !chatMessages.length) && !ready;
  const showAttachments = !!service && !ready && attachmentOpen;
  const turnLocked = !!pendingTurn || sessionUnavailable || restoring;
  const initialInHistory = chatMessages.some(
    (message) => message.role === "user" && message.content === initialIntent,
  );
  const draftMessage =
    pendingTurn?.text || (!initialInHistory ? initialIntent : "");
  const draftInHistory = pendingTurn
    ? consultationTurnRecorded(chatMessages, pendingTurn)
    : initialInHistory;
  const uploadControls = (
    <>
      <input
        ref={inputRef}
        className="sr-only"
        type="file"
        accept="image/jpeg,image/png"
        aria-label="Upload consultation photo"
        onChange={onFileChange}
        disabled={busy || turnLocked}
      />
      <div className="cc-attachment-tools">
        <button
          ref={photoButton}
          type="button"
          className="cc-button cc-secondary"
          disabled={busy || turnLocked}
          onClick={() => inputRef.current?.click()}
        >
          <ImagePlus size={15} aria-hidden="true" />
          {file ? "Change photo" : "Upload photo"}
        </button>
        <CameraCapture
          disabled={!!busy || turnLocked}
          facing={service === "nails" ? "environment" : "user"}
          onCapture={acceptFile}
        />
        {!trial && (
          <ReferenceImagePicker
            disabled={!!busy || turnLocked}
            onSelect={acceptFile}
          />
        )}
      </div>
    </>
  );

  return (
    <div
      className={`studio-page consultation-workspace ${trial ? "cc-guest" : ""}`}
    >
      <div className="cc-breadcrumb">
        <Link href={trial ? "/" : "/client/dashboard"}>
          {trial ? "Andrea’s" : "Client portal"}
        </Link>
        <span aria-hidden="true">/</span>
        <span>AI Consultation</span>
        <nav aria-label="Consultation links">
          <Link href="/how-ai-works">How our AI works</Link>
          {trial && (
            <>
              <Link href="/register?continue=consultation">Sign up</Link>
              <Link href="/login?continue=consultation">Log in</Link>
            </>
          )}
        </nav>
      </div>
      <section className="cc-workspace" aria-labelledby="cc-title">
        <header className="cc-header">
          <div>
            <p className="cc-eyebrow">A PERSONAL BEAUTY EXPERIENCE</p>
            <h1 id="cc-title">Your beauty consultation</h1>
          </div>
          <span className="cc-mode">
            <span aria-hidden="true" />
            {providerMode === "loading"
              ? "Connecting…"
              : providerMode === "gemini"
                ? "AI consultant"
                : "Guided consultation"}
          </span>
          <nav className="cc-progress" aria-label="Consultation progress">
            {([1, 2, 3] as const).map((number) => (
              <div
                key={number}
                className={`${number === currentStage ? "is-current" : number < currentStage ? "is-complete" : ""}`}
                aria-current={number === currentStage ? "step" : undefined}
              >
                <span className="cc-step-number">
                  {number < currentStage ? (
                    <Check size={17} aria-hidden="true" />
                  ) : (
                    number
                  )}
                </span>
                <span>
                  <strong>
                    {number === 1
                      ? "Your direction"
                      : number === 2
                        ? "Consultation"
                        : "Your looks"}
                  </strong>
                  <small>
                    {number === 1
                      ? "Your idea and photo"
                      : number === 2
                        ? "Refine your preferences"
                        : "Compare, choose and book"}
                  </small>
                </span>
              </div>
            ))}
          </nav>
        </header>
        {trial && (
          <div className="cc-trial-note">
            <strong>One free AI preview.</strong> Explore three recommendations,
            then choose one image to generate.
            <details>
              <summary>About your guest preview</summary>
              <p>
                Your photo and preview are temporary and can disappear when the
                AI session ends. Signing up starts a fresh consultation; your
                guest preview is not automatically saved or transferred.
              </p>
              <p>
                The trial includes one generation attempt per browser during the
                trial period. An accepted request may use it even if
                interrupted. A confirmed busy response does not use it.
              </p>
            </details>
            {trialStatus?.state !== "available" && !trialLoading && !ready && (
              <GuestTrialIndicator
                state={trialFeedback}
                onOpen={() => setTrialLimitOpen(true)}
              />
            )}
          </div>
        )}
        <div className={`cc-body ${ready ? "cc-with-looks" : ""}`}>
          <section className="cc-chat" aria-label="Consultation conversation">
            {!started ? (
              <div className="cc-welcome">
                <div className="cc-emblem" aria-hidden="true">
                  <Sparkles size={26} />
                </div>
                <p className="cc-eyebrow">LET’S FIND YOUR NEXT LOOK</p>
                <h2>
                  A little inspiration.
                  <br />
                  <em>A look that’s yours.</em>
                </h2>
                <p>
                  Tell us what you have in mind.
                  <br />
                  We’ll guide you from your first idea to your next look.
                </p>
                <div
                  className="cc-services"
                  role="group"
                  aria-label="Choose service"
                >
                  {SERVICES.map((item) => {
                    const Icon =
                      item.id === "hairstyle"
                        ? Scissors
                        : item.id === "makeup"
                          ? WandSparkles
                          : Hand;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        className="cc-service"
                        aria-label={`${item.label} — ${item.detail}`}
                        aria-pressed={service === item.id}
                        disabled={
                          phase === "preparing" ||
                          phase === "generating" ||
                          trialLoading
                        }
                        onClick={() => changeService(item.id)}
                      >
                        <Icon size={16} aria-hidden="true" />
                        {item.label}
                      </button>
                    );
                  })}
                </div>
                <small>
                  {serviceInfo
                    ? `${serviceInfo.label} selected. Tell us what you have in mind below.`
                    : "Choose a service, or simply describe what you’re looking for."}
                </small>
              </div>
            ) : (
              <>
                <div className="cc-chat-heading">
                  <span>
                    <Sparkles size={13} aria-hidden="true" />
                    {serviceInfo
                      ? `${serviceInfo.label} consultation`
                      : "Your consultation"}
                  </span>
                  {service && !ready && (
                    <button
                      className="cc-text-button"
                      type="button"
                      aria-expanded={attachmentOpen}
                      aria-controls="cc-attachments"
                      onClick={() => setAttachmentOpen((value) => !value)}
                    >
                      Your photo
                    </button>
                  )}
                </div>
                <div
                  ref={transcript}
                  className="cc-transcript"
                  role="log"
                  aria-label="Consultation conversation"
                  aria-live="polite"
                  aria-relevant="additions text"
                  onScroll={(event) => {
                    const log = event.currentTarget;
                    following.current =
                      log.scrollHeight - log.scrollTop - log.clientHeight < 75;
                    if (following.current) setShowLatest(false);
                  }}
                >
                  {chatMessages.map((item, index) => (
                    <div key={index} className={`cc-message cc-${item.role}`}>
                      {item.role === "assistant" && (
                        <span className="cc-message-avatar" aria-hidden="true">
                          <Sparkles size={13} />
                        </span>
                      )}
                      <div>
                        <strong>
                          {item.role === "assistant"
                            ? "Andrea’s consultant"
                            : "You"}
                        </strong>
                        <p>{item.content}</p>
                      </div>
                    </div>
                  ))}
                  {draftMessage && !draftInHistory && (
                    <div className="cc-message cc-user">
                      <div>
                        <strong>You</strong>
                        <p>{draftMessage}</p>
                        {pendingTurn && (
                          <small>
                            {phase === "preparing"
                              ? "Sending…"
                              : "Awaiting confirmation"}
                          </small>
                        )}
                      </div>
                    </div>
                  )}
                  {!consultationId && initialIntent && (
                    <div className="cc-message cc-assistant">
                      <span className="cc-message-avatar" aria-hidden="true">
                        <Sparkles size={13} />
                      </span>
                      <div>
                        <strong>Before we begin</strong>
                        <p>
                          {!service
                            ? "Which service would you like to focus on first? Choose hairstyle, makeup or nails below."
                            : file
                              ? "Your photo is attached. Continue when you’re ready, and we’ll keep your original direction in mind."
                              : `To prepare your previews, attach ${service === "nails" ? "a clear hand photo" : "a clear portrait"} using the controls below. Your description is kept here until you continue.`}
                        </p>
                      </div>
                    </div>
                  )}
                  {phase === "preparing" && (
                    <p className="cc-waiting" role="status">
                      <span className="cc-spinner" aria-hidden="true" />
                      {consultationId
                        ? "Waiting for your consultant…"
                        : "Preparing your consultation…"}
                    </p>
                  )}
                </div>
              </>
            )}
            {showLatest && (
              <button
                className="cc-latest"
                type="button"
                onClick={() => {
                  following.current = true;
                  setShowLatest(false);
                  if (transcript.current)
                    transcript.current.scrollTop =
                      transcript.current.scrollHeight;
                }}
              >
                Latest message ↓
              </button>
            )}
            <div className="cc-composer-region">
              {restoring && (
                <p role="status" className="cc-note">
                  Restoring your consultation…
                </p>
              )}
              {error && (
                <p role="alert" className="cc-error">
                  {error}
                </p>
              )}
              {pendingTurn && (
                <div className="cc-recovery">
                  <p>
                    Your message is kept here. Checking status does not send it
                    again.
                  </p>
                  <button
                    type="button"
                    className="cc-button cc-secondary"
                    disabled={phase === "preparing"}
                    onClick={() => void checkConversation()}
                  >
                    Check conversation status
                  </button>
                </div>
              )}
              {sessionUnavailable && (
                <button
                  type="button"
                  className="cc-button cc-secondary"
                  disabled={busy}
                  onClick={startNewConsultation}
                >
                  Start a new consultation
                </button>
              )}
              {initialIntent && !consultationId && (
                <div
                  className="cc-services"
                  role="group"
                  aria-label="Choose service"
                >
                  {SERVICES.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="cc-service"
                      aria-pressed={service === item.id}
                      disabled={busy}
                      onClick={() => changeService(item.id)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              )}
              {providerMode === "gemini" &&
                consultationId &&
                !ready &&
                !turnLocked &&
                quickReplies.length > 0 && (
                  <div
                    className="cc-quick-replies"
                    aria-label="Suggested replies"
                  >
                    {quickReplies.map((reply) => (
                      <button
                        key={reply}
                        type="button"
                        className="cc-chip"
                        disabled={busy}
                        aria-pressed={chatInput === reply}
                        onClick={() => {
                          setChatInput(reply);
                          replyInput.current?.focus();
                        }}
                      >
                        {reply}
                      </button>
                    ))}
                  </div>
                )}
              <div className="cc-composer">
                {showAttachments && (
                  <div
                    id="cc-attachments"
                    className={`cc-attachments ${dragging ? "is-dragging" : ""}`}
                    onDragOver={(event) => {
                      event.preventDefault();
                      if (!busy && !turnLocked) setDragging(true);
                    }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={(event) => {
                      event.preventDefault();
                      setDragging(false);
                      acceptFile(event.dataTransfer.files[0]);
                    }}
                  >
                    {preview ? (
                      <div className="cc-photo-attachment">
                        <img src={preview} alt="Consultation photo preview" />
                        <div>
                          <strong>
                            {file?.name || "Your consultation photo"}
                          </strong>
                          <small>
                            {consultationId
                              ? "Changing the photo starts a fresh consultation."
                              : "Photo attached · Ready to continue"}
                          </small>
                        </div>
                      </div>
                    ) : (
                      <>
                        <h3>
                          <ImagePlus size={17} aria-hidden="true" />
                          Add your{" "}
                          {service === "nails" ? "hand photo" : "portrait"}
                        </h3>
                        <p>Choose or drop a JPG or PNG, up to 8 MB.</p>
                      </>
                    )}
                    {uploadControls}
                    <p className="cc-photo-privacy">
                      Your photo is used for your visual previews. It is not
                      sent to the conversational AI.
                    </p>
                  </div>
                )}
                {ready ? (
                  <div className="cc-ready" role="status">
                    <Check size={18} aria-hidden="true" />
                    <span>
                      Your three directions are ready. Explore your looks in the
                      panel.
                    </span>
                    <button
                      type="button"
                      className="cc-text-button"
                      onClick={() => {
                        setStep(3);
                        setLooksOpen(true);
                        requestAnimationFrame(() => {
                          resultsPanel.current?.focus();
                          resultsPanel.current?.scrollIntoView({
                            behavior: "auto",
                            block: "nearest",
                          });
                        });
                      }}
                    >
                      Explore My Looks
                    </button>
                  </div>
                ) : providerMode === "deterministic" &&
                  !!service &&
                  (!!initialIntent || step === 2) ? (
                  <div
                    className="cc-guided"
                    aria-label="Guided consultation preferences"
                  >
                    <p className="cc-guided-intro">
                      A few thoughtful choices help us find your direction.
                    </p>
                    <div className="cc-guided-grid">
                      <label>
                        Occasion or event
                        <input
                          value={occasion}
                          maxLength={80}
                          disabled={busy || turnLocked}
                          onChange={(event) => setOccasion(event.target.value)}
                          placeholder="Everyday, celebration, formal…"
                        />
                      </label>
                      <label>
                        Desired vibe
                        <input
                          value={vibe}
                          maxLength={80}
                          disabled={busy || turnLocked}
                          onChange={(event) => setVibe(event.target.value)}
                          placeholder="Natural, classic, bold…"
                        />
                      </label>
                      <label>
                        {service === "hairstyle"
                          ? "Maintenance preference"
                          : service === "makeup"
                            ? "Makeup intensity"
                            : "Nail finish"}
                        <select
                          value={servicePreference}
                          disabled={busy || turnLocked}
                          onChange={(event) =>
                            setServicePreference(event.target.value)
                          }
                        >
                          <option value="">No preference</option>
                          {(service === "hairstyle"
                            ? ["low", "medium", "high"]
                            : service === "makeup"
                              ? ["natural", "soft", "bold"]
                              : ["glossy", "matte", "ombre", "french"]
                          ).map((option) => (
                            <option key={option} value={option}>
                              {option[0].toUpperCase() + option.slice(1)}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                    <button
                      className="cc-text-button"
                      type="button"
                      aria-expanded={showMorePreferences}
                      onClick={() => setShowMorePreferences((value) => !value)}
                    >
                      {showMorePreferences
                        ? "Hide optional details"
                        : "Add optional details"}
                    </button>
                    {showMorePreferences && (
                      <div className="cc-guided-grid">
                        <label>
                          Anything to avoid? <small>(comma separated)</small>
                          <input
                            value={avoids}
                            maxLength={160}
                            disabled={busy || turnLocked}
                            onChange={(event) => setAvoids(event.target.value)}
                          />
                        </label>
                        <label>
                          Optional notes
                          <textarea
                            value={notes}
                            maxLength={500}
                            disabled={busy || turnLocked}
                            onChange={(event) => setNotes(event.target.value)}
                            rows={2}
                          />
                        </label>
                      </div>
                    )}
                    <button
                      ref={continueButton}
                      className="cc-button cc-primary"
                      type="button"
                      disabled={(!file && !photoUploaded) || busy || turnLocked}
                      onClick={() => void start()}
                    >
                      {phase === "preparing" ? "Preparing…" : "Find my looks"}
                      <Sparkles size={14} aria-hidden="true" />
                    </button>
                  </div>
                ) : (
                  <>
                    {((preparation && !initialIntent) ||
                      (!preparation &&
                        consultationId &&
                        !turnLocked &&
                        photoUploaded)) && (
                      <>
                        <label className="sr-only" htmlFor="consult-reply">
                          Your reply
                        </label>
                        <textarea
                          ref={replyInput}
                          id="consult-reply"
                          value={chatInput}
                          maxLength={500}
                          rows={2}
                          disabled={
                            busy ||
                            turnLocked ||
                            (providerMode === "loading" && !!consultationId)
                          }
                          onChange={(event) => setChatInput(event.target.value)}
                          onKeyDown={(event) => {
                            if (
                              event.key === "Enter" &&
                              !event.shiftKey &&
                              !event.nativeEvent.isComposing
                            ) {
                              event.preventDefault();
                              void replyToConsultant();
                            }
                          }}
                          placeholder={
                            consultationId
                              ? "Tell us what feels like you…"
                              : "I’m looking for a soft makeup look for graduation…"
                          }
                        />
                      </>
                    )}
                    <div className="cc-composer-toolbar">
                      <div>
                        {!turnLocked && (
                          <button
                            className="cc-attach-button"
                            type="button"
                            aria-label="Attach consultation photo"
                            aria-expanded={attachmentOpen}
                            aria-controls="cc-attachments"
                            disabled={!service || busy}
                            onClick={() => setAttachmentOpen((value) => !value)}
                          >
                            <Paperclip size={16} aria-hidden="true" />
                          </button>
                        )}
                        <span>
                          {phase === "preparing"
                            ? "Your consultant is responding…"
                            : !initialIntent && !consultationId
                              ? "Tell us your idea. We’ll guide you from here."
                              : !consultationId
                                ? file
                                  ? "Your photo is ready. Continue when you’re ready."
                                  : "Attach your photo to continue."
                                : `${chatInput.length}/500 · Enter to send`}
                        </span>
                      </div>
                      {!turnLocked &&
                        preparation &&
                        initialIntent &&
                        service && (
                          <button
                            ref={continueButton}
                            className="cc-button cc-primary"
                            type="button"
                            disabled={
                              (!file && !photoUploaded) ||
                              busy ||
                              providerMode === "loading"
                            }
                            onClick={() => void beginConversation()}
                          >
                            Continue consultation
                            <ChevronRight size={14} aria-hidden="true" />
                          </button>
                        )}
                      {!turnLocked &&
                        ((preparation && !initialIntent) ||
                          (!preparation &&
                            consultationId &&
                            photoUploaded)) && (
                          <button
                            type="button"
                            className="cc-send"
                            aria-label="Send reply"
                            disabled={!chatInput.trim() || busy}
                            onClick={() => void replyToConsultant()}
                          >
                            <ArrowUp size={18} aria-hidden="true" />
                          </button>
                        )}
                    </div>
                  </>
                )}
              </div>
              <p className="cc-disclaimer">
                Beauty previews are inspiration, not a guaranteed salon result.
              </p>
              {!ready && customLink && (
                <div className="cc-custom">{customLink}</div>
              )}
            </div>
          </section>
          {ready && (
            <button
              type="button"
              className="cc-looks-toggle cc-button cc-secondary"
              aria-expanded={looksOpen}
              aria-controls="cc-results"
              onClick={() => setLooksOpen((value) => !value)}
            >
              {looksOpen ? "Hide your looks" : "Show your looks"}
            </button>
          )}
          {ready && (
            <aside
              id="cc-results"
              ref={resultsPanel}
              tabIndex={-1}
              className={`cc-details ${looksOpen ? "" : "cc-looks-collapsed"}`}
              aria-label="Your recommended looks"
            >
              {preview && (
                <div className="cc-source-photo">
                  <div>
                    <strong>Your photo</strong>
                    <small>
                      {service === "nails" ? "HAND PHOTO" : "PORTRAIT"}
                    </small>
                  </div>
                  <img src={preview} alt="Your original consultation photo" />
                </div>
              )}
              <div className="cc-results-title">
                <h2>
                  {trial ? "Your trial recommendations" : "Your three looks"}
                </h2>
                <small>
                  {cards.filter((card) => card.status === "completed").length}{" "}
                  OF 3 READY
                </small>
              </div>
              {trial && (
                <GuestTrialIndicator
                  state={trialFeedback}
                  onOpen={() => setTrialLimitOpen(true)}
                />
              )}
              <div className="cc-look-list" aria-label="Recommendation cards">
                {cards.map((card, index) => (
                  <button
                    key={card.recommendation.id}
                    type="button"
                    className="cc-look-choice"
                    aria-label={`View look ${index + 1}: ${card.recommendation.primary.style_name}`}
                    aria-pressed={
                      activeCard?.recommendation.id === card.recommendation.id
                    }
                    onClick={() => switchLook(card)}
                  >
                    <span>{`0${index + 1}`}</span>
                    <div>
                      <strong>{card.recommendation.primary.style_name}</strong>
                      <small>{cardLabel(card)}</small>
                    </div>
                    {card.status === "completed" ? (
                      <Check size={14} aria-hidden="true" />
                    ) : trial && trialFeedback === "used" ? (
                      <LockKeyhole size={14} aria-hidden="true" />
                    ) : null}
                  </button>
                ))}
              </div>
              {activeCard && (
                <article className="cc-featured" aria-label="Featured look">
                  <div className="cc-result-image">
                    {activeCard.result ? (
                      <StudioPhoto
                        src={activeCard.result.image.data_url}
                        alt={`Generated ${activeCard.recommendation.primary.style_name} preview`}
                      />
                    ) : (
                      <div className="cc-placeholder">
                        {activeCard.status === "generating" ||
                        activeCard.status === "completed" ? (
                          <span className="cc-spinner" />
                        ) : (
                          <Sparkles size={24} aria-hidden="true" />
                        )}
                        <p>
                          {activeCard.status === "pending"
                            ? pendingPreviewMessage
                            : activeCard.status === "generating"
                              ? "Creating this look…"
                              : activeCard.status === "completed"
                                ? "Recovering this preview…"
                                : activeCard.status === "unknown"
                                  ? "Check your request status"
                                  : "Preview unavailable"}
                        </p>
                      </div>
                    )}
                  </div>
                  <p className="cc-look-index">
                    LOOK 0{activeIndex + 1} / 03 · {cardLabel(activeCard)}
                  </p>
                  <h3>{activeCard.recommendation.primary.style_name}</h3>
                  <p className="cc-reason">
                    {activeCard.recommendation.reason}
                  </p>
                  <LookInformation
                    feature={activeCard.recommendation.primary.feature}
                    styleId={activeCard.recommendation.primary.style_id}
                  />
                  {activeCard.recommendation.complements.length > 0 && (
                    <p className="cc-note">
                      Pairs with{" "}
                      {activeCard.recommendation.complements
                        .map((item) => item.style_name)
                        .join(", ")}
                      . Complementary visuals are not generated.
                    </p>
                  )}
                  {activeCard.error && (
                    <p role="alert" className="cc-error">
                      {activeCard.error}
                    </p>
                  )}
                  <div className="cc-result-actions">
                    {activeCard.status === "completed" && activeCard.result && (
                      <>
                        {!trial && (
                          <button
                            type="button"
                            className="cc-button cc-primary"
                            disabled={selectionBusy || restoring}
                            onClick={() => void select(activeCard)}
                          >
                            {selectedId === activeCard.recommendation.id
                              ? "Selected"
                              : "Select This Look"}
                          </button>
                        )}
                        <a
                          className="cc-button cc-secondary"
                          href={activeCard.result.image.data_url}
                          download={`andreas-${activeCard.recommendation.primary.style_id}.${activeCard.result.image.content_type === "image/jpeg" ? "jpg" : "png"}`}
                        >
                          Download
                        </a>
                      </>
                    )}
                    {!trial && activeCard.canRetry && (
                      <button
                        className="cc-button cc-secondary"
                        type="button"
                        disabled={busy || manualBusy || turnLocked}
                        onClick={() => void retry(activeCard)}
                      >
                        Retry this look
                      </button>
                    )}
                    {activeCard.status === "unknown" && (
                      <button
                        className="cc-button cc-secondary"
                        type="button"
                        disabled={
                          phase === "preparing" || phase === "generating"
                        }
                        onClick={() => void checkStatus(activeCard)}
                      >
                        Check status
                      </button>
                    )}
                    {trial &&
                      activeCard.status !== "completed" &&
                      (trialFeedback === "used" ||
                        trialFeedback === "unresolved") && (
                        <button
                          className="cc-button cc-primary"
                          type="button"
                          onClick={() => setTrialLimitOpen(true)}
                        >
                          {trialFeedback === "used"
                            ? "Unlock this preview"
                            : "View trial details"}
                        </button>
                      )}
                  </div>
                </article>
              )}
              {cards.every((card) => card.status === "pending") &&
                (!trial || trialStatus?.state === "available") && (
                  <button
                    type="button"
                    className="cc-button cc-primary cc-generate"
                    disabled={busy || manualBusy || turnLocked}
                    onClick={() => void generateLooks()}
                  >
                    {trial
                      ? "Generate " +
                        (activeCard?.recommendation.primary.style_name ||
                          "This Look")
                      : "Generate My Looks"}
                    <Sparkles size={14} aria-hidden="true" />
                  </button>
                )}
              {phase === "generating" && (
                <p role="status" className="cc-note">
                  {trial
                    ? "Creating your chosen trial preview."
                    : "Your previews are generated one at a time."}{" "}
                  Nails can take several minutes.
                </p>
              )}
              {!trial &&
                phase === "attention" &&
                cards.some((card) => card.status === "pending") &&
                !cards.some((card) => card.status === "unknown") && (
                  <button
                    type="button"
                    className="cc-button cc-secondary"
                    disabled={manualBusy || !!pendingTurn}
                    onClick={() => void continuePending()}
                  >
                    Continue remaining looks
                  </button>
                )}
              {!trial && selected && selected.result && (
                <section
                  className="cc-selection"
                  aria-label="Selected recommendation"
                >
                  <p>
                    <Check size={14} aria-hidden="true" />
                    Your selected look
                  </p>
                  <h3>{selected.recommendation.primary.style_name}</h3>
                  <p className="cc-note">
                    Save this preview, or bring it to an appointment. No booking
                    has been made.
                  </p>
                  {!restoring && (
                    <SavedLookActions
                      key={selected.recommendation.id}
                      feature={selected.recommendation.primary.feature}
                      result={selected.result}
                      sourceKind="consultation"
                      bookLabel="Book Selected Look"
                    />
                  )}
                </section>
              )}
              {customLink && <div className="cc-custom">{customLink}</div>}
            </aside>
          )}
        </div>
      </section>
      <footer className="cc-footer">
        <span>
          ANDREA’S <Sparkles size={10} aria-hidden="true" /> AI STUDIO
        </span>
        <span>Explore a look that feels like you.</span>
      </footer>
      {trial && (
        <GuestTrialLimitDialog
          state={trialFeedback}
          open={trialLimitOpen}
          hasPreview={hasTrialPreview}
          onClose={() => setTrialLimitOpen(false)}
        />
      )}
    </div>
  );
}

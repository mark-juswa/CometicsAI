import { AiClientError, generateCustom, resumeCustom, type FeatureId, type GeneratedResult } from './browser-client';
import { browserDrafts, DRAFT_TTL, FEATURES, readTicket, ticketKey, STORAGE_PREFIX, type DraftStorage, type Ticket } from './generation-storage';

export type StudioDraft = { file: File | null; preview: string; styleId: string; result: GeneratedResult | null;
  resultOpen: boolean; phase: 'idle' | Ticket['phase']; error: string; jobId?: string; expires: number };
const empty = (): StudioDraft => ({ file: null, preview: '', styleId: '', result: null,
  resultOpen: false, phase: 'idle', error: '', expires: 0 });
export type Snapshot = { ready: boolean; warning: string; drafts: Record<FeatureId, StudioDraft>; consultation: Record<string, unknown> };
type Dependencies = { storage: Storage; assets: DraftStorage; generate: typeof generateCustom; resume: typeof resumeCustom };
export const pending = (draft: StudioDraft) => ['submitting', 'generating', 'unknown'].includes(draft.phase) && draft.expires > Date.now();

/** Owns jobs independently of route lifetimes. Server admission remains authoritative. */
export class GenerationStore {
  private snapshot: Snapshot = { ready: false, warning: '', drafts: { hairstyle: empty(), makeup: empty(), nails: empty() }, consultation: {} };
  private refs = new Map<string, { current: unknown }>();
  private listeners = new Set<() => void>();
  private controllers = new Map<FeatureId, AbortController>();
  private writes: Promise<unknown> = Promise.resolve();
  private consultationWriteScheduled = false;
  private epoch = 0;
  private closed = false;
  private deps: Dependencies;
  constructor(readonly owner: string, dependencies: Partial<Dependencies> = {}) {
    this.deps = { storage: globalThis.localStorage, assets: browserDrafts,
      generate: generateCustom, resume: resumeCustom, ...dependencies };
  }
  getSnapshot = () => this.snapshot;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private publish() { this.snapshot = { ...this.snapshot }; this.listeners.forEach(listener => listener()); }
  private warn() {
    this.snapshot.warning = 'Browser storage is unavailable. Keep this tab open until generation finishes; refresh recovery may be unavailable.';
    this.publish();
  }
  private ticket(feature: FeatureId): Ticket {
    const draft = this.snapshot.drafts[feature];
    return { owner: this.owner, feature, styleId: draft.styleId, jobId: draft.jobId,
      phase: draft.phase === 'idle' ? 'completed' : draft.phase, expires: draft.expires, error: draft.error };
  }
  private persist(feature: FeatureId) {
    if (this.closed) return;
    const draft = this.snapshot.drafts[feature], key = ticketKey(this.owner, feature);
    try { this.deps.storage.setItem(key, JSON.stringify(this.ticket(feature))); } catch { this.warn(); }
    const assets = { file: draft.file, result: draft.result, expires: draft.expires, jobId: draft.jobId };
    this.writes = this.writes.then(async () => {
      if (this.closed) return;
      if (!assets.file && assets.jobId) {
        const existing = await this.deps.assets.read(key);
        if (existing?.jobId !== assets.jobId) return;
        assets.file = existing.file;
      }
      await this.deps.assets.write(key, assets);
      // Notify other tabs only after the matching photo/result transaction commits.
      if (!this.closed) try { this.deps.storage.setItem(STORAGE_PREFIX + this.owner + ':assets:' + feature, String(Date.now()) + Math.random()); } catch { this.warn(); }
    }).catch(() => { if (!this.closed) this.warn(); });
  }
  private patch(feature: FeatureId, change: Partial<StudioDraft>, persist = true) {
    if (this.closed) return;
    this.snapshot.drafts = { ...this.snapshot.drafts, [feature]: { ...this.snapshot.drafts[feature], ...change } };
    if (persist) this.persist(feature);
    this.publish();
  }
  async start() {
    this.closed = false;
    const epoch = ++this.epoch;
    await Promise.all(FEATURES.map(async feature => {
      const key = ticketKey(this.owner, feature);
      let ticket: Ticket | null = null;
      try { ticket = readTicket(this.deps.storage, this.owner, feature); } catch { this.warn(); }
      if (!ticket) {
        try { this.deps.storage.removeItem(key); } catch { this.warn(); }
        await this.deps.assets.remove(key).catch(() => {});
        return;
      }
      let assets;
      try { assets = await this.deps.assets.read(key); } catch { this.warn(); }
      if (this.closed || epoch !== this.epoch) return;
      const old = this.snapshot.drafts[feature];
      if (old.preview) URL.revokeObjectURL(old.preview);
      const matching = assets && assets.expires > Date.now() && assets.jobId === ticket.jobId;
      const file = matching && assets ? assets.file : null;
      const result = matching && assets ? assets.result : null;
      this.patch(feature, { ...ticket, file, preview: file ? URL.createObjectURL(file) : '', result,
        resultOpen: !!result, error: ticket.error || '', phase: pending({ ...empty(), ...ticket }) ? 'unknown' : ticket.phase }, false);
    }));
    if (this.closed || epoch !== this.epoch) return;
    const consultationKey = STORAGE_PREFIX + this.owner + ':consultation';
    let consultationTicket: { owner: string; handle: string; expires: number } | null = null;
    try {
      const value = JSON.parse(this.deps.storage.getItem(consultationKey) || 'null');
      if (value?.owner === this.owner && typeof value.handle === 'string' && value.handle.length < 8192 &&
          value.expires > Date.now() && value.expires <= Date.now() + DRAFT_TTL + 1000) consultationTicket = value;
    } catch { this.warn(); }
    try {
      const saved = await this.deps.assets.read(consultationKey);
      if (this.closed || epoch !== this.epoch) return;
      if (saved?.consultation && saved.expires > Date.now() &&
          (!consultationTicket || (saved.consultation.consultationId || '') === consultationTicket.handle)) {
        this.snapshot.consultation = { ...saved.consultation, selectionBusy: false,
          phase: saved.consultation.consultationId ? 'attention' : 'setup',
          cards: Array.isArray(saved.consultation.cards) ? saved.consultation.cards.map(card =>
            card.status === 'generating' ? { ...card, status: 'unknown', canRetry: false } : card) : [],
          preview: saved.file ? URL.createObjectURL(saved.file) : '', file: saved.file };
      } else await this.deps.assets.remove(consultationKey);
    } catch { this.warn(); }
    if (consultationTicket?.handle && !this.snapshot.consultation.consultationId)
      this.snapshot.consultation = { consultationId: consultationTicket.handle, phase: 'attention' };
    if (this.closed || epoch !== this.epoch) return;
    this.snapshot.ready = true; this.publish();
    for (const feature of FEATURES) {
      const draft = this.snapshot.drafts[feature];
      if (pending(draft) || draft.phase === 'completed' && draft.jobId && !draft.result) void this.recover(feature);
    }
  }
  stop() {
    this.closed = true; this.epoch++;
    this.controllers.forEach(controller => controller.abort()); this.controllers.clear();
    for (const draft of Object.values(this.snapshot.drafts)) if (draft.preview) URL.revokeObjectURL(draft.preview);
    if (typeof this.snapshot.consultation.preview === 'string') URL.revokeObjectURL(this.snapshot.consultation.preview);
  }
  busyFeature(): FeatureId | undefined {
    const manual = FEATURES.find(feature => pending(this.snapshot.drafts[feature]));
    if (manual) return manual;
    const service = this.snapshot.consultation.service;
    return this.snapshot.consultation.phase === 'generating' && FEATURES.includes(service as FeatureId) ? service as FeatureId : undefined;
  }
  private canEdit(feature: FeatureId) {
    if (!this.snapshot.ready || pending(this.snapshot.drafts[feature])) return false;
    const shared = readTicket(this.deps.storage, this.owner, feature);
    if (shared && pending({ ...empty(), ...shared })) { void this.sync(); return false; }
    return true;
  }
  setFile(feature: FeatureId, file: File | null) {
    if (!this.canEdit(feature)) return;
    const old = this.snapshot.drafts[feature];
    if (old.preview) URL.revokeObjectURL(old.preview);
    this.patch(feature, { file, preview: file ? URL.createObjectURL(file) : '', result: null, resultOpen: false,
      jobId: undefined, phase: 'idle', error: '', expires: Date.now() + DRAFT_TTL });
  }
  select(feature: FeatureId, styleId: string) {
    if (!this.canEdit(feature)) return;
    this.patch(feature, { styleId, result: null, resultOpen: false, jobId: undefined, phase: 'idle', error: '', expires: Date.now() + DRAFT_TTL });
  }
  open(feature: FeatureId, resultOpen: boolean) { this.patch(feature, { resultOpen }, false); }
  setConsultation<T>(key: string, value: T | ((old: T) => T), initial: T) {
    if (this.closed) return;
    const old = (key in this.snapshot.consultation ? this.snapshot.consultation[key] : initial) as T;
    this.snapshot.consultation = { ...this.snapshot.consultation, [key]: typeof value === 'function' ? (value as (old: T) => T)(old) : value };
    if (key === 'consultationId') try {
      this.deps.storage.setItem(STORAGE_PREFIX + this.owner + ':consultation', JSON.stringify({
        owner: this.owner, handle: this.snapshot.consultation.consultationId, expires: Date.now() + DRAFT_TTL }));
    } catch { this.warn(); }
    if (!this.consultationWriteScheduled) {
      this.consultationWriteScheduled = true;
      this.writes = this.writes.then(async () => {
        this.consultationWriteScheduled = false;
        if (this.closed) return;
        const { preview: _preview, ...view } = this.snapshot.consultation;
        const assets = { file: (view.file as File | null) || null, result: null, expires: Date.now() + DRAFT_TTL, consultation: view };
        await this.deps.assets.write(STORAGE_PREFIX + this.owner + ':consultation', assets);
      }).catch(() => { if (!this.closed) this.warn(); });
    }
    this.publish();
  }
  consultationRef<T>(key: string, initial: T): { current: T } {
    if (!this.refs.has(key)) this.refs.set(key, { current: initial });
    return this.refs.get(key)! as { current: T };
  }
  async run(feature: FeatureId) {
    const draft = this.snapshot.drafts[feature];
    if (!this.snapshot.ready || !draft.file || !draft.styleId || this.busyFeature()) return;
    // Claim synchronously before yielding, including rapid double clicks.
    this.patch(feature, { phase: 'submitting', error: '', result: null, resultOpen: false,
      jobId: undefined, expires: Date.now() + DRAFT_TTL }, false);
    const execute = async () => {
      // Another tab may have admitted work before this lock became available.
      for (const other of FEATURES) {
        let ticket: Ticket | null = null;
        try { ticket = readTicket(this.deps.storage, this.owner, other); } catch { this.warn(); }
        if (ticket && pending({ ...empty(), ...ticket })) {
          this.patch(feature, { phase: 'failed', error: 'Another preview is running. Return to its studio or browser tab to check it.' }, false); return;
        }
      }
      this.persist(feature);
      await this.perform(feature, false);
    };
    if (typeof navigator !== 'undefined' && navigator.locks) {
      await navigator.locks.request('beautycore-generation', { ifAvailable: true }, async lock => {
        if (!lock) { this.patch(feature, { phase: 'failed', error: 'A preview is running in another tab. Check that tab before generating again.' }, false); return; }
        await execute();
      });
    } else await execute();
  }
  async recover(feature: FeatureId) {
    const draft = this.snapshot.drafts[feature];
    if (this.closed || this.controllers.has(feature)) return;
    if (draft.expires <= Date.now()) {
      this.patch(feature, { phase: 'failed', error: 'This preview recovery window has expired. You can explicitly generate a new preview.' }); return;
    }
    if (!draft.jobId) {
      this.patch(feature, { phase: 'unknown', error: 'The original request was interrupted before its ticket arrived. No replacement was sent. Keep the original tab open or wait for the 30 minute recovery window to end.' }); return;
    }
    await this.perform(feature, true);
  }
  private async perform(feature: FeatureId, resume: boolean) {
    const draft = this.snapshot.drafts[feature], epoch = this.epoch;
    const controller = new AbortController(); this.controllers.set(feature, controller);
    const current = () => !this.closed && epoch === this.epoch && !controller.signal.aborted;
    this.patch(feature, { phase: 'generating', error: '' }, !resume);
    try {
      const options = { signal: controller.signal, onAccepted: (jobId: string) => {
        if (current()) this.patch(feature, { jobId }, !resume);
      } };
      const result = resume ? await this.deps.resume(draft.jobId!, options) :
        await this.deps.generate(feature, draft.file!, draft.styleId, options);
      if (current()) this.patch(feature, { result, resultOpen: true, phase: 'completed', error: '' });
    } catch (cause) {
      if (!current()) return;
      const missing = cause instanceof AiClientError && [401, 403, 404, 410, 422].includes(cause.status);
      const ambiguous = cause instanceof AiClientError && cause.ambiguous && !missing;
      this.patch(feature, { phase: ambiguous ? 'unknown' : 'failed', error: missing ?
        'The original preview is unavailable or expired. No replacement was generated.' :
        cause instanceof Error ? cause.message : 'Preview failed. Please try again.' });
    } finally { if (this.controllers.get(feature) === controller) this.controllers.delete(feature); }
  }
  /** Storage events are notices only. Read the accepted ticket, never replay a POST. */
  async sync() {
    if (this.closed) return;
    for (const feature of FEATURES) {
      const ticket = readTicket(this.deps.storage, this.owner, feature);
      if (!ticket) continue;
      let draft = this.snapshot.drafts[feature];
      const changedJob = ticket.jobId && ticket.jobId !== draft.jobId;
      if (changedJob && !this.controllers.has(feature)) {
        if (draft.preview) URL.revokeObjectURL(draft.preview);
        this.patch(feature, { ...ticket, file: null, preview: '', result: null, resultOpen: false }, false);
        draft = this.snapshot.drafts[feature];
      }
      if (ticket.jobId === draft.jobId && ticket.jobId && !draft.file) {
        try {
          const saved = await this.deps.assets.read(ticketKey(this.owner, feature));
          if (!this.closed && saved?.jobId === ticket.jobId && saved.expires > Date.now() && saved.file &&
              this.snapshot.drafts[feature].jobId === ticket.jobId)
            this.patch(feature, { file: saved.file, preview: URL.createObjectURL(saved.file) }, false);
        } catch { this.warn(); }
      }
      if (changedJob && !this.controllers.has(feature)) {
        void this.recover(feature);
      } else if (!ticket.jobId && ['submitting', 'generating', 'unknown'].includes(ticket.phase) && !this.controllers.has(feature)) {
        this.patch(feature, { ...ticket, phase: 'unknown', error: 'A preview request is being admitted in another tab. Check that tab for its status.' }, false);
      }
    }
    this.publish();
  }
  tick() {
    for (const feature of FEATURES) {
      const draft = this.snapshot.drafts[feature];
      if (draft.expires > 0 && draft.expires <= Date.now()) {
        this.controllers.get(feature)?.abort(); this.controllers.delete(feature);
        if (draft.preview) URL.revokeObjectURL(draft.preview);
        this.patch(feature, { ...empty(), phase: 'failed', error: 'The preview recovery window expired. No replacement was generated. Upload a photo to explicitly try a new preview.' }, false);
        const key = ticketKey(this.owner, feature);
        try { this.deps.storage.removeItem(key); } catch { this.warn(); }
        this.writes = this.writes.then(() => this.deps.assets.remove(key)).catch(() => this.warn());
      }
    }
  }
}

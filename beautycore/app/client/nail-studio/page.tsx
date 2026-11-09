"use client";
import { ReferenceImagePicker } from "@/components/reference-image-picker";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import {
  GenerationProgress,
  ResultDialog,
  StudioPanel,
  StudioPhoto,
  StudioShell,
} from "@/components/ai-studio";
import {
  API_BASE_URL,
  getStyles,
  type Style,
} from "@/lib/ai/studio-api";
import { useStudioGeneration } from "@/components/generation-provider";
import { takeCustomPhoto } from "@/lib/ai/studio-photo-handoff";

const MAX_BYTES = 8 * 1024 * 1024;
const COLORS: Record<string, string> = {
  classic_red: "#aa2138",
  nude_pink: "#d696a3",
  glossy_black: "#24232a",
  french_tip: "#e9d7d6",
  pink_ombre: "#c6719e",
};

export default function NailsPage() {
  const [styles, setStyles] = useState<Style[]>([]);
  const [loading, setLoading] = useState(true);
  const [stylesError, setStylesError] = useState("");
  const job = useStudioGeneration("nails");
  const { file, preview, styleId, result, resultOpen, generating: working } = job;
  const [uploadError, setError] = useState("");
  const error = uploadError || job.error;
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;
    const transferred = takeCustomPhoto("nails");
    if (
      transferred &&
      ["image/jpeg", "image/png"].includes(transferred.type) &&
      transferred.size > 0 &&
      transferred.size <= MAX_BYTES
    ) {
      job.setFile(transferred);
    }
    getStyles("nails")
      .then((items) => {
        if (active) setStyles(items);
      })
      .catch(() => {
        if (active)
          setStylesError(`The local API is unavailable at ${API_BASE_URL}.`);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  function resetResult() {
    job.open(false);
  }

  function choose(event: ChangeEvent<HTMLInputElement>) {
    const next = event.target.files?.[0];
    event.target.value = "";
    if (next) acceptFile(next);
  }

  function acceptFile(next: File) {
    if (job.locked || !job.ready) return;
    if (
      !["image/jpeg", "image/png"].includes(next.type) ||
      next.size < 1 ||
      next.size > MAX_BYTES
    ) {
      setError("Choose a JPG or PNG image up to 8 MB.");
      return;
    }
    job.setFile(next);
    setError("");
    resetResult();
  }

  function clear() {
    job.setFile(null);
    resetResult();
    setError("");
  }

  async function generate() { setError(""); await job.run(); }

  const selectedStyle = styles.find((style) => style.id === styleId);
  return (
    <StudioShell
      feature="nails"
      eyebrow="THE AI BEAUTY STUDIO"
      title="A polished look."
      emphasis="Made for your hands."
      description="Try a nail finish on your own photo. For the clearest preview, show the back of your hand with three to five visible nails."
      badge="Virtual nail try-on"
    >
      <div className="studio-workspace">
        <StudioPanel
          id="nails-photo-heading"
          number="01"
          title="Your hand photo"
          detail="Show the back of your hand in clear light."
        >
          <input
            ref={input}
            className="sr-only"
            type="file"
            accept="image/jpeg,image/png"
            onChange={choose}
            disabled={!job.ready || job.locked}
            aria-label="Choose a hand photo"
          />
          {preview ? (
            <StudioPhoto src={preview} alt="Uploaded hand photo" />
          ) : (
            <button
              type="button"
              className="studio-upload"
              onClick={() => input.current?.click()}
            >
              <span className="studio-upload-icon" aria-hidden="true">
                ↑
              </span>
              <strong>Choose your hand photo</strong>
              <small>
                JPG or PNG image, up to 8 MB. Your original stays available for
                comparison.
              </small>
            </button>
          )}
          {file && (
            <div className="studio-file-row">
              <div>
                <strong>{file.name}</strong>
                <small>{(file.size / 1024 / 1024).toFixed(2)} MB</small>
              </div>
              <div>
                <button
                  type="button"
                  className="studio-text-button"
                  disabled={!job.ready || job.locked}
                  onClick={() => input.current?.click()}
                >
                  Replace
                </button>
                <button
                  type="button"
                  className="studio-text-button"
                  disabled={!job.ready || job.locked}
                  onClick={clear}
                >
                  Remove
                </button>
              </div>
            </div>
          )}
          <ReferenceImagePicker
            disabled={!job.ready || job.locked}
            onSelect={acceptFile}
            purpose="Nail Studio"
          />
        </StudioPanel>
        <StudioPanel
          id="nails-styles-heading"
          number="02"
          title="Choose a nail look"
          detail="Pick the finish you want to see."
        >
          {loading && (
            <p role="status" className="studio-loading-styles">
              Loading styles…
            </p>
          )}
          {stylesError && (
            <p role="alert" className="studio-alert">
              {stylesError}
            </p>
          )}
          <div className="studio-nail-grid">
            {styles.map((style) => (
              <button
                key={style.id}
                type="button"
                className="studio-nail-card"
                disabled={!job.ready || job.locked}
                aria-pressed={styleId === style.id}
                onClick={() => {
                  job.select(style.id);
                  resetResult();
                  setError("");
                }}
              >
                <span
                  className="studio-nail-swatch"
                  style={{ background: COLORS[style.id] || "#9a7ab8" }}
                  aria-hidden="true"
                />
                <span>
                  <strong>{style.name}</strong>
                  <small>{style.description}</small>
                </span>
              </button>
            ))}
          </div>
          <p className="studio-tip">
            <strong>Photo tip</strong>
            <br />
            Keep nails visible and in focus. Model-backed looks are applied
            across each nail and may take several minutes.
          </p>
        </StudioPanel>
      </div>
      <section
        aria-label="Generate nails preview"
        className="studio-action-bar"
      >
        <div>
          <small>03 / CREATE YOUR LOOK</small>
          <h2>Ready for your nail preview?</h2>
          <p>
            {selectedStyle
              ? `Selected: ${selectedStyle.name}`
              : "Upload a hand photo and select a style."}
          </p>
        </div>
        <button
          type="button"
          className="studio-primary-button"
          disabled={!job.ready || !file || !styleId || job.busy}
          onClick={() => void generate()}
        >
          {working ? "Applying nail style…" : "Try this style"}{" "}
          <span aria-hidden="true">✦</span>
        </button>
      </section>
      {error && (
        <p role="alert" className="studio-alert">
          {error}
        </p>
      )}
      {job.phase === "unknown" && <button type="button" className="studio-text-button" onClick={() => void job.recover()}>Check existing preview</button>}
      {result && !resultOpen && (
        <button
          type="button"
          className="studio-view-result"
          onClick={() => job.open(true)}
        >
          View your result again
        </button>
      )}
      {working && job.progressOpen && <GenerationProgress onBrowse={job.hideProgress} feature="nails" />}
      <ResultDialog
        feature="nails"
        result={result}
        open={resultOpen}
        original={preview}
        originalAlt="Original hand photo"
        generatedAlt={
          result?.status === "placeholder"
            ? "Original photo preview"
            : `Hand with ${result?.style.name} nails`
        }
        title={
          result?.status === "placeholder"
            ? "A preview of the workflow"
            : "Your nail look is ready"
        }
        note={
          result?.status === "placeholder"
            ? "Nail styling is unavailable in this development preview."
            : "AI previews may differ from real polish. Check the comparison before downloading."
        }
        onClose={() => job.open(false)}
        onRegenerate={() => void generate()}
      />
    </StudioShell>
  );
}

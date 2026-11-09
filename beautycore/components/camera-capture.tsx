'use client';

import { useEffect, useId, useRef, useState } from 'react';
import { Camera } from 'lucide-react';

type Facing = 'user' | 'environment';
const MAX_BYTES = 8 * 1024 * 1024;

function cameraError(error: unknown): string {
  const name = error instanceof Error ? error.name : '';
  if (name === 'NotAllowedError' || name === 'SecurityError')
    return 'Camera access was not allowed. You can allow it in your browser settings, use the device camera picker, or upload a photo instead.';
  if (name === 'NotFoundError' || name === 'DevicesNotFoundError')
    return 'No camera was found. Connect a camera, use the device camera picker, or upload a photo instead.';
  return 'The camera could not start. It may be in use by another app. Try again or upload a photo instead.';
}

export function CameraCapture({ onCapture, disabled = false, facing = 'user' }: {
  onCapture: (file: File) => void; disabled?: boolean; facing?: Facing;
}) {
  const titleId = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const nativeInput = useRef<HTMLInputElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const revision = useRef(0);
  const [open, setOpen] = useState(false);
  const [direction, setDirection] = useState<Facing>(facing);
  const [attempt, setAttempt] = useState(0);
  const [ready, setReady] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [error, setError] = useState('');
  const [photo, setPhoto] = useState<File | null>(null);
  const [still, setStill] = useState('');

  function stop() {
    revision.current++;
    stream.current?.getTracks().forEach(track => track.stop());
    stream.current = null;
    if (video.current) video.current.srcObject = null;
  }
  function close() { stop(); setOpen(false); setPhoto(null); setReady(false); setCapturing(false); }

  useEffect(() => {
    if (!photo) { setStill(''); return; }
    const url = URL.createObjectURL(photo); setStill(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  useEffect(() => {
    if (!open) return;
    if (disabled) { setOpen(false); setPhoto(null); return; }
    dialog.current?.showModal();
    if (photo) return;
    const token = ++revision.current;
    let active = true;
    setReady(false); setError(''); setCapturing(false);
    async function start() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setError('Live camera preview is not supported here. On a supported phone, try the device camera picker, or upload a photo instead.');
        return;
      }
      try {
        const acquired = await navigator.mediaDevices.getUserMedia({ audio: false,
          video: { facingMode: { ideal: direction }, width: { ideal: 1600 }, height: { ideal: 1200 } } });
        if (!active || token !== revision.current) { acquired.getTracks().forEach(track => track.stop()); return; }
        stream.current = acquired;
        if (video.current) {
          video.current.srcObject = acquired;
          try { await video.current.play(); }
          catch { if (active && token === revision.current) { stop(); setError('The camera preview could not play. Try again or upload a photo instead.'); } }
        }
      } catch (cause) { if (active && token === revision.current) setError(cameraError(cause)); }
    }
    void start();
    return () => { active = false; stop(); };
  }, [open, disabled, direction, attempt, photo]);

  function review(file: File) {
    if (!['image/jpeg', 'image/png'].includes(file.type) || !file.size || file.size > MAX_BYTES) {
      setCapturing(false); setError('Choose a JPG or PNG photo up to 8 MB.'); return;
    }
    stop(); setPhoto(file); setCapturing(false); setReady(false); setError('');
  }
  function capture() {
    const source = video.current;
    if (!source?.videoWidth || !source.videoHeight || !ready || capturing) return;
    const token = revision.current;
    setCapturing(true); setError('');
    try {
      const canvas = document.createElement('canvas');
      const scale = Math.min(1, 1600 / Math.max(source.videoWidth, source.videoHeight));
      canvas.width = Math.max(1, Math.round(source.videoWidth * scale));
      canvas.height = Math.max(1, Math.round(source.videoHeight * scale));
      const context = canvas.getContext('2d');
      if (!context) throw new Error('Capture unavailable');
      context.drawImage(source, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(blob => {
        if (token !== revision.current) return;
        if (!blob) { setCapturing(false); setError('The photo could not be captured. Please try again.'); return; }
        review(new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' }));
      }, 'image/jpeg', 0.9);
    } catch { setCapturing(false); setError('The photo could not be captured. Please try again.'); }
  }

  return <div className="studio-camera-option">
    <button type="button" className="studio-secondary-button" disabled={disabled}
      onClick={() => { setPhoto(null); setError(''); setDirection(facing); setOpen(true); }}>
      <Camera size={16} aria-hidden="true" /> Use camera
    </button>
    {open && <dialog ref={dialog} className="studio-camera-dialog" aria-labelledby={titleId}
      onCancel={close} onClose={close}>
      <div className="studio-camera-heading"><div><p className="studio-eyebrow">YOUR PHOTO</p>
        <h2 id={titleId}>Take a photo</h2></div>
        <button type="button" className="studio-icon-button" aria-label="Close camera" onClick={close}>×</button>
      </div>
      <p className="studio-camera-help">{photo ? 'Check your photo before using it.' : direction === 'environment'
        ? 'Keep your hand and nails clearly visible in good light.' : 'Face the camera in good light and keep your face and hair visible.'}</p>
      <div className="studio-camera-preview">
        {photo ? still ? <img src={still} alt="Captured photo for review" /> : <p role="status">Preparing photo review…</p> : <video ref={video} autoPlay playsInline muted
          aria-label="Live camera preview" onLoadedData={() => setReady(true)} />}
      </div>
      {error && <p role="alert" className="studio-alert">{error}</p>}
      {!photo && !ready && !error && <p role="status">Waiting for camera permission and preview…</p>}
      <div className="studio-camera-actions">
        {photo ? <><button type="button" className="studio-secondary-button" onClick={() => { setPhoto(null); setAttempt(value => value + 1); }}>Retake</button>
          <button type="button" className="studio-primary-button" disabled={disabled} onClick={() => { onCapture(photo); close(); }}>Use photo</button></>
          : <><button type="button" className="studio-secondary-button" disabled={capturing} onClick={() => { setDirection(value => value === 'user' ? 'environment' : 'user'); }}>Switch camera</button>
            <button type="button" className="studio-primary-button" disabled={!ready || capturing || disabled} onClick={capture}>{capturing ? 'Capturing…' : 'Take photo'}</button>
            {error && <button type="button" className="studio-text-button" onClick={() => setAttempt(value => value + 1)}>Try camera again</button>}</>}
      </div>
      {!photo && <><input ref={nativeInput} type="file" accept="image/jpeg,image/png" capture={direction}
        className="sr-only" aria-label="Device camera photo" onChange={event => {
          const chosen = event.target.files?.[0]; event.target.value = ''; if (chosen) review(chosen);
        }} />
        <button type="button" className="studio-text-button" disabled={capturing || disabled} onClick={() => nativeInput.current?.click()}>Use device camera picker</button></>}
      <p className="studio-camera-privacy">Only the photo you choose enters your upload. No audio is requested. You can close this window and use the ordinary upload instead.</p>
    </dialog>}
  </div>;
}

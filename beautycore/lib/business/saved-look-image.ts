import {
  MAX_SAVED_LOOK_BYTES,
  SAVED_LOOK_COPY_BYTES,
} from "./saved-look-limits";

function imageBytes(dataUrl: string) {
  const start = dataUrl.indexOf(",") + 1;
  return (
    Math.floor(((dataUrl.length - start) * 3) / 4) -
    (dataUrl.endsWith("==") ? 2 : dataUrl.endsWith("=") ? 1 : 0)
  );
}

export function needsSavedLookCopy(dataUrl: string) {
  return imageBytes(dataUrl) > MAX_SAVED_LOOK_BYTES;
}

/** Prepare only the persisted reference copy. Never mutate the generated result. */
export async function prepareSavedLookImage(dataUrl: string): Promise<string> {
  if (!needsSavedLookCopy(dataUrl)) return dataUrl;
  if (!/^data:image\/(png|jpeg);base64,/.test(dataUrl))
    throw new Error("This preview must be a PNG or JPEG image.");
  if (typeof document === "undefined" || typeof Image === "undefined")
    throw new Error(
      "A smaller saved copy could not be prepared. Please try again in your browser.",
    );
  const image = new Image();
  const canvas = document.createElement("canvas");
  try {
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () =>
        reject(
          new Error(
            "This preview could not be prepared for saving. Please try again.",
          ),
        );
      image.src = dataUrl;
    });
    const width = image.naturalWidth,
      height = image.naturalHeight;
    if (!width || !height)
      throw new Error("The preview has no readable image dimensions.");
    const context = canvas.getContext("2d");
    if (!context)
      throw new Error(
        "Your browser could not prepare a saved copy. Please try again.",
      );
    let edge = Math.min(2048, Math.max(width, height));
    while (true) {
      const scale = Math.min(1, edge / Math.max(width, height));
      canvas.width = Math.max(1, Math.round(width * scale));
      canvas.height = Math.max(1, Math.round(height * scale));
      context.fillStyle = "#fff";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      for (const quality of [0.92, 0.85, 0.78]) {
        const copy = canvas.toDataURL("image/jpeg", quality);
        if (
          copy.startsWith("data:image/jpeg;base64,") &&
          imageBytes(copy) <= SAVED_LOOK_COPY_BYTES
        )
          return copy;
      }
      if (edge <= 256) break;
      edge = Math.max(256, Math.floor(edge * 0.75));
    }
    throw new Error(
      "This preview could not be made small enough to save. Please try again.",
    );
  } finally {
    image.onload = null;
    image.onerror = null;
    image.src = "";
    // Release the canvas backing store on mobile browsers.
    canvas.width = canvas.height = 1;
  }
}

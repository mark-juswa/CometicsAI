import test from "node:test";
import assert from "node:assert/strict";
import {
  needsSavedLookCopy,
  prepareSavedLookImage,
} from "../lib/business/saved-look-image";
import {
  MAX_SAVED_LOOK_BYTES,
  SAVED_LOOK_COPY_BYTES,
} from "../lib/business/saved-look-limits";

const data = (bytes: number, type = "png") =>
  `data:image/${type};base64,${Buffer.alloc(bytes).toString("base64")}`;
const large = data(MAX_SAVED_LOOK_BYTES + 1);
function browser({
  width = 4032,
  height = 3024,
  loadError = false,
  noContext = false,
  encode = () => data(1024, "jpeg"),
} = {}) {
  const oldDocument = Object.getOwnPropertyDescriptor(globalThis, "document"),
    oldImage = Object.getOwnPropertyDescriptor(globalThis, "Image");
  const draws: unknown[][] = [],
    qualities: number[] = [],
    fills: string[] = [];
  let source = "";
  class Preview {
    naturalWidth = width;
    naturalHeight = height;
    onload: (() => void) | null = null;
    onerror: (() => void) | null = null;
    set src(value: string) {
      source = value;
      if (value)
        queueMicrotask(() => (loadError ? this.onerror?.() : this.onload?.()));
    }
  }
  const ctx = {
    fillStyle: "",
    fillRect() {
      fills.push(this.fillStyle);
    },
    drawImage(...args: unknown[]) {
      draws.push(args);
    },
  };
  const canvas = {
    width: 0,
    height: 0,
    getContext: () => (noContext ? null : ctx),
    toDataURL: (type: string, quality: number) => {
      assert.equal(type, "image/jpeg");
      qualities.push(quality);
      return encode();
    },
  };
  Object.defineProperty(globalThis, "document", {
    configurable: true,
    value: {
      createElement: (tag: string) => {
        assert.equal(tag, "canvas");
        return canvas;
      },
    },
  });
  Object.defineProperty(globalThis, "Image", {
    configurable: true,
    value: Preview,
  });
  return {
    draws,
    qualities,
    fills,
    canvas,
    source: () => source,
    restore() {
      if (oldDocument)
        Object.defineProperty(globalThis, "document", oldDocument);
      else Reflect.deleteProperty(globalThis, "document");
      if (oldImage) Object.defineProperty(globalThis, "Image", oldImage);
      else Reflect.deleteProperty(globalThis, "Image");
    },
  };
}

test("byte boundary includes base64 padding and leaves accepted PNG/JPEG originals untouched", async () => {
  assert.equal(needsSavedLookCopy(data(MAX_SAVED_LOOK_BYTES)), false);
  assert.equal(needsSavedLookCopy(large), true);
  for (const type of ["png", "jpeg"])
    for (const bytes of [1, 2, 3, 1024, MAX_SAVED_LOOK_BYTES]) {
      const original = data(bytes, type);
      assert.equal(await prepareSavedLookImage(original), original);
    }
});
test("oversized preview gets a bounded saved copy, proportional dimensions, white alpha background and cleanup", async () => {
  const env = browser();
  try {
    const copy = await prepareSavedLookImage(large);
    assert.equal(copy, data(1024, "jpeg"));
    assert.deepEqual(env.draws[0].slice(1), [0, 0, 2048, 1536]);
    assert.deepEqual(env.fills, ["#fff"]);
    assert.deepEqual(env.qualities, [0.92]);
    assert.equal(env.canvas.width, 1);
    assert.equal(env.canvas.height, 1);
    assert.equal(env.source(), "");
    assert.equal(needsSavedLookCopy(large), true);
  } finally {
    env.restore();
  }
});
test("save copy lowers quality then dimensions until its encoded byte size fits", async () => {
  const oversized = data(SAVED_LOOK_COPY_BYTES + 1, "jpeg");
  let tries = 0;
  const env = browser({
    encode: () =>
      ++tries < 4 ? oversized : data(SAVED_LOOK_COPY_BYTES, "jpeg"),
  });
  try {
    assert.equal(
      await prepareSavedLookImage(large),
      data(SAVED_LOOK_COPY_BYTES, "jpeg"),
    );
    assert.deepEqual(env.qualities, [0.92, 0.85, 0.78, 0.92]);
    assert.deepEqual(env.draws[1].slice(1), [0, 0, 1536, 1152]);
  } finally {
    env.restore();
  }
});
test("small dimensions with large metadata still get an encoding attempt", async () => {
  const env = browser({ width: 128, height: 64 });
  try {
    await prepareSavedLookImage(large);
    assert.deepEqual(env.draws[0].slice(1), [0, 0, 128, 64]);
  } finally {
    env.restore();
  }
});
test("decode/context/encoding failures fail clearly and release mobile canvas memory", async () => {
  for (const options of [
    { loadError: true },
    { noContext: true },
    { encode: () => "data:image/png;base64,AAAA" },
  ]) {
    const env = browser(options);
    try {
      await assert.rejects(prepareSavedLookImage(large), /preview|saved copy/);
      assert.equal(env.canvas.width, 1);
      assert.equal(env.source(), "");
      assert.ok(env.qualities.length <= 27);
    } finally {
      env.restore();
    }
  }
});

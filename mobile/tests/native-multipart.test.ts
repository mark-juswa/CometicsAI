import test from 'node:test';
import assert from 'node:assert/strict';
// Exercise this installed SDK's actual encoder, not a substitute implementation.
import { convertFormDataAsync } from 'expo/src/winter/fetch/convertFormData';

function nativeForm(value: unknown) {
  return { entries: () => [['image', value], ['style_id', 'crew_cut']][Symbol.iterator]() } as unknown as FormData;
}
test('SDK 57 rejects the old URI descriptor before transport, but encodes a File blob and style correctly', async () => {
  await assert.rejects(convertFormDataAsync(nativeForm({ uri: 'file:///private/photo.jpg', name: 'photo.jpg', type: 'image/jpeg' })), /Unsupported FormDataPart/);
  // File's documented bytes() interface; no real device or photo is accessed.
  const image = new Uint8Array([255, 216, 255, 217]);
  const file = { name: 'local-cache.jpg', type: 'image/jpeg', bytes: async () => image };
  const { body, boundary } = await convertFormDataAsync(nativeForm(file), 'test-boundary');
  const wire = new TextDecoder('latin1').decode(body);
  assert.equal(boundary, 'test-boundary');
  assert.match(wire, /name="image"; filename="local-cache.jpg"/);
  assert.match(wire, /content-type: image\/jpeg/);
  assert.match(wire, /name="style_id"\r\n\r\ncrew_cut/);
  assert.deepEqual(body.slice(wire.indexOf('\r\n\r\n') + 4, wire.indexOf('\r\n\r\n') + 8), image);
});

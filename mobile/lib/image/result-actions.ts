import { File, Paths } from 'expo-file-system';
import { StorageAccessFramework, writeAsStringAsync, deleteAsync, EncodingType } from 'expo-file-system/legacy';
// Expo Go 57 includes the legacy native module, but not ExpoMediaLibraryNext.
import { saveToLibraryAsync, requestPermissionsAsync } from 'expo-media-library/legacy';
import * as Sharing from 'expo-sharing';
import { Platform } from 'react-native';
import type { GenerationResult } from '../api/contracts';

export class PhotoPermissionError extends Error {
  constructor(public readonly canAskAgain: boolean) { super('Saving requires permission to add this result to your photos. Your result has not been saved.'); }
}
async function withResultFile(result: GenerationResult, action: (file: File) => Promise<void>) {
  if (Platform.OS === 'web') throw new Error('Use the Android app to Save or Share this result.');
  const file = new File(Paths.cache, `beautycore-${Date.now()}-${Math.random().toString(36).slice(2)}.${result.image.content_type === 'image/png' ? 'png' : 'jpg'}`);
  try {
    file.create(); file.write(result.image.data_url.split(',')[1], { encoding: 'base64' });
    await action(file);
  } finally { if (file.exists) file.delete(); }
}
export async function shareResult(result: GenerationResult) {
  if (!await Sharing.isAvailableAsync()) throw new Error('Sharing is unavailable on this device. Your result is still available.');
  await withResultFile(result, file => Sharing.shareAsync(file.uri, { mimeType: result.image.content_type, dialogTitle: 'Share your BeautyCore look', UTI: result.image.content_type === 'image/png' ? 'public.png' : 'public.jpeg' }));
}
export async function saveResult(result: GenerationResult) {
  if (Platform.OS === 'android') {
    // The Expo Go legacy media saver requests broad read access. Use Android's
    // system folder chooser instead: a grant only to the user's chosen folder.
    const permission = await StorageAccessFramework.requestDirectoryPermissionsAsync();
    if (!permission.granted) return false;
    const name = `BeautyCore-${Date.now()}.${result.image.content_type === 'image/png' ? 'png' : 'jpg'}`;
    const uri = await StorageAccessFramework.createFileAsync(permission.directoryUri, name, result.image.content_type);
    try {
      await writeAsStringAsync(uri, result.image.data_url.split(',')[1], { encoding: EncodingType.Base64 });
    } catch (error) {
      // Remove only the new, incomplete file this Save action created.
      await deleteAsync(uri, { idempotent: true }).catch(() => {});
      throw error;
    }
    return true;
  }
  if (Platform.OS === 'ios') {
    const permission = await requestPermissionsAsync(true, ['photo']);
    if (!permission.granted) throw new PhotoPermissionError(permission.canAskAgain);
  }
  await withResultFile(result, async file => { await saveToLibraryAsync(file.uri); });
  return true;
}

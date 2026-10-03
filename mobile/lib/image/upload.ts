import { Platform } from 'react-native';
import { File } from 'expo-file-system';
import { validatePhoto, type LocalPhoto } from './validation';

export async function generationUpload(photo: LocalPhoto, styleId: string): Promise<FormData> {
  validatePhoto(photo);
  const body = new FormData();
  if (Platform.OS === 'web') {
    const response = await fetch(photo.uri);
    if (!response.ok) throw new Error('Your selected photo is no longer available. Choose it again.');
    body.append('image', await response.blob(), photo.name);
  } else {
    // SDK 57 installs Expo fetch globally. Its multipart encoder accepts File
    // blobs, but rejects React Native's older { uri, name, type } descriptor.
    const file = new File(photo.uri);
    if (!file.exists) throw new Error('Your selected photo is no longer available. Choose it again.');
    body.append('image', file);
  }
  body.append('style_id', styleId);
  return body;
}

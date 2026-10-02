import * as ImagePicker from 'expo-image-picker';
import { File } from 'expo-file-system';
import { Platform } from 'react-native';
import { validatePhoto, type LocalPhoto } from './validation';

async function fromAsset(asset: ImagePicker.ImagePickerAsset): Promise<LocalPhoto> {
  const size = asset.fileSize ?? asset.file?.size ?? (Platform.OS === 'web' ? 0 : new File(asset.uri).size);
  return validatePhoto({ uri: asset.uri, name: asset.fileName, mimeType: asset.mimeType ?? asset.file?.type,
    width: asset.width, height: asset.height, size });
}
export async function pickPhoto(): Promise<LocalPhoto | null> {
  // Android's system photo picker grants access only to the selected image. No broad gallery permission.
  const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], allowsEditing: false, quality: 1, allowsMultipleSelection: false });
  if (result.canceled) return null;
  if (!result.assets[0]) throw new Error('No photo was returned. Choose another photo.');
  return fromAsset(result.assets[0]);
}
export async function recoverPhoto(): Promise<LocalPhoto | null> {
  if (Platform.OS !== 'android') return null;
  const result = await ImagePicker.getPendingResultAsync();
  if (!result) return null;
  if ('code' in result) throw new Error('Photo selection was interrupted. Please choose your photo again.');
  return result.canceled || !result.assets[0] ? null : fromAsset(result.assets[0]);
}

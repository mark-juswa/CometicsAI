export type LocalPhoto = { uri: string; name: string; mimeType: 'image/jpeg' | 'image/png'; width: number; height: number; size: number };
export type PhotoInput = { uri: string; name?: string | null; mimeType?: string | null; width: number; height: number; size: number };
export function validatePhoto(photo: PhotoInput): LocalPhoto {
  if (!['image/jpeg', 'image/png'].includes(photo.mimeType ?? '')) throw new Error('Choose a JPG or PNG photo. Other image formats are not supported.');
  if (!Number.isFinite(photo.size) || photo.size <= 0) throw new Error('This photo is empty or its size could not be read. Choose another photo.');
  if (photo.size > 8 * 1024 * 1024) throw new Error('Image must be 8 MB or smaller.');
  if (![photo.width, photo.height].every(value => Number.isInteger(value) && value >= 64 && value <= 4096) || photo.width * photo.height > 16_777_216) {
    throw new Error('Image width and height must each be between 64 and 4096 pixels.');
  }
  return { ...photo, name: photo.name || 'Selected photo', mimeType: photo.mimeType as LocalPhoto['mimeType'] };
}

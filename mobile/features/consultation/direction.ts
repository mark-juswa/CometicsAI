// Actual vocabulary and limits from BeautyCore's Consultation Direction fields.
export const occasions = ['Everyday', 'Celebration', 'Formal'];
export const vibes = ['Natural', 'Classic', 'Bold'];
export const preferenceOptions = {
  hairstyle: { label: 'Maintenance preference', choices: ['Low', 'Medium', 'High'] },
  makeup: { label: 'Makeup intensity', choices: ['Natural', 'Soft', 'Bold'] },
  nails: { label: 'Nail finish', choices: ['Glossy', 'Matte', 'Ombre', 'French'] },
};
export function consultationPreferences(feature: import('../../lib/api/contracts').FeatureId, direction: import('../../store/consultation').Direction): import('../../lib/api/consultation-contracts').Preferences {
  const preferences: import('../../lib/api/consultation-contracts').Preferences = {
    occasion: direction.occasion.trim() || undefined, vibe: direction.vibe.trim() || undefined,
    avoids: direction.avoids.split(',').map(v => v.trim()).filter(Boolean).slice(0, 5), notes: direction.notes.trim() || undefined,
  };
  const value = direction.servicePreference.toLowerCase();
  if (feature === 'hairstyle' && ['low', 'medium', 'high'].includes(value)) preferences.hair_maintenance = value as 'low' | 'medium' | 'high';
  if (feature === 'makeup' && ['natural', 'soft', 'bold'].includes(value)) preferences.makeup_intensity = value as 'natural' | 'soft' | 'bold';
  if (feature === 'nails' && ['glossy', 'matte', 'ombre', 'french'].includes(value)) preferences.nail_finish = value as 'glossy' | 'matte' | 'ombre' | 'french';
  return preferences;
}

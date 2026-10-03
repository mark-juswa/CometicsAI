import { Platform } from 'react-native';

// Translated from the existing ai-studio.css; native sizing preserves its hierarchy.
export const colors = {
  deep: '#0f0520', card: '#1a0a2e', surface: '#2d1054', purple: '#b040d8',
  gold: '#f0a800', goldLight: '#f5c040', secondary: '#e0c8f0', muted: '#ae91c4',
  white: '#ffffff', ink: '#1b0a28', border: '#72458a', photo: '#170c27',
  selected: '#54256f', error: '#ffd6cf', errorSurface: '#3a172b', success: '#6fcf97',
  tones: ['#743c83', '#ac6b8b', '#6e6daa', '#bb7860', '#9c588f'],
};
export const spacing = { xs: 6, sm: 12, md: 16, lg: 24, xl: 32, hero: 40 };
export const type = { small: 12, body: 15, button: 13, panel: 25, hero: 40, brand: 18 };
export const serif = Platform.select({ ios: 'Georgia', web: 'Georgia', default: 'serif' });
// Compact mobile equivalents of the web's editorial cards and action bar.
export const layout = { maxWidth: 720, touch: 48, previewMin: 180, previewMax: 280, radius: 12 };
export const compactType = { heading: 30, headingLine: 36, stage: 22, glyph: 24 };

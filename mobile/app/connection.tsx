import { Redirect } from 'expo-router';
// Preserve the existing diagnostic deep link after relocating it to Settings.
export default function Connection() { return <Redirect href="/settings" />; }

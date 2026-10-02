import { useQuery } from '@tanstack/react-query';
import { api } from './client';
import type { FeatureId } from './contracts';

export function useHealth() {
  return useQuery({ queryKey: ['health'], queryFn: ({ signal }) => api.health(signal), staleTime: 0 });
}
export function useFeatures() {
  return useQuery({ queryKey: ['features'], queryFn: ({ signal }) => api.features(signal), staleTime: 60_000 });
}
export function useStyles(feature: FeatureId) {
  return useQuery({ queryKey: ['styles', feature], queryFn: ({ signal }) => api.styles(feature, signal), staleTime: 60_000 });
}

// ==========================================================================
// API client stub.
//
// In this phase every request is served from local mock data with a
// simulated network delay. The shape of these functions mirrors what a
// real FastAPI backend will expose, so swapping the implementation later
// only requires changing the function bodies below (e.g. using `fetch`
// against BASE_URL) — callers in pages/components do not need to change.
// ==========================================================================

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const MOCK_LATENCY_MS = 350;

export function delay<T>(value: T, ms: number = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

// Placeholder for future real requests, e.g.:
// export async function apiGet<T>(path: string): Promise<T> {
//   const res = await fetch(`${BASE_URL}${path}`);
//   if (!res.ok) throw new Error(`API error ${res.status}`);
//   return res.json();
// }

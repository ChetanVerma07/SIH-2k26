// ==========================================================================
// Shared HTTP client for the canonical FastAPI backend.
// ==========================================================================

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

export const BASE_URL = configuredBaseUrl || '';
export const USE_MOCK_API =
  import.meta.env.VITE_USE_MOCK_API === 'true' ||
  import.meta.env.MODE === 'test' ||
  (import.meta.env.PROD && !configuredBaseUrl);

export const MOCK_LATENCY_MS = 350;

export function delay<T>(value: T, ms: number = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error((await response.text()) || `API request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'GET' });
}

export function apiPost<T>(path: string, payload: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

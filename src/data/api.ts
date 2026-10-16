// Keep the same loopback hostname so browser mutations remain same-site.
const BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? `http://${window.location.hostname}:8000`

export function apiUrl(path: string): string {
  return `${BASE}${path}`
}

export async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

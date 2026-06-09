import type {
  BenchmarkResponse,
  SearchParams,
  SearchResponse,
  StatsResponse,
} from "./types";

const BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

async function toError(res: Response): Promise<Error> {
  let detail = res.statusText;
  try {
    const body = await res.json();
    detail = body.detail ?? detail;
  } catch {
    /* non-JSON body */
  }
  return new Error(`${res.status}: ${detail}`);
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await toError(res);
  return (await res.json()) as T;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw await toError(res);
  return (await res.json()) as T;
}

export const api = {
  baseUrl: BASE_URL,
  search: (params: SearchParams) => postJson<SearchResponse>("/search", params),
  stats: () => getJson<StatsResponse>("/stats"),
  benchmark: (n_queries = 20) =>
    postJson<BenchmarkResponse>("/benchmark", { n_queries }),
  health: () => getJson<{ status: string }>("/health"),
};

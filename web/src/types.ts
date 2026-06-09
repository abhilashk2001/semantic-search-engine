export interface SearchParams {
  query?: string;
  vector?: number[];
  k?: number;
  ef_search?: number;
}

export interface SearchResultItem {
  id: number;
  text: string | null;
  score: number;
}

export interface SearchResponse {
  results: SearchResultItem[];
  latency_ms: number;
  k: number;
  ef_search: number;
}

export interface StatsResponse {
  node_count: number;
  layer_distribution: Record<string, number>;
  build_time_ms: number | null;
  config: { M: number; ef_construction: number; metric: string; dim: number };
}

export interface BenchmarkResponse {
  recall_at_k: number;
  k: number;
  n_queries: number;
  sample_latency_ms: number;
}

export interface BenchmarkPoint {
  ef_search: number;
  recall_at_10: number;
  p50_latency_ms: number;
}

export interface BenchmarkResults {
  dataset: string;
  n: number;
  dim: number;
  metric: string;
  k: number;
  sweep: BenchmarkPoint[];
  generated_at: string;
}
